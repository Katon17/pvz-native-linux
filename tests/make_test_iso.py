"""Bangun ISO9660 sintetis untuk menguji alur ekstraksi tanpa aset berhak cipta.

Tidak ada aset PopCap di sini — hanya file dummy dengan magic number yang
benar dan struktur direktori yang menyerupai ISO PvZ asli.
"""

from __future__ import annotations

import os
import struct
from pathlib import Path

SECTOR = 2048


def _both32(value: int) -> bytes:
    return struct.pack("<I", value) + struct.pack(">I", value)


def _both16(value: int) -> bytes:
    return struct.pack("<H", value) + struct.pack(">H", value)


def _dir_record(name: bytes, lba: int, size: int, is_dir: bool) -> bytes:
    name_len = len(name)
    padding = (4 - ((33 + name_len) % 2)) % 2
    rec_len = 33 + name_len + padding

    record = bytearray()
    record.append(rec_len)
    record.append(0)                      # extended attr length
    record += _both32(lba)
    record += _both32(size)
    record += bytes(7)                    # recording date
    record.append(0x02 if is_dir else 0x00)
    record.append(0)                      # file unit size
    record.append(0)                      # interleave gap
    record += _both16(1)                  # volume sequence number
    record.append(name_len)
    record += name
    record += bytes(padding)
    assert len(record) == rec_len
    return bytes(record)


def build_iso(
    path: Path,
    files: dict[str, bytes],
    *,
    volume_id: str = "PVZ_TEST",
    joliet: bool = False,
) -> Path:
    """Buat ISO9660 berisi `files` (path relatif -> isi).

    Direktori dibuat otomatis dari path. Root ada di LBA 20.
    """
    root_lba = 20
    dir_lbas: dict[str, int] = {"/": root_lba}
    next_lba = root_lba + 1

    # Kumpulkan semua direktori (root direpresentasikan sebagai "/"),
    # urut supaya layout deterministik.
    dirs: set[str] = {"/"}
    for rel in files:
        parts = rel.split("/")
        for index in range(1, len(parts)):
            dirs.add("/" + "/".join(parts[:index]))

    for directory in sorted(dirs, key=lambda d: (d.count("/"), d)):
        if directory not in dir_lbas:
            dir_lbas[directory] = next_lba
            next_lba += 1

    file_lbas: dict[str, tuple[int, int]] = {}
    for rel in sorted(files):
        payload = files[rel]
        file_lbas[rel] = (next_lba, len(payload))
        next_lba += max(1, (len(payload) + SECTOR - 1) // SECTOR)

    total_sectors = next_lba
    image = bytearray(total_sectors * SECTOR)

    def put(lba: int, offset: int, data: bytes) -> None:
        start = lba * SECTOR + offset
        image[start:start + len(data)] = data

    # --- volume descriptors
    def volume_descriptor(vd_type: int, vol_id: str, escape: bytes = b"") -> bytes:
        vd = bytearray(SECTOR)
        vd[0] = vd_type
        vd[1:6] = b"CD001"
        vd[6] = 1
        if escape:
            vd[88:91] = escape
        ident = vol_id.encode("ascii")[:32].ljust(32, b" ")
        vd[40:72] = ident
        struct.pack_into("<I", vd, 80, total_sectors)
        struct.pack_into(">I", vd, 84, total_sectors)
        struct.pack_into("<H", vd, 120, 1)
        struct.pack_into(">H", vd, 122, 1)
        struct.pack_into("<H", vd, 124, 1)
        struct.pack_into(">H", vd, 126, 1)
        struct.pack_into("<H", vd, 128, SECTOR)
        struct.pack_into(">H", vd, 130, SECTOR)
        root = _dir_record(b"\x00", root_lba, SECTOR, True)
        vd[156:156 + len(root)] = root
        return bytes(vd)

    put(16, 0, volume_descriptor(1, volume_id))
    if joliet:
        put(17, 0, volume_descriptor(2, volume_id, b"%/E"))
        put(18, 0, volume_descriptor(255, volume_id))
    else:
        put(17, 0, volume_descriptor(255, volume_id))

    # --- isi direktori
    def encode(name: str) -> bytes:
        if joliet:
            return name.encode("utf-16-be")
        return name.upper().encode("ascii")

    for directory, lba in dir_lbas.items():
        parent = "/".join(directory.rstrip("/").split("/")[:-1]) or "/"
        if parent == directory or parent == "":
            parent = "/"

        records = bytearray()
        records += _dir_record(b"\x00", lba, SECTOR, True)
        records += _dir_record(b"\x01", dir_lbas[parent], SECTOR, True)

        children = sorted(
            d.rsplit("/", 1)[-1]
            for d in dirs
            if d != "/" and (d.rsplit("/", 1)[0] or "/") == directory
        )
        for child in children:
            child_path = "/" + child if directory == "/" else f"{directory}/{child}"
            records += _dir_record(encode(child), dir_lbas[child_path], SECTOR, True)

        prefix = "" if directory == "/" else directory.lstrip("/") + "/"
        for rel, (file_lba, size) in sorted(file_lbas.items()):
            if not rel.startswith(prefix):
                continue
            remainder = rel[len(prefix):]
            if "/" in remainder:
                continue
            name = remainder + (";1" if not joliet else "")
            records += _dir_record(encode(name), file_lba, size, False)

        put(lba, 0, bytes(records))

    # --- isi file
    for rel, (lba, _size) in file_lbas.items():
        put(lba, 0, files[rel])

    path.write_bytes(bytes(image))
    return path


def dummy_pak(size: int = 4096) -> bytes:
    """main.pak palsu dengan magic PopCap yang benar (0xBAC04AC0, LE)."""
    header = struct.pack("<I", 0xBAC04AC0) + struct.pack("<I", 1) + struct.pack("<I", 0)
    filler = bytes((index * 7) % 251 for index in range(size - len(header)))
    return header + filler


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1] if len(sys.argv) > 1 else "test.iso")
    build_iso(
        target,
        {
            "main.pak": dummy_pak(),
            "properties/default.xml": b"<properties/>\n",
            "properties/resources.xml": b"<resources/>\n",
            "properties/LawnStrings.txt": (
                b"[CRAZY_DAVE_1700]\n${SELL_PRICE}0\n"
            ),
            "readme.txt": b"dummy iso for testing\n",
        },
    )
    print(f"ISO dibuat: {target} ({os.path.getsize(target)} byte)")
