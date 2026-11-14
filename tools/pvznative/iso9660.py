# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Pembaca ISO9660 minimal, murni Python (tanpa 7z / unar / fuse).

Tujuan: user cukup menunjuk file .iso Plants vs Zombies, tanpa perlu
memasang tool eksternal apa pun untuk mengekstraknya.

Yang didukung:
  * ISO9660 level 1/2/3 (nama 8.3 maupun panjang)
  * Joliet (SVD tipe 2) untuk nama file yang lebih panjang/Unicode
  * Direktori bersarang

Yang TIDAK didukung (tidak dibutuhkan untuk kasus ini):
  * Rock Ridge / POSIX permission
  * Multi-extent file (> 4 GiB)
  * UDF

Referensi format: ECMA-119 (ISO9660).
"""

from __future__ import annotations

import io
import os
import re
import struct
from dataclasses import dataclass
from typing import BinaryIO, Iterator

SECTOR_SIZE = 2048
PVD_LBA = 16
_CD001 = b"CD001"


class IsoError(Exception):
    """Gagal membaca struktur ISO."""


@dataclass(frozen=True)
class IsoEntry:
    """Satu entri (file atau direktori) di dalam image ISO."""

    path: str          # path relatif, dipisah "/"
    lba: int           # sektor awal data
    size: int          # ukuran dalam byte
    is_dir: bool


def _both_endian_u32(raw: bytes, offset: int) -> int:
    """Baca field 8-byte "both-endian" ISO, ambil setengah little-endian."""
    return struct.unpack_from("<I", raw, offset)[0]


class Iso9660:
    """Image ISO9660 yang sudah di-parse, siap dibaca isinya."""

    def __init__(self, fileobj: BinaryIO) -> None:
        self._f = fileobj
        self._f.seek(0, os.SEEK_END)
        self._total_bytes = self._f.tell()
        self._root: IsoEntry | None = None
        self._use_joliet = False
        try:
            self._load_volume_descriptors()
        except Exception:
            # Jangan tinggalkan file handle terbuka kalau parsing gagal.
            self._f.close()
            raise

    # ------------------------------------------------------------------ setup
    @classmethod
    def open(cls, path: str | os.PathLike[str]) -> "Iso9660":
        return cls(open(os.fspath(path), "rb"))

    def close(self) -> None:
        self._f.close()

    def __enter__(self) -> "Iso9660":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _read_sector(self, lba: int) -> bytes:
        self._f.seek(lba * SECTOR_SIZE)
        data = self._f.read(SECTOR_SIZE)
        if len(data) < SECTOR_SIZE:
            raise IsoError(f"ISO terpotong: sektor {lba} tidak terbaca penuh.")
        return data

    def _load_volume_descriptors(self) -> None:
        primary: bytes | None = None
        joliet: bytes | None = None

        for lba in range(PVD_LBA, PVD_LBA + 32):
            vd = self._read_sector(lba)
            if vd[1:6] != _CD001:
                raise IsoError(
                    "Ini bukan image ISO9660 yang valid "
                    "(signature 'CD001' tidak ditemukan)."
                )
            vd_type = vd[0]
            if vd_type == 1 and primary is None:
                primary = vd
            elif vd_type == 2 and joliet is None:
                # Escape sequence "%/E" (UCS-2 level 3) dsb. ada di offset 88.
                if vd[88:91] in (b"%/@", b"%/C", b"%/E"):
                    joliet = vd
            elif vd_type == 255:
                break

        chosen = joliet or primary
        if chosen is None:
            raise IsoError("Volume descriptor ISO9660 tidak ditemukan.")

        self._use_joliet = chosen is joliet
        root_rec = chosen[156:156 + 34]
        if not root_rec:
            raise IsoError("Root directory record tidak ditemukan.")
        root = self._parse_dir_record(root_rec, parent="")
        # Root direpresentasikan dengan path kosong, sehingga anak-anaknya
        # menjadi "MAIN.PAK" / "PROPERTIES", bukan "./MAIN.PAK".
        self._root = IsoEntry(path="", lba=root.lba, size=root.size, is_dir=True)

    # ------------------------------------------------------------- dir records
    def _parse_dir_record(self, raw: bytes, parent: str) -> IsoEntry:
        name_len = raw[32]
        is_dir = bool(raw[25] & 0x02)
        lba = _both_endian_u32(raw, 2)
        size = _both_endian_u32(raw, 10)
        raw_name = raw[33:33 + name_len]

        if raw_name == b"\x00":
            name = ""
        elif raw_name == b"\x01":
            name = ""
        elif self._use_joliet:
            name = raw_name.decode("utf-16-be", errors="replace")
        else:
            name = raw_name.decode("latin-1", errors="replace")
            # ISO level 1 menyimpan nama sebagai "FILE.TXT;1"
            name = re.sub(r";\d+$", "", name)
            name = name.rstrip(".")

        if not name:
            path = ""
        elif not parent:
            path = name
        else:
            path = f"{parent}/{name}"
        return IsoEntry(path=path, lba=lba, size=size, is_dir=is_dir)

    def _iter_raw_dir(self, entry: IsoEntry) -> Iterator[IsoEntry]:
        """Iterasi entri mentah di dalam satu direktori."""
        remaining = entry.size
        lba = entry.lba
        while remaining > 0:
            block = self._read_sector(lba)
            offset = 0
            while offset < SECTOR_SIZE:
                rec_len = block[offset]
                if rec_len == 0:
                    break  # padding akhir sektor
                rec = block[offset:offset + rec_len]
                child = self._parse_dir_record(rec, entry.path)
                if child.path:
                    yield child
                offset += rec_len
            remaining -= SECTOR_SIZE
            lba += 1

    # ------------------------------------------------------------------ public
    def walk(self) -> Iterator[IsoEntry]:
        """Telusuri seluruh isi ISO (depth-first)."""
        if self._root is None:
            return
        stack = [self._root]
        visited: set[int] = set()
        while stack:
            current = stack.pop()
            if current.lba in visited:
                continue
            visited.add(current.lba)
            children = list(self._iter_raw_dir(current))
            yield from children
            stack.extend(c for c in children if c.is_dir)

    def read(self, entry: IsoEntry) -> bytes:
        if entry.is_dir:
            raise IsADirectoryError(entry.path)
        self._f.seek(entry.lba * SECTOR_SIZE)
        return self._f.read(entry.size)

    def open_entry(self, entry: IsoEntry) -> io.BufferedReader:  # pragma: no cover
        """Reader streaming untuk file besar (hindari muat ke RAM)."""
        if entry.is_dir:
            raise IsADirectoryError(entry.path)
        return _IsoRangeReader(self._f, entry.lba * SECTOR_SIZE, entry.size)


class _IsoRangeReader(io.RawIOBase):
    """File-like read-only view atas rentang byte di dalam ISO."""

    def __init__(self, fileobj: BinaryIO, start: int, length: int) -> None:
        self._f = fileobj
        self._start = start
        self._length = length
        self._pos = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        if whence == os.SEEK_SET:
            self._pos = offset
        elif whence == os.SEEK_CUR:
            self._pos += offset
        elif whence == os.SEEK_END:
            self._pos = self._length + offset
        self._pos = max(0, min(self._pos, self._length))
        return self._pos

    def readinto(self, buffer) -> int:  # type: ignore[no-untyped-def]
        if self._pos >= self._length:
            return 0
        chunk = min(len(buffer), self._length - self._pos)
        self._f.seek(self._start + self._pos)
        data = self._f.read(chunk)
        buffer[: len(data)] = data
        self._pos += len(data)
        return len(data)
