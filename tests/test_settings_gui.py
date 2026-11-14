"""Test untuk preferensi tampilan di jendela Pengaturan."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pvznative import settings_gui


class WideConfTests(unittest.TestCase):
    def test_default_is_false(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": temp}):
                self.assertFalse(settings_gui.read_wide())

    def test_write_then_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": temp}):
                settings_gui.write_wide(True)
                self.assertTrue(settings_gui.read_wide())
                settings_gui.write_wide(False)
                self.assertFalse(settings_gui.read_wide())

    def test_empty_file_means_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": temp}):
                path = settings_gui.wide_conf()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("")
                self.assertFalse(settings_gui.read_wide())

    def test_apply_now_reports_missing_launcher(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": temp}):
                with mock.patch.object(settings_gui, "_launcher_candidates",
                                       return_value=[]):
                    message = settings_gui.apply_now(True)
                    self.assertIn("pvz-native", message)
                # Preferensi tetap tersimpan walau game gagal dijalankan.
                self.assertTrue(settings_gui.read_wide())

    def test_apply_now_launches_first_working_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": temp}):
                with mock.patch.object(settings_gui, "_launcher_candidates",
                                       return_value=["/nonexistent/launcher"]):
                    with mock.patch.object(settings_gui.subprocess, "Popen") as popen:
                        popen.side_effect = OSError("boom")
                        message = settings_gui.apply_now(True)
                        self.assertIn("Tidak menemukan", message)
