"""TEN Thüringer Energienetze — custom platform (AR, Einspeisung).

Mapping key: "Kundennummer-Vertragskonto" composite, e.g. "50023840-27078391".
  TEN PDFs put labels and values on separate lines:
    "Vertragskonto" / "Kundennummer" / "27078391" / "50023840"
Rechnungsnummer: may be in scientific notation (e.g. "9.1200275929e+11").
Date: German long format "13. Mai 2026".
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import parse_german_long_date, parse_zeitraum_end_month, fix_scientific_notation


class TENProvider(BaseProvider):
    company = "TEN"

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Mapping key: Kundennummer-Vertragskonto composite
        kd = ""
        m = re.search(
            r"Vertragskonto\s*\nKundennummer\s*\n(\d{6,12})\s*\n(\d{6,12})",
            text, re.IGNORECASE,
        )
        if m:
            kd = f"{m.group(2)}-{m.group(1)}"  # KN-VK

        # Rechnungsnummer — may be scientific notation
        rn = ""
        m = re.search(r"Rechnungsnummer\s*\n?\s*([\d.e+E]+)", text, re.IGNORECASE)
        if not m:
            m = re.search(r"Einspeiseabrechnung\s+Nr\.\s*([\d.e+E]+)", text, re.IGNORECASE)
        if m:
            rn = fix_scientific_notation(m.group(1))

        # Date — "13. Mai 2026"
        date_str = parse_german_long_date(text) or ""

        zr = parse_zeitraum_end_month(text) or ""

        return ExtractedFields(
            kundennummer=kd, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
        )
