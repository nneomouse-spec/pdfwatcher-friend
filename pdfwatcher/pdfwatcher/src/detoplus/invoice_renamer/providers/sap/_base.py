"""SAP platform base — shared extraction for Avacon, Bayernwerk, E.Dis, Mitnetz.

These four Netzbetreiber use the same SAP backend and produce PDFs with:
  - #!#VNR#!#<digits>#!# metadata line (cleanest Vertragskonto source)
  - Vertragskonto: <spaced digits> footer
  - Datum\nDD.MM.YYYY date label block (except Mitnetz: "Cottbus, DD.MM.YYYY")
  - Rechnungsnummer: <spaced digits> footer (except Mitnetz: "Rechn.-Nr.:")
  - Abrechnung von DD.MM.YYYY bis DD.MM.YYYY

Subclasses override only the 1-2 patterns that differ.
"""

from __future__ import annotations

import re

from ..base import BaseProvider, ExtractedFields
from ...extraction.common import clean_spaced_number, parse_zeitraum_end_month


class SAPPlatformProvider(BaseProvider):
    """Base for SAP-platform Netzbetreiber: Avacon, Bayernwerk, E.Dis, Mitnetz."""

    # ── Override points ───────────────────────────────────────────────
    date_pattern: str = r"\bDatum\b\s*\n?\s*(\d{2})\.(\d{2})\.(\d{4})"
    rechnungsnr_label: str = r"Rechnungsnummer"
    default_doc_type: str = "AR"

    # ── Extraction ────────────────────────────────────────────────────

    def _extract_fields(self, text: str) -> ExtractedFields:
        return ExtractedFields(
            kundennummer=self._extract_vertragskonto(text),
            date_str=self._extract_date(text),
            rechnungsnr=self._extract_rechnungsnr(text),
            zeitraum=self._extract_zeitraum(text),
            doc_type=self.default_doc_type,
        )

    def _extract_vertragskonto(self, text: str) -> str:
        """Extract Vertragskonto — metadata first, then fallbacks."""
        # Priority 1: SAP metadata line (cleanest, no spaces)
        m = re.search(r"#!#VNR#!#(\d+)#!#", text)
        if m:
            return m.group(1)

        # Priority 2: Inline footer "Vertragskonto: 215000385783"
        m = re.search(r"Vertragskonto:\s*([\d ]+)", text)
        if m:
            return clean_spaced_number(m.group(1))

        # Priority 3: Label block "Vertragskonto\n215 0003 857 83"
        m = re.search(r"Vertragskonto\s*\n\s*([\d ]+)", text)
        if m:
            return clean_spaced_number(m.group(1))

        return ""

    def _extract_date(self, text: str) -> str:
        """Extract invoice date using the provider-specific pattern."""
        m = re.search(self.date_pattern, text, re.IGNORECASE)
        if m:
            return f"{m.group(3)}{m.group(2)}{m.group(1)}"
        return ""

    def _extract_rechnungsnr(self, text: str) -> str:
        """Extract invoice number."""
        # Footer: "Rechnungsnummer: 3111 4005 9500"
        m = re.search(rf"{self.rechnungsnr_label}:\s*([\d ]+)", text)
        if m:
            return clean_spaced_number(m.group(1))

        # Label block: "Rechnungsnummer\n3111 4005 9500"
        m = re.search(rf"{self.rechnungsnr_label}\s*\n\s*([\d ]+)", text)
        if m:
            return clean_spaced_number(m.group(1))

        return ""

    def _extract_zeitraum(self, text: str) -> str:
        """Extract billing period from 'Abrechnung von ... bis ...'."""
        return parse_zeitraum_end_month(text) or ""
