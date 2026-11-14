# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Pembaca PopCap `main.pak`.

`main.pak` versi PC lama (termasuk yang dijual di CD) menyimpan seluruh byte
file dengan XOR 0xF7. Header aslinya `0xBAC04AC0` (little-endian) sehingga di
disk terlihat sebagai `0x4D37BD37`. Engine resmi melakukan XOR yang sama saat
membaca, jadi file mentah dari CD tetap valid — launcher harus menerima
keduanya, dan kalau perlu membaca isinya lewat XOR.

Struktur (setelah XOR):
    u32 magic    = 0xBAC04AC0
    u32 version  = 0 (hanya versi 0 yang didukung)
    berulang:
        u8  flags        (bit 0x80 = akhir tabel)
        u8  name_width
        u8  name[name_width]   (pemisah '\\', dikonversi ke '/')
        i32 size
        i64 filetime
    lalu data setiap file secara berurutan.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator

PAK_MAGIC = 0xBAC04AC0
PAK_MAGIC_ON_DISK_XOR = PAK_MAGIC ^ 0xF7F7F7F7   # 0x4D37BD37
XOR_KEY = 0xF7
FLAG_END = 0x80


class PakError(Exception):
    """main.pak tidak bisa dibaca."""


@dataclass(frozen=True)
class PakEntry:
    name: str
    size: int
    data_offset: int


def _xor(data: bytes) -> bytes:
    return bytes(byte ^ XOR_KEY for byte in data)


def read_magic(path: "Path | str") -> int:
    with open(path, "rb") as handle:
        head = handle.read(4)
    if len(head) < 4:
        raise PakError("main.pak terlalu kecil.")
    return int.from_bytes(head, "little")


def is_valid_magic(value: int) -> bool:
    return value in (PAK_MAGIC, PAK_MAGIC_ON_DISK_XOR)


def is_xor_encoded(path: "Path | str") -> bool:
    """True kalau file di disk XOR-encoded (dump mentah dari CD)."""
    return read_magic(path) == PAK_MAGIC_ON_DISK_XOR


class PakReader:
    """Iterasi tabel isi main.pak tanpa memuat seluruh file ke RAM."""

    def __init__(self, path: "Path | str | BinaryIO", *, xor: bool | None = None) -> None:
        # Terima file object juga supaya pak bisa dibaca langsung dari ISO/ZIP
        # tanpa mengekstrak ke disk lebih dulu.
        if hasattr(path, "read"):
            self.path = None
            self._stream = path
            self._stream.seek(0)
            head = self._stream.read(4)
            if len(head) < 4:
                raise PakError("main.pak terlalu kecil.")
            magic = int.from_bytes(head, "little")
        else:
            self.path = Path(path)
            self._stream = None
            magic = read_magic(self.path)
        if not is_valid_magic(magic):
            raise PakError(
                f"Bukan main.pak PvZ yang valid (magic 0x{magic:08X})."
            )
        self.xor = xor if xor is not None else magic == PAK_MAGIC_ON_DISK_XOR
        self._handle: BinaryIO | None = None
        self.entries: list[PakEntry] = []
        self.data_start = 0
        self._parse_table()

    def _read(self, handle: BinaryIO, count: int) -> bytes:
        raw = handle.read(count)
        if len(raw) != count:
            raise PakError("main.pak terpotong saat membaca tabel.")
        return _xor(raw) if self.xor else raw

    def _parse_table(self) -> None:
        if self._stream is not None:
            handle = self._stream
            handle.seek(0)
            self._parse_from(handle)
            return
        with open(self.path, "rb") as handle:
            self._parse_from(handle)

    def _parse_from(self, handle: BinaryIO) -> None:
        if int.from_bytes(self._read(handle, 4), "little") != PAK_MAGIC:
            raise PakError("Signature main.pak tidak valid.")
        if int.from_bytes(self._read(handle, 4), "little") != 0:
            raise PakError("Versi main.pak tidak didukung (hanya versi 0).")

        running = 0
        while True:
            flags = self._read(handle, 1)[0]
            if flags & FLAG_END:
                break
            name_width = self._read(handle, 1)[0]
            name = self._read(handle, name_width).decode("utf-8", errors="replace")
            size = struct.unpack("<i", self._read(handle, 4))[0]
            self._read(handle, 8)  # filetime, tidak dipakai
            if size < 0:
                raise PakError(f"Ukuran negatif untuk entri {name}.")
            normalized = name.replace("\\", "/")
            self.entries.append(
                PakEntry(name=normalized, size=size, data_offset=running)
            )
            running += size
        self.data_start = handle.tell()

    def open(self, entry: PakEntry) -> bytes:
        """Baca isi satu entri (dekode XOR kalau perlu)."""
        with open(self.path, "rb") as handle:
            handle.seek(self.data_start + entry.data_offset)
            raw = handle.read(entry.size)
        if len(raw) != entry.size:
            raise PakError(f"Entri {entry.name} terpotong.")
        return _xor(raw) if self.xor else raw

    def find(self, suffix: str) -> PakEntry | None:
        needle = suffix.lower().lstrip("/")
        for entry in self.entries:
            if entry.name.lower() == needle:
                return entry
        for entry in self.entries:
            if entry.name.lower().endswith("/" + needle):
                return entry
        return None

    def iter_text(self, suffix: str) -> Iterator[str]:
        """Baca entri sebagai teks, menebak UTF-16 vs UTF-8."""
        entry = self.find(suffix)
        if entry is None:
            return
        raw = self.open(entry)
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            yield raw.decode("utf-16", errors="replace")
            return
        try:
            yield raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            yield raw.decode("cp1252", errors="replace")

    def property_entries(self) -> list[str]:
        return [
            entry.name
            for entry in self.entries
            if entry.name.lower().startswith("properties/")
        ]


def read_lawnstrings(path: "Path | str") -> str | None:
    """Ambil isi properties/LawnStrings.txt dari dalam main.pak."""
    try:
        reader = PakReader(path)
    except (PakError, OSError):
        return None
    for text in reader.iter_text("properties/lawnstrings.txt"):
        return text
    return None
