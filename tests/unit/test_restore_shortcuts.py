"""Unit tests for RestoreGoldenShortcutsUseCase across Linux, Windows, and macOS."""

import plistlib
import unittest

from netejator98.sanitisation.application.restore_shortcuts import (
    RestoreGoldenShortcutsUseCase,
)
from netejator98.shared.errors import FileWriteError
from tests.fakes.fake_sanitisation_ports import (
    FakeFileSystemPort,
    FakePlatformPathsPort,
)


class TestRestoreGoldenShortcuts(unittest.TestCase):
    def setUp(self) -> None:
        self.fs = FakeFileSystemPort()
        self.paths = FakePlatformPathsPort("/home/student")
        self.fs.add_dir("/home/student/Desktop")

    def test_restore_linux_shortcut(self) -> None:
        use_case = RestoreGoldenShortcutsUseCase(
            fs=self.fs,
            paths=self.paths,
            platform_name="linux",
        )
        shortcuts = [
            {"name": "insestatut.cat", "url": "https://insestatut.cat"}
        ]
        res = use_case.execute(shortcuts)

        self.assertTrue(res.is_ok())
        created = res.unwrap()
        self.assertEqual(len(created), 1)
        expected_path = "/home/student/Desktop/insestatut.cat.desktop"
        self.assertEqual(created[0], expected_path)

        content = self.fs.read_text_file(expected_path)
        self.assertIsNotNone(content)
        self.assertIn("[Desktop Entry]", content)
        self.assertIn("Type=Link", content)
        self.assertIn("Name=insestatut.cat", content)
        self.assertIn("URL=https://insestatut.cat", content)
        self.assertIn("Icon=web-browser", content)

    def test_restore_windows_shortcut(self) -> None:
        use_case = RestoreGoldenShortcutsUseCase(
            fs=self.fs,
            paths=self.paths,
            platform_name="windows",
        )
        shortcuts = [
            {"name": "Institut Estatut", "url": "https://insestatut.cat"}
        ]
        res = use_case.execute(shortcuts)

        self.assertTrue(res.is_ok())
        created = res.unwrap()
        self.assertEqual(len(created), 1)
        expected_path = "/home/student/Desktop/Institut Estatut.url"
        self.assertEqual(created[0], expected_path)

        content = self.fs.read_text_file(expected_path)
        self.assertIsNotNone(content)
        self.assertIn("[InternetShortcut]", content)
        self.assertIn("URL=https://insestatut.cat", content)
        self.assertIn("\r\n", content)

    def test_restore_macos_shortcut(self) -> None:
        use_case = RestoreGoldenShortcutsUseCase(
            fs=self.fs,
            paths=self.paths,
            platform_name="darwin",
        )
        shortcuts = [
            {"name": "INS Estatut Web", "url": "https://insestatut.cat"}
        ]
        res = use_case.execute(shortcuts)

        self.assertTrue(res.is_ok())
        created = res.unwrap()
        self.assertEqual(len(created), 1)
        expected_path = "/home/student/Desktop/INS Estatut Web.webloc"
        self.assertEqual(created[0], expected_path)

        content = self.fs.read_text_file(expected_path)
        self.assertIsNotNone(content)
        parsed = plistlib.loads(content.encode("utf-8"))
        self.assertEqual(parsed.get("URL"), "https://insestatut.cat")

    def test_url_normalization_prepends_https(self) -> None:
        use_case = RestoreGoldenShortcutsUseCase(
            fs=self.fs,
            paths=self.paths,
            platform_name="linux",
        )
        shortcuts = [
            {"name": "NoSchema", "url": "insestatut.cat"}
        ]
        res = use_case.execute(shortcuts)
        self.assertTrue(res.is_ok())
        content = self.fs.read_text_file("/home/student/Desktop/NoSchema.desktop")
        self.assertIsNotNone(content)
        self.assertIn("URL=https://insestatut.cat", content)

    def test_url_normalization_preserves_existing_http_or_https(self) -> None:
        use_case = RestoreGoldenShortcutsUseCase(
            fs=self.fs,
            paths=self.paths,
            platform_name="linux",
        )
        shortcuts = [
            {"name": "HttpLink", "url": "http://example.com/portal"}
        ]
        res = use_case.execute(shortcuts)
        self.assertTrue(res.is_ok())
        content = self.fs.read_text_file("/home/student/Desktop/HttpLink.desktop")
        self.assertIsNotNone(content)
        self.assertIn("URL=http://example.com/portal", content)

    def test_filename_sanitization_removes_invalid_characters(self) -> None:
        use_case = RestoreGoldenShortcutsUseCase(
            fs=self.fs,
            paths=self.paths,
            platform_name="windows",
        )
        shortcuts = [
            {"name": 'Portal: "Aules" / <2024>? *Special*|', "url": "https://insestatut.cat"}
        ]
        res = use_case.execute(shortcuts)
        self.assertTrue(res.is_ok())
        created = res.unwrap()
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0], "/home/student/Desktop/Portal_ _Aules_ _ _2024__ _Special__.url")

    def test_empty_or_invalid_shortcuts_handled_gracefully(self) -> None:
        use_case = RestoreGoldenShortcutsUseCase(
            fs=self.fs,
            paths=self.paths,
            platform_name="linux",
        )
        # Empty list
        res = use_case.execute([])
        self.assertTrue(res.is_ok())
        self.assertEqual(res.unwrap(), [])

        # List with empty/invalid entries
        res2 = use_case.execute([
            {"name": "", "url": "https://foo.com"},
            {"name": "Bar", "url": ""},
            {"name": "   ", "url": "   "},
        ])
        self.assertTrue(res2.is_ok())
        self.assertEqual(res2.unwrap(), [])

    def test_restore_multiple_shortcuts(self) -> None:
        use_case = RestoreGoldenShortcutsUseCase(
            fs=self.fs,
            paths=self.paths,
            platform_name="linux",
        )
        shortcuts = [
            {"name": "Web1", "url": "https://one.insestatut.cat"},
            {"name": "Web2", "url": "https://two.insestatut.cat"},
            {"name": "Web3", "url": "https://three.insestatut.cat"},
        ]
        res = use_case.execute(shortcuts)
        self.assertTrue(res.is_ok())
        created = res.unwrap()
        self.assertEqual(len(created), 3)
        for i, s in enumerate(shortcuts, 1):
            path = f"/home/student/Desktop/Web{i}.desktop"
            self.assertIn(path, created)
            self.assertTrue(self.fs.exists(path))

    def test_file_write_error_propagates(self) -> None:
        class FailingFileSystem(FakeFileSystemPort):
            def write_text_file(self, path: str, content: str):
                from netejator98.shared.result import Err
                return Err(FileWriteError("Disk is read only"))

        failing_fs = FailingFileSystem()
        use_case = RestoreGoldenShortcutsUseCase(
            fs=failing_fs,
            paths=self.paths,
            platform_name="linux",
        )
        res = use_case.execute([{"name": "test", "url": "https://test.com"}])
        self.assertTrue(res.is_err())
        self.assertEqual(res.unwrap_err().code, "FILE_WRITE_FAILED")


if __name__ == "__main__":
    unittest.main()

