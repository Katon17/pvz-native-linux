# pvz-native-linux — Copyright (C) 2026 Katon Bagaskoro <cimong2356@gmail.com>
# Licensed under GNU GPL-3.0-or-later. See LICENSE.
"""Entry point CLI: python3 -m pvznative <perintah>."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import __version__, config, setup
from . import assets as assets_mod


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pvz-native",
        description="Launcher Plants vs. Zombies native Linux (aset milik user sendiri).",
    )
    parser.add_argument("--version", action="version", version=f"pvz-native {__version__}")
    sub = parser.add_subparsers(dest="command")

    setup_cmd = sub.add_parser("setup", help="Pasang aset dari ISO atau folder")
    setup_cmd.add_argument(
        "--target", type=Path, default=None, help="Folder tujuan (default: XDG data dir)"
    )
    setup_cmd.add_argument(
        "--iso", "--file", dest="iso", type=Path, default=None,
        help="Langsung tunjuk file ISO atau ZIP (tanpa dialog)"
    )
    setup_cmd.add_argument(
        "--from-dir", type=Path, default=None, help="Langsung tunjuk folder aset"
    )
    setup_cmd.add_argument(
        "--exe", type=Path, default=None,
        help="Langsung tunjuk installer Plants vs. Zombies (.exe)",
    )
    setup_cmd.add_argument(
        "--force", action="store_true", help="Timpa aset yang sudah ada"
    )
    setup_cmd.add_argument(
        "--yes", action="store_true",
        help="Jangan minta konfirmasi (untuk skrip/CI, dipakai bersama --iso/--from-dir)",
    )

    settings_cmd = sub.add_parser("settings", help="Buka jendela Pengaturan (GUI)")
    settings_cmd.add_argument(
        "--about", action="store_true", help="Langsung buka dialog Tentang"
    )

    display = sub.add_parser(
        "display", help="Lihat/ubah mode layar (fullscreen atau jendela)"
    )
    display.add_argument(
        "mode", nargs="?", choices=["fullscreen", "windowed", "show"],
        default="show", help="Mode layar yang diinginkan (default: show)",
    )

    inspect = sub.add_parser(
        "inspect", help="Periksa ISO/ZIP/folder/exe tanpa memasang apa pun"
    )
    inspect.add_argument("path", type=Path, help="File ISO/ZIP/.exe atau folder")
    inspect.add_argument("--json", action="store_true", help="Keluaran JSON")

    sub.add_parser("doctor", help="Diagnosa lingkungan & aset")
    sub.add_parser("verify", help="Validasi ulang aset terpasang")

    uninstall = sub.add_parser("uninstall", help="Hapus aset yang sudah diekstrak")
    uninstall.add_argument(
        "--keep-saves", action="store_true", default=True,
        help="Biarkan save game (default)",
    )
    uninstall.add_argument(
        "--purge-saves", dest="keep_saves", action="store_false",
        help="Hapus save game juga",
    )

    where = sub.add_parser("where", help="Tampilkan lokasi file & folder")
    where.set_defaults(command="where")

    return parser


def cmd_setup(args: argparse.Namespace) -> int:
    target = args.target or config.assets_dir()

    if getattr(args, "yes", False):
        os.environ["PVZ_NATIVE_ASSUME_YES"] = "1"

    if args.iso:
        try:
            found = assets_mod.scan_auto(args.iso)
        except assets_mod.AssetError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return setup._finalize(found, target)

    if getattr(args, "exe", None):
        try:
            found = assets_mod.scan_installer(args.exe)
        except assets_mod.AssetError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return setup._finalize(found, target)

    if args.from_dir:
        try:
            found = assets_mod.scan_dir(args.from_dir)
        except assets_mod.AssetError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return setup._finalize(found, target)

    return setup.run_setup(target, force=args.force)


def cmd_verify() -> int:
    target = config.assets_dir()
    if not config.assets_ready():
        print("Aset belum terpasang.", file=sys.stderr)
        return 1

    state = config.load_state()
    pak = target / "main.pak"
    size = pak.stat().st_size
    import datetime

    modified = datetime.datetime.fromtimestamp(pak.stat().st_mtime).strftime("%Y-%m-%d")
    print(f"main.pak      : {pak}")
    print(f"ukuran        : {config.human_size(size)} ({size:,} byte)")
    print(f"tanggal file  : {modified}")

    try:
        found = assets_mod.scan_dir(target)
    except assets_mod.AssetError as exc:
        print(f"GAGAL: {exc}", file=sys.stderr)
        return 1

    print(f"sha256        : {found.pak_sha256}")
    checksum_changed = bool(
        state.get("assets_sha256")
        and state["assets_sha256"] != found.pak_sha256
    )
    print(f"versi (tebakan): {found.version_hint}")

    # main.pak PC 1.2.0.1073 berukuran ~44 MB (42,8 MiB). Paket yang jauh lebih
    # kecil biasanya berasal dari build mobile/reduced dan sering membuat
    # engine crash karena resources.xml menunjuk file yang tidak ada.
    if size < 35 * 1024 * 1024:
        print(
            f"\nPERINGATAN: main.pak hanya {config.human_size(size)}, sedangkan "
            "rilis PC Plants vs. Zombies 1.2.0.1073 berukuran ~42,8 MiB.\n"
            "Kemungkinan ini build versi lain (mobile/reduced) yang tidak "
            "lengkap. Kalau game crash, coba aset dari sumber PC lengkap.\n",
            file=sys.stderr,
        )

    # Audit aset yang dideklarasikan resources.xml (menangkap file longgar yang
    # tidak ikut terekesktrak, mis. partner_logo.jpg).
    from . import installer as installer_mod

    try:
        report = installer_mod.audit_resources(target)
    except Exception as exc:  # pragma: no cover - audit bersifat informatif
        print(f"audit resources: dilewati ({exc})")
        report = {"missing": [], "checked": 0}

    if report["checked"]:
        print(f"aset gambar   : {report['checked'] - len(report['missing'])}"
              f"/{report['checked']} tersedia")
    # Preflight isi pak: file yang diminta engine saat startup.
    try:
        content = installer_mod.audit_pak_contents(pak)
    except Exception as exc:  # pragma: no cover
        content = {"error": str(exc), "missing": [], "entries": 0, "size": 0}

    if content.get("error"):
        print(f"\nGAGAL membaca isi main.pak: {content['error']}",
              file=sys.stderr)
        return 2

    print(f"entri pak     : {content['entries']:,}")
    if content["missing"]:
        print("\nGAGAL: main.pak tidak berisi file wajib berikut:", file=sys.stderr)
        for name in content["missing"]:
            print(f"  - {name}", file=sys.stderr)
        print(
            "\nVersi aset ini tidak kompatibel dengan engine dan game akan "
            "berhenti dengan 'missing resource'.\n"
            "Gunakan aset dari rilis PC 1.2.0.1073 lengkap (main.pak ~42,8 MiB):\n"
            "  pvz-native --setup --force", file=sys.stderr,
        )
        return 2

    if report["missing"]:
        print("\nPERINGATAN: gambar berikut dideklarasikan resources.xml "
              "tetapi tidak ditemukan:", file=sys.stderr)
        for name in report["missing"]:
            print(f"  - {name}", file=sys.stderr)
        print("\nGame bisa berhenti dengan \"Failed to load image\". "
              "Jalankan ulang penyiapan dengan sumber aset yang lengkap:\n"
              "  pvz-native --setup --force", file=sys.stderr)
        return 2

    # Checksum diperiksa terakhir: kalau isinya sudah tidak kompatibel,
    # masalahnya bukan "file berubah", jadi jangan berhenti di situ.
    if checksum_changed:
        print("\nPERINGATAN: checksum berbeda dari saat dipasang "
              "(file berubah atau dipasang ulang secara manual).",
              file=sys.stderr)

    print("OK")
    return 0


def cmd_display(args: argparse.Namespace) -> int:
    from . import display as display_mod

    registry = config.saves_dir() / "registry.regemu"
    if args.mode == "show":
        current = display_mod.screen_mode(registry)
        print(f"registry : {registry}")
        print(f"mode     : {current}")
        if current == "belum diatur":
            print("\nBelum pernah dijalankan, atau belum diubah dari menu Options.")
            print("Engine memakai mode default (jendela) sampai kamu mengubahnya.")
        print("\nUbah dengan: pvz-native display fullscreen   (atau windowed)")
        return 0

    fullscreen = args.mode == "fullscreen"
    try:
        display_mod.set_screen_mode(registry, fullscreen)
    except (display_mod.RegEmuError, OSError) as exc:
        print(f"GAGAL: {exc}", file=sys.stderr)
        return 1

    print(f"Mode layar diset ke: {args.mode}")
    print("\nCatatan: game tetap menjaga rasio 4:3. Di layar 16:9 akan ada")
    print("batang hitam di kiri-kanan — itu disengaja, karena engine belum")
    print("mendukung peregangan widescreen.")
    print("\nJalankan game untuk menerapkan.")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    """Periksa satu sumber aset tanpa menyalin apa pun ke disk."""
    import json

    from . import assets as assets_mod

    path = Path(args.path).expanduser()
    if not path.exists():
        print(f"Error: Path tidak ditemukan: {path}", file=sys.stderr)
        return 1

    try:
        if path.is_dir():
            found = assets_mod.scan_dir(path)
        else:
            found = assets_mod.scan_auto(path)
    except assets_mod.IncompatibleAssets as exc:
        print("TIDAK KOMPATIBEL", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2
    except assets_mod.AssetError as exc:
        print(f"GAGAL: {exc}", file=sys.stderr)
        return 1

    report = {
        "sumber": str(path),
        "main_pak": found.pak_path,
        "ukuran": found.pak_size,
        "ukuran_manusia": config.human_size(found.pak_size),
        "sha256": found.pak_sha256,
        "versi": found.version_hint,
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"sumber        : {report['sumber']}")
        print(f"main.pak      : {report['main_pak']}")
        print(f"ukuran        : {report['ukuran_manusia']} ({found.pak_size:,} byte)")
        print(f"sha256        : {found.pak_sha256}")
        print(f"versi (tebakan): {report['versi']}")
        print("\nStatus        : KOMPATIBEL — bisa dipakai untuk --setup")
        if path.is_dir():
            flag = "--from-dir"
        elif path.suffix.lower() == ".exe":
            flag = "--exe"
        else:
            flag = "--iso"
        print("Lanjutkan dengan:")
        print(f"  pvz-native --setup --force --yes {flag} {path}")
    return 0


def cmd_where() -> int:
    engine = config.resolve_engine()
    rows = [
        ("engine", str(engine) if engine else "TIDAK DITEMUKAN"),
        ("aset", str(config.assets_dir())),
        ("save", str(config.saves_dir())),
        ("log", str(config.log_dir())),
        ("config", str(config.state_path())),
    ]
    width = max(len(name) for name, _ in rows)
    for name, value in rows:
        print(f"{name.ljust(width)} : {value}")
    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    return setup.run_uninstall(keep_saves=args.keep_saves)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        # Tanpa subcommand: perlakukan seperti launcher biasa.
        launcher = Path(__file__).resolve().parent.parent.parent / "scripts" / "pvz-native"
        if launcher.is_file():
            return subprocess.call([str(launcher)])
        parser.print_help()
        return 1

    if args.command == "setup":
        return cmd_setup(args)
    if args.command == "doctor":
        return setup.run_doctor()
    if args.command == "verify":
        return cmd_verify()
    if args.command == "uninstall":
        return cmd_uninstall(args)
    if args.command == "where":
        return cmd_where()
    if args.command == "inspect":
        return cmd_inspect(args)
    if args.command == "display":
        return cmd_display(args)
    if args.command == "settings":
        from . import settings_gui
        return settings_gui.run(about_only=getattr(args, "about", False))

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
