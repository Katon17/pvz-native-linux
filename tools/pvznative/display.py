# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Baca/tulis preferensi tampilan engine lewat registry.regemu.

Engine PvZ-Portable menyimpan pengaturan di `$SAVES/registry.regemu`, format
biner sederhana (lihat RegEmu.cpp di upstream). Launcher perlu membacanya
supaya bisa menampilkan status layar yang sebenarnya, dan menulisnya supaya
pengguna bisa mengubah mode layar tanpa harus masuk ke menu dalam game.
"""

from __future__ import annotations

import os
import struct
from pathlib import Path

MAGIC = b"REGEMU"
VERSION = 1
APP_KEY = "SOFTWARE\\PopCap\\PlantsVsZombies"

TYPE_INT = 4

# Nilai ScreenMode yang dikenal engine. SexyAppBase.cpp membaca:
#     mIsWindowed = (ScreenMode == 0);
SCREEN_WINDOWED = 0
SCREEN_FULLSCREEN = 1


class RegEmuError(Exception):
    """File registry tidak bisa dibaca atau ditulis."""


def _read_u32(data: bytes, offset: int) -> tuple[int, int]:
    if offset + 4 > len(data):
        raise RegEmuError("File registry terpotong.")
    return struct.unpack_from("<I", data, offset)[0], offset + 4


def _read_str(data: bytes, offset: int) -> tuple[str, int]:
    length, offset = _read_u32(data, offset)
    if offset + length > len(data):
        raise RegEmuError("File registry terpotong.")
    raw = data[offset:offset + length]
    return raw.split(b"\x00", 1)[0].decode("utf-8", errors="replace"), offset + length


def load(path: "Path | str") -> dict[str, dict[str, tuple[int, bytes]]]:
    """Baca registry. Return {key: {nama_nilai: (tipe, data)}}."""
    path = Path(path)
    if not path.is_file():
        return {}
    data = path.read_bytes()
    if len(data) < 10 or not data.startswith(MAGIC):
        raise RegEmuError(f"Bukan file registry yang valid: {path}")

    version = struct.unpack_from("<H", data, 6)[0]
    if version != VERSION:
        raise RegEmuError(f"Versi registry tidak didukung: {version}")

    offset = 8
    num_keys, offset = _read_u32(data, offset)
    registry: dict[str, dict[str, tuple[int, bytes]]] = {}
    for _ in range(num_keys):
        key_name, offset = _read_str(data, offset)
        num_values, offset = _read_u32(data, offset)
        values: dict[str, tuple[int, bytes]] = {}
        for _ in range(num_values):
            value_name, offset = _read_str(data, offset)
            vtype, offset = _read_u32(data, offset)
            length, offset = _read_u32(data, offset)
            if offset + length > len(data):
                raise RegEmuError("File registry terpotong.")
            values[value_name] = (vtype, data[offset:offset + length])
            offset += length
        registry[key_name] = values
    return registry


def save(path: "Path | str", registry: dict[str, dict[str, tuple[int, bytes]]]) -> None:
    """Tulis registry kembali, mempertahankan urutan key & nilai."""
    chunks = [MAGIC, struct.pack("<H", VERSION), struct.pack("<I", len(registry))]
    for key_name, values in registry.items():
        encoded = (key_name + "\x00").encode("utf-8")
        chunks.append(struct.pack("<I", len(encoded)) + encoded)
        chunks.append(struct.pack("<I", len(values)))
        for value_name, (vtype, payload) in values.items():
            encoded_name = (value_name + "\x00").encode("utf-8")
            chunks.append(struct.pack("<I", len(encoded_name)) + encoded_name)
            chunks.append(struct.pack("<II", vtype, len(payload)) + payload)
    Path(path).write_bytes(b"".join(chunks))


def read_int(path: "Path | str", name: str) -> int | None:
    """Baca nilai integer dari key PopCap. None kalau tidak ada."""
    try:
        registry = load(path)
    except RegEmuError:
        return None
    entry = registry.get(APP_KEY, {}).get(name)
    if entry is None:
        return None
    vtype, payload = entry
    if vtype != TYPE_INT or len(payload) != 4:
        return None
    return struct.unpack("<i", payload)[0]


def write_int(path: "Path | str", name: str, value: int) -> None:
    """Set nilai integer pada key PopCap, buat file/key kalau perlu."""
    path = Path(path)
    try:
        registry = load(path)
    except RegEmuError:
        registry = {}
    registry.setdefault(APP_KEY, {})[name] = (TYPE_INT, struct.pack("<i", value))
    path.parent.mkdir(parents=True, exist_ok=True)
    save(path, registry)


def screen_mode(path: "Path | str") -> str:
    """'fullscreen' | 'windowed' | 'belum diatur'."""
    value = read_int(path, "ScreenMode")
    if value is None:
        return "belum diatur"
    return "windowed" if value == SCREEN_WINDOWED else "fullscreen"


def set_screen_mode(path: "Path | str", fullscreen: bool) -> None:
    write_int(path, "ScreenMode", SCREEN_FULLSCREEN if fullscreen else SCREEN_WINDOWED)


# --------------------------------------------------------------- widescreen
#
# Dilapisi oleh engine hasil patch (PVZ_WIDESCREEN=1): renderer mengisi seluruh
# jendela alih-alih letterbox 4:3. Engine bawaan tidak mengenal variabel ini,
# jadi nilainya tidak berefek apa pun di sana.

def widescreen_enabled() -> bool:
    value = os.environ.get("PVZ_WIDESCREEN", "")
    return bool(value) and value != "0"
