"""Shared extraction helpers used across all provider analysers.

Every analyser needs to:
  - Clean spaced numbers (fitz layout engine inserts spaces)
  - Parse German long-form dates ("13. Mai 2026")
  - Parse DMY dates ("09.04.2026")
  - Parse Zeitraum into end-month format
  - Fix scientific notation from broken PDF renderers
"""

from __future__ import annotations

import re
from datetime import date

from .constants import GERMAN_MONTHS


# ── Number cleaning ──────────────────────────────────────────────────

def clean_spaced_number(raw: str | None) -> str:
    """Remove all whitespace from a number string.

    e.g. '215 0003 857 83' → '215000385783'
         '3111 4005 9500'  → '311140059500'
    """
    if not raw:
        return ""
    return re.sub(r"\s+", "", raw.strip())


def fix_scientific_notation(s: str) -> str:
    """Convert scientific notation string to plain integer string.

    e.g. '9.1200275929e+11' → '912002759290'

    Used by TEN provider where fitz renders large invoice numbers
    in scientific notation.
    """
    s = re.sub(r"[\s,]", "", s.strip())
    if "e" not in s.lower():
        return s

    parts = re.split(r"[eE]", s)
    mantissa = parts[0]
    exp = int(parts[1].lstrip("+"))

    if "." in mantissa:
        dot_idx = mantissa.index(".")
        digits = mantissa.replace(".", "")
    else:
        dot_idx = len(mantissa)
        digits = mantissa

    new_dot = dot_idx + exp
    if new_dot >= len(digits):
        digits = digits + "0" * (new_dot - len(digits))
    else:
        digits = digits[:new_dot]

    return digits.lstrip("0") or "0"


# ── Date parsing ─────────────────────────────────────────────────────

def parse_german_long_date(text: str) -> str | None:
    """Parse German long-format date: '13. Mai 2026' → '20260513'.

    Returns YYYYMMDD string or None.
    """
    m = re.search(
        r"(\d{1,2})\.\s*(Januar|Februar|M[aä]rz|April|Mai|Juni|Juli|"
        r"August|September|Oktober|November|Dezember)\s*(\d{4})",
        text, re.IGNORECASE,
    )
    if not m:
        return None

    day = int(m.group(1))
    month_name = m.group(2).lower().replace("ä", "ae")
    mon = GERMAN_MONTHS.get(month_name, GERMAN_MONTHS.get(m.group(2).lower(), 0))
    if not mon:
        return None
    return f"{m.group(3)}{mon:02d}{day:02d}"


def parse_dmy_date(text: str) -> str | None:
    """Parse DD.MM.YYYY or DD.MM.YY date → YYYYMMDD.

    Handles 2-digit years by assuming 20xx.
    """
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4}|\d{2})", text)
    if not m:
        return None
    yr = m.group(3) if len(m.group(3)) == 4 else "20" + m.group(3)
    return f"{yr}{m.group(2)}{m.group(1)}"


def parse_city_date(text: str) -> str | None:
    """Parse 'CityName, DD.MM.YYYY' format (used by Mitnetz).

    Example: 'Cottbus, 09.04.2026' → '20260409'
    """
    m = re.search(r"\w[\w\s]+,\s*(\d{2})\.(\d{2})\.(\d{4})", text)
    if not m:
        return None
    return f"{m.group(3)}{m.group(2)}{m.group(1)}"


# ── Zeitraum parsing ─────────────────────────────────────────────────

def parse_zeitraum_end_month(text: str) -> str | None:
    """Extract billing period end month from various German formats.

    'Abrechnung von 01.02.2026 bis 28.02.2026'  → '2026.02'
    'vom 01.08.23 bis 31.08.23'                 → '2023.08'
    'Schlussrechnung für Oktober 2025'           → '2025.10'

    Returns 'YYYY.MM' or None.
    """
    # Pattern 1: "Abrechnung von ... bis DD.MM.YYYY"
    m = re.search(
        r"Abrechnung\s+von\s+\d{1,2}\.\d{1,2}\.\d{4}\s+bis\s+"
        r"\d{1,2}\.(\d{1,2})\.(\d{4})",
        text, re.IGNORECASE,
    )
    if m:
        return f"{m.group(2)}.{int(m.group(1)):02d}"

    # Pattern 2: "vom DD.MM.YY(YY) bis DD.MM.YY(YY)"
    m = re.search(
        r"vom\s+\d{1,2}\.\d{2}\.(\d{2,4})\s+bis\s+\d{1,2}\.(\d{2})\.(\d{2,4})",
        text, re.IGNORECASE,
    )
    if m:
        yr = m.group(3) if len(m.group(3)) == 4 else "20" + m.group(3)
        return f"{yr}.{int(m.group(2)):02d}"

    # Pattern 3: "Schlussrechnung für Monat Jahr"
    m = re.search(
        r"(?:Schlussrechnung|Rechnung|Abrechnung)\s+für\s+"
        r"(Januar|Februar|März|April|Mai|Juni|Juli|"
        r"August|September|Oktober|November|Dezember)\s+(\d{4})",
        text, re.IGNORECASE,
    )
    if m:
        mon = GERMAN_MONTHS.get(m.group(1).lower(), 0)
        if mon:
            return f"{m.group(2)}.{mon:02d}"

    # Pattern 4: "für den Zeitraum vom ... bis ..."
    m = re.search(
        r"(?:vom|für(?:\s+den\s+Zeitraum)?\s+vom)\s+"
        r"\d{1,2}\.\d{2}\.\d{4}\s+bis\s+\d{1,2}\.(\d{2})\.(\d{4})",
        text, re.IGNORECASE,
    )
    if m:
        return f"{m.group(2)}.{int(m.group(1)):02d}"

    # Pattern 5: "Zeit vom ... bis ..."
    m = re.search(
        r"(?:vom|Zeit\s+vom)\s+\d{1,2}\.\d{2}\.(\d{4})\s+bis\s+"
        r"\d{1,2}\.(\d{2})\.(\d{4})",
        text, re.IGNORECASE,
    )
    if m:
        return f"{m.group(3)}.{int(m.group(2)):02d}"

    # Pattern 6: Simple DD.MM.YY - DD.MM.YY (Lichtblick)
    m = re.search(
        r"(?:vom|für)\s+\d{1,2}\.\d{2}\.\d{4}\s+[-–]\s+"
        r"\d{1,2}\.(\d{2})\.(\d{4})",
        text, re.IGNORECASE,
    )
    if m:
        return f"{m.group(2)}.{int(m.group(1)):02d}"

    return None


# ── Zeitraum day-count for the >35 day rule ──────────────────────────

def compute_zeitraum_days(zeitraum_str: str) -> int | None:
    """Compute number of days in a Zeitraum string.

    Formats: 'MM.YYYY-MM.YYYY' or 'DD.MM.YYYY-DD.MM.YYYY'
    Returns days or None if unparseable.
    """
    import re as _re

    # MM.YYYY - MM.YYYY
    m = _re.search(
        r"(\d{2})[./](\d{4})\s*[-–]\s*(\d{2})[./](\d{4})", zeitraum_str
    )
    if m:
        try:
            d_start = date(int(m.group(2)), int(m.group(1)), 1)
            d_end = date(int(m.group(4)), int(m.group(3)), 1)
            return (d_end - d_start).days
        except ValueError:
            pass

    # DD.MM.YYYY - DD.MM.YYYY
    m = _re.search(
        r"(\d{2})[./](\d{2})[./](\d{4})\s*[-–]\s*"
        r"(\d{2})[./](\d{2})[./](\d{4})", zeitraum_str
    )
    if m:
        try:
            d_start = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            d_end = date(int(m.group(6)), int(m.group(5)), int(m.group(4)))
            return (d_end - d_start).days
        except ValueError:
            pass

    return None
