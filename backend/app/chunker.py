"""
CodEx Chunker — splits source code files into overlapping chunks for embedding.
"""

import re
from app.config import CHUNK_SIZE, CHUNK_OVERLAP
from app.utils import detect_language


def chunk_code(content: str, file_path: str) -> list[dict]:
    """
    Split file content into overlapping chunks with metadata.

    Each chunk is a dict with:
        - text: the chunk content
        - file_path: originating file path
        - file_name: just the filename
        - language: detected programming language
        - chunk_index: position index within the file
    """
    if not content or not content.strip():
        return []

    file_name = file_path.split("/")[-1] if "/" in file_path else file_path.split("\\")[-1]
    language = detect_language(file_path)

    chunks = _smart_chunk(content, CHUNK_SIZE, CHUNK_OVERLAP)

    results = []
    for i, chunk_text in enumerate(chunks):
        if chunk_text.strip():
            results.append({
                "text": chunk_text,
                "file_path": file_path,
                "file_name": file_name,
                "language": language,
                "chunk_index": i,
            })

    return results


def _smart_chunk(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into chunks, trying to break on natural code boundaries.

    Priority for split points:
    1. Class definitions
    2. Function definitions
    3. Blank lines
    4. Any line boundary
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunks.append(text[start:])
            break

        # Try to find a good break point near the end of the chunk
        segment = text[start:end]

        # Look for natural split points in the last 30% of the chunk
        search_start = int(len(segment) * 0.7)
        search_region = segment[search_start:]

        best_break = None

        # Priority 1: Class or function definition
        pattern = re.compile(r'\n(?=\s*(?:class |def |function |public |private |protected |async ))', re.MULTILINE)
        matches = list(pattern.finditer(search_region))
        if matches:
            best_break = search_start + matches[-1].start() + 1  # +1 to keep newline

        # Priority 2: Blank line
        if best_break is None:
            blank_matches = list(re.finditer(r'\n\s*\n', search_region))
            if blank_matches:
                best_break = search_start + blank_matches[-1].start() + 1

        # Priority 3: Any newline
        if best_break is None:
            newline_pos = search_region.rfind('\n')
            if newline_pos != -1:
                best_break = search_start + newline_pos + 1

        if best_break is not None:
            actual_end = start + best_break
        else:
            actual_end = end

        chunks.append(text[start:actual_end])
        start = actual_end - overlap

    return chunks


def chunk_file_contents(files: list[dict]) -> list[dict]:
    """
    Process a list of file dicts (with 'path' and 'content' keys)
    into a flat list of chunk dicts.
    """
    all_chunks = []
    for f in files:
        file_chunks = chunk_code(f["content"], f["path"])
        all_chunks.extend(file_chunks)
    return all_chunks
