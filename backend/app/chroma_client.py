"""
CodEx ChromaDB Client — manages vector database collections.
"""

import logging
import chromadb
from app.config import CHROMA_PERSIST_DIR

logger = logging.getLogger(__name__)

# Singleton ChromaDB client
_client: chromadb.ClientAPI | None = None


def get_client() -> chromadb.ClientAPI:
    """Get or create the persistent ChromaDB client."""
    global _client
    if _client is None:
        logger.info(f"Initializing ChromaDB at: {CHROMA_PERSIST_DIR}")
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _client


def get_or_create_collection(collection_name: str) -> chromadb.Collection:
    """Get or create a ChromaDB collection by name."""
    client = get_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},     # cosine similarity
    )


def delete_collection(collection_name: str) -> bool:
    """Delete a ChromaDB collection. Returns True if deleted."""
    client = get_client()
    try:
        client.delete_collection(name=collection_name)
        logger.info(f"Deleted collection: {collection_name}")
        return True
    except Exception:
        return False


def list_collections() -> list[str]:
    """List all collection names in ChromaDB."""
    client = get_client()
    return [c.name for c in client.list_collections()]


def upsert_chunks(
    collection_name: str,
    ids: list[str],
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
) -> None:
    """
    Upsert document chunks with their embeddings into a collection.
    Handles ChromaDB's batch size limits by splitting into sub-batches.
    """
    collection = get_or_create_collection(collection_name)

    # ChromaDB recommends batches of ~5000
    batch_size = 5000
    for i in range(0, len(ids), batch_size):
        end = i + batch_size
        collection.upsert(
            ids=ids[i:end],
            documents=documents[i:end],
            embeddings=embeddings[i:end],
            metadatas=metadatas[i:end],
        )
    logger.info(f"Upserted {len(ids)} chunks into '{collection_name}'")


def query_collection(
    collection_name: str,
    query_embedding: list[float],
    n_results: int = 10,
) -> dict:
    """
    Query a collection for similar chunks.

    Returns dict with keys: ids, documents, metadatas, distances
    """
    collection = get_or_create_collection(collection_name)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    return results
