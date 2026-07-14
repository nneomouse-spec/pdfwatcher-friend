"""Theme definitions — dark and light color schemes."""

from __future__ import annotations
from typing import Any

# ── Dark theme (WatchDog default) ─────────────────────────────────────
DARK: dict[str, str] = {
    "BG": "#0d1117",
    "PANEL": "#161b22",
    "SIDEBAR": "#161b22",
    "TITLEBAR_BG": "#161b22",
    "ACCENT": "#1f6feb",
    "TEXT": "#e6edf3",
    "MUTED": "#8b949e",
    "BORDER": "#30363d",
    "ROW_EVEN": "#161b22",
    "ROW_ODD": "#1c2230",
    "ROW_SELECTED": "#1f3460",
    "OK_COLOR": "#3fb950",
    "WARN_COLOR": "#d29922",
    "ERR_COLOR": "#f85149",
    "PILL_IDLE": "#1c2230",
    "PILL_SEL": "#1f3460",
    "CONFIRM_BTN": "#1a7f37",
    "CANCEL_BTN": "#30363d",
}

# ── Light theme ───────────────────────────────────────────────────────
LIGHT: dict[str, str] = {
    "BG": "#f0f2f5",
    "PANEL": "#ffffff",
    "SIDEBAR": "#e8ecf0",
    "TITLEBAR_BG": "#f8f9fa",
    "ACCENT": "#0d6efd",
    "TEXT": "#1c1e21",
    "MUTED": "#6c757d",
    "BORDER": "#ced4da",
    "ROW_EVEN": "#ffffff",
    "ROW_ODD": "#f3f4f6",
    "ROW_SELECTED": "#cce5ff",
    "OK_COLOR": "#1a7f37",
    "WARN_COLOR": "#b26a00",
    "ERR_COLOR": "#c62828",
    "PILL_IDLE": "#dde3ed",
    "PILL_SEL": "#0d6efd",
    "CONFIRM_BTN": "#1a7f37",
    "CANCEL_BTN": "#64748b",
}

THEMES: dict[str, dict[str, str]] = {
    "Dunkel (WatchDog)": DARK,
    "Hell (Standard)": LIGHT,
}

DEFAULT_THEME = "Dunkel (WatchDog)"


def apply_theme_colors(theme: dict[str, str]) -> None:
    """Set global color module-level variables from a theme dict.

    Called by the GUI on theme change.
    """
    import detoplus.invoice_renamer.ui.theme as mod
    for key, value in theme.items():
        setattr(mod, key, value)


# Expose all color keys as module-level variables for import convenience
BG = DARK["BG"]
PANEL = DARK["PANEL"]
SIDEBAR = DARK["SIDEBAR"]
TITLEBAR_BG = DARK["TITLEBAR_BG"]
ACCENT = DARK["ACCENT"]
TEXT = DARK["TEXT"]
MUTED = DARK["MUTED"]
BORDER = DARK["BORDER"]
ROW_EVEN = DARK["ROW_EVEN"]
ROW_ODD = DARK["ROW_ODD"]
ROW_SELECTED = DARK["ROW_SELECTED"]
OK_COLOR = DARK["OK_COLOR"]
WARN_COLOR = DARK["WARN_COLOR"]
ERR_COLOR = DARK["ERR_COLOR"]
PILL_IDLE = DARK["PILL_IDLE"]
PILL_SEL = DARK["PILL_SEL"]
CONFIRM_BTN = DARK["CONFIRM_BTN"]
CANCEL_BTN = DARK["CANCEL_BTN"]
