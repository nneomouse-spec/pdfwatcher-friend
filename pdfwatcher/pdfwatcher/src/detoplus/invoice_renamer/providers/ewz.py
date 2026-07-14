"""EWZ Energiewerke Zeulenroda — custom platform.

Mapping key: Kundennummer as "310031/3100031" → "310031-3100".
Rechnungsnummer: "ES23-0146" → "0146" (digits after "-" only).
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import clean_spaced_number


class EWZProvider(BaseProvider):
    company = "EWZ"

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Kundennummer: "310031/3100031" → "310031-3100"
        kd = ""
        m = re.search(
            r"Kunden-?(?:/Verbrauchsstellen-)?Nr\.?[:\s]+([\d]+)\s*/\s*([\d]+)",
            text, re.IGNORECASE,
        )
        if m:
            part1 = m.group(1).strip()
            part2 = m.group(2).strip()[:4]
            kd = f"{part1}-{part2}"

        # Rechnungsnummer: "ES23-0146" → "0146"
        rn = ""
        m = re.search(r"Rechnungsnummer\s*\n?\s*[A-Z]{2}\d{2}-\s*(\d+)", text, re.IGNORECASE)
        if m:
            rn = clean_spaced_number(m.group(1))

        # Date — "Rechnungsdatum\n12.09.2023"
        date_str = ""
        m = re.search(
            r"Rechnungsdatum\s*\n?\s*(\d{2})\.(\d{2})\.(\d{4}|\d{2})",
            text, re.IGNORECASE,
        )
        if m:
            yr = m.group(3) if len(m.group(3)) == 4 else "20" + m.group(3)
            date_str = f"{yr}{m.group(2)}{m.group(1)}"

        # Zeitraum — "vom 01.08.23 bis 31.08.23" → 2023.08
        zr = ""
        m = re.search(
            r"vom\s+\d{1,2}\.\d{2}\.(\d{2,4})\s+bis\s+\d{1,2}\.(\d{2})\.(\d{2,4})",
            text, re.IGNORECASE,
        )
        if m:
            yr = m.group(3) if len(m.group(3)) == 4 else "20" + m.group(3)
            zr = f"{yr}.{int(m.group(2)):02d}"

        return ExtractedFields(
            kundennummer=kd, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
        )
