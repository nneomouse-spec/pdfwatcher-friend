"""Wemag Netz — custom platform (AR, Einspeisung).

Mapping key: Kundennummer with dashes e.g. "0002-6288567-1217875".
Rechnungsnummer: last segment of "Rechnungs-Nr." e.g. "0002-ARV-2026-200117785" → "200117785".
Date: "Rechnungsdatum DD.MM.YYYY".
Special: "Korrigiert Rg.-Nr." also triggers Korrektur detection.
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import parse_zeitraum_end_month


class WemagProvider(BaseProvider):
    company = "Wemag"

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Kundennummer: full format with dashes
        kd = ""
        m = re.search(r"Kundennummer[:\s]*([\d][\d\-]+[\d])", text, re.IGNORECASE)
        if m:
            kd = m.group(1).strip()

        # Rechnungsnummer: last segment after final "-"
        rn = ""
        m = re.search(r"Rechnungs-Nr\.\s*([\w\-]+)", text, re.IGNORECASE)
        if m:
            rn = m.group(1).strip().split("-")[-1]

        # Date: "Rechnungsdatum DD.MM.YYYY"
        date_str = ""
        m = re.search(r"Rechnungsdatum\s+(\d{2})\.(\d{2})\.(\d{4})", text, re.IGNORECASE)
        if m:
            date_str = f"{m.group(3)}{m.group(2)}{m.group(1)}"

        zr = parse_zeitraum_end_month(text) or ""

        return ExtractedFields(
            kundennummer=kd, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
        )
