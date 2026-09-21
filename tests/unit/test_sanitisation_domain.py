import os
import unittest

from netejator98.sanitisation.application.build_plan import (
    BuildSanitisationPlanUseCase,
)
from netejator98.sanitisation.application.dry_run import DryRunUseCase
from netejator98.sanitisation.application.execute import (
    ExecuteSanitisationUseCase,
)
from netejator98.sanitisation.domain.events import (
    SanitisationCompleted,
    SanitisationRequested,
)
from netejator98.sanitisation.domain.path_pattern import PathPattern
from netejator98.sanitisation.domain.policy import CleaningPolicy
from netejator98.sanitisation.domain.protected_path import ProtectedPathRule
from netejator98.sanitisation.domain.strategy import DeletionStrategy
from netejator98.sanitisation.domain.target import CleaningTarget, TargetCategory
from netejator98.shared.errors import ProtectedPathViolationError
from netejator98.shared.event_bus import EventBus
from tests.fakes.fake_sanitisation_ports import (
    FakeCredentialStorePort,
    FakeFileSystemPort,
    FakePlatformPathsPort,
    FakeProcessPort,
)


class TestPathPattern(unittest.TestCase):
    def test_valid_patterns(self) -> None:
        p1 = PathPattern("Downloads/*")
        self.assertEqual(str(p1), "Downloads/*")
        self.assertTrue(p1.is_glob())

        p2 = PathPattern(".bash_history")
        self.assertEqual(str(p2), ".bash_history")
        self.assertFalse(p2.is_glob())

    def test_rejects_path_traversal(self) -> None:
        for bad in ["../system", "foo/../../bar", "..", "foo/.."]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    PathPattern(bad)

    def test_empty_pattern_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PathPattern("   ")


class TestProtectedPathRule(unittest.TestCase):
    def test_protection_boundary_violations(self) -> None:
        rule = ProtectedPathRule("/etc", "System configuration")

        # Exact match
        self.assertTrue(rule.is_violating("/etc"))
        self.assertTrue(rule.is_violating("/etc/"))

        # Child path
        self.assertTrue(rule.is_violating("/etc/passwd"))
        self.assertTrue(rule.is_violating("/etc/netplan/01-net.yaml"))

        # Ancestor path (deleting / would delete /etc)
        self.assertTrue(rule.is_violating("/"))

        # Non-violating paths
        self.assertFalse(rule.is_violating("/home/student"))
        self.assertFalse(rule.is_violating("/tmp"))
        self.assertFalse(rule.is_violating("/etc_backup"))

    def test_windows_protection_rules(self) -> None:
        win_rule = ProtectedPathRule("C:/Windows", "Windows OS")
        self.assertTrue(win_rule.is_violating("c:\\windows\\system32"))
        self.assertTrue(win_rule.is_violating("C:/"))
        self.assertFalse(win_rule.is_violating("C:/Users/Student/Downloads"))


class TestCleaningPolicy(unittest.TestCase):
    def test_invariant_prevents_protected_target(self) -> None:
        policy = CleaningPolicy()

        # Attempting to add target that points to /etc must fail invariant check
        dangerous_target = CleaningTarget(
            name="DangerousSystemClean",
            category=TargetCategory.CUSTOM,
            patterns=(PathPattern("/etc"),),
        )

        with self.assertRaises(ProtectedPathViolationError):
            policy.add_target(dangerous_target)

    def test_add_safe_target_succeeds(self) -> None:
        policy = CleaningPolicy()
        safe_target = CleaningTarget(
            name="StudentDownloads",
            category=TargetCategory.USER_DOCUMENTS,
            patterns=(PathPattern("Downloads/*"),),
        )
        policy.add_target(safe_target)
        self.assertIn(safe_target, policy.targets)

    def test_serialization_roundtrip(self) -> None:
        target = CleaningTarget(
            name="BrowserCache",
            category=TargetCategory.TEMP_AND_CACHE,
            patterns=(PathPattern(".cache/*"),),
            strategy=DeletionStrategy.STANDARD,
            os="Linux",
        )
        policy = CleaningPolicy(targets=[target], secure_delete=True)
        data = policy.to_dict()
        restored = CleaningPolicy.from_dict(data)

        self.assertTrue(restored.secure_delete)
        self.assertEqual(len(restored.targets), 1)
        self.assertEqual(restored.targets[0].name, "BrowserCache")
        self.assertEqual(restored.targets[0].os, "Linux")

    def test_target_os_and_applies_to_os(self) -> None:
        target_all = CleaningTarget(
            name="AllOS",
            category=TargetCategory.USER_DOCUMENTS,
            patterns=(PathPattern("Docs/*"),),
            os="ALL",
        )
        target_linux = CleaningTarget(
            name="LinuxOnly",
            category=TargetCategory.USER_DOCUMENTS,
            patterns=(PathPattern("Docs/*"),),
            os="Linux",
        )
        target_windows = CleaningTarget(
            name="WindowsOnly",
            category=TargetCategory.USER_DOCUMENTS,
            patterns=(PathPattern("Docs/*"),),
            os="Windows",
        )
        target_macos = CleaningTarget(
            name="MacOnly",
            category=TargetCategory.USER_DOCUMENTS,
            patterns=(PathPattern("Docs/*"),),
            os="macOS",
        )

        self.assertTrue(target_all.applies_to_os("Linux"))
        self.assertTrue(target_all.applies_to_os("Windows"))
        self.assertTrue(target_all.applies_to_os("macOS"))
        self.assertTrue(target_all.applies_to_os("Darwin"))

        self.assertTrue(target_linux.applies_to_os("Linux"))
        self.assertFalse(target_linux.applies_to_os("Windows"))
        self.assertFalse(target_linux.applies_to_os("macOS"))

        self.assertTrue(target_windows.applies_to_os("Windows"))
        self.assertFalse(target_windows.applies_to_os("Linux"))

        self.assertTrue(target_macos.applies_to_os("macOS"))
        self.assertTrue(target_macos.applies_to_os("Darwin"))
        self.assertFalse(target_macos.applies_to_os("Linux"))

    def test_golden_profile_serialization(self) -> None:
        policy = CleaningPolicy(
            reset_to_golden_profile=True,
            golden_profile_path="/etc/skel",
            golden_profile_shortcuts=[
                {"name": "insestatut.cat", "url": "https://insestatut.cat"},
                {"name": "Moodle", "url": "https://moodle.insestatut.cat"},
            ],
        )
        data = policy.to_dict()
        self.assertTrue(data["reset_to_golden_profile"])
        self.assertEqual(data["golden_profile_path"], "/etc/skel")
        self.assertEqual(len(data["golden_profile_shortcuts"]), 2)
        self.assertEqual(data["golden_profile_shortcuts"][0]["name"], "insestatut.cat")

        restored = CleaningPolicy.from_dict(data)
        self.assertTrue(restored.reset_to_golden_profile)
        self.assertEqual(restored.golden_profile_path, "/etc/skel")
        self.assertEqual(len(restored.golden_profile_shortcuts), 2)
        self.assertEqual(restored.golden_profile_shortcuts[1]["name"], "Moodle")

    def test_thorough_logging_serialization(self) -> None:
        policy = CleaningPolicy(thorough_logging=True)
        data = policy.to_dict()
        self.assertTrue(data["thorough_logging"])

        restored = CleaningPolicy.from_dict(data)
        self.assertTrue(restored.thorough_logging)

        # Default is False
        policy_default = CleaningPolicy()
        self.assertFalse(policy_default.thorough_logging)
        data_default = policy_default.to_dict()
        self.assertFalse(data_default["thorough_logging"])
        self.assertFalse(CleaningPolicy.from_dict(data_default).thorough_logging)

    def test_all_categories_and_strategies_per_os(self) -> None:
        import yaml
        from pathlib import Path
        repo_root = Path(__file__).resolve().parent.parent.parent
        policy_file = repo_root / "policies" / "defaults" / "linux.yaml"
        self.assertTrue(policy_file.exists())
        with open(policy_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        policy = CleaningPolicy.from_dict(data)
        all_categories = {c.value for c in TargetCategory}

        for os_name in ("Linux", "Windows", "macOS"):
            os_targets = [t for t in policy.targets if t.os == os_name]
            # Verify each OS has all 11 categories represented
            os_categories = {t.category.value for t in os_targets}
            self.assertEqual(all_categories, os_categories, f"Missing categories for {os_name}: {all_categories - os_categories}")
            # Verify diverse strategies are used (not just STANDARD)
            os_strategies = {t.strategy.value for t in os_targets}
            self.assertGreaterEqual(len(os_strategies), 6, f"Not enough strategies for {os_name}: {os_strategies}")
            self.assertIn("PURGE_CHILDREN", os_strategies)
            self.assertIn("TRUNCATE", os_strategies)
            self.assertIn("SHRED_NIST", os_strategies)
            self.assertIn("EMPTY_TRASH", os_strategies)



class TestSanitisationExecution(unittest.TestCase):
    def setUp(self) -> None:
        self.fs = FakeFileSystemPort()
        self.paths = FakePlatformPathsPort("/home/student")
        self.bus = EventBus()
        self.process = FakeProcessPort()
        self.credential = FakeCredentialStorePort()

        # Populate fake student directory
        self.fs.add_file("/home/student/Downloads/homework.pdf", size=5000)
        self.fs.add_file("/home/student/Downloads/game.zip", size=10000)
        self.fs.add_file("/home/student/Desktop/notes.txt", size=200)
        self.fs.add_file("/home/student/.bash_history", size=800)

        # Locked file that will unlock after 2 attempts
        self.fs.add_file("/home/student/.cache/session.lock", size=100, locked=True)

        self.policy = CleaningPolicy(
            targets=[
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
            ]
        )

    def test_dry_run_leaves_filesystem_untouched(self) -> None:
        dry_run_use_case = DryRunUseCase(self.fs, self.paths)
        outcome = dry_run_use_case.execute(self.policy, user_email="student@insestatut.cat")

        self.assertTrue(outcome.dry_run)
        self.assertEqual(outcome.files_deleted, 5)
        self.assertEqual(outcome.bytes_freed, 16100)

        # Verify nothing was deleted from virtual filesystem
        self.assertTrue(self.fs.exists("/home/student/Downloads/homework.pdf"))
        self.assertTrue(self.fs.exists("/home/student/Desktop/notes.txt"))
        self.assertEqual(len(self.fs.deleted_paths), 0)

    def test_execute_sanitisation_deletes_files_with_resilient_retry(self) -> None:
        executor = ExecuteSanitisationUseCase(
            fs=self.fs,
            paths=self.paths,
            event_bus=self.bus,
            process_port=self.process,
            credential_port=self.credential,
            max_retries=3,
            retry_delay_seconds=0.01,
        )

        outcome = executor.execute(self.policy, user_email="student@insestatut.cat")

        self.assertFalse(outcome.dry_run)
        self.assertTrue(outcome.is_success)
        self.assertEqual(outcome.files_deleted, 5)

        # Files should be deleted now
        self.assertFalse(self.fs.exists("/home/student/Downloads/homework.pdf"))
        self.assertFalse(self.fs.exists("/home/student/Downloads/game.zip"))
        self.assertFalse(self.fs.exists("/home/student/Desktop/notes.txt"))
        self.assertFalse(self.fs.exists("/home/student/.bash_history"))
        self.assertFalse(self.fs.exists("/home/student/.cache/session.lock"))

        # Process and credential ports called
        self.assertIn(TargetCategory.BROWSER_PROFILES, self.process.terminated_targets)
        self.assertTrue(self.credential.cleared)

        # Verify domain events fired
        req_events = [e for e in self.bus.recorded_events if isinstance(e, SanitisationRequested)]
        comp_events = [e for e in self.bus.recorded_events if isinstance(e, SanitisationCompleted)]
        self.assertEqual(len(req_events), 1)
        self.assertEqual(len(comp_events), 1)

    def test_runtime_safety_invariant_blocks_protected_deletion(self) -> None:
        from unittest.mock import patch
        from netejator98.sanitisation.domain.plan import PlannedDeletion, SanitisationPlan

        # Add a file in /etc to fake filesystem
        self.fs.add_file("/etc/shadow", size=100)

        # 1. Test that SanitisationPlanner filters out protected path during planning
        dangerous_target = CleaningTarget(
            name="BypassedTarget",
            category=TargetCategory.CUSTOM,
            patterns=(PathPattern("safe_target"),),
        )
        object.__setattr__(dangerous_target.patterns[0], "pattern", "/etc/shadow")
        self.policy.targets.append(dangerous_target)

        plan = BuildSanitisationPlanUseCase(self.fs, self.paths).execute(self.policy)
        self.assertNotIn("/etc/shadow", [item.path for item in plan.items])

        # 2. Test defense-in-depth: Even if a corrupted plan contains a protected path,
        # ExecuteSanitisationUseCase refuses to delete it at runtime
        executor = ExecuteSanitisationUseCase(
            fs=self.fs,
            paths=self.paths,
            event_bus=self.bus,
        )

        corrupted_plan = SanitisationPlan(
            user_profile_root="/home/student",
            items=(
                PlannedDeletion(
                    path="/etc/shadow",
                    target_name="CorruptTarget",
                    strategy=DeletionStrategy.STANDARD,
                    is_directory=False,
                    estimated_bytes=100,
                ),
            ),
        )
        with patch.object(executor._builder, "execute", return_value=corrupted_plan):
            outcome = executor.execute(self.policy)

        # /etc/shadow must NOT be deleted!
        self.assertTrue(self.fs.exists("/etc/shadow"))
        self.assertFalse(outcome.is_success)
        self.assertTrue(any("Runtime safety invariant violation" in err for err in outcome.errors))

    def test_truncate_and_purge_strategies(self) -> None:
        from unittest.mock import patch
        from netejator98.sanitisation.domain.plan import PlannedDeletion, SanitisationPlan

        # Add a history file to truncate
        hist_path = "/home/student/.bash_history"
        self.fs.add_file(hist_path, size=500)
        self.fs.file_contents[self.fs._norm(hist_path)] = "secret_command_history"

        # Add directory and files to purge
        down_dir = "/home/student/Downloads"
        self.fs.add_dir(down_dir)
        self.fs.add_file(f"{down_dir}/doc1.pdf", size=200)
        self.fs.add_file(f"{down_dir}/doc2.pdf", size=300)

        executor = ExecuteSanitisationUseCase(
            fs=self.fs,
            paths=self.paths,
            event_bus=self.bus,
        )

        plan = SanitisationPlan(
            user_profile_root="/home/student",
            items=(
                PlannedDeletion(
                    path=hist_path,
                    target_name="ShellHistory",
                    strategy=DeletionStrategy.TRUNCATE,
                    is_directory=False,
                    estimated_bytes=500,
                ),
                PlannedDeletion(
                    path=down_dir,
                    target_name="UserDocuments",
                    strategy=DeletionStrategy.PURGE_CHILDREN,
                    is_directory=True,
                    estimated_bytes=500,
                ),
            ),
        )

        with patch.object(executor._builder, "execute", return_value=plan):
            outcome = executor.execute(self.policy)

        self.assertTrue(outcome.is_success)
        # History file should still exist but size 0 and content empty
        self.assertTrue(self.fs.exists(hist_path))
        self.assertEqual(self.fs.get_size(hist_path), 0)
        self.assertEqual(self.fs.file_contents.get(self.fs._norm(hist_path)), "")

        # Directory should still exist, but children purged
        self.assertTrue(self.fs.is_dir(down_dir))
        self.assertFalse(self.fs.exists(f"{down_dir}/doc1.pdf"))
        self.assertFalse(self.fs.exists(f"{down_dir}/doc2.pdf"))

    def test_absolute_pattern_with_glob_matches_files(self) -> None:
        from netejator98.sanitisation.application.dry_run import DryRunUseCase
        from netejator98.sanitisation.infrastructure.real_filesystem import RealFileSystem
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = os.path.join(tmpdir, "Documents")
            os.makedirs(docs_dir, exist_ok=True)
            doc_file = os.path.join(docs_dir, "document.pdf")
            with open(doc_file, "w") as f:
                f.write("content")

            pat = f"{docs_dir}/*"
            target = CleaningTarget(
                name="Absolute User Documents",
                category=TargetCategory.USER_DOCUMENTS,
                patterns=(PathPattern(pat),),
                strategy=DeletionStrategy.STANDARD,
                os="ALL",
            )
            policy = CleaningPolicy(dry_run=True, targets=[target])

            real_fs = RealFileSystem()
            matches = real_fs.find_matching_paths(pat, "")
            self.assertIn(os.path.normpath(doc_file), matches)

            dry_runner = DryRunUseCase(fs=real_fs, paths=self.paths)
            outcome = dry_runner.execute(policy)
            self.assertEqual(outcome.files_deleted, 1)
            self.assertGreater(outcome.bytes_freed, 0)

    def test_thorough_logging_generates_trace_file(self) -> None:
        import tempfile
        from netejator98.sanitisation.infrastructure.real_filesystem import RealFileSystem
        from netejator98.sanitisation.application.dry_run import DryRunUseCase

        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = os.path.join(tmpdir, "Documents")
            os.makedirs(docs_dir, exist_ok=True)
            doc_file = os.path.join(docs_dir, "test_doc.txt")
            with open(doc_file, "w") as f:
                f.write("test content")

            target = CleaningTarget(
                name="Thorough User Docs",
                category=TargetCategory.USER_DOCUMENTS,
                patterns=(PathPattern(f"{docs_dir}/*"),),
                strategy=DeletionStrategy.STANDARD,
                os="ALL",
            )
            policy = CleaningPolicy(
                dry_run=True,
                thorough_logging=True,
                targets=[target],
            )

            real_fs = RealFileSystem()
            dry_runner = DryRunUseCase(fs=real_fs, paths=self.paths)
            outcome = dry_runner.execute(policy)

            self.assertEqual(outcome.files_deleted, 1)
            self.assertIsNotNone(outcome.log_file_path)
            self.assertTrue(os.path.exists(outcome.log_file_path))
            with open(outcome.log_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("STARTING CLEANING PROCESS", content)
            self.assertIn("CLEANING PROCESS FINISHED", content)
            self.assertIn("Thorough User Docs", content)


if __name__ == "__main__":
    unittest.main()
