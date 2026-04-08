"""
CodEx Backend — FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.chroma_client import get_client, list_collections, get_or_create_collection
from app.config import GEMINI_API_KEY
from app.ingest import router as ingest_router
from app.query import router as query_router

# ── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("🚀 CodEx Backend starting up...")

    if not GEMINI_API_KEY:
        logger.error("❌ GEMINI_API_KEY is not set! Please set it in .env file.")
    else:
        logger.info("✅ Gemini API key loaded")

    # Initialize ChromaDB
    get_client()
    logger.info("✅ ChromaDB initialized")

    collections = list_collections()
    logger.info(f"📚 Found {len(collections)} existing collection(s)")

    yield

    # Shutdown
    logger.info("👋 CodEx Backend shutting down...")


# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="CodEx API",
    description="GitHub Repository RAG Analyzer — Ask questions about any codebase",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(ingest_router, tags=["Ingestion"])
app.include_router(query_router, tags=["Query"])


# ── Health & Info Endpoints ──────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    timestamp: str


class RepoInfo(BaseModel):
    name: str
    chunks: int


class ReposResponse(BaseModel):
    repos: list[RepoInfo]


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/repos", response_model=ReposResponse)
async def list_repos():
    """List all ingested repositories."""
    collections = list_collections()
    repos = []
    for name in collections:
        try:
            col = get_or_create_collection(name)
            count = col.count()
            # Try to recover original repo name from collection metadata
            display_name = name.replace("_", "/", 1)
            repos.append(RepoInfo(name=display_name, chunks=count))
        except Exception:
            repos.append(RepoInfo(name=name, chunks=0))

    return ReposResponse(repos=repos)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
