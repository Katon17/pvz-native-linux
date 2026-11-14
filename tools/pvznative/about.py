# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Dialog About (Tentang) untuk jendela Pengaturan.

Dijalankan dari tombol "Tentang" di jendela Pengaturan, atau langsung lewat
`pvz-native --settings --about`.
"""

from __future__ import annotations

import subprocess
import sys

APP_TITLE = "Tentang"

AUTHOR = "Katon Bagaskoro"

LINKS = (
    ("Saweria", "https://saweria.co/Kabako"),
    ("Ko-fi", "https://ko-fi.com/katonbagaskoro"),
    ("PvZ-Portable (engine)", "https://github.com/wszqkzqk/PvZ-Portable"),
    ("Lisensi engine (LGPL-3.0)", "https://www.gnu.org/licenses/lgpl-3.0.html"),
)

DONATE_LINKS = LINKS[:2]


def get_version() -> str:
    """Versi paket. File VERSION ditanam build-deb.sh di sisi paket."""
    from pathlib import Path

    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "VERSION",   # terpasang: /usr/lib/pvz-native/VERSION
        here.parent / "VERSION",
        here.parent.parent.parent / "VERSION",  # source tree: <repo>/VERSION
    ]
    for candidate in candidates:
        try:
            text = candidate.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if text:
            return text
    try:
        from . import __version__ as fallback
    except ImportError:  # pragma: no cover
        return "0.0.0"
    return fallback


def _open_url(url: str) -> str:
    """Buka URL di browser. Kembalikan pesan galat ("" kalau berhasil)."""
    try:
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return ""
    except OSError:
        pass
    try:
        import webbrowser

        if webbrowser.open(url):
            return ""
    except Exception:  # pragma: no cover - webbrowser jarang melempar
        pass
    return url


def run(parent=None) -> int:
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
    except (ImportError, ValueError):
        print(
            "GTK3 (python3-gi) tidak tersedia.\n\n"
            f"pvz-native — dibuat oleh {AUTHOR}\n"
            + "\n".join(f"  {nama}: {url}" for nama, url in LINKS),
            file=sys.stderr,
        )
        return 1

    window = Gtk.Dialog(title=APP_TITLE)
    window.set_default_size(460, -1)
    window.set_border_width(16)
    window.set_position(Gtk.WindowPosition.CENTER)
    if parent is not None:
        window.set_transient_for(parent)
        window.set_modal(True)
    window.add_button("Tutup", Gtk.ResponseType.CLOSE)

    box = window.get_content_area()
    box.set_spacing(10)

    judul = Gtk.Label()
    judul.set_markup("<b>Plants vs. Zombies — Linux Native</b>")
    judul.set_xalign(0)
    box.add(judul)

    versi = Gtk.Label()
    versi.set_markup(f"<small>Versi {get_version()}</small>")
    versi.set_xalign(0)
    box.add(versi)

    penulis = Gtk.Label()
    penulis.set_markup(f"Dibuat oleh <b>{AUTHOR}</b>")
    penulis.set_xalign(0)
    box.add(penulis)

    desk = Gtk.Label()
    desk.set_markup(
        "<small>Launcher dan installer ini membantu menjalankan Plants vs. "
        "Zombies di Linux memakai engine sumber terbuka PvZ-Portable.\n"
        "Paket tidak memuat aset game; aset diambil dari salinan milikmu "
        "sendiri.</small>"
    )
    desk.set_xalign(0)
    desk.set_line_wrap(True)
    desk.set_max_width_chars(48)
    box.add(desk)

    box.add(Gtk.Separator())

    dukung = Gtk.Label()
    dukung.set_markup("<b>Dukung proyek ini</b>")
    dukung.set_xalign(0)
    box.add(dukung)

    pesan_galat = Gtk.Label()
    pesan_galat.set_xalign(0)
    pesan_galat.set_line_wrap(True)

    def buat_baris(teks: str, url: str) -> "Gtk.Box":
        """Satu tautan: nama (bisa diklik) + URL tercetak di bawahnya."""
        baris = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        tombol = Gtk.LinkButton.new_with_label(url, teks)
        tombol.set_halign(Gtk.Align.START)
        tombol.set_tooltip_text(url)

        def saat_klik(_btn) -> bool:
            galat = _open_url(url)
            if galat:
                pesan_galat.set_markup(
                    f"<small>Tidak bisa membuka browser. Salin sendiri:\n"
                    f"<tt>{galat}</tt></small>"
                )
            return True  # True = jangan pakai handler bawaan GTK

        tombol.connect("activate-link", saat_klik)

        alamat = Gtk.Label()
        alamat.set_markup(f"<small><span alpha='55%'>{url}</span></small>")
        alamat.set_xalign(0)
        alamat.set_selectable(True)
        alamat.set_margin_start(2)

        baris.add(tombol)
        baris.add(alamat)
        return baris

    for nama, url in DONATE_LINKS:
        box.add(buat_baris(nama, url))

    box.add(pesan_galat)
    box.add(Gtk.Separator())

    kredit = Gtk.Label()
    kredit.set_markup("<b>Kredit</b>")
    kredit.set_xalign(0)
    box.add(kredit)

    for nama, url in LINKS[2:]:
        box.add(buat_baris(nama, url))

    hak = Gtk.Label()
    hak.set_markup(
        "<small>Plants vs. Zombies © Electronic Arts. Proyek ini tidak resmi "
        "dan tidak berafiliasi dengan EA.</small>"
    )
    hak.set_xalign(0)
    hak.set_line_wrap(True)
    hak.set_max_width_chars(48)
    box.add(hak)

    window.show_all()
    # Rapatkan tinggi dialog ke isinya; jangan sisakan ruang kosong besar.
    window.set_resizable(False)
    lebar, _tinggi = window.get_size()
    while Gtk.events_pending():
        Gtk.main_iteration()
    window.resize(lebar, window.get_size()[1])
    window.run()
    window.destroy()
    return 0
