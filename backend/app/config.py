"""
CodEx Configuration — centralized settings for the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# ── Model Configuration ─────────────────────────────────────────────────────
EMBEDDING_MODEL: str = "gemini-embedding-001"
LLM_MODEL: str = "gemini-2.5-flash"

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent.parent
CLONE_DIR: Path = BASE_DIR / "temp_repos"
CHROMA_PERSIST_DIR: str = str(BASE_DIR / "chroma_data")

# ── Chunking ─────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = 2000        # ~500 tokens in characters
CHUNK_OVERLAP: int = 200      # overlap between consecutive chunks

# ── RAG ──────────────────────────────────────────────────────────────────────
TOP_K_RESULTS: int = 10       # number of chunks to retrieve per query

# ── Embedding Batching ───────────────────────────────────────────────────────
EMBEDDING_BATCH_SIZE: int = 50  # chunks per batch for embedding API calls

# ── Ignored Directories ─────────────────────────────────────────────────────
IGNORED_DIRS: set[str] = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".env", "build", "dist", ".next", ".nuxt", ".output",
    "target", "bin", "obj", ".idea", ".vscode", ".vs",
    "vendor", "coverage", ".tox", ".mypy_cache", ".pytest_cache",
    ".eggs", "*.egg-info", "migrations", ".terraform",
}

# ── Ignored File Extensions ──────────────────────────────────────────────────
IGNORED_EXTENSIONS: set[str] = {
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp", ".tiff",
    # Audio/Video
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv", ".flac", ".ogg",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".rar", ".7z", ".xz",
    # Binaries
    ".exe", ".dll", ".so", ".dylib", ".o", ".a", ".lib", ".pyc", ".pyo",
    ".class", ".jar", ".war",
    # Documents
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    # Data (large)
    ".sqlite", ".db", ".sqlite3",
    # Fonts
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    # Lock files
    ".lock",
    # Misc
    ".min.js", ".min.css", ".map",
}

# ── Max File Size (skip files larger than this) ──────────────────────────────
MAX_FILE_SIZE_BYTES: int = 500_000  # 500 KB
