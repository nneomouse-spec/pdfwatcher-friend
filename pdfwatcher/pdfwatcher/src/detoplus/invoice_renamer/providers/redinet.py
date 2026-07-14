"""Redinet Burgenland — custom platform (AR, Einspeisung).

Mapping key: Vertragskonto (NOT Kundennummer — both exist on invoice!).
Rechnungsnummer: "Rechnungs-Nr.:" or "Rechnungsnummer:".
Date: "Datum: DD.MM.YYYY" label block.
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import clean_spaced_number, parse_zeitraum_end_month


class RedinetProvider(BaseProvider):
    company = "Redinet"

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Vertragskonto (mapping key — ignore Kundennummer!)
        vk = ""
        m = re.search(r"Vertragskonto[:\s]*\n?\s*([\d]+)", text, re.IGNORECASE)
        if m:
            vk = m.group(1).strip()

        # Rechnungsnummer
        rn = ""
        m = re.search(r"Rechnungs-Nr\.:\s*\n?\s*([\d]+)", text, re.IGNORECASE)
        if not m:
            m = re.search(r"Rechnungsnummer:\s*\n?\s*([\d]+)", text, re.IGNORECASE)
        if m:
            rn = clean_spaced_number(m.group(1))

        # Date — "Datum: DD.MM.YYYY"
        date_str = ""
        m = re.search(r"Datum[:\s]*\n?\s*(\d{2})\.(\d{2})\.(\d{4})", text, re.IGNORECASE)
        if m:
            date_str = f"{m.group(3)}{m.group(2)}{m.group(1)}"

        zr = parse_zeitraum_end_month(text) or ""

        return ExtractedFields(
            kundennummer=vk, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
        )
