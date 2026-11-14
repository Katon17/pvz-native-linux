"""Tes ekstraksi dari installer & pembacaan main.pak.

CAB dibuat sintetis (kompresi NONE/MSZIP) supaya tes tidak membutuhkan file
berhak cipta maupun cabextract. Jalur LZX diuji lewat deteksi, bukan dekode.
"""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from pvznative import cab, installer, pak  # noqa: E402

PAK_MAGIC = 0xBAC04AC0


# --------------------------------------------------------------- fixtures
# File wajib engine: fixture instalasi harus lengkap agar mewakili pak yang
# benar-benar bisa boot.
BOOT_ENTRIES = {
    "properties/LawnStrings.txt": None,
    "properties/resources.xml": b"<resources/>",
    "reanim/LoadBar_sprout.reanim": b"<reanim/>",
    "compiled/reanim/LoadBar_sprout.reanim.compiled": b"X",
}


def boot_files(extra: dict[str, bytes] | None = None) -> dict[str, bytes]:
    files = {
        name: (LAWNSTRINGS_1073.encode() if payload is None else payload)
        for name, payload in BOOT_ENTRIES.items()
    }
    if extra:
        files.update(extra)
    return files


def make_pak(files: dict[str, bytes], *, xor: bool = True) -> bytes:
    """Bangun main.pak PopCap asli (opsional XOR 0xF7 seperti versi CD)."""
    table = bytearray(struct.pack("<II", PAK_MAGIC, 0))
    for name, payload in files.items():
        encoded = name.replace("/", "\\").encode("utf-8")
        table += bytes([0x00, len(encoded)])
        table += encoded
        table += struct.pack("<i", len(payload))
        table += struct.pack("<q", 0)
    table += bytes([0x80])
    body = b"".join(files.values())
    blob = bytes(table) + body
    return bytes(b ^ 0xF7 for b in blob) if xor else blob


def make_cab(files: dict[str, bytes], *, compress: bool = False) -> bytes:
    """CAB satu folder dengan layout seperti CAB PopCap sungguhan.

    Urutan di dalam file: CFHEADER (36) | CFFOLDER (8) | tabel CFFILE |
    CFDATA (data terkompresi) | penanda akhir folder.
    """
    names = list(files)
    payload = b"".join(files[n] for n in names)

    if compress:
        compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
        packed = b"CK" + compressor.compress(payload) + compressor.flush()
        comp_type = 1
    else:
        packed = payload
        comp_type = 0

    header_size = 36
    folder_entry_size = 8
    file_table_start = header_size + folder_entry_size      # 44
    data_start = file_table_start + 16 * len(names) + sum(
        len(n.replace("/", "\\").encode("latin-1")) + 1 for n in names
    )

    file_table = bytearray()
    offset = 0
    for name in names:
        encoded = name.replace("/", "\\").encode("latin-1")
        file_table += struct.pack(
            "<IIHHHH", len(files[name]), offset, 0, 0, 0, 0x20
        )
        file_table += encoded + b"\x00"
        offset += len(files[name])

    cfdata = struct.pack("<IHH", 0, len(packed), len(payload)) + packed
    cfdata += struct.pack("<IHH", 0, 0, 0)      # penanda akhir folder
    cabinet_size = data_start + len(cfdata)

    out = bytearray()
    out += struct.pack(
        "<4sIIIIIBBHHHHH",
        b"MSCF", 0, cabinet_size, 0, file_table_start, 0, 3, 1, 1, len(names), 0, 0, 0,
    )
    out += struct.pack("<IHH", data_start, 0, comp_type)
    out += file_table
    out += cfdata
    assert len(out) == cabinet_size, (len(out), cabinet_size)
    return bytes(out)


def make_lzx_cab(files: dict[str, bytes]) -> bytes:
    """CAB dengan comp_type LZX (isi tidak valid — hanya untuk tes deteksi)."""
    blob = bytearray(make_cab(files, compress=False))
    struct.pack_into("<H", blob, 36 + 6, 3)   # comp_type folder 0 = LZX
    return bytes(blob)


LAWNSTRINGS_1073 = "[CRAZY_DAVE_1700]\r\n{NO_CLICK}${SELL_PRICE}0 ok\r\n"


class PakReaderTests(unittest.TestCase):
    def test_reads_xor_encoded_pak(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "main.pak"
            path.write_bytes(make_pak(boot_files({"properties/LawnStrings.txt": b"halo"})))
            reader = pak.PakReader(path)
            self.assertTrue(reader.xor)
            entry = reader.find("properties/lawnstrings.txt")
            self.assertIsNotNone(entry)
            self.assertEqual(reader.open(entry), b"halo")

    def test_reads_plain_pak(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "main.pak"
            path.write_bytes(make_pak({"a.txt": b"x"}, xor=False))
            reader = pak.PakReader(path)
            self.assertFalse(reader.xor)

    def test_rejects_bad_magic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.pak"
            path.write_bytes(b"\x00" * 64)
            with self.assertRaises(pak.PakError):
                pak.PakReader(path)

    def test_read_lawnstrings_detects_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "main.pak"
            path.write_bytes(
                make_pak({"properties/LawnStrings.txt": LAWNSTRINGS_1073.encode()})
            )
            text = pak.read_lawnstrings(path)
            self.assertIsNotNone(text)
            self.assertIn("CRAZY_DAVE_1700", text)

    def test_is_valid_magic_accepts_both_forms(self) -> None:
        self.assertTrue(pak.is_valid_magic(PAK_MAGIC))
        self.assertTrue(pak.is_valid_magic(pak.PAK_MAGIC_ON_DISK_XOR))
        self.assertFalse(pak.is_valid_magic(0x12345678))


class CabReaderTests(unittest.TestCase):
    def test_uncompressed_cab(self) -> None:
        blob = make_cab({"files/Plants vs. Zombies/main.pak": b"PAKDATA"})
        indexes = cab.describe_installers(blob)
        self.assertEqual(len(indexes), 1)
        files = dict(cab.extract_files(blob, indexes[0]))
        self.assertEqual(files["files/Plants vs. Zombies/main.pak"], b"PAKDATA")

    def test_mszip_cab(self) -> None:
        payload = bytes(range(256)) * 40
        blob = make_cab({"main.pak": payload}, compress=True)
        indexes = cab.describe_installers(blob)
        files = dict(cab.extract_files(blob, indexes[0]))
        self.assertEqual(files["main.pak"], payload)

    def test_cab_hidden_inside_exe(self) -> None:
        stub = b"MZ" + b"\x90" * 5000
        blob = stub + make_cab({"main.pak": b"X" * 100}) + b"tail-data"
        indexes = cab.describe_installers(blob)
        self.assertEqual(len(indexes), 1)
        self.assertEqual(indexes[0].base_offset, len(stub))

    def test_detects_lzx_as_unsupported(self) -> None:
        blob = make_lzx_cab({"main.pak": b"x" * 10})
        indexes = cab.describe_installers(blob)
        self.assertEqual(len(indexes), 1)
        self.assertEqual(cab.unsupported_compression(indexes[0]), "LZX")

    def test_false_positive_mscf_is_skipped(self) -> None:
        fake = b"MSCF" + b"\x00" * 100
        real = make_cab({"main.pak": b"y" * 50})
        blob = fake + real
        indexes = cab.describe_installers(blob)
        self.assertEqual(len(indexes), 1)
        self.assertEqual(indexes[0].base_offset, len(fake))


class InstallerFlowTests(unittest.TestCase):
    def _make_exe(self, *, compress: bool = False) -> bytes:
        inner_pak = make_pak(
            boot_files()
        )
        return (
            b"MZ" + b"\x00" * 2048
            + make_cab(
                {
                    "files/Plants vs. Zombies/main.pak": inner_pak,
                    "files/Plants vs. Zombies/PlantsVsZombies.dat": b"junk",
                },
                compress=compress,
            )
        )

    def test_find_and_extract_from_installer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "PlantsVsZombiesSetup.exe"
            exe.write_bytes(self._make_exe())

            plan = installer.find_main_pak(exe)
            self.assertIsNotNone(plan)
            self.assertEqual(
                plan.member_path, "files/Plants vs. Zombies/main.pak"
            )

            target = Path(temp) / "assets"
            installer.extract_main_pak(plan, target / "main.pak")
            self.assertTrue((target / "main.pak").is_file())

            written = installer.extract_properties(target / "main.pak", target)
            self.assertIn("LawnStrings.txt", written)
            self.assertTrue((target / "properties" / "resources.xml").is_file())
            self.assertEqual(installer.detect_version(target / "main.pak"),
                             "1.2.0.1073")

    def test_non_installer_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "something.exe"
            exe.write_bytes(b"MZ" + b"\x00" * 4096)
            self.assertIsNone(installer.find_main_pak(exe))


class ScanInstallerTests(unittest.TestCase):
    def test_scan_installer_reports_kind(self) -> None:
        from pvznative import assets

        inner = make_pak(boot_files())
        blob = b"MZ" + b"\x00" * 1024 + make_cab({"main.pak": inner})
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "setup.exe"
            exe.write_bytes(blob)
            found = assets.scan_installer(exe)
            self.assertEqual(found.kind, "installer")
            self.assertTrue(found.warnings)

    def test_scan_auto_routes_exe(self) -> None:
        from pvznative import assets

        inner = make_pak(boot_files())
        blob = b"MZ" + b"\x00" * 1024 + make_cab({"main.pak": inner})
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "setup.exe"
            exe.write_bytes(blob)
            self.assertEqual(assets.scan_auto(exe).kind, "installer")


class IsoWithInstallerTests(unittest.TestCase):
    """ISO yang isinya installer (persis kasus ISO CD PopCap)."""

    def _iso_with_installer(self, temp: Path) -> Path:
        from make_test_iso import build_iso

        inner = make_pak(
            boot_files()
        )
        exe = b"MZ" + b"\x00" * 1022 + make_cab(
            {"files/Plants vs. Zombies/main.pak": inner}, compress=False
        )
        return build_iso(
            temp / "disc.iso",
            {
                "AUTORUN.INF": b"[autorun]\nopen=PopCDRun.exe",
                "PopCDRun.exe": b"MZ" + b"\x00" * 512,
                "installers/PlantsVsZombiesSetup.exe": exe,
                "images/btn_play.bmp": b"BM" + b"\x00" * 64,
            },
        )

    def test_scan_iso_finds_installer_and_extracts(self) -> None:
        from pvznative import assets

        with tempfile.TemporaryDirectory() as temp:
            iso = self._iso_with_installer(Path(temp))
            found = assets.scan_iso(iso)
            self.assertEqual(found.kind, "installer")
            self.assertEqual(found.version_hint, "unknown")  # dideteksi nanti

            target = Path(temp) / "assets"
            assets.install_assets(found, target)
            self.assertTrue((target / "main.pak").is_file())
            self.assertTrue((target / "properties" / "LawnStrings.txt").is_file())

            again = assets.scan_dir(target)
            self.assertEqual(again.version_hint, "1.2.0.1073")

    def test_installer_iso_without_main_pak_still_explains(self) -> None:
        from make_test_iso import build_iso
        from pvznative import assets

        with tempfile.TemporaryDirectory() as temp:
            iso = build_iso(
                Path(temp) / "bad.iso",
                {"SETUP.EXE": b"MZ" + b"\x00" * 2048, "AUTORUN.INF": b"[autorun]"},
            )
            with self.assertRaises(assets.AssetError) as ctx:
                assets.scan_iso(iso)
            self.assertIn("installer", str(ctx.exception).lower())


RESOURCES_XML = (
    b'<Resources>'
    b'<Image id="PARTNER_LOGO" path="partner_logo" />'
    b'<Image id="POPCAP_LOGO" path="PopCap_Logo" />'
    b'<Image id="BLANK" path="blank" />'
    b'</Resources>'
)


class LoosePropertiesTests(unittest.TestCase):
    """Installer mengirim sebagian properties/ sebagai file longgar."""

    def _exe(self) -> bytes:
        inner = make_pak(
            {
                "properties/resources.xml": RESOURCES_XML,
                "properties/LawnStrings.txt": LAWNSTRINGS_1073.encode(),
                "images/PopCap_Logo.png": b"\x89PNG fake",
            }
        )
        return b"MZ" + b"\x00" * 1022 + make_cab(
            {
                "files/Plants vs. Zombies/main.pak": inner,
                "files/Plants vs. Zombies/properties/partner.xml": b"<Properties/>",
                "files/Plants vs. Zombies/properties/partner_logo.jpg": b"\xff\xd8JPEG",
            },
            compress=False,
        )

    def test_loose_properties_are_extracted(self) -> None:
        from pvznative import assets

        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "setup.exe"
            exe.write_bytes(self._exe())
            target = Path(temp) / "assets"
            assets.install_assets(assets.scan_installer(exe), target)

            # File longgar dari installer
            self.assertTrue((target / "properties" / "partner_logo.jpg").is_file())
            self.assertTrue((target / "properties" / "partner.xml").is_file())
            # File dari dalam pak tetap ada
            self.assertTrue((target / "properties" / "resources.xml").is_file())

    def test_audit_detects_missing_image(self) -> None:
        from pvznative import assets, installer

        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "assets"
            inner = make_pak(
                {
                    "properties/resources.xml": RESOURCES_XML,
                    "properties/LawnStrings.txt": LAWNSTRINGS_1073.encode(),
                    "images/PopCap_Logo.png": b"png",
                }
            )
            target.mkdir(parents=True)
            (target / "main.pak").write_bytes(inner)
            (target / "properties").mkdir()
            (target / "properties" / "resources.xml").write_bytes(RESOURCES_XML)

            report = installer.audit_resources(target)
            # partner_logo tidak ada -> harus dilaporkan; "blank" diabaikan.
            self.assertEqual(report["missing"], ["partner_logo"])

            # Setelah file longgar ditambahkan, audit bersih.
            (target / "properties" / "partner_logo.jpg").write_bytes(b"jpeg")
            self.assertEqual(installer.audit_resources(target)["missing"], [])

    def test_audit_clean_when_complete(self) -> None:
        from pvznative import assets, installer

        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "setup.exe"
            exe.write_bytes(self._exe())
            target = Path(temp) / "assets"
            assets.install_assets(assets.scan_installer(exe), target)
            self.assertEqual(installer.audit_resources(target)["missing"], [])


class PakContentPreflightTests(unittest.TestCase):
    """Preflight menangkap pak versi lain sebelum game dijalankan."""

    def test_missing_reanim_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            # Pak "versi lain": resources + LawnStrings OK, tapi tanpa reanim.
            pak_path = Path(temp) / "main.pak"
            pak_path.write_bytes(
                make_pak(
                    {
                        "properties/resources.xml": b"<Resources/>",
                        "properties/LawnStrings.txt": LAWNSTRINGS_1073.encode(),
                    }
                )
            )
            report = installer.audit_pak_contents(pak_path)
            self.assertIn(
                "compiled/reanim/LoadBar_sprout.reanim.compiled",
                report["missing"],
            )
            self.assertIn("reanim/LoadBar_sprout.reanim", report["missing"])

    def test_complete_pak_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pak_path = Path(temp) / "main.pak"
            pak_path.write_bytes(
                make_pak(
                    {
                        "properties/resources.xml": b"<Resources/>",
                        "properties/LawnStrings.txt": LAWNSTRINGS_1073.encode(),
                        "reanim/LoadBar_sprout.reanim": b"<reanim/>",
                        "compiled/reanim/LoadBar_sprout.reanim.compiled": b"X",
                    }
                )
            )
            self.assertEqual(installer.audit_pak_contents(pak_path)["missing"], [])

    def test_unreadable_pak_reports_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pak_path = Path(temp) / "main.pak"
            pak_path.write_bytes(b"not a pak at all")
            self.assertIsNotNone(installer.audit_pak_contents(pak_path)["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
