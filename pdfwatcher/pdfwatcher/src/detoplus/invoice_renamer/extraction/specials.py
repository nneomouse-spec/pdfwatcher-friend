"""Special suffix detection — single canonical implementation.

Detects Redispatch, Storno, Korrektur, Korrekturnote markers in PDF text.
"Gutschrift" (credit note) is explicitly NOT appended to filenames
per business rules — only Storno/Redispatch/Korrekturnote trigger a suffix.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Optional


class SpecialSuffix(StrEnum):
    REDISPATCH = "Redispatch"
    STORNO = "Storno"
    KORREKTUR = "Korrektur"
    KORREKTURNOTE = "Korrekturnote"


# Priority order: Redispatch > Korrektur > Storno
# (if multiple keywords present, the first match wins)
_DETECTION_RULES: list[tuple[SpecialSuffix, list[str]]] = [
    (SpecialSuffix.REDISPATCH, ["redispatch"]),
    (SpecialSuffix.KORREKTURNOTE, ["korrekturnote", "korrekturrechnung", "korrektur", "korrigiert"]),
    (SpecialSuffix.STORNO, ["storno", "stornorechnung", "stornierung"]),
]


def detect_special_suffix(text: str) -> Optional[SpecialSuffix]:
    """Detect if a PDF contains a special marker that should appear in the filename.

    Gutschrift is intentionally excluded — it does NOT get a suffix.
    """
    if not text:
        return None
    tl = text.lower()
    for suffix, keywords in _DETECTION_RULES:
        if any(kw in tl for kw in keywords):
            return suffix
    return None
