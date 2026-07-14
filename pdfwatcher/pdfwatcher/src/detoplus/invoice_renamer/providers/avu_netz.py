"""Avu Netz — custom platform.

Differences from SAP:
  - Mapping key: Kundennummer (NOT Vertragskonto!)
  - Rechnungsnummer: "Nr.: XXXXXXXXX"
  - Date: "Datum:\nDD.MM.YYYY"
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import clean_spaced_number, parse_zeitraum_end_month


class AvuNetzProvider(BaseProvider):
    company = "Avu Netz"

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Kundennummer — label block
        kd = ""
        m = re.search(r"Kundennummer[:\s]*\n?\s*(\d{6,})", text, re.IGNORECASE)
        if m:
            kd = re.sub(r"\s+", "", m.group(1))

        # Date
        date_str = ""
        m = re.search(r"Datum[:\s]*\n?\s*(\d{2})\.(\d{2})\.(\d{4})", text, re.IGNORECASE)
        if m:
            date_str = f"{m.group(3)}{m.group(2)}{m.group(1)}"

        # Rechnungsnummer — "Nr.: 300355083"
        rn = ""
        m = re.search(r"Nr\.:\s*(\d{6,})", text, re.IGNORECASE)
        if m:
            rn = re.sub(r"\s+", "", m.group(1))

        # Zeitraum
        zr = parse_zeitraum_end_month(text) or ""

        return ExtractedFields(
            kundennummer=kd, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
        )
