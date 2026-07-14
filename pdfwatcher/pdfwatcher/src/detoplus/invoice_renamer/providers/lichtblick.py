"""Lichtblick SE — energy supplier (ER).

Mapping key: Lieferstelle (NOT Kundennummer or Vertragskonto!).
Rechnungsnummer: Belegnummer (different label!).
Date: German long format "02. April 2026".
"""

import re
from .base import BaseProvider, ExtractedFields
from ..extraction.common import parse_german_long_date


class LichtblickProvider(BaseProvider):
    company = "Lichtblick"
    default_doc_type = "ER"

    def _extract_fields(self, text: str) -> ExtractedFields:
        # Lieferstelle (mapping key — NOT Kundennummer)
        kd = ""
        m = re.search(r"Lieferstelle[:\s]*\n?\s*(\d{6,})", text, re.IGNORECASE)
        if not m:
            m = re.search(r"Lieferstelle:\s*(\d{6,})", text, re.IGNORECASE)
        if m:
            kd = m.group(1).strip()

        # Date — "02. April 2026"
        date_str = parse_german_long_date(text) or ""

        # Belegnummer (= Rechnungsnummer)
        rn = ""
        m = re.search(r"Belegnummer[:\s]*\n?\s*(\d{6,})", text, re.IGNORECASE)
        if not m:
            m = re.search(r"Belegnummer:\s*(\d{6,})", text, re.IGNORECASE)
        if m:
            rn = m.group(1).strip()

        # Zeitraum — various formats
        zr = ""
        m = re.search(
            r"(?:vom|für)\s+\d{1,2}\.\d{2}\.\d{4}\s+[-–]\s+"
            r"\d{1,2}\.(\d{2})\.(\d{4})", text, re.IGNORECASE)
        if not m:
            m = re.search(
                r"(?:vom|für)\s+\d{1,2}\.\d{2}\.\d{4}\s+bis(?:\s+zum)?\s+"
                r"\d{1,2}\.(\d{2})\.(\d{4})", text, re.IGNORECASE)
        if not m:
            m = re.search(r"\d{1,2}\.\d{2}\.\d{4}\s+[-–]\s+\d{1,2}\.(\d{2})\.(\d{4})", text)
        if m:
            zr = f"{m.group(2)}.{int(m.group(1)):02d}"

        return ExtractedFields(
            kundennummer=kd, date_str=date_str,
            rechnungsnr=rn, zeitraum=zr,
            doc_type="ER",
        )
