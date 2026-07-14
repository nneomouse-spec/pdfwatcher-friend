"""ENA Energienetze Apolda — custom platform.

Mapping key: Kundennummer.
Rechnungsnummer: strips "ER " prefix.
No SAP metadata block.
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import parse_zeitraum_end_month


class ENAProvider(BaseProvider):
    company = "ENA"

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Kundennummer
        kd = ""
        m = re.search(r"Kundennummer\s*[:\s]\s*(\d{5,})", text, re.IGNORECASE)
        if m:
            kd = m.group(1).strip()

        # Date — "Rechnungsdatum : 13.11.2025"
        date_str = ""
        m = re.search(r"Rechnungsdatum\s*[:\s]\s*(\d{2})\.(\d{2})\.(\d{4})", text, re.IGNORECASE)
        if m:
            date_str = f"{m.group(3)}{m.group(2)}{m.group(1)}"

        # Rechnungsnummer — strip "ER " prefix
        rn = ""
        m = re.search(r"Rechnungsnummer\s*[:\s]\s*(?:ER\s+)?(\d{6,})", text, re.IGNORECASE)
        if m:
            rn = m.group(1).strip()

        # Zeitraum
        zr = ""
        m = re.search(
            r"(?:vom|für die Zeit vom)\s+\d{1,2}\.\d{1,2}\.\d{4}\s+bis\s+"
            r"\d{1,2}\.(\d{1,2})\.(\d{4})", text, re.IGNORECASE)
        if not m:
            m = re.search(r"\d{1,2}\.\d{1,2}\.\s*-\s*\d{1,2}\.(\d{1,2})\.(\d{4})", text)
        if m:
            zr = f"{m.group(2)}.{int(m.group(1)):02d}"
        if not zr:
            zr = parse_zeitraum_end_month(text) or ""

        return ExtractedFields(
            kundennummer=kd, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
        )
