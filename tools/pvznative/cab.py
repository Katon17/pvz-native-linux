# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Pembaca Microsoft Cabinet (MSCF) + ekstraktor InstallShield self-extractor.

Dipakai untuk kasus yang sangat umum di Indonesia (dan di mana saja): ISO
Plants vs. Zombies resmi ternyata berisi **installer**, bukan file game yang
sudah terpasang. Di dalam `installers/PlantsVsZombiesSetup.exe` ada CAB
Microsoft yang berisi `files/Plants vs. Zombies/main.pak` + `properties/`.

Semua kode di sini memakai standard library saja — user tidak perlu
memasang cabextract, unshield, 7z, atau Wine.

Format yang didukung:
  * Microsoft Cabinet (MSCF), kompresi NONE dan MSZIP (deflate)
  * CAB bersarang di dalam file apa pun (dicari lewat signature)
  * InstallShield self-extracting EXE, selama CAB-nya memakai format MSCF
    (yang dipakai PopCap untuk PvZ GOTY 1.2.0.1073)

Yang TIDAK didukung: Quantum (Q)、LZX, dan CAB InstallShield asli (`ISc(`).
Untuk kasus itu pengguna diberi pesan yang menjelaskan langkah alternatif.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field
from typing import BinaryIO, Iterator

MSCF = b"MSCF"
_CAB_HEADER = struct.Struct("<4sIIIIIBBHHHHH")
_CFHEADER_SIZE = _CAB_HEADER.size  # 36 byte

FLAG_HAS_PREV = 0x0001
FLAG_HAS_NEXT = 0x0002
FLAG_RESERVE_PRESENT = 0x0004

COMPRESS_NONE = 0
COMPRESS_MSZIP = 1
COMPRESS_QUANTUM = 2
COMPRESS_LZX = 3


class CabError(Exception):
    """CAB tidak bisa dibaca / tidak didukung."""


@dataclass
class CabEntry:
    """Satu file di dalam CAB."""

    name: str
    size: int
    folder_offset: int
    folder_index: int
    date: int
    time: int
    attribs: int


@dataclass
class CabFolder:
    """Satu folder (stream terkompresi) di dalam CAB."""

    offset: int
    comp_type: int
    block_count: int


@dataclass
class CabIndex:
    """Hasil parsing header CAB: daftar folder dan file."""

    base_offset: int
    cabinet_size: int
    files_offset: int = 0            # offset tabel file (relatif dari base)
    folders: list[CabFolder] = field(default_factory=list)
    files: list[CabEntry] = field(default_factory=list)


# ------------------------------------------------------------------ discovery
def find_cabinets(data: bytes, *, limit: int = 8) -> list[int]:
    """Cari offset semua CAB yang *header-nya valid* di dalam sebuah file.

    InstallShield self-extractor menyisipkan MSCF di tengah data lain, dan
    false positive "MSCF" bisa muncul di dalam payload terkompresi. Karena
    itu setiap kandidat divalidasi dengan mem-parse header-nya.
    """
    offsets: list[int] = []
    position = 0
    while True:
        position = data.find(MSCF, position)
        if position < 0 or len(offsets) >= limit:
            break
        if valid_cab_header(data, position):
            offsets.append(position)
        position += 4
    return offsets


def valid_cab_header(data: bytes, offset: int) -> bool:
    if offset + _CFHEADER_SIZE > len(data):
        return False
    (sig, _r1, cabinet_size, _r2, coff_files, _r3,
     _minor, _major, folder_count, file_count, _flags,
     _set_id, _icab) = _CAB_HEADER.unpack_from(data, offset)
    if sig != MSCF:
        return False
    if cabinet_size == 0 or offset + cabinet_size > len(data) + 64:
        return False
    if not (1 <= folder_count <= 4096 and 1 <= file_count <= 20000):
        return False
    if coff_files >= cabinet_size:
        return False
    return True


def parse_index(data: bytes, base: int) -> CabIndex:
    """Parse CFHEADER + CFFOLDER + CFFILE di dalam CAB pada offset `base`."""
    (sig, _r1, cabinet_size, _r2, coff_files, _r3,
     _minor, _major, folder_count, file_count, flags,
     _set_id, _icab) = _CAB_HEADER.unpack_from(data, base)
    if sig != MSCF:
        raise CabError("Header MSCF tidak ditemukan.")

    cursor = base + _CFHEADER_SIZE
    if flags & FLAG_RESERVE_PRESENT:
        reserve = struct.unpack_from("<H", data, cursor)[0]
        cursor += 2 + reserve

    index = CabIndex(
        base_offset=base, cabinet_size=cabinet_size, files_offset=coff_files
    )
    for _ in range(folder_count):
        _coff_start, _i_folder, comp_type = struct.unpack_from("<IHH", data, cursor)
        cursor += 8
        index.folders.append(
            CabFolder(offset=_coff_start, comp_type=comp_type & 0x000F, block_count=0)
        )

    cursor = base + coff_files
    for _ in range(file_count):
        if cursor + 16 > len(data):
            raise CabError("Daftar file CAB terpotong.")
        (size, folder_offset, folder_index, date, time, attribs) = struct.unpack_from(
            "<IIHHHH", data, cursor
        )
        cursor += 16
        end = data.find(b"\x00", cursor)
        if end < 0:
            raise CabError("Nama file CAB tidak diakhiri NUL.")
        name = data[cursor:end].decode("latin-1", errors="replace")
        cursor = end + 1
        index.files.append(
            CabEntry(
                name=name.replace("\\", "/"),
                size=size,
                folder_offset=folder_offset,
                folder_index=folder_index,
                date=date,
                time=time,
                attribs=attribs,
            )
        )
    return index


# --------------------------------------------------------------- extraction
def _folder_stream(data: bytes, index: CabIndex, folder: CabFolder) -> bytes:
    """Dekompilasi satu folder CAB menjadi stream utuh di memori."""
    base = index.base_offset
    # coffCabStart relatif terhadap awal header CAB, bukan awal file.
    cursor = base + folder.offset
    data_end = base + index.cabinet_size
    blocks: list[bytes] = []
    used = 0
    history = b""

    while used < index.cabinet_size and cursor < data_end:
        if cursor + 8 > len(data):
            break
        checksum, cb_data, cb_uncomp = struct.unpack_from("<IHH", data, cursor)
        cursor += 8
        # Penanda akhir folder: tidak ada data lagi. CAB PopCap mengisi field
        # checksum dengan nilai sisa, jadi jangan bergantung pada checksum==0.
        if cb_data == 0 and cb_uncomp == 0:
            break
        payload = data[cursor:cursor + cb_data]
        cursor += cb_data
        used += 8 + cb_data

        if folder.comp_type == COMPRESS_NONE:
            blocks.append(payload)
            continue

        if folder.comp_type == COMPRESS_MSZIP:
            if payload[:2] != b"CK":
                raise CabError("Blok MSZIP tidak diawali signature 'CK'.")
            try:
                chunk = zlib.decompressobj(-15).decompress(payload[2:], cb_uncomp)
            except zlib.error as exc:
                raise CabError(f"Gagal dekompresi MSZIP: {exc}") from exc
            if len(chunk) < cb_uncomp:
                # Beberapa encoder memakai jendela sebelumnya; coba gabungkan.
                try:
                    chunk = zlib.decompressobj(-15, zdict=history[-32768:]).decompress(
                        payload[2:], cb_uncomp
                    )
                except zlib.error:
                    pass
            blocks.append(chunk)
            history = (history + chunk)[-32768:]
            continue

        raise CabError(
            "Kompresi CAB tipe "
            f"{folder.comp_type} tidak didukung dekoder bawaan."
        )

    return b"".join(blocks)


def extract_files(
    data: bytes,
    index: CabIndex,
    wanted: list[str] | None = None,
) -> Iterator[tuple[str, bytes]]:
    """Hasilkan (nama, isi) untuk file di dalam CAB.

    Kalau `wanted` diberikan, hanya nama yang cocok (case-insensitive).
    """
    wanted_lower = {name.lower() for name in wanted} if wanted else None
    streams: dict[int, bytes] = {}

    for entry in index.files:
        if wanted_lower and entry.name.lower() not in wanted_lower:
            continue
        if entry.folder_index >= len(index.folders):
            raise CabError(f"File {entry.name} menunjuk folder yang tidak ada.")
        if entry.folder_index not in streams:
            streams[entry.folder_index] = _folder_stream(
                data, index, index.folders[entry.folder_index]
            )
        stream = streams[entry.folder_index]
        start = entry.folder_offset
        yield entry.name, stream[start:start + entry.size]


def unsupported_compression(index: CabIndex) -> str | None:
    """Nama algoritma kompresi yang tidak bisa didekode murni dengan Python."""
    for folder in index.folders:
        if folder.comp_type == COMPRESS_QUANTUM:
            return "Quantum"
        if folder.comp_type == COMPRESS_LZX:
            return "LZX"
    return None


def find_file(index: CabIndex, suffix: str) -> CabEntry | None:
    """Cari file pertama yang namanya diakhiri `suffix` (case-insensitive)."""
    needle = suffix.lower()
    for entry in index.files:
        if entry.name.lower().endswith(needle):
            return entry
    return None


def list_main_pak_candidates(index: CabIndex) -> list[CabEntry]:
    return [e for e in index.files if e.name.lower().rsplit("/", 1)[-1] == "main.pak"]


def describe_installers(data: bytes) -> list[CabIndex]:
    """Semua CAB valid di dalam file, sudah di-parse."""
    results: list[CabIndex] = []
    for offset in find_cabinets(data):
        try:
            results.append(parse_index(data, offset))
        except CabError:
            continue
    return results


# ------------------------------------------------------------------ MSZIP zip
def extract_to_stream(
    source: BinaryIO,
    index: CabIndex,
    entry: CabEntry,
    destination: BinaryIO,
) -> int:
    """Ekstrak satu file ke stream tujuan tanpa memuat seluruh folder ke disk."""
    stream = _folder_stream_blockwise(source, index, index.folders[entry.folder_index])
    start = entry.folder_offset
    remaining = entry.size
    written = 0
    for chunk in stream:
        if start > 0:
            if start >= len(chunk):
                start -= len(chunk)
                continue
            chunk = chunk[start:]
            start = 0
        piece = chunk[:remaining]
        destination.write(piece)
        written += len(piece)
        remaining -= len(piece)
        if remaining <= 0:
            break
    return written


def _folder_stream_blockwise(
    source: BinaryIO, index: CabIndex, folder: CabFolder
) -> Iterator[bytes]:
    """Seperti _folder_stream tapi menerima file object (lebih hemat RAM)."""
    source.seek(index.base_offset + folder.offset)
    data_end = index.base_offset + index.cabinet_size
    used = 0
    history = b""
    while used < index.cabinet_size and index.base_offset + used < data_end:
        header = source.read(8)
        if len(header) < 8:
            break
        checksum, cb_data, cb_uncomp = struct.unpack("<IHH", header)
        if cb_data == 0 and cb_uncomp == 0:
            break
        payload = source.read(cb_data)
        used += 8 + cb_data
        if folder.comp_type == COMPRESS_NONE:
            yield payload
            continue
        if payload[:2] != b"CK":
            raise CabError("Blok MSZIP tidak diawali 'CK'.")
        try:
            chunk = zlib.decompressobj(-15).decompress(payload[2:], cb_uncomp)
        except zlib.error as exc:
            raise CabError(f"Gagal dekompresi MSZIP: {exc}") from exc
        if not chunk and cb_uncomp:
            try:
                chunk = zlib.decompressobj(-15, zdict=history[-32768:]).decompress(
                    payload[2:], cb_uncomp
                )
            except zlib.error:
                pass
        history = (history + chunk)[-32768:]
        yield chunk
