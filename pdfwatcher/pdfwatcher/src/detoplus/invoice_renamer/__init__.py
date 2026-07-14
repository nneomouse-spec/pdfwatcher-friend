"""DETOPlus Invoice Renamer — auto-rename energy billing PDFs."""

from .identity import Identity, UNKNOWN, resolve_identity, SettingsRepository
from .extraction import (
    extract_text, GERMAN_MONTHS, SpecialSuffix, detect_special_suffix,
    clean_spaced_number, fix_scientific_notation,
    parse_german_long_date, parse_dmy_date, parse_city_date,
    parse_zeitraum_end_month, compute_zeitraum_days,
    COMPANIES, DEFAULT_WATCH, DEFAULT_DEST,
)
from .naming import build_filename, RenameStatus
from .providers import get_provider, has_dedicated_analyser
from .watcher import MasterWatchHandler

__all__ = [
    "Identity", "UNKNOWN", "resolve_identity", "SettingsRepository",
    "extract_text", "GERMAN_MONTHS", "SpecialSuffix", "detect_special_suffix",
    "clean_spaced_number", "fix_scientific_notation",
    "parse_german_long_date", "parse_dmy_date", "parse_city_date",
    "parse_zeitraum_end_month", "compute_zeitraum_days",
    "COMPANIES", "DEFAULT_WATCH", "DEFAULT_DEST",
    "build_filename", "RenameStatus",
    "get_provider", "has_dedicated_analyser",
    "MasterWatchHandler",
]
