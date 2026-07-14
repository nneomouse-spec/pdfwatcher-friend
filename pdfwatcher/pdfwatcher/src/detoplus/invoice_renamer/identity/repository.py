"""Thread-safe JSON persistence for company settings and mapping tables.

Two separate files to prevent UI preference writes from corrupting identity data:
  - mappings.json  — Kundennummer→(Standort,Firma) mappings (critical business data)
  - preferences.json — theme, language, layout, window geometry (cosmetic)
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any


class SettingsRepository:
    """Read/write JSON settings with thread-safe atomic writes."""

    def __init__(self, filepath: str | Path):
        self._path = Path(filepath)
        self._lock = threading.RLock()

    def read(self) -> dict[str, Any]:
        """Load all settings. Returns {} if file missing or corrupt."""
        with self._lock:
            try:
                if self._path.exists():
                    with open(self._path, "r", encoding="utf-8") as f:
                        return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def write(self, data: dict[str, Any]) -> None:
        """Atomically overwrite the file."""
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self._path)

    def update(self, **kwargs: Any) -> dict[str, Any]:
        """Read, merge, write — all under lock. Returns the merged dict.

        Usage:
            repo.update(theme="dark", lang="de")
        """
        with self._lock:
            data = self._read_unlocked()
            data.update(kwargs)
            self._write_unlocked(data)
            return data

    def _read_unlocked(self) -> dict[str, Any]:
        try:
            if self._path.exists():
                with open(self._path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
        return {}

    def _write_unlocked(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self._path)
