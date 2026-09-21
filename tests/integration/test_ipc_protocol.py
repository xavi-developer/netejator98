"""Integration tests for IPC communication between presentation client and privileged agent daemon."""

from pathlib import Path
import tempfile
import time
import unittest

from netejator98.agent.daemon import AgentDaemon
from netejator98.agent.ipc_server import IPCServer
from netejator98.presentation.ipc_client import IPCClient


class TestIPCProtocolIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.tmp_dir.name) / "agent_storage"
        self.student_home = Path(self.tmp_dir.name) / "student_home"
        self.student_home.mkdir(parents=True, exist_ok=True)
        (self.student_home / "Downloads").mkdir()
        (self.student_home / "Downloads" / "test_download.zip").write_text("dummy download")

        # Socket path
        self.sock_path = Path(self.tmp_dir.name) / "agent.sock"

        # Start daemon & server with active policy for deletion verification
        self.daemon = AgentDaemon(storage_dir=self.storage_dir)
        from netejator98.sanitisation.domain.path_pattern import PathPattern
        from netejator98.sanitisation.domain.policy import CleaningPolicy
        from netejator98.sanitisation.domain.target import CleaningTarget, TargetCategory

        self.daemon.policy = CleaningPolicy(
            dry_run=False,
            targets=[
                CleaningTarget(
                    name="Downloads",
                    category=TargetCategory.USER_DOCUMENTS,
                    enabled=True,
                    patterns=(PathPattern("Downloads/*"),),
                )
            ],
        )
        self.server = IPCServer(self.daemon, socket_path=self.sock_path)
        self.server.start()

        time.sleep(0.05)  # brief wait for server thread
        self.client = IPCClient(socket_path=self.sock_path)

    def tearDown(self) -> None:
        self.server.stop()
        self.tmp_dir.cleanup()

    def test_full_agent_ipc_lifecycle(self) -> None:
        # 1. Initial status: password not set, daemon disabled by default
        status_res = self.client.get_status()
        self.assertTrue(status_res.is_ok())
        status = status_res.unwrap()
        self.assertFalse(status["has_admin_password"])
        self.assertFalse(status["daemon_enabled"])
        self.assertEqual(status["version"], "0.1.0")

        # 2. Bypass fails before admin password is initialized
        bad_bypass = self.client.admin_bypass("SomePassword")
        self.assertTrue(bad_bypass.is_err())

        # 3. Setup initial admin password
        setup_res = self.client.admin_setup_password("MasterAdminSecret2026!")
        self.assertTrue(setup_res.is_ok())
        session_token = setup_res.unwrap()["session_token"]
        self.assertTrue(len(session_token) > 0)

        # Status now reports admin password initialized, daemon still disabled
        status = self.client.get_status().unwrap()
        self.assertTrue(status["has_admin_password"])
        self.assertFalse(status["daemon_enabled"])

        # 4. Admin bypass testing
        # 4a. Wrong admin password fails bypass
        wrong_bypass = self.client.admin_bypass("WrongPassword123")
        self.assertTrue(wrong_bypass.is_err())

        # 4b. Correct admin password succeeds bypass without cleaning
        correct_bypass = self.client.admin_bypass("MasterAdminSecret2026!")
        self.assertTrue(correct_bypass.is_ok())
        bypass_data = correct_bypass.unwrap()
        self.assertTrue(bypass_data["unlocked"])
        self.assertTrue(bypass_data["bypassed"])
        self.assertFalse(bypass_data["sanitised"])
        self.assertTrue((self.student_home / "Downloads" / "test_download.zip").exists())

        # 5. Login while daemon is disabled: no sanitisation occurs
        s0_login = self.client.identify_user(
            "student0@insestatut.cat", target_user_home=str(self.student_home)
        )
        self.assertTrue(s0_login.is_ok())
        s0_data = s0_login.unwrap()
        self.assertEqual(s0_data["user"], "student0@insestatut.cat")
        self.assertFalse(s0_data["sanitised"])
        self.assertTrue((self.student_home / "Downloads" / "test_download.zip").exists())

        # 6. Admin enables daemon
        enable_res = self.client.set_daemon_state(session_token, True)
        self.assertTrue(enable_res.is_ok())
        status = self.client.get_status().unwrap()
        self.assertTrue(status["daemon_enabled"])

        # 7. Student email validation: invalid domain rejected
        bad_login = self.client.identify_user("hacker@gmail.com")
        self.assertTrue(bad_login.is_err())
        self.assertIn("INVALID", bad_login.unwrap_err().code)

        # 8. Student 1 login: first user under enabled daemon triggers sanitisation
        s1_login = self.client.identify_user(
            "student1@insestatut.cat", target_user_home=str(self.student_home)
        )
        self.assertTrue(s1_login.is_ok())
        s1_data = s1_login.unwrap()
        self.assertEqual(s1_data["user"], "student1@insestatut.cat")
        self.assertTrue(s1_data["sanitised"])

        # 9. Student 1 logs in again: same user skips sanitisation
        s1_again = self.client.identify_user(
            "student1@insestatut.cat", target_user_home=str(self.student_home)
        )
        self.assertTrue(s1_again.is_ok())
        self.assertFalse(s1_again.unwrap()["sanitised"])

        # 10. Student 2 logs in: different user triggers sanitisation
        # Place new file in downloads
        (self.student_home / "Downloads" / "s1_file.pdf").write_text("s1 data")
        s2_login = self.client.identify_user(
            "student2@insestatut.cat", target_user_home=str(self.student_home)
        )
        self.assertTrue(s2_login.is_ok())
        s2_data = s2_login.unwrap()
        self.assertEqual(s2_data["user"], "student2@insestatut.cat")
        self.assertTrue(s2_data["sanitised"])
        # s1 file was wiped
        self.assertFalse((self.student_home / "Downloads" / "s1_file.pdf").exists())
        # golden profile shortcut created on Desktop
        self.assertTrue((self.student_home / "Desktop" / "insestatut.cat.desktop").exists())

        # 11. Unauthenticated hash chain verification
        verify_res = self.client.admin_verify_chain()
        self.assertTrue(verify_res.is_ok())
        v_data = verify_res.unwrap()
        self.assertTrue(v_data["is_valid"])
        self.assertTrue(v_data["total_entries"] >= 4)

        # 12. Admin Authentication
        auth_res = self.client.admin_auth("MasterAdminSecret2026!")
        self.assertTrue(auth_res.is_ok())
        admin_token = auth_res.unwrap()["session_token"]

        # 13. Admin queries decrypted audit logs
        logs_res = self.client.admin_get_logs(admin_token)
        self.assertTrue(logs_res.is_ok())
        logs = logs_res.unwrap()
        self.assertTrue(len(logs) >= 4)
        emails = [entry.get("email") for entry in logs]
        self.assertIn("student1@insestatut.cat", emails)
        self.assertIn("student2@insestatut.cat", emails)

        # 10. Admin exports logs to CSV
        export_csv = Path(self.tmp_dir.name) / "exported_audit.csv"
        exp_res = self.client.admin_export_logs(admin_token, str(export_csv))
        self.assertTrue(exp_res.is_ok())
        self.assertTrue(export_csv.exists())
        self.assertIn("student1@insestatut.cat", export_csv.read_text())

        # 11. Admin policy inspection and update
        policy_res = self.client.admin_get_policy(admin_token)
        self.assertTrue(policy_res.is_ok())
        policy_data = policy_res.unwrap()
        self.assertIn("targets", policy_data)

        # Update policy with secure_delete = True
        policy_data["secure_delete"] = True
        up_res = self.client.admin_update_policy(admin_token, policy_data)
        self.assertTrue(up_res.is_ok())
        updated = self.client.admin_get_policy(admin_token).unwrap()
        self.assertTrue(updated["secure_delete"])

        # Reset policy to defaults
        reset_res = self.client.admin_reset_policy(admin_token)
        self.assertTrue(reset_res.is_ok())
        reset_policy = reset_res.unwrap()
        self.assertIn("targets", reset_policy)
        self.assertGreaterEqual(len(reset_policy["targets"]), 30)

        # 12. Admin changes password
        ch_res = self.client.admin_change_password(
            admin_token, "MasterAdminSecret2026!", "NewUpdatedAdminPassword2026!"
        )
        self.assertTrue(ch_res.is_ok())

        # Old password now fails
        self.assertTrue(self.client.admin_auth("MasterAdminSecret2026!").is_err())
        # New password succeeds
        new_auth = self.client.admin_auth("NewUpdatedAdminPassword2026!")
        self.assertTrue(new_auth.is_ok())
        new_token = new_auth.unwrap()["session_token"]

        # 14. Admin disables daemon
        disable_res = self.client.set_daemon_state(new_token, False)
        self.assertTrue(disable_res.is_ok())
        final_status = self.client.get_status().unwrap()
        self.assertFalse(final_status["daemon_enabled"])

    def test_legacy_policy_migration_on_load(self) -> None:
        import yaml
        legacy_config = {
            "dry_run": True,
            "targets": [
                {
                    "name": "UserDocuments",
                    "category": "USER_DOCUMENTS",
                    "patterns": ["Desktop/*", "Documents/*"],
                    "enabled": False,
                },
                {
                    "name": "CachesAndTemp",
                    "category": "TEMP_AND_CACHE",
                    "patterns": [".cache/*"],
                    "enabled": False,
                },
            ],
        }
        test_storage = Path(self.tmp_dir.name) / "legacy_storage"
        test_storage.mkdir(parents=True, exist_ok=True)
        config_file = test_storage / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(legacy_config, f)

        daemon = AgentDaemon(storage_dir=test_storage)
        # Verify that legacy targets without OS were upgraded to full multi-OS targets
        self.assertGreaterEqual(len(daemon.policy.targets), 30)
        os_values = {t.os for t in daemon.policy.targets}
        self.assertIn("Linux", os_values)
        self.assertIn("Windows", os_values)
        self.assertIn("macOS", os_values)

        # Verify strategy diversity across categories
        strategies = {t.strategy.value for t in daemon.policy.targets}
        self.assertIn("PURGE_CHILDREN", strategies)
        self.assertIn("TRUNCATE", strategies)
        self.assertIn("SHRED_NIST", strategies)
        self.assertIn("EMPTY_TRASH", strategies)
        self.assertGreaterEqual(len(strategies), 6)


if __name__ == "__main__":
    unittest.main()

