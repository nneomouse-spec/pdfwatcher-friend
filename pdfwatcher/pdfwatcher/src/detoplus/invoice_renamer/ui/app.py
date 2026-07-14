"""PDF Watcher GUI — Tkinter application.

Wires the domain layer (identity, extraction, naming, providers) to a
dark-themed Tkinter UI. Fixes the critical settings data-loss bug by
using SettingsRepository with atomic read-modify-write.
"""

from __future__ import annotations

import os
import json
import shutil
import queue
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import customtkinter as ctk

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    CTK_OK = True
except ImportError:
    CTK_OK = False

import fitz  # PyMuPDF
from PIL import Image, ImageTk

from ..identity import Identity, UNKNOWN, resolve_identity, SettingsRepository
from ..extraction import COMPANIES, DEFAULT_WATCH, DEFAULT_DEST, extract_text
from ..extraction.constants import CONFIDENCE_AUTO
from ..naming import build_filename, RenameStatus
from ..providers import get_provider, has_dedicated_analyser
from ..watcher import MasterWatchHandler
from .i18n import tr

# ── Persistence ───────────────────────────────────────────────────────

_SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
_PREFS_FILE = _SCRIPT_DIR / "preferences.json"
_MAPPINGS_FILE = _SCRIPT_DIR / "mappings.json"
_MOVES_LOG = _SCRIPT_DIR / "moves.log"

_prefs_repo = SettingsRepository(_PREFS_FILE)
_mappings_repo = SettingsRepository(_MAPPINGS_FILE)


def _load_preferences() -> dict[str, Any]:
    return _prefs_repo.read()


def _save_preferences(data: dict[str, Any]) -> None:
    _prefs_repo.write(data)


def _load_mappings() -> dict[str, Any]:
    return _mappings_repo.read()


def _save_mappings(data: dict[str, Any]) -> None:
    _mappings_repo.write(data)


# ═══════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════

BG = "#0d1117"
PANEL = "#161b22"
SIDEBAR = "#161b22"
ACCENT = "#1f6feb"
TEXT = "#e6edf3"
MUTED = "#8b949e"
BORDER = "#30363d"
ROW_EVEN = "#161b22"
ROW_ODD = "#1c2230"
ROW_SEL = "#1f3460"
OK_COLOR = "#3fb950"
WARN_COLOR = "#d29922"
ERR_COLOR = "#f85149"
PILL_IDLE = "#1c2230"
PILL_SEL = "#1f3460"
CONFIRM_BTN = "#1a7f37"
CANCEL_BTN = "#30363d"


class PDFWatcherApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("PDF Watcher")

        # ── State ─────────────────────────────────────────────────────
        prefs = _load_preferences()
        self.lang: str = prefs.get("lang", "de")
        self.watch_folder = tk.StringVar(value=DEFAULT_WATCH)
        self.dest_folder = tk.StringVar(value=DEFAULT_DEST)
        self.selected_company = tk.StringVar(value=COMPANIES[0])
        self.dry_run = tk.BooleanVar(value=False)
        self.auto_rename = tk.BooleanVar(value=True)

        # Scan state
        self.scan_results: list[dict[str, Any]] = []
        self.approved: list[bool] = []
        self._scan_gen = 0

        # Preview state
        self._prev_doc: Any = None
        self._prev_pageno = 0
        self._prev_photo: Any = None
        self._preview_iid: str | None = None

        # Watcher
        self._observer: Any = None
        self._master_handler: MasterWatchHandler | None = None
        self._bg_counts: dict[str, int] = {}

        # Window geometry
        geo = prefs.get("window_geometry", "1420x870")
        try:
            self.geometry(geo)
        except Exception:
            self.geometry("1420x870")
        self.minsize(900, 600)

        # ── Build UI ──────────────────────────────────────────────────
        self._build_titlebar()
        self._build_main()
        self._build_statusbar()
        self._refresh_language()

        # Auto-start watcher
        self.after(500, self._auto_start)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═══════════════════════════════════════════════════════════════════
    # UI CONSTRUCTION
    # ═══════════════════════════════════════════════════════════════════

    def _build_titlebar(self):
        bar = tk.Frame(self, bg=PANEL, height=52)
        bar.pack(side=tk.TOP, fill=tk.X)
        bar.pack_propagate(False)

        tk.Label(
            bar, text="📄  PDF Watcher", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 13, "bold"),
        ).pack(side=tk.LEFT, padx=16, pady=10)

        # Right side: buttons
        self._ar_btn = tk.Button(
            bar, text="⚡ Auto: ON", bg="#1c2230", fg=OK_COLOR,
            relief="flat", bd=0, padx=10, pady=3,
            font=("Segoe UI", 8, "bold"), cursor="hand2",
            command=self._toggle_auto_rename,
        )
        self._ar_btn.pack(side=tk.RIGHT, padx=(0, 4))

        self._dr_btn = tk.Button(
            bar, text="🔵 Dry Run: OFF", bg="#1c2230", fg=MUTED,
            relief="flat", bd=0, padx=10, pady=3,
            font=("Segoe UI", 8, "bold"), cursor="hand2",
            command=self._toggle_dry_run,
        )
        self._dr_btn.pack(side=tk.RIGHT, padx=(0, 6))

        ttk.Separator(bar, orient="vertical").pack(
            side=tk.RIGHT, fill=tk.Y, padx=6, pady=8,
        )

        self.btn_move = tk.Button(
            bar, text=self.tr("move_approved"), bg=CONFIRM_BTN, fg="#ffffff",
            relief="flat", bd=0, padx=14, pady=6,
            font=("Segoe UI", 10, "bold"), cursor="hand2",
            command=self._move_all_approved,
        )
        self.btn_move.pack(side=tk.RIGHT, padx=(4, 2))

        # Language dropdown
        tk.Label(
            bar, text=self.tr("language") + ":", bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side=tk.RIGHT, padx=(10, 4))
        self.lang_var = tk.StringVar(value=self.lang)
        lang_box = ttk.Combobox(
            bar, textvariable=self.lang_var, width=5, state="readonly",
            values=["de", "en"],
        )
        lang_box.pack(side=tk.RIGHT, padx=(0, 10))
        lang_box.bind("<<ComboboxSelected>>", lambda e: self._set_language(self.lang_var.get()))

    def _build_main(self):
        main = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=BG, sashwidth=5)
        main.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 0))

        # ── Sidebar ──────────────────────────────────────────────────
        sidebar = tk.Frame(main, bg=SIDEBAR, width=240)
        sidebar.pack_propagate(False)
        main.add(sidebar, minsize=160, width=240)

        tk.Label(
            sidebar, text=self.tr("companies"), bg=SIDEBAR, fg=TEXT,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 6))

        self._pill_buttons: dict[str, tuple[tk.Button, tk.Label]] = {}

        canvas = tk.Canvas(sidebar, bg=SIDEBAR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(sidebar, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._pill_frame = tk.Frame(canvas, bg=SIDEBAR)
        canvas.create_window((0, 0), window=self._pill_frame, anchor="nw")
        self._pill_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._build_pills()

        # ── Center ───────────────────────────────────────────────────
        center = tk.Frame(main, bg=PANEL)
        main.add(center, minsize=400, width=800)

        # Header
        ch = tk.Frame(center, bg=PANEL)
        ch.pack(fill=tk.X, padx=12, pady=(12, 6))
        self._center_title = tk.Label(
            ch, text=f"{COMPANIES[0]} — PDFs", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 12, "bold"),
        )
        self._center_title.pack(side=tk.LEFT)
        self._scan_label = tk.Label(ch, text="", bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self._scan_label.pack(side=tk.RIGHT, padx=8)

        # Treeview
        tf = tk.Frame(center, bg=PANEL)
        tf.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        cols = ("approve", "old", "arrow", "new", "status", "conf")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="extended")
        self.tree.heading("approve", text="✓")
        self.tree.heading("old", text=self.tr("old_name"))
        self.tree.heading("arrow", text="")
        self.tree.heading("new", text=self.tr("new_name"))
        self.tree.heading("status", text=self.tr("status"))
        self.tree.heading("conf", text="%")
        self.tree.column("approve", width=40, stretch=False, anchor="center")
        self.tree.column("old", width=280, stretch=True, anchor="w")
        self.tree.column("arrow", width=24, stretch=False, anchor="center")
        self.tree.column("new", width=380, stretch=True, anchor="w")
        self.tree.column("status", width=90, stretch=False, anchor="center")
        self.tree.column("conf", width=50, stretch=False, anchor="center")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<space>", self._on_key)
        self.tree.bind("<Delete>", lambda e: self._delete_selected())
        self.tree.bind("<Button-3>", self._on_right_click)

        # Tags
        self.tree.tag_configure("ok", foreground=OK_COLOR)
        self.tree.tag_configure("approved", background="#0f2d1a", foreground=OK_COLOR)
        self.tree.tag_configure("partial", foreground=WARN_COLOR)
        self.tree.tag_configure("error", foreground=ERR_COLOR)
        self.tree.tag_configure("moved", foreground="#555555")
        self.tree.tag_configure("manual", foreground="#58a6ff")
        self.tree.tag_configure("dryrun", foreground="#58a6ff")
        self.tree.tag_configure("dup", foreground="#e3b341")
        self.tree.tag_configure("low_conf", foreground="#e3b341")

        # ── Preview ──────────────────────────────────────────────────
        preview_frame = tk.Frame(main, bg=BG, width=320)
        preview_frame.pack_propagate(False)
        main.add(preview_frame, minsize=200, width=320)

        ph = tk.Frame(preview_frame, bg=PANEL, height=32)
        ph.pack(fill=tk.X)
        ph.pack_propagate(False)
        tk.Label(ph, text="👁  PDF Vorschau", bg=PANEL, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10, pady=6)

        self._prev_page_lbl = tk.Label(ph, text="", bg=PANEL, fg=MUTED, font=("Segoe UI", 8))
        self._prev_page_lbl.pack(side=tk.RIGHT, padx=4)
        tk.Button(ph, text="▶", bg=PANEL, fg=MUTED, relief="flat", bd=0, font=("Segoe UI", 9), cursor="hand2", command=lambda: self._prev_turn(1)).pack(side=tk.RIGHT, padx=2)
        tk.Button(ph, text="◀", bg=PANEL, fg=MUTED, relief="flat", bd=0, font=("Segoe UI", 9), cursor="hand2", command=lambda: self._prev_turn(-1)).pack(side=tk.RIGHT, padx=2)

        self._prev_canvas = tk.Canvas(preview_frame, bg=BG, highlightthickness=0)
        self._prev_canvas.pack(fill=tk.BOTH, expand=True)
        self._prev_canvas.bind("<Configure>", lambda e: self._prev_render())

        # Footer
        footer = tk.Frame(center, bg=PANEL)
        footer.pack(fill=tk.X, padx=12, pady=(0, 10))
        self._stat_label = tk.Label(footer, text="0 Dateien", bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self._stat_label.pack(side=tk.LEFT)
        tk.Button(
            footer, text=self.tr("all_ok"), bg=PANEL, fg=MUTED,
            relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
            font=("Segoe UI", 9), command=self._approve_all,
        ).pack(side=tk.LEFT, padx=(16, 4))
        tk.Button(
            footer, text=self.tr("all_unok"), bg=PANEL, fg=MUTED,
            relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
            font=("Segoe UI", 9), command=self._unapprove_all,
        ).pack(side=tk.LEFT)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG, height=28)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        bar.pack_propagate(False)
        self._status_var = tk.StringVar(value=self.tr("ready"))
        tk.Label(
            bar, textvariable=self._status_var, bg=BG, fg=MUTED,
            font=("Segoe UI", 9), anchor="w",
        ).pack(side=tk.LEFT, padx=12)

    def _build_pills(self):
        for w in self._pill_frame.winfo_children():
            w.destroy()
        self._pill_buttons.clear()

        for company in COMPANIES:
            selected = company == self.selected_company.get()
            bg_c = PILL_SEL if selected else PILL_IDLE
            fg_c = TEXT if selected else MUTED
            dot = "#3fb950" if has_dedicated_analyser(company) else "#30363d"

            row = tk.Frame(self._pill_frame, bg=SIDEBAR)
            row.pack(fill=tk.X, padx=8, pady=2)

            btn = tk.Button(
                row, text=company, bg=bg_c, fg=fg_c,
                relief="flat", bd=0, anchor="w", padx=12, pady=7,
                font=("Segoe UI", 10, "bold" if selected else "normal"),
                activebackground=PILL_SEL, activeforeground=TEXT,
                cursor="hand2",
                command=lambda c=company: self._select_company(c),
            )
            badge = tk.Label(row, text="—", bg=bg_c, fg=MUTED, font=("Segoe UI", 9), padx=4, pady=7)
            badge.pack(side=tk.RIGHT, padx=(0, 8))

            tk.Label(row, text="●", bg=bg_c, fg=dot, font=("Segoe UI", 9), padx=2, pady=7).pack(side=tk.RIGHT, padx=(0, 2))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._pill_buttons[company] = (btn, badge)

        self.after(50, self._refresh_badges)

    # ═══════════════════════════════════════════════════════════════════
    # TRANSLATION
    # ═══════════════════════════════════════════════════════════════════

    def tr(self, key: str, **fmt) -> str:
        return tr(self.lang, key, **fmt)

    def _set_language(self, lang: str):
        self.lang = lang
        # FIXED: atomic read-modify-write — does not overwrite other settings
        _prefs_repo.update(lang=lang)
        self._refresh_language()

    def _refresh_language(self):
        self.title(self.tr("app_title"))
        if hasattr(self, '_center_title'):
            self._center_title.configure(text=f"{self.selected_company.get()} — PDFs")
        self.tree.heading("old", text=self.tr("old_name"))
        self.tree.heading("new", text=self.tr("new_name"))
        self.tree.heading("status", text=self.tr("status"))
        self.btn_move.configure(text=self.tr("move_approved"))

    # ═══════════════════════════════════════════════════════════════════
    # COMPANY SELECTION & SCANNING
    # ═══════════════════════════════════════════════════════════════════

    def _select_company(self, company: str):
        self.selected_company.set(company)
        self._center_title.configure(text=f"{company} — PDFs")
        self._build_pills()
        self._scan()

    def _refresh_badges(self):
        base = self.watch_folder.get()
        if not base:
            return
        for company, (btn, badge) in self._pill_buttons.items():
            folder = os.path.join(base, company)
            if os.path.isdir(folder):
                count = sum(1 for f in os.listdir(folder) if f.lower().endswith(".pdf"))
                badge.configure(text=str(count) if count else "—")

    def _scan(self):
        company = self.selected_company.get()
        base = self.watch_folder.get()

        folder = os.path.join(base, company)
        if not os.path.isdir(folder):
            self._status_var.set(self.tr("folder_not_found", company=company))
            return

        # Clear tree
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.scan_results.clear()
        self.approved.clear()

        pdfs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf"))
        self._status_var.set(self.tr("scanning", count=len(pdfs), company=company))

        # Background scan with queue
        self._scan_gen += 1
        gen = self._scan_gen
        result_q: queue.Queue = queue.Queue()
        stats = {"ok": 0, "partial": 0, "err": 0, "seen": set()}

        lookup = _load_mappings()

        def worker():
            provider = get_provider(company, lookup_table=lookup)
            for i, fname in enumerate(pdfs):
                if gen != self._scan_gen:
                    return
                fp = os.path.join(folder, fname)
                try:
                    result = provider.analyse(fp)
                except Exception as e:
                    result_q.put((i, fname, fp, None, f"Fehler: {e}", {}))
                    continue
                result_q.put((i, fname, fp, result.new_name, result.status, result.info))
            result_q.put((None, None, None, None, None, None))

        threading.Thread(target=worker, daemon=True).start()
        self.after(30, lambda: self._poll_scan(gen, result_q, len(pdfs), company, stats))

    def _poll_scan(self, gen, result_q, total, company, stats):
        if gen != self._scan_gen:
            return
        processed = 0
        while processed < 25:
            try:
                i, fname, fp, nn, status, info = result_q.get_nowait()
            except queue.Empty:
                break
            if i is None:
                self._refresh_badges()
                self._refresh_stats()
                self._status_var.set(self.tr("scan_done", total=total, ok=stats["ok"], partial=stats["partial"], err=stats["err"]))
                return

            # Determine tag
            if status == "OK":
                tag = "ok"
                stats["ok"] += 1
            elif status == "Manuell umbenennen":
                tag = "manual"
                stats["partial"] += 1
            elif "Unvollständig" in str(status):
                tag = "partial"
                stats["partial"] += 1
            else:
                tag = "error"
                stats["err"] += 1

            conf = info.get("confidence", 0)
            conf_str = f"{conf}%" if conf > 0 else "—"
            if 0 < conf < 70 and tag not in ("error", "moved"):
                tag = "low_conf"

            disp_name = f"[DRY] {nn}" if self.dry_run.get() and nn else (nn or "")
            if self.dry_run.get() and tag not in ("dup",):
                tag = "dryrun"

            self.tree.insert("", "end", values=("☐", fname, "→", disp_name, status, conf_str), tags=(tag,))
            self.scan_results.append({"old": fname, "new": nn or "", "status": status, "path": fp, "info": info, "conf": conf})
            self.approved.append(False)
            processed += 1

        if processed:
            self._status_var.set(f"{len(self.scan_results)}/{total} analysiert…")
        self.after(15, lambda: self._poll_scan(gen, result_q, total, company, stats))

    # ═══════════════════════════════════════════════════════════════════
    # TREE INTERACTIONS
    # ═══════════════════════════════════════════════════════════════════

    def _on_tree_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        if iid == self._preview_iid:
            return
        self._preview_iid = iid
        idx = list(self.tree.get_children()).index(iid)
        if idx >= len(self.scan_results):
            return
        path = self.scan_results[idx].get("path", "")
        self._prev_load(path)

    def _on_double_click(self, event):
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row or col != "#4":
            return
        x, y, w, h = self.tree.bbox(row, col)
        cur = self.tree.item(row, "values")[3]
        entry = tk.Entry(self.tree, bg="#161b22", fg=TEXT, insertbackground=TEXT, font=("Segoe UI", 10), relief="flat", bd=2)
        entry.insert(0, cur)
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus()

        def save(e=None):
            val = entry.get().strip()
            vals = list(self.tree.item(row, "values"))
            vals[3] = val
            self.tree.item(row, values=vals)
            idx = self.tree.index(row)
            if idx < len(self.scan_results):
                self.scan_results[idx]["new"] = val
            entry.destroy()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)
        entry.bind("<Escape>", lambda e: entry.destroy())

    def _on_key(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        indices = [self.tree.index(s) for s in sel if self.tree.index(s) < len(self.approved)]
        new_state = not all(self.approved[i] for i in indices)
        for s in sel:
            idx = self.tree.index(s)
            if idx < len(self.approved):
                self.approved[idx] = new_state
                self._refresh_row(s, idx)
        self._refresh_stats()
        if new_state:
            self._move_all_approved()

    def _on_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            if row not in self.tree.selection():
                self.tree.selection_set(row)
            menu = tk.Menu(self, tearoff=0, bg="#161b22", fg=TEXT, activebackground=ACCENT)
            menu.add_command(label=self.tr("approve"), command=lambda: self._ctx_approve(True))
            menu.add_command(label=self.tr("unapprove"), command=lambda: self._ctx_approve(False))
            menu.add_separator()
            menu.add_command(label="🗑 Löschen", command=self._delete_selected)
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

    def _ctx_approve(self, state):
        for s in self.tree.selection():
            idx = self.tree.index(s)
            if idx < len(self.approved):
                self.approved[idx] = state
                self._refresh_row(s, idx)
        self._refresh_stats()
        if state:
            self._move_all_approved()

    def _refresh_row(self, item, idx):
        vals = list(self.tree.item(item, "values"))
        if self.approved[idx]:
            vals[0] = "✅"
            self.tree.item(item, values=vals, tags=("approved",))
        else:
            vals[0] = "☐"
            status = self.scan_results[idx]["status"]
            tag = "ok" if status == "OK" else ("manual" if status == "Manuell umbenennen" else ("partial" if "Unvollständig" in str(status) else "error"))
            self.tree.item(item, values=vals, tags=(tag,))

    def _approve_all(self):
        for i, item in enumerate(self.tree.get_children()):
            if i < len(self.approved):
                self.approved[i] = True
                self._refresh_row(item, i)
        self._refresh_stats()

    def _unapprove_all(self):
        for i, item in enumerate(self.tree.get_children()):
            if i < len(self.approved):
                self.approved[i] = False
                self._refresh_row(item, i)
        self._refresh_stats()

    def _refresh_stats(self):
        total = len(self.scan_results)
        ok = sum(1 for r in self.scan_results if r["status"] == "OK")
        partial = sum(1 for r in self.scan_results if "Unvollständig" in str(r["status"]))
        err = sum(1 for r in self.scan_results if r["status"] in ("Unlesbar", "Fehler"))
        moved = sum(1 for r in self.scan_results if r["status"] == "Verschoben")
        approved = sum(1 for a in self.approved if a)
        self._stat_label.configure(
            text=f"{total} Dateien  •  ✅ {ok} OK  •  🟡 {partial}  •  🔴 {err}  •  📦 {moved} verschoben  •  ☑ {approved} markiert"
        )

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        indices = [self.tree.index(s) for s in sel if self.tree.index(s) < len(self.scan_results)]
        paths = [self.scan_results[i]["path"] for i in indices if os.path.isfile(self.scan_results[i]["path"])]
        if not paths:
            return
        desc = "Diese Datei" if len(paths) == 1 else f"{len(paths)} Dateien"
        if not messagebox.askyesno("PDF löschen", self.tr("delete_confirm", count_desc=desc), icon="warning"):
            return
        deleted = 0
        for p in paths:
            try:
                os.remove(p)
                deleted += 1
            except Exception as e:
                self._status_var.set(f"Fehler: {e}")
                return
        self._status_var.set(self.tr("deleted", count=deleted))
        self._scan()

    # ═══════════════════════════════════════════════════════════════════
    # MOVE
    # ═══════════════════════════════════════════════════════════════════

    def _move_all_approved(self):
        if self.dry_run.get():
            messagebox.showinfo("Dry Run", self.tr("dry_run_on"))
            return

        dest = self.dest_folder.get()
        if not dest or not os.path.isdir(dest):
            messagebox.showerror("Zielordner fehlt", f"Zielordner nicht gefunden:\n{dest}")
            return

        items = list(self.tree.get_children())
        to_move = [(items[i], self.scan_results[i]) for i in range(len(items)) if i < len(self.approved) and self.approved[i]]
        if not to_move:
            self._status_var.set(self.tr("no_approved"))
            return

        # Duplicate check
        dups = []
        for item, r in to_move:
            nn = r.get("new", "")
            if nn and os.path.exists(os.path.join(dest, nn)):
                dups.append(nn)
        if dups:
            if not messagebox.askyesno("⚠ Duplikate", self.tr("duplicate_warning", count=len(dups)), parent=self):
                return

        moved = 0
        for item, r in to_move:
            src = r["path"]
            if not os.path.isfile(src):
                continue
            nn = r.get("new", os.path.basename(src))
            dp = os.path.join(dest, nn)
            if os.path.exists(dp):
                base, ext = os.path.splitext(nn)
                counter = 2
                while os.path.exists(os.path.join(dest, f"{base}_{counter}{ext}")):
                    counter += 1
                dp = os.path.join(dest, f"{base}_{counter}{ext}")
            try:
                shutil.move(src, dp)
                self._log_move(src, dp)
                vals = list(self.tree.item(item, "values"))
                vals[0] = "📦"
                vals[4] = "Verschoben"
                self.tree.item(item, values=vals, tags=("moved",))
                r["status"] = "Verschoben"
                moved += 1
            except Exception as e:
                self._status_var.set(f"Fehler: {e}")
        self._status_var.set(f"✅ {self.tr('moved', count=moved)}")
        self._refresh_stats()

    # ═══════════════════════════════════════════════════════════════════
    # PREVIEW
    # ═══════════════════════════════════════════════════════════════════

    def _prev_load(self, path):
        if self._prev_doc:
            try:
                self._prev_doc.close()
            except Exception:
                pass
            self._prev_doc = None
        if not path or not os.path.isfile(path):
            self._prev_canvas.delete("all")
            self._prev_page_lbl.configure(text="")
            return
        try:
            self._prev_doc = fitz.open(path)
            self._prev_pageno = 0
            self._prev_render()
        except Exception:
            self._prev_canvas.delete("all")

    def _prev_turn(self, delta):
        if not self._prev_doc:
            return
        total = len(self._prev_doc)
        self._prev_pageno = max(0, min(total - 1, self._prev_pageno + delta))
        self._prev_render()

    def _prev_render(self):
        if not self._prev_doc:
            return
        try:
            cw = self._prev_canvas.winfo_width()
            ch = self._prev_canvas.winfo_height()
            if cw < 10 or ch < 10:
                return
            total = len(self._prev_doc)
            page = self._prev_doc[self._prev_pageno]
            pw, ph = page.rect.width, page.rect.height
            scale = min(cw / pw, ch / ph, 2.0)
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self._prev_photo = ImageTk.PhotoImage(img)
            self._prev_canvas.delete("all")
            x = max(0, (cw - pix.width) // 2)
            self._prev_canvas.create_image(x, 0, anchor="nw", image=self._prev_photo)
            self._prev_page_lbl.configure(text=f"{self._prev_pageno + 1}/{total}")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════
    # WATCHER
    # ═══════════════════════════════════════════════════════════════════

    def _auto_start(self):
        folder = self.watch_folder.get()
        if folder and os.path.isdir(folder):
            self._start_watcher(folder)
            self._refresh_badges()
            # Select first company with PDFs
            for c in COMPANIES:
                p = os.path.join(folder, c)
                if os.path.isdir(p) and any(f.lower().endswith(".pdf") for f in os.listdir(p)):
                    self._select_company(c)
                    return

    def _start_watcher(self, root_folder):
        self._stop_watcher()
        if not os.path.isdir(root_folder):
            return

        class Callbacks:
            def on_rename(self_, company):
                self._bg_counts[company] = self._bg_counts.get(company, 0) + 1
                self.after(0, lambda: self._on_bg_rename(company))

            def on_move_log(self_, src, dst):
                self._log_move(src, dst)

        self._master_handler = MasterWatchHandler(
            callbacks=Callbacks(),
            lookup_table=_load_mappings(),
            auto_rename_enabled=self.auto_rename.get(),
        )

        try:
            from watchdog.observers import Observer
            self._observer = Observer()
            self._observer.schedule(self._master_handler, root_folder, recursive=True)
            self._observer.start()
        except Exception as e:
            self._status_var.set(f"Watcher Fehler: {e}")

    def _stop_watcher(self):
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=3)
            except Exception:
                pass
            self._observer = None
            self._master_handler = None

    def _on_bg_rename(self, company):
        self._refresh_badges()
        if company == self.selected_company.get():
            self._scan()

    # ═══════════════════════════════════════════════════════════════════
    # TOGGLES
    # ═══════════════════════════════════════════════════════════════════

    def _toggle_dry_run(self):
        val = not self.dry_run.get()
        self.dry_run.set(val)
        if val:
            self._dr_btn.configure(text="🟠 Dry Run: ON", fg="#e3b341")
            self._status_var.set(self.tr("dry_run_on"))
        else:
            self._dr_btn.configure(text="🔵 Dry Run: OFF", fg=MUTED)
            self._status_var.set(self.tr("dry_run_off"))

    def _toggle_auto_rename(self):
        val = not self.auto_rename.get()
        self.auto_rename.set(val)
        if val:
            self._ar_btn.configure(text="⚡ Auto: ON", fg=OK_COLOR)
            self._status_var.set(self.tr("auto_on"))
        else:
            self._ar_btn.configure(text="⏸ Auto: OFF", fg=MUTED)
            self._status_var.set(self.tr("auto_off"))
        if self._master_handler:
            self._master_handler.auto_rename_enabled = val

    # ═══════════════════════════════════════════════════════════════════
    # LOG & CLOSE
    # ═══════════════════════════════════════════════════════════════════

    def _log_move(self, src, dst):
        entry = {"ts": datetime.now().isoformat(), "src": src, "dst": dst}
        try:
            with open(_MOVES_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def _on_close(self):
        self._stop_watcher()
        # Save window geometry (FIXED: does not overwrite other settings)
        try:
            _prefs_repo.update(window_geometry=self.geometry())
        except Exception:
            pass
        self.destroy()
