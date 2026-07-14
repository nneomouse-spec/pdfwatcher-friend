"""File-system watcher — monitors the root folder for new PDFs and auto-renames them.

Uses watchdog for cross-platform filesystem events. Identifies the Netzbetreiber
from the subfolder name, runs the appropriate analyser, and renames in-place
if confidence meets the auto-rename threshold.

Completely decoupled from the GUI — communicates via callback protocol.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Callable, Protocol

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..extraction.constants import (
    CONFIDENCE_AUTO, DEBOUNCE_SECONDS,
    FILE_WAIT_RETRIES, FILE_WAIT_INTERVAL,
)
from ..extraction.reader import extract_text
from ..providers import get_provider


class WatcherCallbacks(Protocol):
    """Callback protocol — implement this in the GUI layer."""

    def on_rename(self, company: str) -> None:
        """Called when a file was auto-renamed (or deleted) for a company."""
        ...

    def on_move_log(self, src: str, dst: str) -> None:
        """Called to log a file move for undo support."""
        ...


class MasterWatchHandler(FileSystemEventHandler):
    """Watches the entire root folder recursively.

    On new PDF → identifies company from subfolder → runs analyser → renames.
    """

    def __init__(
        self,
        callbacks: WatcherCallbacks,
        lookup_table: dict[str, list[dict[str, str]]],
        auto_rename_enabled: bool = True,
    ):
        super().__init__()
        self._callbacks = callbacks
        self._lookup_table = lookup_table
        self._auto_rename_enabled = auto_rename_enabled
        self._timers: dict[str, threading.Timer] = {}
        self._processing: set[str] = set()
        self._lock = threading.Lock()

    @property
    def auto_rename_enabled(self) -> bool:
        return self._auto_rename_enabled

    @auto_rename_enabled.setter
    def auto_rename_enabled(self, value: bool) -> None:
        self._auto_rename_enabled = value

    # ── Company detection ─────────────────────────────────────────────

    def _company_from_path(self, path: str) -> str | None:
        """Extract Netzbetreiber name from the subfolder hierarchy.

        Path is like: .../WatchFolder/Avacon/file.pdf
        Matches any path segment against known companies from the lookup table.
        """
        try:
            parts = os.path.normpath(path).split(os.sep)
            for company in self._lookup_table:
                if any(company.lower() == p.lower() for p in parts):
                    return company
            return os.path.basename(os.path.dirname(path))
        except Exception:
            return None

    # ── Debounce ──────────────────────────────────────────────────────

    def _debounce_file(self, path: str, delay: float = DEBOUNCE_SECONDS) -> None:
        """Debounce per file — wait for write to finish before processing."""
        with self._lock:
            if path in self._timers:
                self._timers[path].cancel()
            timer = threading.Timer(delay, self._process_file, args=[path])
            self._timers[path] = timer
            timer.start()

    # ── Processing ────────────────────────────────────────────────────

    def _process_file(self, path: str) -> None:
        """Background thread: analyse + rename the PDF."""
        with self._lock:
            self._timers.pop(path, None)

        if path in self._processing:
            return
        if not os.path.isfile(path):
            return

        self._processing.add(path)
        try:
            company = self._company_from_path(path)
            if not company:
                return

            provider = get_provider(company, lookup_table=self._lookup_table)

            # Wait for file to be fully written
            for _ in range(FILE_WAIT_RETRIES):
                try:
                    with open(path, "rb"):
                        break
                except PermissionError:
                    time.sleep(FILE_WAIT_INTERVAL)

            result = provider.analyse(path)

            if not self._auto_rename_enabled:
                return

            if result.is_ok and result.new_name and result.confidence >= CONFIDENCE_AUTO:
                folder = os.path.dirname(path)
                new_path = os.path.join(folder, result.new_name)

                # Handle duplicates
                if os.path.exists(new_path) and new_path != path:
                    base, ext = os.path.splitext(result.new_name)
                    counter = 2
                    while os.path.exists(os.path.join(folder, f"{base}_{counter}{ext}")):
                        counter += 1
                    new_path = os.path.join(folder, f"{base}_{counter}{ext}")

                if new_path != path:
                    os.rename(path, new_path)
                    self._callbacks.on_move_log(path, new_path)

            self._callbacks.on_rename(company)

        except Exception:
            pass  # Errors are logged; GUI will reflect on next scan
        finally:
            self._processing.discard(path)

    # ── watchdog event handlers ───────────────────────────────────────

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".pdf"):
            self._debounce_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory and event.dest_path.lower().endswith(".pdf"):
            self._debounce_file(event.dest_path)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".pdf"):
            company = self._company_from_path(event.src_path)
            if company:
                self._callbacks.on_rename(company)
