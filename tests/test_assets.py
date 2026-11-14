"""Tes otomatis untuk pembaca ISO dan manajemen aset.

Jalankan:  python3 -m unittest discover -s tests -v
Tidak butuh aset Plants vs. Zombies sungguhan — ISO dibuat secara sintetis.
"""

from __future__ import annotations

import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from pvznative import assets  # noqa: E402
from pvznative.iso9660 import Iso9660, IsoError  # noqa: E402

from make_test_iso import build_iso, dummy_pak  # noqa: E402


class TempDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()


class IsoReaderTests(TempDirTestCase):
    def test_reads_root_files(self) -> None:
        iso_path = build_iso(self.tmp / "a.iso", {"main.pak": dummy_pak(512)})
        with Iso9660.open(iso_path) as iso:
            entries = {entry.path: entry for entry in iso.walk()}
        self.assertIn("MAIN.PAK", entries)
        self.assertEqual(entries["MAIN.PAK"].size, 512)
        self.assertFalse(entries["MAIN.PAK"].is_dir)

    def test_reads_nested_directories(self) -> None:
        iso_path = build_iso(
            self.tmp / "b.iso",
            {"main.pak": dummy_pak(256), "properties/default.xml": b"<x/>"},
        )
        with Iso9660.open(iso_path) as iso:
            entries = {entry.path: entry for entry in iso.walk()}
            self.assertIn("PROPERTIES", entries)
            self.assertTrue(entries["PROPERTIES"].is_dir)
            data = iso.read(entries["PROPERTIES/DEFAULT.XML"])
        self.assertEqual(data, b"<x/>")

    def test_streaming_reader_matches_full_read(self) -> None:
        payload = dummy_pak(6000)
        iso_path = build_iso(self.tmp / "c.iso", {"main.pak": payload})
        with Iso9660.open(iso_path) as iso:
            entry = next(e for e in iso.walk() if e.path == "MAIN.PAK")
            with iso.open_entry(entry) as stream:
                self.assertEqual(stream.read(100), payload[:100])
                stream.seek(1000)
                self.assertEqual(stream.read(50), payload[1000:1050])
                stream.seek(-10, os.SEEK_END)
                self.assertEqual(stream.read(10), payload[-10:])

    def test_rejects_non_iso(self) -> None:
        bad = self.tmp / "bad.iso"
        bad.write_bytes(b"this is not an iso at all" * 4000)
        with self.assertRaises(IsoError):
            Iso9660.open(bad)

    def test_joliet_names(self) -> None:
        iso_path = build_iso(
            self.tmp / "j.iso", {"main.pak": dummy_pak(128)}, joliet=True
        )
        with Iso9660.open(iso_path) as iso:
            names = [entry.path for entry in iso.walk()]
        self.assertIn("main.pak", names)


class AssetScanTests(TempDirTestCase):
    def _make_assets(self, version_marker: str = "{SELL_PRICE}0") -> Path:
        root = self.tmp / "game"
        (root / "properties").mkdir(parents=True)
        (root / "main.pak").write_bytes(dummy_pak(2048))
        (root / "properties" / "default.xml").write_text("<properties/>")
        (root / "properties" / "LawnStrings.txt").write_text(
            f"[CRAZY_DAVE_1700]\n{version_marker}\n[CRAZY_DAVE_1800]\nhalo\n"
        )
        return root

    def test_scan_dir_accepts_str_and_path(self) -> None:
        root = self._make_assets()
        self.assertEqual(assets.scan_dir(str(root)).pak_size, 2048)
        self.assertEqual(assets.scan_dir(root).pak_size, 2048)

    def test_detects_1073(self) -> None:
        found = assets.scan_dir(self._make_assets("{SELL_PRICE}0"))
        self.assertEqual(found.version_hint, "1.2.0.1073")

    def test_detects_1096(self) -> None:
        found = assets.scan_dir(self._make_assets("{SELL_PRICE}"))
        self.assertEqual(found.version_hint, "1.2.0.1096?")
        self.assertTrue(found.warnings)

    def test_rejects_wrong_magic(self) -> None:
        root = self._make_assets()
        (root / "main.pak").write_bytes(b"\x00\x00\x00\x00" + bytes(2044))
        with self.assertRaises(assets.AssetError):
            assets.scan_dir(root)

    def test_missing_properties_is_an_error(self) -> None:
        root = self.tmp / "broken"
        root.mkdir()
        (root / "main.pak").write_bytes(dummy_pak(128))
        with self.assertRaises(assets.AssetError):
            assets.scan_dir(root)

    def test_iso_without_assets_gives_helpful_error(self) -> None:
        iso_path = build_iso(self.tmp / "empty.iso", {"readme.txt": b"hello"})
        with self.assertRaises(assets.AssetError) as ctx:
            assets.scan_iso(iso_path)
        self.assertIn("properties", str(ctx.exception))


class InstallTests(TempDirTestCase):
    def test_install_from_iso_uses_canonical_lowercase_names(self) -> None:
        iso_path = build_iso(
            self.tmp / "g.iso",
            {
                "main.pak": dummy_pak(4096),
                "properties/default.xml": b"<properties/>",
                "properties/LawnStrings.txt": b"[CRAZY_DAVE_1700]\n{SELL_PRICE}0\n",
            },
        )
        found = assets.scan_iso(iso_path)
        target = self.tmp / "installed"
        assets.install_assets(found, target)

        self.assertTrue((target / "main.pak").is_file())
        # Engine mencari "properties/" huruf kecil; ISO menyimpan huruf besar.
        self.assertTrue((target / "properties").is_dir())
        self.assertTrue((target / "properties" / "DEFAULT.XML").is_file())
        self.assertEqual((target / "main.pak").read_bytes(), dummy_pak(4096))

    def test_install_from_dir(self) -> None:
        root = self.tmp / "src"
        (root / "properties").mkdir(parents=True)
        (root / "main.pak").write_bytes(dummy_pak(1024))
        (root / "properties" / "default.xml").write_text("<properties/>")

        found = assets.scan_dir(root)
        target = self.tmp / "dst"
        assets.install_assets(found, target)

        self.assertTrue((target / "main.pak").is_file())
        self.assertTrue((target / "properties" / "default.xml").is_file())

    def test_progress_callback_is_called(self) -> None:
        root = self.tmp / "src2"
        (root / "properties").mkdir(parents=True)
        (root / "main.pak").write_bytes(dummy_pak(5000))
        (root / "properties" / "a.xml").write_text("x")

        calls: list[tuple[str, int, int]] = []
        assets.install_assets(
            assets.scan_dir(root), self.tmp / "out", progress=lambda *a: calls.append(a)
        )
        self.assertTrue(calls)
        label, done, total = calls[-1]
        self.assertIn("properties", label)
        self.assertLessEqual(done, total)


class VersionHeuristicTests(unittest.TestCase):
    def test_unknown_when_marker_missing(self) -> None:
        self.assertEqual(assets._detect_version_from_lawnstrings("halo\n"), "unknown")

    def test_ignores_mention_outside_key_block(self) -> None:
        text = "catatan: {SELL_PRICE}0 pernah dipakai\n[CRAZY_DAVE_1700]\n{SELL_PRICE}\n"
        self.assertEqual(assets._detect_version_from_lawnstrings(text), "1.2.0.1096?")


class ZipSourceTests(TempDirTestCase):
    def _make_zip(self, name: str, *, nested: bool = False) -> Path:
        import zipfile

        prefix = "PlantsVsZombies/" if nested else ""
        path = self.tmp / name
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(prefix + "main.pak", dummy_pak(3072))
            archive.writestr(prefix + "properties/default.xml", "<properties/>")
            archive.writestr(
                prefix + "properties/LawnStrings.txt",
                "[CRAZY_DAVE_1700]\n{SELL_PRICE}0\n",
            )
            archive.writestr("unrelated.txt", "abaikan")
        return path

    def test_scan_zip_flat(self) -> None:
        found = assets.scan_zip(self._make_zip("flat.zip"))
        self.assertEqual(found.kind, "zip")
        self.assertEqual(found.pak_size, 3072)
        self.assertEqual(found.version_hint, "1.2.0.1073")

    def test_scan_zip_nested_folder(self) -> None:
        found = assets.scan_zip(self._make_zip("nested.zip", nested=True))
        self.assertEqual(found.kind, "zip")

    def test_install_from_zip(self) -> None:
        found = assets.scan_zip(self._make_zip("install.zip", nested=True))
        target = self.tmp / "out"
        assets.install_assets(found, target)
        self.assertTrue((target / "main.pak").is_file())
        self.assertTrue((target / "properties" / "default.xml").is_file())
        self.assertEqual((target / "main.pak").read_bytes(), dummy_pak(3072))

    def test_scan_auto_dispatches(self) -> None:
        self.assertEqual(assets.scan_auto(self._make_zip("auto.zip")).kind, "zip")
        iso_path = build_iso(
            self.tmp / "auto.iso",
            {"main.pak": dummy_pak(512), "properties/default.xml": b"<x/>"},
        )
        self.assertEqual(assets.scan_auto(iso_path).kind, "iso")

    def test_scan_auto_rejects_unknown(self) -> None:
        junk = self.tmp / "notes.txt"
        junk.write_text("halo")
        with self.assertRaises(assets.AssetError):
            assets.scan_auto(junk)


class InstallerIsoHintTests(TempDirTestCase):
    def test_installer_iso_suggests_alternative(self) -> None:
        iso_path = build_iso(
            self.tmp / "disc.iso",
            {"SETUP.EXE": b"MZ" + bytes(60), "AUTORUN.INF": b"[autorun]"},
        )
        with self.assertRaises(assets.AssetError) as ctx:
            assets.scan_iso(iso_path)
        message = str(ctx.exception)
        self.assertIn("installer", message.lower())
        self.assertIn("mode 'folder'", message)


if __name__ == "__main__":
    unittest.main(verbosity=2)

class ZipSourceTests(TempDirTestCase):
    def _make_zip(self, name: str, *, nested: bool = False) -> Path:
        import zipfile

        prefix = "PlantsVsZombies/" if nested else ""
        path = self.tmp / name
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(prefix + "main.pak", dummy_pak(3072))
            archive.writestr(prefix + "properties/default.xml", "<properties/>")
            archive.writestr(
                prefix + "properties/LawnStrings.txt",
                "[CRAZY_DAVE_1700]\n{SELL_PRICE}0\n",
            )
            archive.writestr("unrelated.txt", "abaikan")
        return path

    def test_scan_zip_flat(self) -> None:
        found = assets.scan_zip(self._make_zip("flat.zip"))
        self.assertEqual(found.kind, "zip")
        self.assertEqual(found.pak_size, 3072)
        self.assertEqual(found.version_hint, "1.2.0.1073")

    def test_scan_zip_nested_folder(self) -> None:
        found = assets.scan_zip(self._make_zip("nested.zip", nested=True))
        self.assertEqual(found.kind, "zip")

    def test_install_from_zip(self) -> None:
        found = assets.scan_zip(self._make_zip("install.zip", nested=True))
        target = self.tmp / "out"
        assets.install_assets(found, target)
        self.assertTrue((target / "main.pak").is_file())
        self.assertTrue((target / "properties" / "default.xml").is_file())
        self.assertEqual((target / "main.pak").read_bytes(), dummy_pak(3072))

    def test_scan_auto_dispatches(self) -> None:
        self.assertEqual(assets.scan_auto(self._make_zip("auto.zip")).kind, "zip")
        iso_path = build_iso(
            self.tmp / "auto.iso",
            {"main.pak": dummy_pak(512), "properties/default.xml": b"<x/>"},
        )
        self.assertEqual(assets.scan_auto(iso_path).kind, "iso")

    def test_scan_auto_rejects_unknown(self) -> None:
        junk = self.tmp / "notes.txt"
        junk.write_text("halo")
        with self.assertRaises(assets.AssetError):
            assets.scan_auto(junk)


class InstallerIsoHintTests(TempDirTestCase):
    def test_installer_iso_suggests_alternative(self) -> None:
        iso_path = build_iso(
            self.tmp / "disc.iso",
            {"SETUP.EXE": b"MZ" + bytes(60), "AUTORUN.INF": b"[autorun]"},
        )
        with self.assertRaises(assets.AssetError) as ctx:
            assets.scan_iso(iso_path)
        message = str(ctx.exception)
        self.assertIn("installer", message.lower())
        self.assertIn("mode 'folder'", message)

class IncompatibleAssetsTests(unittest.TestCase):
    """Pemindai aset menolak paket yang tidak memuat file wajib engine."""

    def _make_tree(self, temp: str, entries: dict) -> Path:
        root = Path(temp) / "game"
        root.mkdir()
        pak_path = root / "main.pak"
        pak_path.write_bytes(self._pak(entries))
        (root / "properties").mkdir()
        (root / "properties" / "resources.xml").write_bytes(b"<Resources/>")
        return root

    @staticmethod
    def _pak(entries: dict) -> bytes:
        import struct

        table = b""
        data = b""
        for name, payload in entries.items():
            raw = name.encode()
            table += struct.pack("<BB", 0, len(raw)) + raw
            table += struct.pack("<i", len(payload)) + b"\x00" * 8
            data += payload
        return struct.pack("<II", 0xBAC04AC0, 0) + table + b"\x80" + data

    def test_incomplete_pak_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._make_tree(temp, {
                "properties/resources.xml": b"<Resources/>",
                "properties/LawnStrings.txt": b"x",
            })
            with self.assertRaises(assets.IncompatibleAssets) as ctx:
                assets.scan_dir(root)
            self.assertIn(
                "compiled/reanim/LoadBar_sprout.reanim.compiled", ctx.exception.missing
            )

    def test_complete_pak_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = self._make_tree(temp, {
                "properties/resources.xml": b"<Resources/>",
                "properties/LawnStrings.txt": b"x",
                "reanim/LoadBar_sprout.reanim": b"<reanim/>",
                "compiled/reanim/LoadBar_sprout.reanim.compiled": b"X",
            })
            found = assets.scan_dir(root)
            self.assertEqual(found.missing_required, [])
