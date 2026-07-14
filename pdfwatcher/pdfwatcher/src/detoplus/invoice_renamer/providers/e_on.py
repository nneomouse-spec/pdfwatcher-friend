"""E.On Energie Deutschland — energy SUPPLIER (ER, not AR).

Mapping key: Vertragskonto.
Date: German long format "4. November 2025".
Zeitraum: "Schlussrechnung für Oktober 2025" (month name).
No SAP metadata block.
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import clean_spaced_number, parse_german_long_date, parse_zeitraum_end_month
from ..extraction.constants import GERMAN_MONTHS


class EOnProvider(BaseProvider):
    company = "E-On"
    default_doc_type = "ER"  # Energy supplier → incoming invoice

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Vertragskonto — label block or inline
        vk = ""
        m = re.search(r"Vertragskonto\s*\n\s*([\d ]+)", text)
        if m:
            vk = clean_spaced_number(m.group(1))
        if not vk:
            m = re.search(r"Vertragskonto\s+([\d ]{10,})", text)
            if m:
                vk = clean_spaced_number(m.group(1))

        # Date — German long format
        date_str = parse_german_long_date(text) or ""

        # Rechnungsnummer
        rn = ""
        m = re.search(r"Rechnungsnummer\s*\n\s*([\d ]+)", text)
        if m:
            rn = clean_spaced_number(m.group(1))
        if not rn:
            m = re.search(r"Rechnungsnummer\s+([\d ]{10,})", text)
            if m:
                rn = clean_spaced_number(m.group(1))

        # Zeitraum — "Schlussrechnung für Oktober 2025"
        zr = parse_zeitraum_end_month(text) or ""

        return ExtractedFields(
            kundennummer=vk, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
            doc_type="ER",
        )
