"""Domain constants — all magic numbers and canonical data in one place."""

# ── German months (single canonical definition) ──────────────────────
# Keys include ASCII-safe variants ("maerz") and umlaut forms ("märz")
GERMAN_MONTHS: dict[str, int] = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "marz": 3,
    "april": 4, "mai": 5, "juni": 6, "juli": 7,
    "august": 8, "september": 9, "oktober": 10,
    "november": 11, "dezember": 12,
}

# ── Confidence scoring weights ───────────────────────────────────────
WEIGHT_DATE         = 35
WEIGHT_RECHNUNGSNR  = 30
WEIGHT_ZEITRAUM     = 20
WEIGHT_MAPPING      = 15

CONFIDENCE_OK        = 85
CONFIDENCE_AUTO      = 75   # threshold for auto-rename by watcher
CONFIDENCE_PARTIAL   = 50

# ── Zeitraum ─────────────────────────────────────────────────────────
ZEITRAUM_LONG_DAYS = 35     # If billing period exceeds this, use year-only in filename

# ── PDF text cache ───────────────────────────────────────────────────
PDF_CACHE_MAX_ENTRIES = 2000

# ── Filename sanitization ────────────────────────────────────────────
ILLEGAL_CHARS_PATTERN = r'[\\/:*?"<>|]'
FILENAME_REPLACEMENT = "_"

# ── Netzbetreiber ────────────────────────────────────────────────────
# Companies that appear in the sidebar (display order)
COMPANIES = [
    "Avacon", "Avu Netz", "Bayernwerk", "Bielefelder", "E.Dis",
    "ENA", "EnR", "E-On", "EWZ", "GeraNetz", "Inter", "Leag",
    "Lichtblick", "Mahnungen", "Mitnetz", "Nur Hochladen",
    "Redinet", "SachsenNetze", "SN24", "Solandeo", "SÜC",
    "Sunnic", "SW DVV", "SW Glauchau", "SW Meerane",
    "SW Staßfurt", "SW Werdau", "TEN", "Trianel",
    "Wattline", "Wemag", "Westnetz",
]

# ── Default folders ──────────────────────────────────────────────────
DEFAULT_WATCH = (
    r"C:\Users\DETO 27\DETOplus GmbH\Finanzverwaltung - Dokumente"
    r"\(01) Rechnungslauf\0 - unbeschriftete Belege (ST)\Companies"
)
DEFAULT_DEST = (
    r"C:\Users\DETO 27\DETOplus GmbH\Finanzverwaltung - Dokumente"
    r"\(01) Rechnungslauf\0 - unbeschriftete Belege (ST)\Test"
)

# ── Watcher ──────────────────────────────────────────────────────────
DEBOUNCE_SECONDS = 1.5
FILE_WAIT_RETRIES = 10
FILE_WAIT_INTERVAL = 0.5
