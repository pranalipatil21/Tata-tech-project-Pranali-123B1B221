"""Utility helper functions for hashing, sanitization, and text processing."""
import hashlib
import re
from datetime import datetime
from pathlib import Path

def compute_file_hash(filepath_or_bytes) -> str:
    """Compute SHA-256 hash of a file or byte stream for duplicate prevention."""
    hasher = hashlib.sha256()
    if isinstance(filepath_or_bytes, (str, Path)):
        with open(filepath_or_bytes, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
    else:
        hasher.update(filepath_or_bytes)
    return hasher.hexdigest()

def clean_text(text: str) -> str:
    """Normalize extracted text by cleaning excessive whitespaces and non-printable chars."""
    if not text:
        return ""
    # Replace non-breaking spaces and exotic whitespace
    text = text.replace("\u00a0", " ").replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple spaces with single space
    text = re.sub(r"[ \t]+", " ", text)
    # Replace more than two newlines with two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from uploaded filenames."""
    filename = Path(filename).name
    return re.sub(r"[^\w\-_\. ]", "_", filename)

def get_iso_timestamp() -> str:
    """Return formatted ISO timestamp string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def truncate_text(text: str, max_chars: int = 150) -> str:
    """Truncate text cleanly with ellipsis."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."
