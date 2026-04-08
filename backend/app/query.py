"""
CodEx Query — RAG pipeline for answering questions about a codebase.
"""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from google import genai

from app.config import GEMINI_API_KEY, LLM_MODEL, TOP_K_RESULTS
from app.utils import sanitize_collection_name
from app.embeddings import embed_query
from app.chroma_client import query_collection, get_or_create_collection

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy-initialized Gemini client
_llm_client: genai.Client | None = None

def _get_llm_client() -> genai.Client:
    global _llm_client
    if _llm_client is None:
        _llm_client = genai.Client(api_key=GEMINI_API_KEY)
    return _llm_client


# ── Prompt Template ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert software engineer analyzing a codebase.

Instructions:
- Answer clearly and concisely
- Base your answer ONLY on the provided context
- Mention relevant file names and functions when applicable
- Use markdown formatting for code blocks and structure
- If the answer is not found in the context, say: "Not enough information in the codebase to answer this question."
"""

def _build_context_prompt(chunks: list[dict], question: str) -> str:
    """Build the RAG prompt with retrieved context and user question."""
    context_parts = []
    for i, chunk in enumerate(chunks):
        file_path = chunk.get("file_path", "unknown")
        language = chunk.get("language", "")
        content = chunk.get("content", "")
        context_parts.append(
            f"--- File: {file_path} ({language}) ---\n{content}"
        )

    context = "\n\n".join(context_parts)

    return f"""Context from the codebase:

{context}

Question: {question}"""


# ── Request/Response Models ──────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    repo_name: str


class QueryResponse(BaseModel):
    answer: str
    referenced_files: list[str]
    chunks_used: int


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/query")
async def query_repository(request: QueryRequest):
    """
    RAG query endpoint. Embeds the question, retrieves relevant chunks,
    and streams the LLM answer via SSE.
    """
    collection_name = sanitize_collection_name(request.repo_name)

    # Verify collection exists and has data
    try:
        collection = get_or_create_collection(collection_name)
        count = collection.count()
        if count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{request.repo_name}' has not been ingested yet.",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Repository not found: {str(e)}")

    # ── Step 1: Embed the query ──────────────────────────────────────
    logger.info(f"Query: {request.question[:100]}...")
    query_embedding = await embed_query(request.question)

    # ── Step 2: Retrieve relevant chunks ─────────────────────────────
    results = query_collection(collection_name, query_embedding, n_results=TOP_K_RESULTS)

    if not results["documents"] or not results["documents"][0]:
        raise HTTPException(
            status_code=404,
            detail="No relevant code found for your question.",
        )

    # Build chunk data for context
    chunks = []
    referenced_files = set()
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({
            "content": doc,
            "file_path": meta.get("file_path", "unknown"),
            "language": meta.get("language", ""),
        })
        referenced_files.add(meta.get("file_path", "unknown"))

    # ── Step 3: Build prompt and stream response ─────────────────────
    prompt = _build_context_prompt(chunks, request.question)
    ref_files = sorted(referenced_files)

    return StreamingResponse(
        _stream_llm_response(prompt, ref_files, len(chunks)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_llm_response(
    prompt: str,
    referenced_files: list[str],
    chunks_used: int,
) -> AsyncGenerator[str, None]:
    """Stream LLM response as Server-Sent Events."""

    try:
        response = _get_llm_client().models.generate_content_stream(
            model=LLM_MODEL,
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.3,
                "max_output_tokens": 4096,
            },
        )

        for chunk in response:
            if chunk.text:
                data = json.dumps({"type": "chunk", "content": chunk.text})
                yield f"data: {data}\n\n"

        # Send completion event with metadata
        done_data = json.dumps({
            "type": "done",
            "referenced_files": referenced_files,
            "chunks_used": chunks_used,
        })
        yield f"data: {done_data}\n\n"

    except Exception as e:
        logger.error(f"LLM streaming error: {e}", exc_info=True)
        error_data = json.dumps({
            "type": "error",
            "content": f"Error generating response: {str(e)}",
        })
        yield f"data: {error_data}\n\n"


# ── Non-streaming fallback (optional) ────────────────────────────────────────

@router.post("/query/sync", response_model=QueryResponse)
async def query_repository_sync(request: QueryRequest):
    """Non-streaming version of the query endpoint."""

    collection_name = sanitize_collection_name(request.repo_name)

    try:
        collection = get_or_create_collection(collection_name)
        count = collection.count()
        if count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{request.repo_name}' has not been ingested yet.",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Repository not found: {str(e)}")

    query_embedding = await embed_query(request.question)
    results = query_collection(collection_name, query_embedding, n_results=TOP_K_RESULTS)

    if not results["documents"] or not results["documents"][0]:
        raise HTTPException(status_code=404, detail="No relevant code found.")

    chunks = []
    referenced_files = set()
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({
            "content": doc,
            "file_path": meta.get("file_path", "unknown"),
            "language": meta.get("language", ""),
        })
        referenced_files.add(meta.get("file_path", "unknown"))

    prompt = _build_context_prompt(chunks, request.question)

    response = _get_llm_client().models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "temperature": 0.3,
            "max_output_tokens": 4096,
        },
    )

    return QueryResponse(
        answer=response.text,
        referenced_files=sorted(referenced_files),
        chunks_used=len(chunks),
    )
