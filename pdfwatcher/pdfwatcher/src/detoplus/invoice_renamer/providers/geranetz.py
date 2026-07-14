"""GeraNetz — custom platform (AR, Einspeisung).

Mapping key: Kunden-Nr. with dash e.g. "4195194-662959".
Rechnungsnummer: last segment of "Rechnungs-Nr." e.g. "10-ARV-2023-168427" → "168427".
Date: German long format "01. November 2023".
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import parse_german_long_date, parse_zeitraum_end_month


class GeraNetzProvider(BaseProvider):
    company = "GeraNetz"

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Kunden-Nr.: full with dash
        kd = ""
        m = re.search(r"Kunden-Nr\.?\s*([\d][\d\-]+[\d])", text, re.IGNORECASE)
        if m:
            kd = m.group(1).strip()

        # Rechnungsnummer: last segment after final "-"
        rn = ""
        m = re.search(r"Rechnungs-Nr\.?\s*([\w\-]+)", text, re.IGNORECASE)
        if m:
            rn = m.group(1).strip().split("-")[-1]

        # Date: German long format
        date_str = parse_german_long_date(text) or ""

        zr = parse_zeitraum_end_month(text) or ""

        return ExtractedFields(
            kundennummer=kd, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
        )
