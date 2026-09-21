"""Cryptographic tests for X25519 sealed boxes, Argon2id key wrapping, and hash-chain tampering detection."""

import os
from pathlib import Path
import tempfile
import unittest

from netejator98.audit.domain.entry import AuditEntry
from netejator98.audit.domain.hash_chain import HashChain
from netejator98.audit.domain.sealed_entry import SealedEntry
from netejator98.audit.domain.trail import AuditTrail
from netejator98.audit.infrastructure.key_wrap_adapter import Argon2KeyWrapAdapter
from netejator98.audit.infrastructure.sealed_repo import (
    EncryptedJsonlAuditRepository,
)
from netejator98.audit.infrastructure.x25519_adapter import X25519SealAdapter
from netejator98.shared.clock import SystemClock


class TestAuditCryptoSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.pub_bytes, self.priv_bytes = X25519SealAdapter.generate_keypair()
        self.sealer = X25519SealAdapter.from_public_key_bytes(self.pub_bytes)
        self.opener = X25519SealAdapter.from_private_key_bytes(self.priv_bytes)
        self.wrapper = Argon2KeyWrapAdapter()

    def test_sealed_entries_roundtrip_with_correct_key(self) -> None:
        message = b"Confidential student login record: student1@insestatut.cat"
        seal_res = self.sealer.seal(message)
        self.assertTrue(seal_res.is_ok())
        ciphertext_b64 = seal_res.unwrap()

        open_res = self.opener.open(ciphertext_b64)
        self.assertTrue(open_res.is_ok())
        self.assertEqual(open_res.unwrap(), message)

    def test_agent_can_append_with_public_key_alone(self) -> None:
        """Agent only possesses the public key and can seal and append entries."""
        agent_sealer = X25519SealAdapter.from_public_key_bytes(self.pub_bytes)
        # Agent cannot decrypt
        self.assertTrue(agent_sealer.open("AAAA").is_err())

        # Agent can successfully seal
        clock = SystemClock()
        entry = AuditEntry(
            timestamp=clock.now_utc(),
            machine_id="agent-box",
            hostname="host",
            event_type="LOGIN",
            email="student@insestatut.cat",
            outcome="SUCCESS",
        )
        sealed_b64 = agent_sealer.seal(entry.to_json_bytes()).unwrap()
        trail = AuditTrail()
        sealed_entry = trail.prepare_next_entry(sealed_b64)
        self.assertEqual(sealed_entry.seq, 1)

    def test_wrong_password_fails_to_unwrap_private_key(self) -> None:
        admin_password = "CorrectSuperSecretPassword123!"
        wrong_password = "WrongPasswordGuess!"

        # Wrap private key
        wrap_res = self.wrapper.wrap_key(self.priv_bytes, admin_password)
        self.assertTrue(wrap_res.is_ok())
        wrapped_blob = wrap_res.unwrap()

        # Unwrap with correct password succeeds
        unwrap_ok = self.wrapper.unwrap_key(wrapped_blob, admin_password)
        self.assertTrue(unwrap_ok.is_ok())
        self.assertEqual(unwrap_ok.unwrap(), self.priv_bytes)

        # Unwrap with wrong password fails
        unwrap_err = self.wrapper.unwrap_key(wrapped_blob, wrong_password)
        self.assertTrue(unwrap_err.is_err())
        self.assertEqual(unwrap_err.unwrap_err().code, "KEY_UNWRAP_FAILED")

    def test_recovery_key_unwraps_same_private_key(self) -> None:
        recovery_key = "RECOVERY-KEY-A1B2-C3D4-E5F6-7890"
        wrap_res = self.wrapper.wrap_with_recovery_key(self.priv_bytes, recovery_key)
        self.assertTrue(wrap_res.is_ok())
        wrapped_blob = wrap_res.unwrap()

        unwrap_res = self.wrapper.unwrap_with_recovery_key(wrapped_blob, recovery_key)
        self.assertTrue(unwrap_res.is_ok())
        self.assertEqual(unwrap_res.unwrap(), self.priv_bytes)

    def test_password_change_preserves_readability_of_prior_entries(self) -> None:
        """Password change re-wraps the private key; previous log entries remain decryptable."""
        old_password = "OldAdminPassword1!"
        new_password = "NewAdminPassword2!"

        # Initial wrap
        wrapped_blob_1 = self.wrapper.wrap_key(self.priv_bytes, old_password).unwrap()

        # Record and seal 2 entries with public key
        trail = AuditTrail()
        msg1 = b"Entry before password change 1"
        msg2 = b"Entry before password change 2"
        e1 = trail.prepare_next_entry(self.sealer.seal(msg1).unwrap())
        e2 = trail.prepare_next_entry(self.sealer.seal(msg2).unwrap())

        # Admin changes password: unwrap with old, re-wrap with new
        unwrapped_priv = self.wrapper.unwrap_key(wrapped_blob_1, old_password).unwrap()
        wrapped_blob_2 = self.wrapper.wrap_key(unwrapped_priv, new_password).unwrap()

        # Old password no longer unwraps new blob
        self.assertTrue(self.wrapper.unwrap_key(wrapped_blob_2, old_password).is_err())

        # New password unwraps key and successfully decrypts historical pre-change entries!
        active_priv = self.wrapper.unwrap_key(wrapped_blob_2, new_password).unwrap()
        new_opener = X25519SealAdapter.from_private_key_bytes(active_priv)

        self.assertEqual(new_opener.open(e1.sealed).unwrap(), msg1)
        self.assertEqual(new_opener.open(e2.sealed).unwrap(), msg2)

    def test_hash_chain_tampering_detection_on_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = EncryptedJsonlAuditRepository(tmpdir)
            trail = AuditTrail()

            # Append 4 valid entries
            for i in range(1, 5):
                sealed_b64 = self.sealer.seal(f"Entry {i}".encode("utf-8")).unwrap()
                entry = trail.prepare_next_entry(sealed_b64)
                repo.append_entry(entry)

            # 1. Unauthenticated verification on untouched log succeeds
            all_entries = repo.get_all_entries()
            self.assertEqual(len(all_entries), 4)
            res = HashChain.verify_chain(all_entries)
            self.assertTrue(res.is_valid)
            self.assertEqual(res.total_entries, 4)

            # 2. Tampering test: Modifying ciphertext on disk
            log_file = Path(tmpdir) / "audit_trail.jsonl"
            with open(log_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            # Modify line 2
            import json
            tampered_dict = json.loads(lines[1])
            tampered_dict["sealed"] = "AAAA" + tampered_dict["sealed"][4:]
            lines_tampered = list(lines)
            lines_tampered[1] = json.dumps(tampered_dict)

            with open(log_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines_tampered) + "\n")

            repo_tampered = EncryptedJsonlAuditRepository(tmpdir)
            tampered_entries = repo_tampered.get_all_entries()
            verify_tampered = HashChain.verify_chain(tampered_entries)
            self.assertFalse(verify_tampered.is_valid)

            # 3. Tampering test: Deleting an entry
            lines_deleted = [lines[0], lines[2], lines[3]]  # dropped line 1 (seq 2)
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines_deleted) + "\n")

            repo_deleted = EncryptedJsonlAuditRepository(tmpdir)
            verify_deleted = HashChain.verify_chain(repo_deleted.get_all_entries())
            self.assertFalse(verify_deleted.is_valid)
            self.assertIn("Sequence break", verify_deleted.failure_reason or "")

            # 4. Tampering test: Reordering entries
            lines_reordered = [lines[1], lines[0], lines[2], lines[3]]
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines_reordered) + "\n")

            repo_reordered = EncryptedJsonlAuditRepository(tmpdir)
            verify_reordered = HashChain.verify_chain(repo_reordered.get_all_entries())
            self.assertFalse(verify_reordered.is_valid)

            # 5. Tampering test: Truncation after entry 2
            lines_truncated = lines[:2]
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines_truncated) + "\n")

            repo_truncated = EncryptedJsonlAuditRepository(tmpdir)
            verify_truncated = HashChain.verify_chain(repo_truncated.get_all_entries())
            # Truncated file is valid up to entry 2, but count is 2
            self.assertTrue(verify_truncated.is_valid)
            self.assertEqual(verify_truncated.total_entries, 2)


if __name__ == "__main__":
    unittest.main()

