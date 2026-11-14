"""Test untuk pembacaan/penulisan registry.regemu (preferensi tampilan)."""

from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from pvznative import display


def make_registry(value: int = 1) -> bytes:
    key = b"SOFTWARE\\PopCap\\PlantsVsZombies\x00"
    name = b"InProgress\x00"
    return (
        b"REGEMU"
        + struct.pack("<H", 1)
        + struct.pack("<I", 1)
        + struct.pack("<I", len(key)) + key
        + struct.pack("<I", 1)
        + struct.pack("<I", len(name)) + name
        + struct.pack("<II", 4, 4) + struct.pack("<i", value)
    )


class RegEmuTests(unittest.TestCase):
    def test_read_existing_integer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.regemu"
            path.write_bytes(make_registry(1))
            self.assertEqual(display.read_int(path, "InProgress"), 1)

    def test_missing_file_is_not_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            self.assertIsNone(display.read_int(Path(temp) / "nope", "ScreenMode"))
            self.assertEqual(display.screen_mode(Path(temp) / "nope"), "belum diatur")

    def test_set_and_read_screen_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.regemu"
            path.write_bytes(make_registry())
            display.set_screen_mode(path, True)
            self.assertEqual(display.screen_mode(path), "fullscreen")
            display.set_screen_mode(path, False)
            self.assertEqual(display.screen_mode(path), "windowed")

    def test_setting_preserves_other_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.regemu"
            path.write_bytes(make_registry(1))
            display.set_screen_mode(path, True)
            self.assertEqual(display.read_int(path, "InProgress"), 1)

    def test_corrupt_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.regemu"
            path.write_bytes(b"GARBAGE and more")
            with self.assertRaises(display.RegEmuError):
                display.load(path)

    def test_write_creates_file_and_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sub" / "registry.regemu"
            display.set_screen_mode(path, True)
            self.assertTrue(path.is_file())
            self.assertIn(display.APP_KEY, display.load(path))
