# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Wizard penyiapan aset (first run) dan diagnosa."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import assets as assets_mod
from . import config, gui

LEGAL_NOTICE = (
    "Launcher ini tidak menyertakan aset Plants vs. Zombies.\n\n"
    "Kamu harus memakai file dari salinan game yang kamu miliki sendiri "
    "(ISO CD, Steam, atau installer PopCap). Semua file hanya disalin ke "
    "komputer ini dan tidak diunggah ke mana pun."
)


def run_setup(target: Path, *, force: bool = False) -> int:
    """Alur penyiapan aset. Return 0 kalau sukses."""
    target = target.expanduser()

    if not force and config.assets_ready() and target == config.assets_dir():
        return 0

    gui.info(LEGAL_NOTICE)

    detected = None
    if not force:
        detected = assets_mod.find_existing_assets()
    if detected is not None:
        message = (
            "Ketemu aset Plants vs. Zombies yang sudah terpasang:\n"
            f"{detected.source}\n"
            f"Versi terdeteksi: {detected.version_hint}\n\n"
            "Pakai aset ini?"
        )
        if gui.ask(message, ok="Pakai", cancel="Pilih manual"):
            return _finalize(detected, target)

    options = [
        ("iso", "Dari file ISO / ZIP / installer (.exe)"),
        ("exe", "Dari file installer Plants vs. Zombies (.exe)"),
        ("dir", "Dari folder (Steam, PopCap, atau hasil ekstrak)"),
        ("help", "Aku belum punya game-nya — jelaskan cara dapat yang legal"),
    ]
    choice = gui.choose(options)
    if choice is None:
        gui.warn("Penyiapan dibatalkan.")
        return 1

    if choice == "help":
        gui.info(
            "Cara mendapatkan aset yang legal:\n\n"
            "1. Steam — 'Plants vs. Zombies: Game of the Year' (app 3590).\n"
            "   Setelah terpasang, launcher bisa mendeteksinya otomatis.\n\n"
            "2. EA App / situs resmi EA — versi GOTY.\n\n"
            "3. CD original Plants vs. Zombies (rilis PopCap 1.2.0.1073) "
            "— versi ini paling direkomendasikan karena paling kompatibel "
            "dengan engine open source yang dipakai.\n\n"
            "Aset dari sumber lain tidak didukung dan tidak akan dibantu "
            "oleh proyek ini."
        )
        return 1

    if choice == "iso":
        iso_path = gui.pick_file("Pilih file ISO atau ZIP Plants vs. Zombies")
        if not iso_path:
            gui.warn("Tidak ada file yang dipilih.")
            return 1
        try:
            found = assets_mod.scan_auto(Path(iso_path))
        except assets_mod.AssetError as exc:
            gui.error(str(exc))
            return 1
        return _finalize(found, target)

    if choice == "exe":
        exe_path = gui.pick_file(
            "Pilih installer Plants vs. Zombies (.exe)",
            patterns=["*.exe", "*.EXE"],
        )
        if not exe_path:
            gui.warn("Tidak ada file yang dipilih.")
            return 1
        try:
            found = assets_mod.scan_installer(Path(exe_path))
        except assets_mod.AssetError as exc:
            gui.error(str(exc))
            return 1
        return _finalize(found, target)

    directory = gui.pick_dir("Pilih folder yang berisi main.pak dan properties/")
    if not directory:
        gui.warn("Tidak ada folder yang dipilih.")
        return 1
    try:
        found = assets_mod.scan_dir(Path(directory))
    except assets_mod.AssetError as exc:
        gui.error(str(exc))
        return 1
    return _finalize(found, target)


def _finalize(found: assets_mod.AssetSet, target: Path) -> int:
    """Konfirmasi, salin, lalu catat ke state."""
    details = [
        f"Sumber     : {found.source}",
        f"main.pak   : {config.human_size(found.pak_size)}",
        f"SHA-256    : {found.pak_sha256[:16]}…",
        f"Versi aset : {found.version_hint}",
    ]
    summary = "Aset ditemukan:\n\n" + "\n".join(details)
    for warning in found.warnings:
        summary += f"\n\n⚠ {warning}"
    summary += f"\n\nSalin ke:\n{target}\n\nLanjutkan?"

    if not gui.ask(summary, ok="Salin sekarang"):
        gui.warn("Dibatalkan oleh user.")
        return 1

    progress = gui.Progress("Menyiapkan aset Plants vs. Zombies")
    try:
        # Bersihkan sisa percobaan sebelumnya supaya tidak ada campuran file.
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        assets_mod.install_assets(found, target, progress=progress.update)
    except (assets_mod.AssetError, OSError) as exc:
        progress.close()
        gui.error(f"Gagal menyalin aset:\n{exc}")
        return 1
    finally:
        progress.close()

    # Pindai ulang hasil instalasi: untuk aset dari installer, versi dan
    # checksum baru diketahui setelah main.pak benar-benar diekstrak.
    try:
        final = assets_mod.scan_dir(target)
    except assets_mod.AssetError:
        final = found

    # Validasi terakhir: jangan pernah menandai "terpasang" untuk aset yang
    # tidak bisa boot. Tanpa ini, wizard bisa selesai dengan gembira padahal
    # game langsung crash dengan "missing resource".
    try:
        with open(target / "main.pak", "rb") as fh:
            assets_mod._reject_incomplete(
                fh, (target / "main.pak").stat().st_size, str(found.source)
            )
    except assets_mod.IncompatibleAssets as exc:
        shutil.rmtree(target, ignore_errors=True)
        gui.error(
            "Aset yang dipilih tidak bisa dipakai, jadi tidak dipasang.\n\n"
            + str(exc)
            + "\n\nFolder aset dikosongkan agar tidak tertukar dengan versi "
            "yang benar."
        )
        return 1
    except OSError:
        pass

    state = config.load_state()
    state.update(
        {
            "assets_installed": True,
            "assets_version": final.version_hint,
            "assets_sha256": final.pak_sha256,
            "assets_source": str(found.source),
            "assets_size": final.pak_size,
        }
    )
    config.save_state(state)

    if final.warnings:
        gui.warn("\n\n".join(final.warnings))

    _ask_display_mode()

    gui.info(
        "Selesai. Plants vs. Zombies siap dijalankan.\n\n"
        f"Aset: {target}\nVersi: {final.version_hint}\n\n"
        "Catatan tampilan: engine menjaga rasio 4:3 asli. Di layar 16:9 akan "
        "muncul batang hitam di kiri-kanan. Itu normal dan bukan bug."
    )
    return 0


def _ask_display_mode() -> None:
    """Tanyakan mode layar setelah aset terpasang (opsional)."""
    from . import display as display_mod

    registry = config.saves_dir() / "registry.regemu"
    current = display_mod.screen_mode(registry)
    if current != "belum diatur":
        return

    choice = gui.choose(
        [
            ("fullscreen", "Layar penuh (fullscreen)"),
            ("windowed", "Jendela (bisa di-resize bebas)"),
            ("later", "Nanti saja — aku atur sendiri di menu Options"),
        ],
        header="Mode layar",
    )
    if choice not in ("fullscreen", "windowed"):
        return
    try:
        display_mod.set_screen_mode(registry, choice == "fullscreen")
    except (display_mod.RegEmuError, OSError):
        return


# -------------------------------------------------------------------- doctor
def run_doctor() -> int:
    """Diagnosa lingkungan; berguna untuk issue report."""
    engine = config.resolve_engine()
    state = config.load_state()

    lines = [
        "Plants vs. Zombies — diagnosa lingkungan",
        "=" * 44,
        f"Sistem        : {_os_pretty()}",
        f"Python        : {sys.version.split()[0]}",
        f"Session       : {os.environ.get('XDG_SESSION_TYPE', 'tidak diketahui')}",
        "",
        f"Engine        : {engine or 'TIDAK DITEMUKAN'}",
        f"Aset terpasang: {'ya' if config.assets_ready() else 'tidak'}",
        f"Folder aset   : {config.assets_dir()}",
        f"Folder save   : {config.saves_dir()}",
        f"State file    : {config.state_path()}",
        f"Versi aset    : {state.get('assets_version', 'unknown')}",
        f"SHA-256 pak   : {state.get('assets_sha256') or '-'}",
        "",
    ]

    problems: list[str] = []
    if engine is None:
        problems.append(
            "Engine PvZ-Portable tidak ditemukan. Pasang ulang paket, atau "
            "set PVZ_ENGINE=/path/ke/pvz-portable."
        )
    if not config.assets_ready():
        problems.append(
            "Aset game belum terpasang. Jalankan: pvz-native --setup"
        )
    if config.assets_ready():
        try:
            from . import installer as installer_mod

            report = installer_mod.audit_resources(config.assets_dir())
            if report["missing"]:
                problems.append(
                    "Aset tidak lengkap: "
                    + ", ".join(report["missing"][:5])
                    + (" …" if len(report["missing"]) > 5 else "")
                    + " (jalankan: pvz-native --setup --force)"
                )
        except Exception:  # pragma: no cover
            pass

    if not _has_vulkan():
        problems.append(
            "Vulkan tidak terdeteksi. Engine butuh OpenGL ES 2.0 / GL 2.1; "
            "kalau driver Mesa belum ada: sudo apt install mesa-utils libgl1-mesa-dri"
        )
    if _in_flatpak_steam_dir():
        problems.append(
            "Terindikasi aset dari Steam Flatpak. Kalau launcher tidak bisa "
            "membacanya karena sandbox, salin foldernya ke lokasi biasa."
        )

    lines.append("Masalah terdeteksi:" if problems else "Tidak ada masalah terdeteksi.")
    for problem in problems:
        lines.append(f"  - {problem}")

    # --- info grafis: penyebab crash paling sering pada proyek ini ---------
    lines.append("")
    lines.append("Informasi grafis:")
    for label, value in _gl_info():
        lines.append(f"  {label:<14}: {value}")

    # --- log crash terakhir ------------------------------------------------
    crash_log = config.log_dir() / "last-crash.log"
    if crash_log.is_file():
        lines.append("")
        lines.append(f"Log crash terakhir ({crash_log}):")
        try:
            interesting = [
                line for line in crash_log.read_text(
                    encoding="utf-8", errors="replace").splitlines()
                if line.strip() and not line.startswith("INFO:")
            ]
        except OSError:
            interesting = []
        for line in interesting[-12:]:
            lines.append(f"  {line}")

    text = "\n".join(lines)
    print(text)
    return 0 if not problems else 2


def _gl_info() -> list[tuple[str, str]]:
    """Kumpulkan informasi driver tanpa membutuhkan tool tambahan."""
    rows: list[tuple[str, str]] = []

    rows.append(("GPU", _gpu_name()))
    rows.append(("OpenGL", _glx_renderer()))

    icds = sorted(p.name for p in Path("/usr/share/vulkan/icd.d").glob("*.json")) \
        if Path("/usr/share/vulkan/icd.d").is_dir() else []
    rows.append(("Vulkan ICD", ", ".join(icds) if icds else "TIDAK ADA"))

    rows.append(("DRI driver", _dri_summary()))

    from . import display as display_mod

    rows.append((
        "Mode layar",
        display_mod.screen_mode(config.saves_dir() / "registry.regemu"),
    ))

    session = os.environ.get("XDG_SESSION_TYPE", "?")
    rows.append(("Session", f"{session} / {os.environ.get('GDK_BACKEND', 'default')}"))
    rows.append(("Env override", _gl_env_overrides() or "tidak ada"))
    return rows


# Driver Mesa yang relevan untuk GPU desktop/laptop umum. Kalau salah satu
# hilang, engine bisa gagal membuat konteks OpenGL.
_RELEVANT_DRI = {
    "iris": "Intel Gen8+ (HD 620, Iris Xe)",
    "i915": "Intel Gen2-7 (driver lama)",
    "crocus": "Intel Gen4-7 (Mesa baru)",
    "radeonsi": "AMD GCN/RDNA",
    "r600": "AMD lama",
    "nouveau": "NVIDIA open source",
    "swrast": "software fallback (llvmpipe)",
    "kms_swrast": "software fallback via KMS",
    "zink": "OpenGL di atas Vulkan",
}


def _dri_summary() -> str:
    """Laporkan driver DRI yang RELEVAN, bukan 6 entri alfabetis pertama.

    Versi sebelumnya memotong daftar secara alfabetis sehingga `iris` dan
    `radeonsi` tidak pernah muncul walau terpasang.
    """
    candidates = [
        Path("/usr/lib/x86_64-linux-gnu/dri"),
        Path("/usr/lib64/dri"),
        Path("/usr/lib/dri"),
    ]
    folder = next((path for path in candidates if path.is_dir()), None)
    if folder is None:
        return "folder DRI tidak ditemukan (paket libgl1-mesa-dri belum ada?)"

    present = {path.stem.replace("_dri", "") for path in folder.glob("*_dri.so")}
    if not present:
        return f"kosong di {folder}"

    found = [
        f"{name} ({_RELEVANT_DRI[name]})"
        for name in sorted(present)
        if name in _RELEVANT_DRI
    ]
    if found:
        return ", ".join(found)
    # Tidak ada yang dikenali: tampilkan apa adanya tapi jangan potong buta.
    return ", ".join(sorted(present)[:12])


def _gpu_name() -> str:
    try:
        result = subprocess.run(
            ["sh", "-c", "lspci 2>/dev/null | grep -iE 'vga|3d|display' | head -1"],
            capture_output=True, text=True, timeout=5,
        )
        text = result.stdout.strip()
        if text:
            return text.split(":", 2)[-1].strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "tidak terdeteksi"


def _glx_renderer() -> str:
    if shutil.which("glxinfo") is None:
        return "glxinfo tidak terpasang (sudo apt install mesa-utils)"
    try:
        result = subprocess.run(
            ["glxinfo", "-B"], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return "gagal menjalankan glxinfo"
    for line in result.stdout.splitlines():
        if "OpenGL renderer string" in line or "OpenGL version string" in line:
            return line.split(":", 1)[1].strip()
    if result.returncode != 0:
        detail = (result.stderr or "").strip().splitlines()
        return "GAGAL: " + (detail[0] if detail else f"kode {result.returncode}")
    return "tidak terbaca"


def _gl_env_overrides() -> str:
    keys = [k for k in os.environ if k.startswith(("MESA_", "LIBGL_", "GALLIUM_", "vblank"))]
    return ", ".join(f"{k}={os.environ[k]}" for k in sorted(keys))


def _os_pretty() -> str:
    try:
        with open("/etc/os-release", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return "Linux"


def _has_vulkan() -> bool:
    return shutil.which("vulkaninfo") is not None or Path(
        "/usr/share/vulkan/icd.d"
    ).is_dir()


def _in_flatpak_steam_dir() -> bool:
    state = config.load_state()
    source = state.get("assets_source") or ""
    return "com.valvesoftware.Steam" in source


def run_uninstall(keep_saves: bool = True) -> int:
    """Hapus aset; save dibiarkan secara default."""
    if not gui.ask(
        "Hapus aset game yang sudah diekstrak?\n\n"
        "Paket .deb-nya sendiri dihapus lewat apt. "
        + ("Save game tidak akan disentuh." if keep_saves else "Save game ikut dihapus."),
        ok="Hapus aset",
    ):
        return 1

    shutil.rmtree(config.assets_dir(), ignore_errors=True)
    if not keep_saves:
        shutil.rmtree(config.saves_dir(), ignore_errors=True)

    state = config.load_state()
    state.update({"assets_installed": False, "assets_sha256": None,
                  "assets_version": "unknown", "assets_source": None})
    config.save_state(state)

    gui.info("Aset dihapus. Jalankan lagi dengan --setup kalau mau pasang ulang.")
    return 0
