"""SachsenNetze HS.HD — custom platform (AR, Einspeisung).

Mapping key: Vertragskontonummer.
Rechnungsnummer: Gutschrift number (credit note, different label).
Date: "Gutschrift vom DD.MM.YYYY".
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import parse_zeitraum_end_month


class SachsenNetzeProvider(BaseProvider):
    company = "SachsenNetze"

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Vertragskontonummer
        vk = ""
        m = re.search(r"Vertragskontonummer[:\s]*\n?\s*([\d]+)", text, re.IGNORECASE)
        if m:
            vk = m.group(1).strip()

        # Gutschrift number = Rechnungsnummer
        rn = ""
        m = re.search(r"^Gutschrift[:\s]*\n\s*(\d{9,})", text, re.IGNORECASE | re.MULTILINE)
        if not m:
            m = re.search(r"Gutschrift(?:snummer)?[:\s]+(\d{9,})", text, re.IGNORECASE)
        if m:
            rn = m.group(1).strip()

        # Date: "Gutschrift vom DD.MM.YYYY"
        date_str = ""
        m = re.search(r"Gutschrift\s+vom\s+(\d{2})\.(\d{2})\.(\d{4})", text, re.IGNORECASE)
        if m:
            date_str = f"{m.group(3)}{m.group(2)}{m.group(1)}"

        zr = parse_zeitraum_end_month(text) or ""

        return ExtractedFields(
            kundennummer=vk, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
        )
