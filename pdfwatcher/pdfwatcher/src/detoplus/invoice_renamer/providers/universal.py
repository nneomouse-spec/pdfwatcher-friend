"""Universal fallback provider — used for companies without a dedicated analyser.

Uses generic common-field extraction to find date, Rechnungsnummer, Zeitraum,
and Kundennummer from any PDF text. Lower accuracy but works as a fallback.
"""

from __future__ import annotations

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.constants import GERMAN_MONTHS


class UniversalProvider(BaseProvider):
    """Fallback analyser using generic field extraction patterns."""

    def __init__(self, company: str, lookup_table=None):
        super().__init__(lookup_table)
        self.company = company

    def _extract_fields(self, text: str) -> ExtractedFields:
        return ExtractedFields(
            kundennummer=self._find_kundennummer(text),
            date_str=self._find_date(text),
            rechnungsnr=self._find_rechnungsnr(text),
            zeitraum=self._find_zeitraum(text),
        )

    # ── Date ──────────────────────────────────────────────────────────

    def _find_date(self, text: str) -> str:
        # DD.MM.YYYY or YYYY.MM.DD
        m = re.search(r"(\d{2})[.\-/](\d{2})[.\-/](\d{4})", text)
        if m:
            g = m.groups()
            if len(g[0]) == 4 and int(g[1]) <= 12:
                return f"{g[0]}{g[1]}{g[2]}"
            return f"{g[2]}{g[1]}{g[0]}"

        # German long date: "1. Januar 2024"
        m = re.search(
            r"(\d{1,2})\.\s*(Januar|Februar|März|April|Mai|Juni|Juli|"
            r"August|September|Oktober|November|Dezember)\s*(\d{4})",
            text, re.IGNORECASE,
        )
        if m:
            mon = GERMAN_MONTHS.get(m.group(2).lower(), "00")
            return f"{m.group(3)}{mon}{int(m.group(1)):02d}"
        return ""

    # ── Rechnungsnummer ───────────────────────────────────────────────

    def _find_rechnungsnr(self, text: str) -> str:
        patterns = [
            r"Rechnungs(?:nummer|nr\.?)[:\s#]*([A-Z0-9\-/]+)",
            r"Belegnummer[:\s#]*([A-Z0-9\-/]+)",
            r"Rechnung\s+Nr\.?\s*[:\s]*([A-Z0-9\-/]+)",
            r"Invoice\s+No\.?\s*[:\s]*([A-Z0-9\-/]+)",
            r"(?:RE|RG|AR|GS|CS|SC)[.\-_]?(\d{6,})",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    # ── Zeitraum ──────────────────────────────────────────────────────

    def _find_zeitraum(self, text: str) -> str:
        from ..extraction.common import parse_zeitraum_end_month
        return parse_zeitraum_end_month(text) or ""

    # ── Kundennummer ──────────────────────────────────────────────────

    def _find_kundennummer(self, text: str) -> str:
        patterns = [
            r"Kundennummer[:\s]*(\d{6,12})",
            r"Kunden-?Nr\.?[:\s]*(\d{6,12})",
            r"Customer\s+No\.?[:\s]*(\d{6,12})",
            r"Vertragskonto[:\s]*(\d{6,12})",
            r"Vertragskontonummer[:\s]*(\d{6,12})",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""
