# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Ekstraksi aset dari **installer** Plants vs. Zombies (bukan dari folder game).

Kenapa modul ini ada
--------------------
Sebagian besar ISO Plants vs. Zombies yang beredar (termasuk rilis resmi CD
PopCap 1.2.0.1073) TIDAK berisi file game yang siap pakai. Isinya adalah
installer:

    installers/PlantsVsZombiesSetup.exe   (InstallShield self-extractor)

dan di dalamnya ada CAB Microsoft berisi:

    files/Plants vs. Zombies/main.pak
    files/Plants vs. Zombies/PlantsVsZombies.dat
    ...

Tanpa modul ini, user harus memasang game di Windows/Wine dulu — yang jadi
tidak masuk akal untuk sebuah proyek "native Linux".

Catatan penting soal struktur asetnya
-------------------------------------
`main.pak` di dalam installer menyimpan **seluruh** aset game, termasuk
`properties/LawnStrings.txt` dan `properties/resources.xml`. Engine membaca
`resources.xml` dan `LawnStrings.txt` dari dalam pak, sementara file
`properties/*` di luar pak hanya override opsional. Jadi cukup:

    main.pak  +  properties/  (hasil ekstraksi entri properties/ dari pak)

dan game bisa jalan tanpa pernah menjalankan installer-nya.

Kenapa butuh cabextract
-----------------------
CAB PopCap memakai kompresi **LZX**, yang tidak didukung pustaka standar
Python. Menulis dekoder LZX sendiri tidak sepadan risikonya. Karena itu:

  * kalau `cabextract` tersedia  -> dipakai (deklarasi dependensi paket .deb)
  * kalau tidak                  -> pesan jelas + perintah yang harus dijalankan
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import cab as cab_mod
from . import pak as pak_mod

ProgressFn = Callable[[str, int, int], None]


class InstallerError(Exception):
    """Installer tidak bisa dibaca atau diekstrak."""


@dataclass
class InstallerPlan:
    """Rencana ekstraksi dari sebuah installer."""

    source: Path
    member_path: str          # path main.pak di dalam arsip, mis. "files/Plants vs. Zombies/main.pak"
    pak_size: int


CABEXTRACT_HINT = (
    "Installer Plants vs. Zombies memakai kompresi CAB 'LZX'. Launcher ini\n"
    "butuh cabextract untuk membukanya (paketnya kecil, ~100 KB):\n\n"
    "    sudo apt install cabextract\n\n"
    "Setelah itu jalankan ulang penyiapan."
)


def have_cabextract() -> bool:
    return shutil.which("cabextract") is not None


def _read_head(path: Path, size: int) -> bytes:
    with open(path, "rb") as handle:
        return handle.read(size)


def find_main_pak(path: Path) -> InstallerPlan | None:
    """Deteksi apakah file ini installer yang berisi main.pak.

    Mengembalikan InstallerPlan kalau iya, None kalau bukan.
    """
    try:
        blob = path.read_bytes()
    except OSError as exc:
        raise InstallerError(f"Tidak bisa membaca {path.name}: {exc}") from exc
    if len(blob) < 64:
        return None

    for index in cab_mod.describe_installers(blob):
        candidates = cab_mod.list_main_pak_candidates(index)
        if candidates:
            best = max(candidates, key=lambda e: e.size)
            return InstallerPlan(path, best.name, best.size)

    return None


def looks_like_windows_installer(path: Path) -> bool:
    """True kalau file tampak installer Windows (untuk pesan error yang tepat)."""
    try:
        with open(path, "rb") as handle:
            magic = handle.read(2)
    except OSError:
        return False
    return magic == b"MZ" or path.suffix.lower() == ".exe"


def extract_main_pak(plan: InstallerPlan, destination: Path,
                     progress: ProgressFn | None = None) -> Path:
    """Ambil main.pak dari installer ke `destination`."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()

    # Strategi: coba dekoder bawaan dulu (CAB NONE/MSZIP, tanpa dependensi).
    # Kalau CAB-nya memakai LZX/Quantum — yang tidak bisa didekode dengan
    # standard library — baru pakai cabextract.
    try:
        return _extract_with_python(plan, destination, progress)
    except (cab_mod.CabError, OSError):
        if not have_cabextract():
            raise InstallerError(CABEXTRACT_HINT) from None

    return _extract_with_cabextract(plan, destination, progress)


def _extract_with_python(plan: InstallerPlan, destination: Path,
                         progress: ProgressFn | None) -> Path:
    blob = plan.source.read_bytes()
    target_name = plan.member_path.replace("\\", "/")
    for index in cab_mod.describe_installers(blob):
        unsupported = cab_mod.unsupported_compression(index)
        if unsupported:
            raise cab_mod.CabError(
                f"CAB memakai kompresi {unsupported}; butuh cabextract."
            )
        for name, payload in cab_mod.extract_files(blob, index, [target_name]):
            destination.write_bytes(payload)
            if progress:
                progress("Mengekstrak main.pak dari installer", 1, 1)
            return destination
    raise cab_mod.CabError("main.pak tidak ditemukan di dalam CAB.")


def _extract_with_cabextract(plan: InstallerPlan, destination: Path,
                             progress: ProgressFn | None) -> Path:
    if progress:
        progress("Mengekstrak main.pak dari installer (LZX)", 0, plan.pak_size)

    with tempfile.TemporaryDirectory(prefix="pvz-cab-") as temp:
        temp_path = Path(temp)
        # cabextract memakai wildcard pada nama lengkap di dalam arsip.
        pattern = "*" + plan.member_path.rsplit("/", 1)[-1]
        command = [
            "cabextract", "--quiet", "--directory", str(temp_path),
            "--filter", pattern, str(plan.source),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            if "no files" in detail.lower() or result.returncode == 1:
                raise InstallerError(
                    "cabextract tidak menemukan main.pak di dalam installer.\n"
                    f"Detail: {detail or 'tidak ada keluaran'}"
                )
            if "is not a cabinet" in detail.lower():
                raise InstallerError(
                    "File ini bukan CAB Microsoft yang bisa dibaca cabextract.\n"
                    "Kalau ini installer InstallShield asli (bukan PopCap CD), "
                    "pasang game-nya dulu di Wine lalu pilih mode folder.\n"
                    f"Detail: {detail}"
                )
            raise InstallerError(f"cabextract gagal: {detail}")

        produced = sorted(temp_path.rglob("main.pak"), key=lambda p: p.stat().st_size)
        if not produced:
            raise InstallerError(
                "cabextract selesai tetapi main.pak tidak muncul. "
                "Laporkan ini sebagai bug beserta nama file installer-nya."
            )
        largest = produced[-1]
        shutil.move(str(largest), destination)

    if not pak_mod.is_valid_magic(pak_mod.read_magic(destination)):
        raise InstallerError(
            "File main.pak hasil ekstraksi tidak valid. "
            "Installer mungkin bukan versi Plants vs. Zombies GOTY PC."
        )
    if progress:
        progress("Mengekstrak main.pak dari installer (LZX)", plan.pak_size,
                 plan.pak_size)
    return destination


def extract_properties(pak_path: Path, target_dir: Path,
                       progress: ProgressFn | None = None) -> list[str]:
    """Keluarkan entri properties/ dari dalam main.pak.

    Ini yang membuat game bisa jalan tanpa menjalankan installer Windows:
    `resources.xml` dan `LawnStrings.txt` memang tinggal di dalam pak.
    Mengeluarkannya juga memudahkan `--verify` dan membuat struktur folder
    sama seperti instalasi biasa.
    """
    reader = pak_mod.PakReader(pak_path)
    names = reader.property_entries()
    if not names:
        return []

    written: list[str] = []
    for position, name in enumerate(names, 1):
        entry = reader.find(name)
        if entry is None:
            continue
        relative = name.split("/", 1)[1] if "/" in name else name.rsplit("/", 1)[-1]
        destination = target_dir / "properties" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(reader.open(entry))
        written.append(relative)
        if progress:
            progress(f"Mengekstrak properties/{relative}", position, len(names))
    return written


def extract_loose_properties(
    plan: InstallerPlan, target_dir: Path, progress: ProgressFn | None = None
) -> list[str]:
    """Ekstrak `properties/` milik installer (file yang TIDAK ada di main.pak).

    `resources.xml` di dalam main.pak mendeklarasikan
    `<Image id="PARTNER_LOGO" path="partner_logo" />`, dan gambar itu hanya
    ada sebagai file longgar di installer. Tanpa file ini engine berhenti
    dengan "Failed to load image: properties/partner_logo".
    """
    wanted_suffix = "/properties/"
    destination_root = target_dir / "properties"

    if have_cabextract():
        written = _extract_loose_with_cabextract(plan, destination_root, progress)
        if written:
            return written

    return _extract_loose_with_python(plan, destination_root, progress)


def _extract_loose_with_cabextract(
    plan: InstallerPlan, destination_root: Path, progress: ProgressFn | None
) -> list[str]:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="pvz-props-") as temp:
        temp_path = Path(temp)
        command = [
            "cabextract", "--quiet", "--directory", str(temp_path),
            "--filter", "*properties/*", str(plan.source),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0 and not list(temp_path.rglob("*")):
            return []

        written: list[str] = []
        candidates = [p for p in temp_path.rglob("*") if p.is_file()]
        for index, candidate in enumerate(sorted(candidates), 1):
            parts = candidate.as_posix().split("/")
            if "properties" not in parts:
                continue
            position = parts.index("properties")
            relative = "/".join(parts[position + 1:])
            if not relative:
                continue
            destination = destination_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, destination)
            written.append(relative)
            if progress:
                progress(f"Mengekstrak properties/{relative}", index, len(candidates))
        return written


def _extract_loose_with_python(
    plan: InstallerPlan, destination_root: Path, progress: ProgressFn | None
) -> list[str]:
    blob = plan.source.read_bytes()
    written: list[str] = []
    for index in cab_mod.describe_installers(blob):
        if cab_mod.unsupported_compression(index):
            continue
        for name, payload in cab_mod.extract_files(blob, index):
            lower = name.lower()
            if "/properties/" not in lower:
                continue
            relative = name.split("/properties/", 1)[1]
            if not relative:
                continue
            destination = destination_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
            written.append(relative)
    if progress and written:
        progress("Mengekstrak properties/ dari installer", len(written), len(written))
    return written


# File yang WAJIB ada di dalam main.pak. Kalau salah satu hilang, engine tidak
# bisa mencapai layar judul dan akan berhenti (atau crash) saat memuat.
REQUIRED_PAK_ENTRIES = (
    "properties/resources.xml",
    "properties/LawnStrings.txt",
    "reanim/LoadBar_sprout.reanim",
    "compiled/reanim/LoadBar_sprout.reanim.compiled",
)


def audit_pak_contents(pak_path: "Path | str") -> dict[str, object]:
    """Periksa apakah main.pak berisi file yang diminta engine saat startup.

    Kasus nyata: main.pak 24 MB dari build lain (bukan rilis PC 1.2.0.1073)
    lolos `--verify` karena semua gambar yang dideklarasikan ada, tetapi
    engine tetap berhenti dengan:

        missing resource compiled/reanim/LoadBar_sprout.reanim.compiled

    Preflight ini menangkap kondisi tersebut sebelum game dijalankan.
    """
    pak_path = Path(pak_path)
    try:
        reader = pak_mod.PakReader(pak_path)
    except (pak_mod.PakError, OSError) as exc:
        return {"error": str(exc), "missing": [], "entries": 0, "size": 0}

    names = {entry.name.lower() for entry in reader.entries}
    missing = [name for name in REQUIRED_PAK_ENTRIES if name.lower() not in names]
    return {
        "error": None,
        "missing": missing,
        "entries": len(reader.entries),
        "size": pak_path.stat().st_size,
    }


# Gambar yang memang dibuat engine saat runtime (tidak perlu ada di disk).
RUNTIME_ONLY_IMAGES = {"blank"}


def audit_resources(assets_dir: Path) -> dict[str, list[str]]:
    """Periksa apakah semua gambar yang dideklarasikan resources.xml tersedia.

    Ini menangkap kasus nyata: `resources.xml` (di dalam main.pak) mendeklarasikan
    `<Image id="PARTNER_LOGO" path="partner_logo" />`, tetapi file gambarnya
    hanya dikirim sebagai file longgar di installer. Kalau file longgar tidak
    diekstrak, engine berhenti dengan "Failed to load image".

    Return: {"missing": [...], "checked": n}
    """
    import re

    pak_path = assets_dir / "main.pak"
    if not pak_path.is_file():
        return {"missing": [], "checked": 0}

    reader = pak_mod.PakReader(pak_path)
    entry = reader.find("properties/resources.xml")
    if entry is None:
        return {"missing": [], "checked": 0}
    manifest = reader.open(entry).decode("utf-8", errors="replace")

    declared = re.findall(r'<Image[^>]*path="([^"]+)"', manifest)

    in_pak = {
        item.name.lower().rsplit("/", 1)[-1] for item in reader.entries
    }
    loose: set[str] = set()
    properties = assets_dir / "properties"
    if properties.is_dir():
        for path in properties.rglob("*"):
            if path.is_file():
                loose.add(path.name.lower())

    missing: list[str] = []
    for candidate in declared:
        stem = candidate.lower().replace("\\", "/").rsplit("/", 1)[-1]
        if stem in RUNTIME_ONLY_IMAGES:
            continue
        if any(f"{stem}{ext}" in in_pak or f"{stem}{ext}" in loose
               for ext in (".png", ".jpg", ".gif", ".jpeg", ".bmp", "")):
            continue
        missing.append(candidate)

    return {"missing": missing, "checked": len(declared)}


def detect_version(pak_path: Path) -> str:
    """Tebak versi aset langsung dari LawnStrings di dalam main.pak."""
    from .assets import _detect_version_from_lawnstrings

    text = pak_mod.read_lawnstrings(pak_path)
    if not text:
        return "unknown"
    return _detect_version_from_lawnstrings(text)
