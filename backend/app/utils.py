"""
CodEx Utilities — shared helpers used across the application.
"""

import re
from pathlib import Path
from app.config import IGNORED_DIRS, IGNORED_EXTENSIONS, MAX_FILE_SIZE_BYTES


# ── Language Detection ───────────────────────────────────────────────────────

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (JSX)",
    ".ts": "TypeScript", ".tsx": "TypeScript (TSX)",
    ".java": "Java", ".kt": "Kotlin", ".scala": "Scala",
    ".c": "C", ".cpp": "C++", ".cc": "C++", ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".swift": "Swift", ".m": "Objective-C",
    ".r": "R", ".R": "R",
    ".lua": "Lua", ".pl": "Perl", ".pm": "Perl",
    ".sh": "Shell", ".bash": "Bash", ".zsh": "Zsh", ".fish": "Fish",
    ".ps1": "PowerShell", ".bat": "Batch", ".cmd": "Batch",
    ".sql": "SQL",
    ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".sass": "Sass", ".less": "Less",
    ".xml": "XML", ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML", ".ini": "INI", ".cfg": "Config",
    ".md": "Markdown", ".rst": "reStructuredText", ".txt": "Text",
    ".dockerfile": "Dockerfile", ".tf": "Terraform", ".hcl": "HCL",
    ".proto": "Protocol Buffers", ".graphql": "GraphQL", ".gql": "GraphQL",
    ".vue": "Vue", ".svelte": "Svelte",
    ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir",
    ".erl": "Erlang", ".hs": "Haskell", ".ml": "OCaml",
    ".clj": "Clojure", ".lisp": "Lisp", ".el": "Emacs Lisp",
    ".zig": "Zig", ".nim": "Nim", ".v": "V",
    ".makefile": "Makefile",
}

# Files with no extension but known names
SPECIAL_FILE_NAMES: dict[str, str] = {
    "Dockerfile": "Dockerfile", "Makefile": "Makefile",
    "Vagrantfile": "Ruby", "Gemfile": "Ruby",
    "Rakefile": "Ruby", "Procfile": "Procfile",
    ".gitignore": "Git Config", ".dockerignore": "Docker Config",
    ".env": "Environment", ".editorconfig": "EditorConfig",
    "CMakeLists.txt": "CMake",
}


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension or name."""
    name = Path(file_path).name
    if name in SPECIAL_FILE_NAMES:
        return SPECIAL_FILE_NAMES[name]

    ext = Path(file_path).suffix.lower()
    return EXTENSION_LANGUAGE_MAP.get(ext, "Unknown")


# ── Repo URL Parsing ─────────────────────────────────────────────────────────

def extract_repo_name(repo_url: str) -> str:
    """
    Extract 'owner/repo' from a GitHub URL.
    Supports: https://github.com/owner/repo[.git]
    """
    pattern = r"github\.com[/:]([^/]+)/([^/.]+?)(?:\.git)?$"
    match = re.search(pattern, repo_url.strip().rstrip("/"))
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    raise ValueError(f"Invalid GitHub URL: {repo_url}")


def sanitize_collection_name(repo_name: str) -> str:
    """
    Convert repo name to a valid ChromaDB collection name.
    ChromaDB requires: 3-63 chars, starts/ends with alphanumeric,
    only alphanumeric, underscores, hyphens.
    """
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", repo_name)
    name = name.strip("_-")
    if len(name) < 3:
        name = name + "_col"
    if len(name) > 63:
        name = name[:63].rstrip("_-")
    return name


# ── File Filtering ───────────────────────────────────────────────────────────

def should_ignore_path(path: Path, base_dir: Path) -> bool:
    """Check if a path should be ignored during ingestion."""
    rel = path.relative_to(base_dir)
    parts = rel.parts

    # Check if any directory component is in the ignored set
    for part in parts:
        if part in IGNORED_DIRS:
            return True
        # Handle glob-style patterns like *.egg-info
        for pattern in IGNORED_DIRS:
            if "*" in pattern and Path(part).match(pattern):
                return True

    return False


def should_ignore_file(file_path: Path) -> bool:
    """Check if a file should be skipped based on extension and size."""
    ext = file_path.suffix.lower()
    if ext in IGNORED_EXTENSIONS:
        return True

    # Skip very large files
    try:
        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return True
    except OSError:
        return True

    return False


def is_text_file(file_path: Path) -> bool:
    """Heuristic check if a file is likely text (not binary)."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
            if b"\x00" in chunk:
                return False
            return True
    except (OSError, PermissionError):
        return False
