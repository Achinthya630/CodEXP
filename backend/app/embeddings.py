"""
CodEx Embeddings — wrapper around Gemini embedding API with batching.
"""

import asyncio
import logging
from google import genai
from app.config import GEMINI_API_KEY, EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE

logger = logging.getLogger(__name__)

# Lazy-initialized Gemini client
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


async def embed_texts(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    """
    Generate embeddings for a list of texts using Gemini, in batches.

    Args:
        texts: List of text strings to embed.
        task_type: "RETRIEVAL_DOCUMENT" for indexing, "RETRIEVAL_QUERY" for searching.

    Returns:
        List of embedding vectors (list of floats).
    """
    if not texts:
        return []

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]
        logger.info(f"Embedding batch {i // EMBEDDING_BATCH_SIZE + 1} "
                     f"({len(batch)} texts)")

        retries = 3
        for attempt in range(retries):
            try:
                result = await asyncio.to_thread(
                    _get_client().models.embed_content,
                    model=EMBEDDING_MODEL,
                    contents=batch,
                    config={
                        "task_type": task_type,
                    }
                )
                batch_embeddings = [e.values for e in result.embeddings]
                all_embeddings.extend(batch_embeddings)
                break
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    wait_time = 2 ** attempt * 5
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif attempt == retries - 1:
                    logger.error(f"Embedding failed after {retries} retries: {e}")
                    raise
                else:
                    logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(2)

    return all_embeddings


async def embed_query(text: str) -> list[float]:
    """Embed a single query string for retrieval."""
    results = await embed_texts([text], task_type="RETRIEVAL_QUERY")
    return results[0]
