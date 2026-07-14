"""Base analyser — template method for all Netzbetreiber providers.

Each provider implements _extract_fields() which returns a dict of
date, rechnungsnr, zeitraum, kundennummer. Everything else (mapping lookup,
special suffix detection, filename assembly, confidence scoring) is handled
by the base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..extraction.reader import extract_text
from ..extraction.specials import detect_special_suffix, SpecialSuffix
from ..identity.mapping import Identity, UNKNOWN, resolve_identity
from ..naming.assembler import build_filename, RenameStatus


@dataclass
class ExtractedFields:
    """Fields extracted from a PDF by a provider."""
    kundennummer: str = ""
    date_str: str = ""
    rechnungsnr: str = ""
    zeitraum: str = ""
    doc_type: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyseResult:
    """Result of analysing a single PDF."""
    new_name: str | None
    status: str
    info: dict[str, Any]

    @property
    def confidence(self) -> int:
        return self.info.get("confidence", 0)

    @property
    def is_ok(self) -> bool:
        return self.status == RenameStatus.OK


class BaseProvider(ABC):
    """Template-method base for all provider analysers.

    Subclasses override _extract_fields(text) → ExtractedFields.
    """

    company: str = ""           # Netzbetreiber name, e.g. "Avacon"
    default_doc_type: str = "AR"  # Most are AR (Einspeisung), energy suppliers are ER

    def __init__(self, lookup_table: dict[str, list[dict[str, str]]] | None = None):
        self._lookup = lookup_table or {}

    # ── Public API ────────────────────────────────────────────────────

    def analyse(self, path: str) -> AnalyseResult:
        """Full analysis pipeline: extract text → extract fields → resolve identity → build filename."""
        text = extract_text(path)
        return self.analyse_text(text)

    def analyse_text(self, text: str, raw_text: str | None = None) -> AnalyseResult:
        """Analyse pre-extracted text (useful for testing without PDF files)."""
        if raw_text is None:
            raw_text = text

        if not text.strip():
            return AnalyseResult(
                new_name=None,
                status=RenameStatus.INCOMPLETE,
                info={"confidence": 0, "error": "Empty PDF text"},
            )

        fields = self._extract_fields(text)
        identity = self._resolve_identity(fields.kundennummer)

        doc_type = fields.doc_type or self.default_doc_type

        new_name, status, info = build_filename(
            company=self.company,
            kundennummer=fields.kundennummer or None,
            date_str=fields.date_str or None,
            rechnungsnr=fields.rechnungsnr or None,
            zeitraum=fields.zeitraum or None,
            doc_type=doc_type,
            identity=identity,
            raw_text=raw_text,
            extra_info=fields.extra.get("extra_info"),
        )

        return AnalyseResult(new_name=new_name, status=status, info=info)

    # ── Subclass interface ────────────────────────────────────────────

    @abstractmethod
    def _extract_fields(self, text: str) -> ExtractedFields:
        """Extract date, rechnungsnr, zeitraum, kundennummer from PDF text.

        Each provider implements this differently depending on the
        Netzbetreiber's PDF layout.
        """
        ...

    # ── Internal ──────────────────────────────────────────────────────

    def _resolve_identity(self, mapping_key: str) -> Identity:
        """Look up the mapping key in the company's mapping table."""
        return resolve_identity(mapping_key, self.company, self._lookup)
