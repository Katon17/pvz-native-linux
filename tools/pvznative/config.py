# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Lokasi standar (XDG) dan penyimpanan konfigurasi launcher."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

APP_NAME = "pvz-native"
APP_ID = "io.github.katon17.pvz-native"

STATE_FILE = "state.json"


def _xdg(env: str, fallback: str) -> Path:
    value = os.environ.get(env)
    return Path(value) if value else Path.home() / fallback


def data_dir() -> Path:
    """Direktori tulis: aset, save, log."""
    return _xdg("XDG_DATA_HOME", ".local/share") / APP_NAME


def config_dir() -> Path:
    return _xdg("XDG_CONFIG_HOME", ".config") / APP_NAME


def cache_dir() -> Path:
    return _xdg("XDG_CACHE_HOME", ".cache") / APP_NAME


def assets_dir() -> Path:
    return data_dir() / "assets"


def saves_dir() -> Path:
    return data_dir() / "saves"


def log_dir() -> Path:
    return data_dir() / "logs"


def state_path() -> Path:
    return config_dir() / STATE_FILE


def bundled_engine() -> Path:
    """Path engine bawaan paket .deb (hasil instalasi)."""
    return Path("/usr/lib") / APP_NAME / "engine" / "pvz-portable"


def resolve_engine() -> Path | None:
    """Cari binary engine: config → env → bawaan paket → PATH."""
    state = load_state()

    configured = state.get("engine_path")
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate

    env_path = os.environ.get("PVZ_ENGINE")
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate

    bundled = bundled_engine()
    if bundled.is_file() and os.access(bundled, os.X_OK):
        return bundled

    which = shutil.which("pvz-portable")
    if which:
        return Path(which)

    return None


# ---------------------------------------------------------------------- state
DEFAULTS: dict[str, Any] = {
    "version": 1,
    "engine_path": None,
    "assets_installed": False,
    "assets_version": "unknown",
    "assets_sha256": None,
    "assets_source": None,
    "assets_size": 0,
    "fullscreen": False,
    "last_played": None,
}


def load_state() -> dict[str, Any]:
    path = state_path()
    state = dict(DEFAULTS)
    if not path.is_file():
        return state
    try:
        with open(path, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
        if isinstance(loaded, dict):
            state.update(loaded)
    except (OSError, json.JSONDecodeError):
        pass
    return state


def save_state(state: dict[str, Any]) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with open(temporary, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    temporary.replace(path)


def assets_ready() -> bool:
    """Aset dianggap siap kalau main.pak + properties/index.xml ada."""
    root = assets_dir()
    return (root / "main.pak").is_file() and (root / "properties").is_dir()


def human_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024.0 or unit == "GiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024.0
    return f"{num_bytes} B"
