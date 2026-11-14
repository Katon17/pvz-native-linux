# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Deteksi, validasi, dan ekstraksi aset Plants vs. Zombies dari image ISO.

Prinsip yang dipegang proyek ini:
  * Launcher TIDAK PERNAH mengunduh, membundel, atau mendistribusikan aset game.
  * Semua aset berasal dari ISO / instalasi Steam / instalasi PopCap milik user.
  * File aset disalin ke XDG data dir, bukan ke dalam paket .deb.
"""

from __future__ import annotations

import atexit
import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from . import cab as cab_mod
from . import config
from . import pak as pak_mod
from .iso9660 import Iso9660, IsoEntry

PAK_MAGIC_LE = 0xBAC04AC0
REQUIRED_FILES = ("main.pak",)
REQUIRED_DIRS = ("properties",)

# Signature versi aset, didokumentasikan oleh upstream PvZ-Portable:
# pada 1.2.0.1073 template CRAZY_DAVE_1700 menyisakan "0" setelah {SELL_PRICE}
# (karena engine membagi harga dengan 10), sedangkan 1.2.0.1096 sudah
# menghapus "0" tersebut. Lihat README upstream bagian "Game Version
# Compatibility". Ini heuristik, bukan kebenaran mutlak.
_SELL_PRICE_1073_MARK = "{SELL_PRICE}0"

ProgressFn = Callable[[str, int, int], None]


class AssetError(Exception):
    """Aset tidak ditemukan / tidak valid."""


@dataclass
class AssetSet:
    """Hasil validasi satu kumpulan aset."""

    source: Path
    kind: str                       # "iso" | "dir"
    pak_path: str                   # lokasi main.pak relatif terhadap source
    properties_path: str            # lokasi folder properties/
    pak_size: int
    pak_sha256: str
    version_hint: str = "unknown"   # "1.2.0.1073" | "1.2.0.1096?" | "unknown"
    warnings: list[str] = field(default_factory=list)
    installer_member: str | None = None   # untuk kind == "installer"
    missing_required: list[str] = field(default_factory=list)


# File yang wajib ada di dalam main.pak agar engine bisa boot. Pak dari build
# lain (mis. 24,9 MB bertanggal 2009) tidak memuat reanim/LoadBar_sprout dan
# membuat engine berhenti dengan "missing resource".
REQUIRED_PAK_ENTRIES = (
    "properties/resources.xml",
    "properties/LawnStrings.txt",
    "reanim/LoadBar_sprout.reanim",
    "compiled/reanim/LoadBar_sprout.reanim.compiled",
)


class IncompatibleAssets(AssetError):
    """Aset ada, tapi tidak memuat file yang dibutuhkan engine."""

    def __init__(self, message: str, missing: "list[str]") -> None:
        super().__init__(message)
        self.missing = missing


def required_missing(pak_stream) -> "list[str]":
    """Kembalikan daftar file wajib yang tidak ada di dalam pak.

    `pak_stream` harus seekable dan berada di posisi awal.
    """
    from . import pak as pak_mod

    pak_stream.seek(0)
    reader = pak_mod.PakReader(pak_stream)
    names = {entry.name.lower() for entry in reader.entries}

    def present(needle: str) -> bool:
        # Sebagian build memakai huruf besar/kecil berbeda, dan sebagian
        # membuang prefix folder. Cocokkan juga berdasarkan basename supaya
        # tidak salah menuduh paket yang sebenarnya lengkap.
        wanted = needle.lower()
        if wanted in names:
            return True
        base = wanted.rsplit("/", 1)[-1]
        return any(name.rsplit("/", 1)[-1] == base for name in names)

    return [name for name in REQUIRED_PAK_ENTRIES if not present(name)]


def _reject_incomplete(pak_stream, size: int, source_desc: str) -> None:
    """Tolak aset yang tidak bisa boot, dengan pesan yang bisa ditindaklanjuti."""
    try:
        missing = required_missing(pak_stream)
    except Exception:  # pak rusak/format aneh: biarkan alur lain yang menangani
        return
    if not missing:
        return
    human = config.human_size(size)
    raise IncompatibleAssets(
        f"Aset di {source_desc} tidak kompatibel dengan engine.\n\n"
        f"main.pak hanya {human} dan tidak memuat file wajib:\n"
        + "\n".join(f"  - {name}" for name in missing)
        + "\n\nIni ciri paket dari versi lain (bukan rilis PC 1.2.0.1073, "
        "yang berukuran ~42,8 MiB dan berisi 3.195 entri).\n\n"
        "Pakai aset dari rilis PC lengkap: CD original PopCap, Steam, atau "
        "EA App.",
        missing,
    )


# --------------------------------------------------------------------- helpers
def _sha256_of_stream(stream, chunk_size: int = 1 << 20) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        digest.update(chunk)
        total += len(chunk)
    return digest.hexdigest(), total


def _norm(name: str) -> str:
    return name.strip().lower()


def _is_pak(name: str) -> bool:
    return _norm(name) == "main.pak"


def _is_properties_dir(name: str) -> bool:
    return _norm(name) == "properties"


def looks_like_iso(path: Path) -> bool:
    try:
        if path.stat().st_size < 32 * 1024:
            return False
        with open(path, "rb") as fh:
            fh.seek(16 * 2048 + 1)
            return fh.read(5) == b"CD001"
    except OSError:
        return False


def _detect_version_from_lawnstrings(text: str) -> str:
    """Heuristik versi berdasarkan signature CRAZY_DAVE_1700.

    LawnStrings.txt berformat blok: satu baris berisi nama kunci di dalam
    kurung siku, lalu baris-baris berikutnya berisi isi template. Jadi
    pencarian harus per blok, bukan per baris.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if "CRAZY_DAVE_1700" not in line:
            continue
        if not line.lstrip().startswith("["):
            continue
        # Kumpulkan isi blok sampai kunci berikutnya.
        block: list[str] = []
        for follower in lines[index + 1:]:
            if follower.lstrip().startswith("[") and follower.rstrip().endswith("]"):
                break
            block.append(follower)
        template = "".join(block).replace(" ", "")
        if not template:
            continue
        if _SELL_PRICE_1073_MARK in template:
            return "1.2.0.1073"
        if "{SELL_PRICE}" in template:
            return "1.2.0.1096?"
    return "unknown"


# ------------------------------------------------------------------ ISO source
def scan_iso(iso_path: "Path | str", progress: ProgressFn | None = None) -> AssetSet:
    """Cari main.pak + properties/ di dalam ISO dan validasi isinya."""
    iso_path = Path(iso_path).expanduser()
    if not iso_path.is_file():
        raise AssetError(f"File ISO tidak ditemukan: {iso_path}")
    if not looks_like_iso(iso_path):
        raise AssetError(
            f"{iso_path.name} bukan image ISO9660 yang valid.\n"
            "Kalau ini file ZIP/RAR hasil unduhan, ekstrak dulu lalu pilih "
            "foldernya (mode 'folder'), bukan file ISO."
        )

    with Iso9660.open(iso_path) as iso:
        entries = list(iso.walk())

        # Kelompokkan berdasarkan direktori induk agar main.pak + properties/
        # yang berpasangan bisa ditemukan walau ISO-nya punya subfolder setup.
        pak_by_parent: dict[str, IsoEntry] = {}
        prop_by_parent: dict[str, IsoEntry] = {}
        for entry in entries:
            parent, _, name = entry.path.rpartition("/")
            if not entry.is_dir and _is_pak(name):
                pak_by_parent[parent] = entry
            elif entry.is_dir and _is_properties_dir(name):
                prop_by_parent[parent] = entry

        candidates = sorted(set(pak_by_parent) & set(prop_by_parent))
        if not candidates:
            found_paths = sorted({e.path for e in entries})
            found = ", ".join(found_paths[:12]) or "(kosong)"
            installer_markers = {
                "SETUP.EXE", "POPCDRUN.EXE", "AUTORUN.INF", "SETUP.INS",
                "DATA", "_SETUP.DLL", "SETUP.EXE;1",
            }
            looks_like_installer = any(
                path.upper() in installer_markers
                or path.upper().endswith(".CAB")
                or path.upper().startswith("DATA/")
                for path in found_paths
            )
            # Coba jalur installer: kadang ISO hanya berisi setup.exe dan
            # main.pak ada di dalam CAB-nya.
            embedded = _find_installer_in_iso(iso, entries, iso_path)
            if embedded is not None:
                return embedded

            hint = ""
            if looks_like_installer:
                hint = (
                    "\n\nISO ini berisi installer, bukan file game yang sudah "
                    "terpasang — dan launcher tidak menemukan main.pak yang "
                    "bisa diekstrak dari installer tersebut.\n"
                    "Pilihannya:\n"
                    "  a) Pasang game-nya dulu di Windows/Wine, lalu jalankan "
                    "launcher ini dan pilih mode 'folder' ke folder hasil "
                    "instalasinya.\n"
                    "  b) Kalau kamu punya folder PlantsVsZombies yang sudah "
                    "terpasang (mis. dari Steam), langsung pakai mode 'folder'.\n"
                    "  c) Kalau installer-nya butuh kata sandi/DRM khusus, "
                    "launcher ini memang tidak bisa membukanya."
                )
            raise AssetError(
                "Tidak menemukan pasangan main.pak + folder properties/ di ISO ini.\n"
                f"Isi ISO yang terbaca: {found}{hint}"
            )
        # Prioritas: pasangan di root, lalu yang path-nya paling pendek.
        parent = min(candidates, key=lambda p: (p != "", len(p)))
        pak_entry = pak_by_parent[parent]
        prop_entry = prop_by_parent[parent]

        warnings: list[str] = []
        if len(candidates) > 1:
            warnings.append(
                "Ditemukan lebih dari satu kumpulan aset; dipakai yang di "
                f"'{parent or '/'}'."
            )

        if progress:
            progress("Validasi main.pak", 0, pak_entry.size)
        stream = iso.open_entry(pak_entry)
        with stream:
            head = stream.read(4)
            stream.seek(0)
            sha, size = _sha256_of_stream(stream)
        if len(head) < 4:
            raise AssetError("main.pak terlalu kecil / korup.")
        magic = int.from_bytes(head, "little")
        if not pak_mod.is_valid_magic(magic):
            raise AssetError(
                "main.pak ditemukan tapi magic number-nya salah "
                f"(0x{magic:08X}, seharusnya 0x{PAK_MAGIC_LE:08X} atau "
                f"0x{pak_mod.PAK_MAGIC_ON_DISK_XOR:08X}). "
                "File kemungkinan korup atau bukan dari PvZ GOTY PC."
            )

        # Tolak ISO berisi paket yang tidak memuat file wajib engine.
        with iso.open_entry(pak_entry) as stream:
            _reject_incomplete(stream, size, f"{iso_path.name}!{pak_entry.path}")

        # Baca LawnStrings.txt (kalau ada) untuk menebak versi aset.
        version = "unknown"
        for entry in entries:
            if entry.is_dir:
                continue
            if entry.path.lower().endswith("lawnstrings.txt"):
                try:
                    raw = iso.read(entry)
                    version = _detect_version_from_lawnstrings(
                        raw.decode("utf-8", errors="replace")
                    )
                except Exception:  # pragma: no cover - heuristik saja
                    version = "unknown"
                break

    if version == "1.2.0.1096?":
        warnings.append(
            "Aset terdeteksi sebagai Steam GOTY 1.2.0.1096. Gameplay berjalan "
            "penuh, tapi ada bug kosmetik yang diketahui: teks biru di Almanac "
            "tidak muncul, label tombol 'Restart' hilang, zombie yang belum "
            "ditemui tampil '???' dan harga jual tanaman Crazy Dave terbaca 1/10. "
            "Untuk hasil terbaik gunakan aset 1.2.0.1073."
        )

    return AssetSet(
        source=iso_path,
        kind="iso",
        pak_path=pak_entry.path,
        properties_path=prop_entry.path,
        pak_size=size,
        pak_sha256=sha,
        version_hint=version,
        warnings=warnings,
    )


# ------------------------------------------------------------------ ZIP source
def scan_zip(zip_path: "Path | str", progress: ProgressFn | None = None) -> AssetSet:
    """Cari main.pak + properties/ di dalam file .zip."""
    import zipfile

    zip_path = Path(zip_path).expanduser()
    if not zip_path.is_file():
        raise AssetError(f"File ZIP tidak ditemukan: {zip_path}")

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        files = [n for n in names if not n.endswith("/")]

        # Untuk setiap main.pak, pasangannya adalah folder "properties/" di
        # direktori yang sama. Nama dibandingkan tanpa peduli huruf besar
        # kecil karena ZIP dari Windows sering memakai "Properties".
        matches: list[tuple[int, str, str]] = []   # (kedalaman, pak, prop_prefix)
        for candidate in files:
            if not _is_pak(candidate.rsplit("/", 1)[-1]):
                continue
            parent = candidate.rsplit("/", 1)[0] if "/" in candidate else ""
            prop_prefix = f"{parent}/properties/" if parent else "properties/"
            lowered = prop_prefix.lower()
            has_props = any(f.lower().startswith(lowered) for f in files) or any(
                n.lower().rstrip("/") + "/" == lowered for n in names
            )
            if has_props:
                matches.append((candidate.count("/"), candidate, prop_prefix))

        if not matches:
            raise AssetError(
                "Tidak menemukan main.pak + folder properties/ di dalam ZIP ini.\n"
                "Pastikan ZIP berisi salinan folder PlantsVsZombies yang utuh, "
                "bukan hanya installer/setup.exe."
            )

        _, pak_name, prop_prefix = min(matches, key=lambda m: m[0])

        import hashlib as _hashlib

        digest = _hashlib.sha256()
        size = 0
        with archive.open(pak_name) as stream:
            head = stream.read(4)
            digest.update(head)
            size += len(head)
            while True:
                chunk = stream.read(1 << 20)
                if not chunk:
                    break
                digest.update(chunk)
                size += len(chunk)
        magic = int.from_bytes(head, "little")
        if not pak_mod.is_valid_magic(magic):
            raise AssetError(
                f"{pak_name} bukan main.pak PvZ GOTY yang valid (magic 0x{magic:08X})."
            )

        with archive.open(pak_name) as stream:
            _reject_incomplete(stream, size, f"{zip_path.name}!{pak_name}")

        version = "unknown"
        lowered_prefix = prop_prefix.lower()
        for name in files:
            if not name.lower().startswith(lowered_prefix):
                continue
            if name.rsplit("/", 1)[-1].lower() != "lawnstrings.txt":
                continue
            try:
                version = _detect_version_from_lawnstrings(
                    archive.read(name).decode("utf-8", errors="replace")
                )
            except Exception:
                version = "unknown"
            break

    warnings: list[str] = []
    if version == "1.2.0.1096?":
        warnings.append(
            "Aset terdeteksi sebagai Steam GOTY 1.2.0.1096 (ada bug kosmetik "
            "yang diketahui; lihat README)."
        )

    return AssetSet(
        source=zip_path,
        kind="zip",
        pak_path=pak_name,
        properties_path=prop_prefix.rstrip("/"),
        pak_size=size,
        pak_sha256=digest.hexdigest(),
        version_hint=version,
        warnings=warnings,
    )


# ------------------------------------------------------------ auto detection
def scan_auto(path: "Path | str") -> AssetSet:
    """Pilih metode scan berdasarkan isi file/folder yang diberikan user."""
    path = Path(path).expanduser()
    if path.is_dir():
        return scan_dir(path)
    if not path.is_file():
        raise AssetError(f"Path tidak ditemukan: {path}")

    suffix = path.suffix.lower()
    if suffix in (".exe", ".msi"):
        return scan_installer(path)
    if suffix == ".zip":
        return scan_zip(path)
    if looks_like_iso(path):
        return scan_iso(path)
    raise AssetError(
        f"{path.name} tidak dikenali sebagai ISO atau ZIP.\n"
        "Kalau ini folder hasil ekstrak, pilih foldernya (mode 'folder')."
    )


# ----------------------------------------------------------- installer source
INSTALLER_SUFFIXES = (".exe", ".msi")

# Installer yang sudah disalin keluar dari ISO disimpan sementara di sini dan
# dibersihkan saat proses Python berakhir (user bisa membatalkan wizard).
_STAGING: list[Path] = []
atexit.register(lambda: [shutil.rmtree(p, ignore_errors=True) for p in _STAGING])


def _find_installer_in_iso(
    iso: Iso9660, entries: list[IsoEntry], iso_path: Path
) -> AssetSet | None:
    """Cari installer di dalam ISO dan periksa apakah main.pak bisa diambil.

    Mengembalikan AssetSet kind="installer" bila berhasil. Yang disalin keluar
    dari ISO hanya file installer-nya (biasanya 40 MB), bukan seluruh ISO.
    """
    from . import installer as installer_mod

    candidates = [
        entry
        for entry in entries
        if not entry.is_dir
        and entry.path.lower().endswith(INSTALLER_SUFFIXES)
    ]
    if not candidates:
        return None
    # Prioritaskan installer yang namanya menyebut Plants vs. Zombies.
    candidates.sort(
        key=lambda e: ("plants" not in e.path.lower() or "zombie" not in e.path.lower(),
                       -e.size)
    )

    staging = Path(tempfile.mkdtemp(prefix="pvz-iso-"))
    _STAGING.append(staging)

    for entry in candidates:
        local = staging / Path(entry.path).name
        with iso.open_entry(entry) as source, open(local, "wb") as sink:
            shutil.copyfileobj(source, sink, 1 << 20)

        try:
            plan = installer_mod.find_main_pak(local)
        except installer_mod.InstallerError:
            plan = None
        if plan is None:
            continue

        return AssetSet(
            source=local,
            kind="installer",
            pak_path=plan.member_path,
            properties_path="properties",
            pak_size=plan.pak_size,
            pak_sha256="",              # dihitung saat ekstraksi
            version_hint="unknown",     # dideteksi setelah ekstraksi
            warnings=[f"Aset akan diekstrak dari {Path(entry.path).name}."],
            installer_member=plan.member_path,
        )

    shutil.rmtree(staging, ignore_errors=True)
    return None


def scan_installer(path: "Path | str") -> AssetSet:
    """Periksa file installer (.exe) dan siapkan rencana ekstraksi."""
    from . import installer as installer_mod

    path = Path(path).expanduser()
    if not path.is_file():
        raise AssetError(f"File installer tidak ditemukan: {path}")

    try:
        plan = installer_mod.find_main_pak(path)
    except installer_mod.InstallerError as exc:
        raise AssetError(str(exc)) from exc

    if plan is None:
        raise AssetError(
            f"Tidak menemukan main.pak di dalam {path.name}.\n\n"
            "Kemungkinan penyebab:\n"
            "  - installer memecah data ke beberapa file (butuh file lain di "
            "folder yang sama)\n"
            "  - installer memakai proteksi/kata sandi\n"
            "  - ini bukan installer Plants vs. Zombies GOTY PC\n\n"
            "Kalau kamu punya folder hasil instalasi (Windows/Wine/Steam), "
            "pakai mode 'folder' dan arahkan ke folder PlantsVsZombies."
        )

    return AssetSet(
        source=path,
        kind="installer",
        pak_path=plan.member_path,
        properties_path="properties",
        pak_size=plan.pak_size,
        pak_sha256="",
        version_hint="unknown",
        warnings=[f"Aset akan diekstrak dari installer {path.name}."],
        installer_member=plan.member_path,
    )


# --------------------------------------------------------------- folder source
def scan_dir(root: "Path | str") -> AssetSet:
    """Cari main.pak + properties/ di dalam folder (Steam, PopCap, hasil ekstrak)."""
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise AssetError(f"Folder tidak ditemukan: {root}")

    pak_candidates: list[Path] = []
    prop_candidates: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        for filename in filenames:
            if _is_pak(filename):
                pak_candidates.append(here / filename)
        for dirname in list(dirnames):
            if _is_properties_dir(dirname):
                prop_candidates.append(here / dirname)
        if len(pak_candidates) > 8:
            break

    pairs = [
        (pak, prop)
        for pak in pak_candidates
        for prop in prop_candidates
        if pak.parent == prop.parent
    ]
    if not pairs:
        raise AssetError(
            f"Tidak menemukan pasangan main.pak + folder properties/ di {root}.\n"
            "Kalau punya ISO, pilih mode ISO. Kalau punya instalasi Steam, "
            "arahkan ke folder 'PlantsVsZombies'."
        )
    pak, prop = min(pairs, key=lambda p: len(str(p[0])))

    with open(pak, "rb") as fh:
        head = fh.read(4)
        fh.seek(0)
        sha, size = _sha256_of_stream(fh)
    magic = int.from_bytes(head, "little")
    if not pak_mod.is_valid_magic(magic):
        raise AssetError(
            f"{pak} bukan main.pak PvZ GOTY yang valid "
            f"(magic 0x{magic:08X})."
        )

    # Tolak paket yang tidak memuat file wajib engine (mis. build 2009 24 MB).
    with open(pak, "rb") as fh:
        _reject_incomplete(fh, size, str(pak))

    version = "unknown"
    for strings_file in sorted(prop.rglob("*")):
        if not strings_file.is_file() or strings_file.name.lower() != "lawnstrings.txt":
            continue
        try:
            version = _detect_version_from_lawnstrings(
                strings_file.read_text(encoding="utf-8", errors="replace")
            )
        except OSError:
            pass
        break

    warnings: list[str] = []
    if version == "1.2.0.1096?":
        warnings.append(
            "Aset terdeteksi sebagai Steam GOTY 1.2.0.1096 (ada bug kosmetik "
            "yang diketahui; lihat README)."
        )

    return AssetSet(
        source=root,
        kind="dir",
        pak_path=str(pak),
        properties_path=str(prop),
        pak_size=size,
        pak_sha256=sha,
        version_hint=version,
        warnings=warnings,
    )


# -------------------------------------------------------------------- install
def install_assets(assets: AssetSet, target: Path, progress: ProgressFn | None = None) -> None:
    """Salin aset dari sumber ke direktori data user."""
    target.mkdir(parents=True, exist_ok=True)

    if assets.kind == "dir":
        pak_src = Path(assets.pak_path)
        prop_src = Path(assets.properties_path)
        _copy_file(pak_src, target / "main.pak", progress)
        _copy_tree(prop_src, target / "properties", progress)
        return

    if assets.kind == "installer":
        from . import installer as installer_mod

        plan = installer_mod.find_main_pak(Path(assets.source))
        if plan is None:
            raise AssetError(
                "Installer tidak lagi berisi main.pak yang bisa dibaca."
            )
        target.mkdir(parents=True, exist_ok=True)
        try:
            installer_mod.extract_main_pak(plan, target / "main.pak", progress)
            # 1) properties yang tersimpan di DALAM pak (resources.xml,
            #    LawnStrings.txt, dsb.)
            installer_mod.extract_properties(target / "main.pak", target, progress)
            # 2) properties yang hanya ada sebagai file longgar di installer
            #    (mis. partner_logo.jpg yang dideklarasikan resources.xml).
            installer_mod.extract_loose_properties(plan, target, progress)
        except installer_mod.InstallerError as exc:
            raise AssetError(str(exc)) from exc

        if progress:
            progress("Memeriksa hasil ekstraksi", 1, 1)
        if not pak_mod.is_valid_magic(pak_mod.read_magic(target / "main.pak")):
            raise AssetError("main.pak hasil ekstraksi tidak valid.")
        return

    if assets.kind == "zip":
        import zipfile

        with zipfile.ZipFile(assets.source) as archive:
            pak_stream = archive.open(assets.pak_path)
            total = archive.getinfo(assets.pak_path).file_size
            done = 0
            with pak_stream, open(target / "main.pak", "wb") as dst:
                while True:
                    chunk = pak_stream.read(1 << 20)
                    if not chunk:
                        break
                    dst.write(chunk)
                    done += len(chunk)
                    if progress:
                        progress("Menyalin main.pak", done, total)

            prefix = assets.properties_path + "/"
            members = [
                n
                for n in archive.namelist()
                if n.startswith(prefix) and not n.endswith("/")
            ]
            for index, member in enumerate(sorted(members), 1):
                relative = member[len(prefix):]
                destination = target / "properties" / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(member))
                if progress:
                    progress(
                        f"Mengekstrak properties/{relative}", index, len(members)
                    )
        return

    with Iso9660.open(assets.source) as iso:
        entries = {e.path: e for e in iso.walk()}
        pak_entry = entries[assets.pak_path]
        with iso.open_entry(pak_entry) as src, open(target / "main.pak", "wb") as dst:
            total = pak_entry.size
            done = 0
            while True:
                chunk = src.read(1 << 20)
                if not chunk:
                    break
                dst.write(chunk)
                done += len(chunk)
                if progress:
                    progress("Menyalin main.pak", done, total)

        prefix = assets.properties_path + "/"
        # Cocokkan tanpa peduli huruf besar/kecil: ISO level 1 menyimpan nama
        # dalam huruf besar, sedangkan engine mencari "properties/".
        prefix_lower = prefix.lower()
        prop_entries = [
            e
            for path, e in entries.items()
            if not e.is_dir and path.lower().startswith(prefix_lower)
        ]
        for index, entry in enumerate(sorted(prop_entries, key=lambda e: e.path), 1):
            relative = entry.path[len(prefix):]
            destination = target / "properties" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(iso.read(entry))
            if progress:
                progress(f"Mengekstrak properties/{relative}", index, len(prop_entries))


def _copy_file(src: Path, dst: Path, progress: ProgressFn | None) -> None:
    total = src.stat().st_size
    done = 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "rb") as fh_in, open(dst, "wb") as fh_out:
        while True:
            chunk = fh_in.read(1 << 20)
            if not chunk:
                break
            fh_out.write(chunk)
            done += len(chunk)
            if progress:
                progress(f"Menyalin {src.name}", done, total)


def _copy_tree(src: Path, dst: Path, progress: ProgressFn | None) -> None:
    files = sorted(p for p in src.rglob("*") if p.is_file())
    for index, file_path in enumerate(files, 1):
        relative = file_path.relative_to(src)
        destination = dst / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, destination)
        if progress:
            progress(f"Mengekstrak properties/{relative}", index, len(files))


# ----------------------------------------------------------- known locations
def guess_candidates(home: Path | None = None) -> Iterable[Path]:
    """Lokasi umum instalasi PvZ yang layak dicoba otomatis."""
    home = home or Path.home()
    yield home / ".steam/steam/steamapps/common/PlantsVsZombies"
    yield home / ".local/share/Steam/steamapps/common/PlantsVsZombies"
    yield home / ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/PlantsVsZombies"
    yield home / ".wine/drive_c/Program Files (x86)/PopCap Games/PlantsVsZombies"
    yield home / ".wine/drive_c/Program Files/PopCap Games/PlantsVsZombies"
    yield home / "Games/PlantsVsZombies"
    yield Path("/usr/share/pvz-portable")


def find_existing_assets(home: Path | None = None) -> AssetSet | None:
    """Coba temukan aset yang sudah terpasang tanpa menanyakan user."""
    for candidate in guess_candidates(home):
        if not candidate.is_dir():
            continue
        try:
            return scan_dir(candidate)
        except (AssetError, OSError):
            continue
    return None
