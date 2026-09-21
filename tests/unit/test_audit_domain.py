"""Unit tests for the Audit domain, hash chain, and application use cases."""

from datetime import datetime, timezone
import tempfile
import unittest

from netejator98.access.domain.admin import AdminSession
from netejator98.audit.application.export_log import ExportAuditLogUseCase
from netejator98.audit.application.query_log import QueryAuditLogUseCase
from netejator98.audit.application.record_login import RecordLoginUseCase
from netejator98.audit.application.record_sanitisation import (
    RecordSanitisationUseCase,
)
from netejator98.audit.application.verify_chain import (
    VerifyChainIntegrityUseCase,
)
from netejator98.audit.domain.entry import AuditEntry
from netejator98.audit.domain.hash_chain import HashChain
from netejator98.audit.domain.sealed_entry import (
    GENESIS_PREV_HASH,
    SealedEntry,
)
from netejator98.audit.domain.trail import AuditTrail
from netejator98.shared.clock import FrozenClock
from netejator98.shared.machine_id import MachineId
from tests.fakes.fake_audit_ports import (
    FakeAuditLogRepository,
    FakeSimpleOpener,
    FakeSimpleSealer,
)


class TestAuditEntry(unittest.TestCase):
    def test_serialization_roundtrip(self) -> None:
        dt = datetime(2026, 9, 16, 11, 30, 0, tzinfo=timezone.utc)
        entry = AuditEntry(
            timestamp=dt,
            machine_id="test-pc-01",
            hostname="pc-lab-01",
            event_type="LOGIN_ATTEMPT",
            email="student1@insestatut.cat",
            outcome="SUCCESS",
            targets_cleaned=["Downloads", "BrowserHistory"],
            errors=[],
        )
        data = entry.to_json_bytes()
        restored = AuditEntry.from_json_bytes(data)

        self.assertEqual(restored.timestamp, dt)
        self.assertEqual(restored.machine_id, "test-pc-01")
        self.assertEqual(restored.email, "student1@insestatut.cat")
        self.assertEqual(restored.targets_cleaned, ["Downloads", "BrowserHistory"])


class TestSealedEntryAndHashChain(unittest.TestCase):
    def test_sealed_entry_creation_and_hash_calculation(self) -> None:
        entry1 = SealedEntry.create(seq=1, prev_hash=GENESIS_PREV_HASH, sealed_base64="AAAA")
        self.assertEqual(entry1.seq, 1)
        self.assertTrue(entry1.is_hash_valid())

        # Hash validation reports invalid if tampered
        tampered = SealedEntry(seq=1, sealed="AAAA", prev_hash=GENESIS_PREV_HASH, entry_hash="tampered")
        self.assertFalse(tampered.is_hash_valid())

        # Structural validation rejects invalid sequence or empty fields
        with self.assertRaises(ValueError):
            SealedEntry(seq=0, sealed="AAAA", prev_hash=GENESIS_PREV_HASH, entry_hash="hash")
        with self.assertRaises(ValueError):
            SealedEntry(seq=1, sealed="", prev_hash=GENESIS_PREV_HASH, entry_hash="hash")

    def test_audit_trail_chain_continuity(self) -> None:
        trail = AuditTrail()
        e1 = trail.prepare_next_entry("CIPHERTEXT_1")
        e2 = trail.prepare_next_entry("CIPHERTEXT_2")
        e3 = trail.prepare_next_entry("CIPHERTEXT_3")

        self.assertEqual(e1.seq, 1)
        self.assertEqual(e1.prev_hash, GENESIS_PREV_HASH)

        self.assertEqual(e2.seq, 2)
        self.assertEqual(e2.prev_hash, e1.entry_hash)

        self.assertEqual(e3.seq, 3)
        self.assertEqual(e3.prev_hash, e2.entry_hash)

        # Verify through HashChain domain service
        result = HashChain.verify_chain([e1, e2, e3])
        self.assertTrue(result.is_valid)
        self.assertEqual(result.total_entries, 3)

    def test_hash_chain_detects_tampered_payload(self) -> None:
        trail = AuditTrail()
        e1 = trail.prepare_next_entry("CIPHERTEXT_1")
        e2 = trail.prepare_next_entry("CIPHERTEXT_2")

        # Tamper e2 ciphertext while keeping old entry_hash
        tampered_e2 = SealedEntry(
            seq=e2.seq,
            sealed="MODIFIED_CIPHERTEXT",
            prev_hash=e2.prev_hash,
            entry_hash=SealedEntry.calculate_hash(e2.seq, e2.prev_hash, "MODIFIED_CIPHERTEXT"),
        )
        # However, next entry e3 would break chain continuity
        e3 = trail.prepare_next_entry("CIPHERTEXT_3")

        result = HashChain.verify_chain([e1, tampered_e2, e3])
        self.assertFalse(result.is_valid)
        self.assertEqual(result.tampered_seq, 3)
        self.assertIn("Hash chain broken", result.failure_reason or "")

    def test_hash_chain_detects_deleted_entry(self) -> None:
        trail = AuditTrail()
        e1 = trail.prepare_next_entry("CIPHERTEXT_1")
        e2 = trail.prepare_next_entry("CIPHERTEXT_2")
        e3 = trail.prepare_next_entry("CIPHERTEXT_3")

        # Remove e2
        result = HashChain.verify_chain([e1, e3])
        self.assertFalse(result.is_valid)
        self.assertEqual(result.tampered_seq, 3)
        self.assertIn("Sequence break", result.failure_reason or "")

    def test_hash_chain_detects_reordered_entries(self) -> None:
        trail = AuditTrail()
        e1 = trail.prepare_next_entry("CIPHERTEXT_1")
        e2 = trail.prepare_next_entry("CIPHERTEXT_2")

        # Reorder
        result = HashChain.verify_chain([e2, e1])
        self.assertFalse(result.is_valid)
        self.assertIn("Sequence break", result.failure_reason or "")


class TestAuditApplicationUseCases(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FakeAuditLogRepository()
        self.sealer = FakeSimpleSealer()
        self.opener = FakeSimpleOpener()
        self.clock = FrozenClock()
        self.mid = MachineId("test-machine-42")

    def test_record_login_and_query_with_admin_session(self) -> None:
        record_use_case = RecordLoginUseCase(
            repository=self.repo,
            sealer=self.sealer,
            machine_id=self.mid,
            clock=self.clock,
        )

        # 1. Record 2 login events
        res1 = record_use_case.execute("student1@insestatut.cat", "LOGIN_SUCCESS", "SUCCESS")
        self.assertTrue(res1.is_ok())

        self.clock.advance_seconds(60)
        res2 = record_use_case.execute("student2@insestatut.cat", "LOGIN_FAILED", "REJECTED")
        self.assertTrue(res2.is_ok())

        self.assertEqual(self.repo.count(), 2)

        # 2. Query log with valid AdminSession
        query_use_case = QueryAuditLogUseCase(self.repo, self.opener, self.clock)
        session = AdminSession.create(ttl_minutes=15, current_time=self.clock.now_utc())

        query_res = query_use_case.execute(session)
        self.assertTrue(query_res.is_ok())
        entries = query_res.unwrap()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].email, "student1@insestatut.cat")
        self.assertEqual(entries[1].email, "student2@insestatut.cat")

        # 3. Query fails with expired session
        self.clock.advance_seconds(1000)
        expired_res = query_use_case.execute(session)
        self.assertTrue(expired_res.is_err())
        self.assertEqual(expired_res.unwrap_err().code, "ADMIN_AUTH_FAILED")

    def test_verify_chain_unauthenticated(self) -> None:
        record_login = RecordLoginUseCase(self.repo, self.sealer, self.mid, self.clock)
        record_login.execute("student1@insestatut.cat", "LOGIN", "SUCCESS")
        record_login.execute("student2@insestatut.cat", "LOGIN", "SUCCESS")

        verify_use_case = VerifyChainIntegrityUseCase(self.repo)
        verification = verify_use_case.execute()
        self.assertTrue(verification.is_valid)
        self.assertEqual(verification.total_entries, 2)

    def test_export_audit_log_to_csv(self) -> None:
        record_sanitisation = RecordSanitisationUseCase(
            self.repo, self.sealer, self.mid, self.clock
        )
        record_sanitisation.execute(
            event_type="SANITISATION_COMPLETED",
            email="student1@insestatut.cat",
            outcome="SUCCESS",
            targets_cleaned=["Downloads", "RecycleBin"],
            errors=[],
        )

        export_use_case = ExportAuditLogUseCase(self.repo, self.opener, self.clock)
        session = AdminSession.create(ttl_minutes=15, current_time=self.clock.now_utc())

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
            csv_path = tf.name

        export_res = export_use_case.execute(session, csv_path)
        self.assertTrue(export_res.is_ok())

        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("timestamp_utc,machine_id,hostname,event_type", content)
            self.assertIn("student1@insestatut.cat", content)
            self.assertIn("Downloads;RecycleBin", content)


if __name__ == "__main__":
    unittest.main()
