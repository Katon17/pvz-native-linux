"""Test untuk dialog Tentang (About) dan tautan donasi."""

from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from pvznative import about


class AuthorAndLinksTests(unittest.TestCase):
    def test_author_name(self) -> None:
        self.assertEqual(about.AUTHOR, "Katon Bagaskoro")

    def test_saweria_link_present(self) -> None:
        urls = [url for _nama, url in about.LINKS]
        self.assertIn("https://saweria.co/Kabako", urls)

    def test_kofi_link_present(self) -> None:
        urls = [url for _nama, url in about.LINKS]
        self.assertIn("https://ko-fi.com/katonbagaskoro", urls)

    def test_donation_links_are_first_two(self) -> None:
        self.assertEqual(
            about.DONATE_LINKS,
            (
                ("Saweria", "https://saweria.co/Kabako"),
                ("Ko-fi", "https://ko-fi.com/katonbagaskoro"),
            ),
        )

    def test_all_links_are_https(self) -> None:
        for nama, url in about.LINKS:
            with self.subTest(nama=nama):
                self.assertTrue(url.startswith("https://"), url)


class VersionTests(unittest.TestCase):
    def test_version_is_non_empty(self) -> None:
        self.assertTrue(about.get_version().strip())

    def test_version_from_repo_file(self) -> None:
        repo_version = Path(__file__).resolve().parent.parent / "VERSION"
        if not repo_version.is_file():
            self.skipTest("VERSION tidak ada (bukan di dalam repo)")
        self.assertEqual(about.get_version(), repo_version.read_text().strip())


class OpenUrlTests(unittest.TestCase):
    def test_prefers_xdg_open(self) -> None:
        with mock.patch.object(subprocess, "Popen") as popen:
            popen.return_value = object()
            pesan = about._open_url("https://example.invalid/x")
        self.assertEqual(pesan, "")
        popen.assert_called_once()
        self.assertEqual(popen.call_args[0][0][0], "xdg-open")

    def test_returns_url_when_everything_fails(self) -> None:
        with mock.patch.object(subprocess, "Popen", side_effect=OSError):
            with mock.patch("webbrowser.open", return_value=False):
                pesan = about._open_url("https://example.invalid/y")
        self.assertEqual(pesan, "https://example.invalid/y")


class SourceHygieneTests(unittest.TestCase):
    """about.py harus tetap bisa diimpor tanpa GTK."""

    def test_module_imports_without_gi(self) -> None:
        kode = (
            "import sys; sys.modules['gi'] = None;"
            "from pvznative import about;"
            "print(about.AUTHOR)"
        )
        hasil = subprocess.run(
            [sys.executable, "-c", kode],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parent.parent / "tools"),
        )
        self.assertEqual(hasil.returncode, 0, hasil.stderr)
        self.assertIn("Katon Bagaskoro", hasil.stdout)

    def test_no_syntax_error(self) -> None:
        sumber = Path(about.__file__).read_text()
        ast.parse(sumber)


if __name__ == "__main__":
    unittest.main()
