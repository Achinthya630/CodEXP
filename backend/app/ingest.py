"""
CodEx Ingest — repository cloning, processing, and embedding pipeline.
"""

import asyncio
import hashlib
import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from git import Repo as GitRepo

from app.auth import get_current_user
from app.models import User

from app.config import CLONE_DIR
from app.utils import (
    extract_repo_name,
    sanitize_collection_name,
    should_ignore_path,
    should_ignore_file,
    is_text_file,
)
from app.chunker import chunk_file_contents
from app.embeddings import embed_texts
from app.chroma_client import (
    upsert_chunks,
    get_or_create_collection,
    delete_collection,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Track ingestion status per repo
_ingestion_status: dict[str, dict] = {}


class IngestRequest(BaseModel):
    repo_url: str


class IngestResponse(BaseModel):
    status: str
    repo_name: str
    files_processed: int
    chunks_created: int
    message: str


class IngestStatusResponse(BaseModel):
    status: str  # "pending" | "processing" | "completed" | "failed"
    progress: str
    repo_name: str


def _get_status_key(user_id: int, repo_name: str) -> str:
    return f"{user_id}:{repo_name}"


@router.post("/ingest", response_model=IngestResponse)
async def ingest_repository(request: IngestRequest, user: User = Depends(get_current_user)):
    """Clone a GitHub repository, chunk its code, embed, and store in ChromaDB."""

    # Parse repo URL
    try:
        repo_name = extract_repo_name(request.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sanitized_repo = sanitize_collection_name(repo_name)
    collection_name = f"user_{user.id}_{sanitized_repo}"
    status_key = _get_status_key(user.id, repo_name)

    # Check if already being ingested
    if status_key in _ingestion_status and _ingestion_status[status_key]["status"] == "processing":
        raise HTTPException(status_code=409, detail="Repository is already being ingested")

    _ingestion_status[status_key] = {
        "status": "processing",
        "progress": "Cloning repository...",
        "repo_name": repo_name,
    }

    clone_path = CLONE_DIR / collection_name

    try:
        # ── Step 1: Clone ────────────────────────────────────────────
        _ingestion_status[status_key]["progress"] = "Cloning repository..."
        logger.info(f"Cloning {request.repo_url} → {clone_path}")

        # Clean up any previous clone
        if clone_path.exists():
            shutil.rmtree(clone_path, ignore_errors=True)

        CLONE_DIR.mkdir(parents=True, exist_ok=True)

        await asyncio.to_thread(
            GitRepo.clone_from,
            request.repo_url,
            str(clone_path),
            depth=1,  # shallow clone for speed
        )

        # ── Step 2: Read Files ───────────────────────────────────────
        _ingestion_status[status_key]["progress"] = "Reading files..."
        logger.info("Reading repository files...")

        files = _read_repo_files(clone_path)
        logger.info(f"Found {len(files)} code files")

        if not files:
            raise HTTPException(
                status_code=400,
                detail="No valid code files found in the repository",
            )

        # ── Step 3: Chunk ────────────────────────────────────────────
        _ingestion_status[status_key]["progress"] = f"Chunking {len(files)} files..."
        logger.info("Chunking files...")

        all_chunks = chunk_file_contents(files)
        logger.info(f"Created {len(all_chunks)} chunks")

        if not all_chunks:
            raise HTTPException(
                status_code=400,
                detail="No content chunks could be generated",
            )

        # ── Step 4: Embed ────────────────────────────────────────────
        _ingestion_status[status_key]["progress"] = f"Generating embeddings for {len(all_chunks)} chunks..."
        logger.info("Generating embeddings...")

        texts = [c["text"] for c in all_chunks]
        embeddings = await embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

        # ── Step 5: Store in ChromaDB ────────────────────────────────
        _ingestion_status[status_key]["progress"] = "Storing in vector database..."
        logger.info("Storing in ChromaDB...")

        # Delete existing collection to re-ingest cleanly
        delete_collection(collection_name)

        ids = [
            hashlib.md5(
                f"{c['file_path']}:{c['chunk_index']}".encode()
            ).hexdigest()
            for c in all_chunks
        ]
        documents = texts
        metadatas = [
            {
                "file_path": c["file_path"],
                "file_name": c["file_name"],
                "language": c["language"],
                "chunk_index": c["chunk_index"],
                "repo_name": repo_name,
            }
            for c in all_chunks
        ]

        upsert_chunks(collection_name, ids, documents, embeddings, metadatas)

        # ── Done ─────────────────────────────────────────────────────
        _ingestion_status[status_key] = {
            "status": "completed",
            "progress": "Done!",
            "repo_name": repo_name,
        }

        return IngestResponse(
            status="success",
            repo_name=repo_name,
            files_processed=len(files),
            chunks_created=len(all_chunks),
            message="Repository ingested successfully",
        )

    except HTTPException:
        _ingestion_status[status_key] = {
            "status": "failed",
            "progress": "Failed",
            "repo_name": repo_name,
        }
        raise
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        _ingestion_status[status_key] = {
            "status": "failed",
            "progress": f"Error: {str(e)}",
            "repo_name": repo_name,
        }
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    finally:
        # Clean up cloned repo
        if clone_path.exists():
            shutil.rmtree(clone_path, ignore_errors=True)


@router.get("/ingest/status/{repo_name:path}", response_model=IngestStatusResponse)
async def get_ingestion_status(repo_name: str, user: User = Depends(get_current_user)):
    """Check the ingestion status of a repository."""
    status_key = _get_status_key(user.id, repo_name)
    if status_key not in _ingestion_status:
        raise HTTPException(status_code=404, detail="No ingestion found for this repo")
    return IngestStatusResponse(**_ingestion_status[status_key])


def _read_repo_files(repo_path: Path) -> list[dict]:
    """
    Recursively read all valid code files from a cloned repository.

    Returns list of dicts with 'path' (relative) and 'content' keys.
    """
    files = []

    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue

        if should_ignore_path(file_path, repo_path):
            continue

        if should_ignore_file(file_path):
            continue

        if not is_text_file(file_path):
            continue

        try:
            # Try reading as UTF-8, fall back to latin-1
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="latin-1")

            rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
            files.append({
                "path": rel_path,
                "content": content,
            })
        except Exception as e:
            logger.warning(f"Skipping file {file_path}: {e}")

    return files
