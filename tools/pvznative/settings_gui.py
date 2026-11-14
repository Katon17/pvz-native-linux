# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Jendela Pengaturan (GTK3) — pengganti terminal untuk opsi tampilan.

Dijalankan lewat `pvz-native --settings`. Semua perubahan ditulis dengan
fungsi yang sama yang dipakai CLI (`display.py`), jadi tidak ada logika ganda.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import config

APP_TITLE = "Pengaturan Plants vs. Zombies"


def _config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
    return Path(base) / "pvz-native"


def wide_conf() -> Path:
    return _config_dir() / "widescreen"


def read_wide() -> bool:
    path = wide_conf()
    if not path.is_file():
        return False
    return path.read_text(errors="replace").strip() not in ("", "0")


def write_wide(enabled: bool) -> None:
    path = wide_conf()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("1" if enabled else "0")


def _launcher_candidates() -> "list[str]":
    """Cari launcher: PATH dulu, lalu lokasi bawaan paket .deb."""
    found: list[str] = []
    which = shutil.which("pvz-native")
    if which:
        found.append(which)
    for candidate in ("/usr/bin/pvz-native", "/usr/local/bin/pvz-native"):
        if os.access(candidate, os.X_OK) and candidate not in found:
            found.append(candidate)
    return found


def apply_now(widescreen: bool) -> str:
    """Tulis preferensi lalu jalankan game di latar belakang."""
    write_wide(widescreen)
    env = dict(os.environ)
    env["PVZ_WIDESCREEN"] = "1" if widescreen else "0"

    candidates = _launcher_candidates()
    for launcher in candidates:
        try:
            subprocess.Popen(
                [launcher],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return ""
        except OSError:
            continue

    return (
        "Tidak menemukan perintah 'pvz-native'.\n\n"
        "Pengaturan sudah tersimpan — jalankan game lewat menu aplikasi "
        "atau terminal."
    )


def run(about_only: bool = False) -> int:
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
    except (ImportError, ValueError):
        print(
            "GTK3 (python3-gi) tidak tersedia. Pakai terminal:\n"
            "  pvz-native --wide\n"
            "  pvz-native --no-wide\n"
            "  pvz-native --display fullscreen",
            file=sys.stderr,
        )
        return 1

    if about_only:
        from . import about as about_mod

        return about_mod.run()

    from . import display as display_mod

    registry = config.saves_dir() / "registry.regemu"
    fullscreen_now = display_mod.screen_mode(registry) != "windowed"

    window = Gtk.Window(title=APP_TITLE)
    window.set_default_size(520, -1)
    window.set_border_width(18)
    window.set_position(Gtk.WindowPosition.CENTER)
    window.connect("destroy", Gtk.main_quit)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    window.add(outer)

    heading = Gtk.Label()
    heading.set_markup("<b>Tampilan</b>")
    heading.set_xalign(0)
    outer.add(heading)

    wide_check = Gtk.CheckButton(label="Isi seluruh layar (16:9, tanpa batang hitam)")
    wide_check.set_active(read_wide())
    outer.add(wide_check)

    note = Gtk.Label()
    note.set_markup(
        "<small>Tanpa opsi ini, layar menjaga rasio asli 4:3 sehingga muncul\n"
        "batang hitam di kiri-kanan. Dengan opsi ini gambar diregangkan penuh,\n"
        "sehingga beberapa elemen menu bergeser sedikit ke tepi.</small>"
    )
    note.set_xalign(0)
    note.set_line_wrap(True)
    outer.add(note)

    full_check = Gtk.CheckButton(label="Mulai dalam mode layar penuh (fullscreen)")
    full_check.set_active(fullscreen_now)
    outer.add(full_check)

    hint = Gtk.Label()
    hint.set_markup(
        "<small>Kalau tidak dicentang, game terbuka sebagai jendela yang bisa\n"
        "di-resize. Kamu juga bisa mengubahnya dari menu Options di dalam game.</small>"
    )
    hint.set_xalign(0)
    hint.set_line_wrap(True)
    outer.add(hint)

    outer.add(Gtk.Separator())

    buttons = Gtk.Box(spacing=8)
    buttons.set_halign(Gtk.Align.END)
    outer.add(buttons)

    about = Gtk.Button(label="Tentang")
    cancel = Gtk.Button(label="Tutup")
    save = Gtk.Button(label="Simpan")
    play = Gtk.Button(label="Simpan & Mainkan")
    buttons.add(about)
    buttons.add(cancel)
    buttons.add(save)
    buttons.add(play)

    def collect() -> None:
        display_mod.set_screen_mode(registry, full_check.get_active())
        write_wide(wide_check.get_active())

    def on_about(_button) -> None:
        from . import about as about_mod

        about_mod.run(parent=window)

    def on_cancel(_button) -> None:
        Gtk.main_quit()

    def on_save(_button) -> None:
        collect()
        Gtk.main_quit()

    def on_play(_button) -> None:
        collect()
        message = apply_now(wide_check.get_active())
        if message:
            dialog = Gtk.MessageDialog(
                transient_for=window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=message,
            )
            dialog.run()
            dialog.destroy()
            return
        Gtk.main_quit()

    about.connect("clicked", on_about)
    cancel.connect("clicked", on_cancel)
    save.connect("clicked", on_save)
    play.connect("clicked", on_play)

    window.show_all()
    Gtk.main()
    return 0
