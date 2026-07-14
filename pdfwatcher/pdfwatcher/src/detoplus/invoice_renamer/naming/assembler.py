"""Filename assembly — the single function that builds the standardized filename.

Universal format:
    [OUR_COMPANY] [AR/ER] [DATE] [NETWORK_FIRMA] [KUNDENNUMMER] [STANDORT]
    [ZEITRAUM]_[RECHNUNGSNR] [Redispatch|Storno|Korrekturnote]

Rules:
    - If Zeitraum > 35 days → use YEAR only in date prefix
    - If our company (from mapping) differs from grid operator → show both
    - Gutschrift is NOT appended as a suffix
"""

from __future__ import annotations

import re
from typing import Optional

from ..extraction.constants import (
    ZEITRAUM_LONG_DAYS, ILLEGAL_CHARS_PATTERN, FILENAME_REPLACEMENT,
    WEIGHT_DATE, WEIGHT_RECHNUNGSNR, WEIGHT_ZEITRAUM, WEIGHT_MAPPING,
    CONFIDENCE_OK, CONFIDENCE_PARTIAL,
)
from ..extraction.specials import detect_special_suffix, SpecialSuffix
from ..extraction.common import compute_zeitraum_days
from ..identity.mapping import Identity, UNKNOWN, resolve_identity


class RenameStatus:
    OK = "OK"
    INCOMPLETE = "Unvollständig: fehlende Felder"
    MANUAL = "Manuell umbenennen"


def sanitize_filename(name: str) -> str:
    """Replace illegal filename characters."""
    return re.sub(ILLEGAL_CHARS_PATTERN, FILENAME_REPLACEMENT, name).strip()


def build_filename(
    *,
    company: str,
    kundennummer: str | None = None,
    date_str: str | None = None,
    rechnungsnr: str | None = None,
    zeitraum: str | None = None,
    doc_type: str = "ER",
    identity: Identity | None = None,
    raw_text: str = "",
    extra_info: str | None = None,
) -> tuple[str | None, str, dict]:
    """Build a standardized filename from extracted fields and resolved identity.

    Args:
        company: Netzbetreiber name (e.g. "Avacon")
        kundennummer: The mapping key (Vertragskonto, Kundennummer, etc.)
        date_str: Invoice date as YYYYMMDD
        rechnungsnr: Invoice number
        zeitraum: Billing period as 'YYYY.MM'
        doc_type: 'ER' (Eingangsrechnung) or 'AR' (Ausgangsrechnung)
        identity: Pre-resolved Identity from mapping lookup
        raw_text: Full PDF text for special suffix detection
        extra_info: Optional extra text to append

    Returns:
        (new_filename, status, info_dict)
    """
    info: dict = {}
    identity = identity or UNKNOWN
    firma = identity.firma or company
    standort = identity.standort or ""

    # ── Confidence scoring ────────────────────────────────────────────
    confidence = 0
    if date_str:                     confidence += WEIGHT_DATE
    if rechnungsnr:                  confidence += WEIGHT_RECHNUNGSNR
    if zeitraum:                     confidence += WEIGHT_ZEITRAUM
    if kundennummer and standort:    confidence += WEIGHT_MAPPING

    info["confidence"] = confidence
    info["date"] = date_str or ""
    info["rechnungsnr"] = rechnungsnr or ""
    info["zeitraum"] = zeitraum or ""
    info["standort"] = standort
    info["firma"] = firma
    info["kundennummer"] = kundennummer or ""
    info["doc_type"] = doc_type

    # ── Status determination ──────────────────────────────────────────
    if confidence >= CONFIDENCE_OK:
        status = RenameStatus.OK
    elif confidence >= CONFIDENCE_PARTIAL:
        status = RenameStatus.INCOMPLETE
    else:
        status = RenameStatus.MANUAL

    if status != RenameStatus.OK and confidence < CONFIDENCE_PARTIAL:
        return None, status, info

    # ── RULE A: Zeitraum > 35 days → year-only date ──────────────────
    date_prefix = (date_str or "").replace("/", ".")
    if zeitraum:
        days = compute_zeitraum_days(zeitraum)
        if days is not None:
            info["zeitraum_days"] = days
            if days > ZEITRAUM_LONG_DAYS and date_str and len(date_str) >= 6:
                date_prefix = date_str[:4]
                info["date_format"] = "year_only"

    # ── RULE B: Special suffix detection ──────────────────────────────
    special_suffix = detect_special_suffix(raw_text)
    if special_suffix:
        info["special"] = special_suffix.value

    # ── Build filename parts ──────────────────────────────────────────
    # FIXED ORDER:
    # [OUR_COMPANY] [AR/ER] [DATE] [NETWORK_FIRMA] [KUNDENNUMMER] [STANDORT]
    # [ZEITRAUM]_[RECHNUNGSNR] [REDISPATCH|STORNO|KORREKTURNOTE]

    our_company = firma
    network_firma = company if (firma and firma != company) else ""

    parts: list[str] = []
    parts.append(our_company)
    parts.append(doc_type)
    if date_prefix:
        parts.append(date_prefix)
    if network_firma:
        parts.append(network_firma)
    if kundennummer:
        parts.append(kundennummer)
    if standort:
        parts.append(standort)

    # Zeitraum_Rechnungsnummer
    if zeitraum and rechnungsnr:
        parts.append(f"{zeitraum}_{rechnungsnr}")
    elif zeitraum:
        parts.append(str(zeitraum))
    elif rechnungsnr:
        parts.append(str(rechnungsnr))

    if extra_info:
        parts.append(extra_info)
    if special_suffix:
        parts.append(special_suffix.value)

    new_name = sanitize_filename(" ".join(parts) + ".pdf")
    return new_name, status, info
