"""Integration tests for RealFileSystem and Sanitisation execution against a sandboxed directory tree."""

import os
from pathlib import Path
import stat
import tempfile
import unittest

from netejator98.sanitisation.application.dry_run import DryRunUseCase
from netejator98.sanitisation.application.execute import (
    ExecuteSanitisationUseCase,
)
from netejator98.sanitisation.application.restore_shortcuts import (
    RestoreGoldenShortcutsUseCase,
)
from netejator98.sanitisation.domain.path_pattern import PathPattern
from netejator98.sanitisation.domain.policy import CleaningPolicy
from netejator98.sanitisation.domain.protected_path import ProtectedPathRule
from netejator98.sanitisation.domain.strategy import DeletionStrategy
from netejator98.sanitisation.domain.target import CleaningTarget, TargetCategory
from netejator98.sanitisation.infrastructure.linux_paths import LinuxPathsAdapter
from netejator98.sanitisation.infrastructure.real_filesystem import RealFileSystem
from netejator98.shared.event_bus import EventBus


class TestSanitisationSandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.sandbox_root = Path(self.tmp_dir_obj.name).resolve()
        self.user_home = self.sandbox_root / "home" / "student"
        self.user_home.mkdir(parents=True, exist_ok=True)

        self.fs = RealFileSystem()
        self.paths = LinuxPathsAdapter(str(self.user_home))
        self.bus = EventBus()

        # Build realistic student workstation tree
        self.docs_dir = self.user_home / "Documents"
        self.docs_dir.mkdir()
        (self.docs_dir / "essay.docx").write_text("Student essay content")

        self.dl_dir = self.user_home / "Downloads"
        self.dl_dir.mkdir()
        (self.dl_dir / "installer.bin").write_bytes(b"\x7fELF" + b"A" * 1000)

        self.desktop_dir = self.user_home / "Desktop"
        self.desktop_dir.mkdir()
        (self.desktop_dir / "homework.txt").write_text("Math homework")

        # Read-only file (to test resilient permission resetting)
        self.ro_file = self.desktop_dir / "locked_notes.txt"
        self.ro_file.write_text("Important notes - read only")
        os.chmod(self.ro_file, stat.S_IREAD)

        self.cache_dir = self.user_home / ".cache"
        self.cache_dir.mkdir()
        (self.cache_dir / "cached_image.png").write_bytes(b"\x89PNG" + b"0" * 500)

        self.history_file = self.user_home / ".bash_history"
        self.history_file.write_text("ls -la\nrm test\n")

        self.ssh_dir = self.user_home / ".ssh"
        self.ssh_dir.mkdir()
        (self.ssh_dir / "id_rsa").write_text("-----BEGIN RSA PRIVATE KEY-----")

        # Untargeted file that must be preserved
        self.system_settings = self.user_home / ".profile"
        self.system_settings.write_text("export PATH=$PATH:/usr/local/bin")

        self.policy = CleaningPolicy(
            targets=[
                CleaningTarget(
                    name="Documents",
                    category=TargetCategory.USER_DOCUMENTS,
                    patterns=(PathPattern("Documents/*"),),
                ),
                CleaningTarget(
                    name="Downloads",
                    category=TargetCategory.USER_DOCUMENTS,
                    patterns=(PathPattern("Downloads/*"),),
                ),
                CleaningTarget(
                    name="Desktop",
                    category=TargetCategory.USER_DOCUMENTS,
                    patterns=(PathPattern("Desktop/*"),),
                ),
                CleaningTarget(
                    name="Cache",
                    category=TargetCategory.TEMP_AND_CACHE,
                    patterns=(PathPattern(".cache/*"),),
                ),
                CleaningTarget(
                    name="ShellHistory",
                    category=TargetCategory.SHELL_HISTORY,
                    patterns=(PathPattern(".bash_history"),),
                ),
                CleaningTarget(
                    name="Credentials",
                    category=TargetCategory.CREDENTIALS,
                    patterns=(PathPattern(".ssh/*"),),
                ),
            ]
        )

    def tearDown(self) -> None:
        # Restore permissions if needed before cleanup
        try:
            if self.ro_file.exists():
                os.chmod(self.ro_file, stat.S_IWRITE | stat.S_IREAD)
        except OSError:
            pass
        self.tmp_dir_obj.cleanup()

    def test_dry_run_against_real_filesystem_preserves_all_files(self) -> None:
        dry_run = DryRunUseCase(self.fs, self.paths)
        outcome = dry_run.execute(self.policy, user_email="student@insestatut.cat")

        self.assertTrue(outcome.dry_run)
        self.assertTrue(outcome.files_deleted >= 6)

        # All files must remain intact on real disk
        self.assertTrue((self.docs_dir / "essay.docx").exists())
        self.assertTrue((self.dl_dir / "installer.bin").exists())
        self.assertTrue(self.ro_file.exists())
        self.assertTrue(self.history_file.exists())
        self.assertTrue((self.ssh_dir / "id_rsa").exists())

    def test_real_sanitisation_deletes_files_and_clears_read_only(self) -> None:
        executor = ExecuteSanitisationUseCase(
            fs=self.fs,
            paths=self.paths,
            event_bus=self.bus,
        )

        outcome = executor.execute(self.policy, user_email="student@insestatut.cat")

        self.assertFalse(outcome.dry_run)
        self.assertTrue(outcome.is_success)

        # Targeted files must be deleted
        self.assertFalse((self.docs_dir / "essay.docx").exists())
        self.assertFalse((self.dl_dir / "installer.bin").exists())
        self.assertFalse((self.desktop_dir / "homework.txt").exists())
        # Read-only file must also have been deleted through permission resetting!
        self.assertFalse(self.ro_file.exists())
        self.assertFalse((self.cache_dir / "cached_image.png").exists())
        self.assertFalse(self.history_file.exists())
        self.assertFalse((self.ssh_dir / "id_rsa").exists())

        # Preserved untargeted file
        self.assertTrue(self.system_settings.exists())

    def test_secure_delete_overwrites_file_content(self) -> None:
        secret_file = self.user_home / "secret.txt"
        secret_file.write_text("HighlyConfidentialStudentData1234567890")

        # Overwrite file directly via RealFileSystem with secure=True
        self.fs.remove_file(str(secret_file), secure=True)
        self.assertFalse(secret_file.exists())

    def test_protected_path_rules_strictly_defend_system_roots(self) -> None:
        protected_root = self.sandbox_root / "etc"
        protected_root.mkdir(parents=True, exist_ok=True)
        secret_sys_file = protected_root / "passwd"
        secret_sys_file.write_text("root:x:0:0:root:/root:/bin/bash")

        custom_rule = ProtectedPathRule(str(protected_root), "Simulated /etc")
        self.policy.protected_rules.append(custom_rule)

        executor = ExecuteSanitisationUseCase(
            fs=self.fs,
            paths=self.paths,
            event_bus=self.bus,
        )

        # Attempt to target protected file directly
        from unittest.mock import patch
        from netejator98.sanitisation.domain.plan import PlannedDeletion, SanitisationPlan

        injected_plan = SanitisationPlan(
            user_profile_root=str(self.user_home),
            items=(
                PlannedDeletion(
                    path=str(secret_sys_file),
                    target_name="SystemEtc",
                    strategy=DeletionStrategy.STANDARD,
                    is_directory=False,
                    estimated_bytes=100,
                ),
            ),
        )

        with patch.object(executor._builder, "execute", return_value=injected_plan):
            outcome = executor.execute(self.policy)

        # File in protected root must still exist!
        self.assertTrue(secret_sys_file.exists())
        self.assertFalse(outcome.is_success)

    def test_restore_golden_shortcuts_creates_real_files_on_disk(self) -> None:
        use_case = RestoreGoldenShortcutsUseCase(
            fs=self.fs,
            paths=self.paths,
            platform_name="linux",
        )
        shortcuts = [
            {"name": "Institut Estatut", "url": "https://insestatut.cat"}
        ]
        res = use_case.execute(shortcuts)
        self.assertTrue(res.is_ok())
        created = res.unwrap()
        self.assertEqual(len(created), 1)

        expected_file = self.desktop_dir / "Institut Estatut.desktop"
        self.assertTrue(expected_file.exists())
        content = expected_file.read_text(encoding="utf-8")
        self.assertIn("[Desktop Entry]", content)
        self.assertIn("URL=https://insestatut.cat", content)
        self.assertIn("Name=Institut Estatut", content)


if __name__ == "__main__":
    unittest.main()

