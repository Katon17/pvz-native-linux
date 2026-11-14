# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Lapisan dialog: zenity → kdialog → terminal.

Semua fungsi di sini aman dipanggil tanpa display; kalau tidak ada tool GUI
sama sekali, otomatis jatuh ke mode teks.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Sequence

TITLE = "Plants vs. Zombies"


def _headless() -> bool:
    if os.environ.get("PVZ_NATIVE_NO_GUI") == "1":
        return True
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return False
    return True


class Backend:
    def __init__(self) -> None:
        self.zenity = shutil.which("zenity")
        self.kdialog = shutil.which("kdialog")
        self.headless = _headless()

    @property
    def name(self) -> str:
        if self.headless:
            return "terminal"
        if self.zenity:
            return "zenity"
        if self.kdialog:
            return "kdialog"
        return "terminal"


BACKEND = Backend()


def _run(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(argv), capture_output=True, text=True)


# ------------------------------------------------------------------ messages
def info(message: str) -> None:
    if BACKEND.zenity:
        _run([BACKEND.zenity, "--info", f"--title={TITLE}", "--width=460",
              "--no-wrap", f"--text={message}"])
    elif BACKEND.kdialog:
        _run([BACKEND.kdialog, "--title", TITLE, "--msgbox", message])
    else:
        print(message)


def warn(message: str) -> None:
    if BACKEND.zenity:
        _run([BACKEND.zenity, "--warning", f"--title={TITLE}", "--width=480",
              f"--text={message}"])
    elif BACKEND.kdialog:
        _run([BACKEND.kdialog, "--title", TITLE, "--sorry", message])
    else:
        print(f"Peringatan: {message}", file=sys.stderr)


def error(message: str) -> None:
    if BACKEND.zenity:
        _run([BACKEND.zenity, "--error", f"--title={TITLE}", "--width=520",
              f"--text={message}"])
    elif BACKEND.kdialog:
        _run([BACKEND.kdialog, "--title", TITLE, "--error", message])
    else:
        print(f"Error: {message}", file=sys.stderr)


def ask(message: str, ok: str = "Lanjut", cancel: str = "Batal") -> bool:
    if os.environ.get("PVZ_NATIVE_ASSUME_YES") == "1":
        print(message)
        print("→ disetujui otomatis (--yes)")
        return True
    if BACKEND.zenity:
        result = _run([BACKEND.zenity, "--question", f"--title={TITLE}",
                       "--width=460", f"--ok-label={ok}",
                       f"--cancel-label={cancel}", f"--text={message}"])
        return result.returncode == 0
    if BACKEND.kdialog:
        result = _run([BACKEND.kdialog, "--title", TITLE, "--yesno", message])
        return result.returncode == 0
    try:
        answer = input(f"{message} [y/N] ").strip().lower()
    except EOFError:
        # Tidak ada terminal interaktif (mis. dipanggil dari skrip/CI).
        print("\nTidak ada input interaktif; dibatalkan. Pakai --yes untuk otomatis.",
              file=sys.stderr)
        return False
    return answer in ("y", "ya", "yes")


def choose(options: Sequence[tuple[str, str]]) -> str | None:
    """Pilih satu opsi. options = [(id, label), ...]."""
    if BACKEND.zenity:
        argv = [BACKEND.zenity, "--list", f"--title={TITLE}", "--width=520",
                "--height=260", "--text=Aset game Plants vs. Zombies mau diambil dari mana?",
                "--column=ID", "--column=Pilihan", "--hide-column=1", "--print-column=1"]
        for identifier, label in options:
            argv += [identifier, label]
        result = _run(argv)
        if result.returncode != 0:
            return None
        choice = result.stdout.strip()
        return choice or None
    if BACKEND.kdialog:
        argv = [BACKEND.kdialog, "--title", TITLE, "--menu",
                "Aset game mau diambil dari mana?"]
        for identifier, label in options:
            argv += [identifier, label]
        result = _run(argv)
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None

    print("\nAset game mau diambil dari mana?")
    for index, (_identifier, label) in enumerate(options, 1):
        print(f"  {index}. {label}")
    try:
        raw = input("Pilih nomor: ").strip()
    except EOFError:
        return None
    try:
        return options[int(raw) - 1][0]
    except (ValueError, IndexError):
        return None


# -------------------------------------------------------------------- pickers
def pick_file(message: str, patterns: Sequence[str] | None = None) -> str | None:
    filters = patterns or ["*.iso", "*.ISO", "*.zip", "*.exe", "*.bin", "*.img"]
    filter_args: list[str] = []
    if BACKEND.zenity:
        joined = " ".join(filters)
        filter_args = ["--file-filter", f"ISO / ZIP / EXE | {joined}",
                       "--file-filter", "Semua file | *"]
        result = _run([BACKEND.zenity, "--file-selection", f"--title={message}",
                       *filter_args])
        return result.stdout.strip() if result.returncode == 0 else None
    if BACKEND.kdialog:
        result = _run([BACKEND.kdialog, "--title", message,
                       "--getopenfilename", os.path.expanduser("~"),
                       "ISO / ZIP / EXE (*.iso *.ISO *.zip *.exe *.bin *.img)"])
        return result.stdout.strip() if result.returncode == 0 else None

    try:
        raw = input(f"{message}\nPath file ISO: ").strip()
    except EOFError:
        return None
    return raw or None


def pick_dir(message: str) -> str | None:
    if BACKEND.zenity:
        result = _run([BACKEND.zenity, "--file-selection", "--directory",
                       f"--title={message}"])
        return result.stdout.strip() if result.returncode == 0 else None
    if BACKEND.kdialog:
        result = _run([BACKEND.kdialog, "--title", message, "--getexistingdirectory",
                       os.path.expanduser("~")])
        return result.stdout.strip() if result.returncode == 0 else None

    try:
        raw = input(f"{message}\nPath folder: ").strip()
    except EOFError:
        return None
    return raw or None


# ------------------------------------------------------------------- progress
class Progress:
    """Bar progres; no-op kalau tidak ada GUI."""

    def __init__(self, message: str) -> None:
        self.message = message
        self._proc: subprocess.Popen[str] | None = None
        self._last = -1
        if BACKEND.zenity:
            self._proc = subprocess.Popen(
                [BACKEND.zenity, "--progress", f"--title={TITLE}",
                 "--width=440", "--auto-close", "--no-cancel",
                 f"--text={message}", "--percentage=0"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, text=True,
            )

    def update(self, label: str, done: int, total: int) -> None:
        percent = 0 if total <= 0 else int(done * 100 / total)
        if percent == self._last:
            return
        self._last = percent
        if self._proc and self._proc.stdin:
            try:
                self._proc.stdin.write(f"# {label}\n{percent}\n")
                self._proc.stdin.flush()
            except (BrokenPipeError, ValueError):
                self._proc = None
        elif BACKEND.name == "terminal" and percent % 10 == 0:
            print(f"\r{label}: {percent}%", end="", flush=True)

    def close(self) -> None:
        if self._proc:
            try:
                if self._proc.stdin:
                    self._proc.stdin.write("100\n")
                    self._proc.stdin.close()
            except (BrokenPipeError, ValueError):
                pass
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None
        elif BACKEND.name == "terminal":
            print()
