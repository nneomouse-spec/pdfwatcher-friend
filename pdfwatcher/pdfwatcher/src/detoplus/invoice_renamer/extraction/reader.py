"""PDF text extraction with LRU cache.

One canonical way to extract text from PDFs. The cache is keyed by
(path, size, mtime) so re-scanning unchanged files hits the cache.
Thread-safe for use from watcher background threads.
"""

from __future__ import annotations

import os
import threading
from typing import Optional

import fitz  # PyMuPDF

from .constants import PDF_CACHE_MAX_ENTRIES

_CACHE: dict[tuple, str] = {}
_CACHE_LOCK = threading.Lock()


def extract_text(path: str) -> str:
    """Extract full text from a PDF file, cached by (path, size, mtime).

    Returns empty string on any error.
    """
    key: Optional[tuple] = None
    try:
        st = os.stat(path)
        key = (os.path.abspath(path), st.st_size, st.st_mtime)
    except OSError:
        pass

    if key is not None:
        with _CACHE_LOCK:
            cached = _CACHE.get(key)
        if cached is not None:
            return cached

    try:
        doc = fitz.open(path)
    except Exception:
        return ""

    try:
        text = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()

    if key is not None:
        with _CACHE_LOCK:
            if len(_CACHE) > PDF_CACHE_MAX_ENTRIES:
                _CACHE.clear()
            _CACHE[key] = text

    return text


def clear_cache() -> None:
    """Clear the PDF text cache (useful in tests)."""
    with _CACHE_LOCK:
        _CACHE.clear()
