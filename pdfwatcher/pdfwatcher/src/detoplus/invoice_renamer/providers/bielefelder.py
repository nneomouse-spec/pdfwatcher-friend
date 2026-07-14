"""Bielefelder Netz — custom platform.

Mapping key: Vertragskonto-Nr.
No SAP metadata block — uses inline/label patterns only.
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import clean_spaced_number, parse_zeitraum_end_month


class BielefelderProvider(BaseProvider):
    company = "Bielefelder"

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Vertragskonto — "Vertragskonto-Nr. 9060407070"
        vk = ""
        m = re.search(r"Vertragskonto-Nr\.?\s*\n?\s*(\d{6,})", text, re.IGNORECASE)
        if m:
            vk = re.sub(r"\s+", "", m.group(1))

        # Date — "Datum 10.02.2025" or "Belegdatum\n10.02.2025"
        date_str = ""
        m = re.search(r"\b(?:Datum|Belegdatum)\b\s*\n?\s*(\d{2})\.(\d{2})\.(\d{4})", text, re.IGNORECASE)
        if m:
            date_str = f"{m.group(3)}{m.group(2)}{m.group(1)}"

        # Rechnungsnummer
        rn = ""
        m = re.search(r"Rechnungsnummer\s*\n?\s*(\d{6,})", text, re.IGNORECASE)
        if m:
            rn = re.sub(r"\s+", "", m.group(1))

        zr = parse_zeitraum_end_month(text) or ""

        return ExtractedFields(
            kundennummer=vk, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
        )
