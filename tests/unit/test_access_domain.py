"""Comprehensive unit tests for the Access bounded context."""

from datetime import datetime, timedelta, timezone
import tempfile
import unittest

from netejator98.access.application.authenticate_admin import AuthenticateAdminUseCase
from netejator98.access.application.change_admin_password import ChangeAdminPasswordUseCase
from netejator98.access.application.start_session import StartSessionUseCase
from netejator98.access.domain.admin import AdminCredential, AdminSession
from netejator98.access.domain.detector import (
    UserChangeDetector,
    UserChangeType,
)
from netejator98.access.domain.email import InstitutionalEmail
from netejator98.access.domain.events import (
    AdminAuthenticated,
    AdminAuthenticationFailed,
    DifferentUserDetected,
    SameUserDetected,
    UserIdentified,
)
from netejator98.access.domain.policy import DomainPolicy
from netejator98.access.domain.user import LastUserRecord
from netejator98.access.infrastructure.last_user_repo import FileLastUserRepository
from netejator98.access.infrastructure.password_hasher import Argon2PasswordHasher
from netejator98.shared.clock import FrozenClock
from netejator98.shared.event_bus import EventBus
from tests.fakes.fake_access_repos import (
    FakeAdminCredentialRepository,
    FakeLastUserRepository,
    FakePasswordHasher,
)


class TestInstitutionalEmail(unittest.TestCase):
    def test_valid_institutional_email(self) -> None:
        email = InstitutionalEmail("  Student.One@INSESTATUT.CAT  ")
        self.assertEqual(email.value, "student.one@insestatut.cat")
        self.assertEqual(email.local_part, "student.one")
        self.assertEqual(email.domain, "insestatut.cat")

    def test_rejects_disallowed_domain(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            InstitutionalEmail("student@gmail.com")
        self.assertIn("does not match institutional domain", str(ctx.exception))

    def test_rejects_malformed_email(self) -> None:
        for bad in ["", "notanemail", "user@", "@insestatut.cat", "user @insestatut.cat"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    InstitutionalEmail(bad)

    def test_custom_domain_policy(self) -> None:
        custom_policy = DomainPolicy("custom-school.cat")
        email = InstitutionalEmail("teacher@custom-school.cat", policy=custom_policy)
        self.assertEqual(email.domain, "custom-school.cat")

        with self.assertRaises(ValueError):
            InstitutionalEmail("student@insestatut.cat", policy=custom_policy)


class TestUserChangeDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = UserChangeDetector()
        self.email1 = InstitutionalEmail("student1@insestatut.cat")
        self.email2 = InstitutionalEmail("student2@insestatut.cat")

    def test_no_previous_user(self) -> None:
        decision = self.detector.evaluate(self.email1, last_record=None)
        self.assertEqual(decision.decision, UserChangeType.NO_PREVIOUS_USER)
        self.assertIsNone(decision.previous_hash)
        self.assertTrue(decision.requires_sanitisation_by_identity)
        self.assertTrue(len(decision.new_hash) > 0)

    def test_same_user_detected(self) -> None:
        salt = "testsalt"
        h = self.detector.compute_hash(self.email1, salt)
        last_rec = LastUserRecord(
            email_hash=h,
            salt=salt,
            recorded_at=datetime.now(timezone.utc),
        )

        decision = self.detector.evaluate(self.email1, last_record=last_rec)
        self.assertEqual(decision.decision, UserChangeType.SAME_USER)
        self.assertEqual(decision.previous_hash, h)
        self.assertEqual(decision.new_hash, h)
        self.assertFalse(decision.requires_sanitisation_by_identity)

    def test_different_user_detected(self) -> None:
        salt = "testsalt"
        h1 = self.detector.compute_hash(self.email1, salt)
        last_rec = LastUserRecord(
            email_hash=h1,
            salt=salt,
            recorded_at=datetime.now(timezone.utc),
        )

        decision = self.detector.evaluate(self.email2, last_record=last_rec)
        self.assertEqual(decision.decision, UserChangeType.DIFFERENT_USER)
        self.assertEqual(decision.previous_hash, h1)
        self.assertNotEqual(decision.new_hash, h1)
        self.assertTrue(decision.requires_sanitisation_by_identity)


class TestStartSessionUseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FakeLastUserRepository()
        self.bus = EventBus()
        self.clock = FrozenClock(datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc))
        self.use_case = StartSessionUseCase(
            last_user_repo=self.repo,
            event_bus=self.bus,
            clock=self.clock,
        )

    def test_first_run_requires_sanitisation(self) -> None:
        res = self.use_case.execute("student1@insestatut.cat")
        self.assertTrue(res.is_ok())
        outcome = res.unwrap()
        self.assertTrue(outcome.requires_sanitisation)
        self.assertEqual(outcome.decision.decision, UserChangeType.NO_PREVIOUS_USER)
        # Not yet committed to repo before sanitisation completes
        self.assertIsNone(self.repo.get_last_user())

        # Now commit after sanitisation
        commit_res = self.use_case.commit_sanitised_user(outcome.user, outcome.decision)
        self.assertTrue(commit_res.is_ok())
        self.assertIsNotNone(self.repo.get_last_user())
        self.assertEqual(self.repo.get_last_user().email_hash, outcome.decision.new_hash)

    def test_same_user_skips_sanitisation(self) -> None:
        # First session
        first_res = self.use_case.execute("student1@insestatut.cat").unwrap()
        self.use_case.commit_sanitised_user(first_res.user, first_res.decision)

        # Same student logs in again
        self.clock.advance_seconds(600)
        second_res = self.use_case.execute("student1@insestatut.cat").unwrap()
        self.assertFalse(second_res.requires_sanitisation)
        self.assertEqual(second_res.decision.decision, UserChangeType.SAME_USER)

    def test_always_clean_forces_sanitisation_for_same_user(self) -> None:
        # First session
        first_res = self.use_case.execute("student1@insestatut.cat").unwrap()
        self.use_case.commit_sanitised_user(first_res.user, first_res.decision)

        # Same student logs in with always_clean_on_boot=True
        second_res = self.use_case.execute(
            "student1@insestatut.cat", always_clean_on_boot=True
        ).unwrap()
        self.assertTrue(second_res.requires_sanitisation)
        self.assertEqual(second_res.decision.decision, UserChangeType.SAME_USER)

    def test_invalid_email_returns_error(self) -> None:
        res = self.use_case.execute("notanemail")
        self.assertTrue(res.is_err())
        self.assertEqual(res.unwrap_err().code, "INVALID_EMAIL")


class TestAuthenticateAdminUseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FakeAdminCredentialRepository()
        self.hasher = FakePasswordHasher()
        self.bus = EventBus()
        self.clock = FrozenClock()
        self.auth = AuthenticateAdminUseCase(
            credential_repo=self.repo,
            hasher=self.hasher,
            event_bus=self.bus,
            clock=self.clock,
            max_free_attempts=3,
            base_backoff_seconds=2.0,
        )

    def test_initial_password_setup(self) -> None:
        # No password set initially
        res = self.auth.execute(AdminCredential("my_pass"))
        self.assertTrue(res.is_err())
        self.assertIn("not been initialized", res.unwrap_err().message)

        # Setup initial password (fails if too short)
        weak_res = self.auth.initialize_first_password(AdminCredential("short"))
        self.assertTrue(weak_res.is_err())

        # Setup initial password with >= 8 chars
        setup_res = self.auth.initialize_first_password(AdminCredential("strong_admin_pass"))
        self.assertTrue(setup_res.is_ok())
        session = setup_res.unwrap()
        self.assertTrue(session.is_valid())

    def test_successful_authentication(self) -> None:
        self.auth.initialize_first_password(AdminCredential("correct_password"))

        res = self.auth.execute(AdminCredential("correct_password"))
        self.assertTrue(res.is_ok())
        session = res.unwrap()
        self.assertTrue(session.is_valid())

        events = [e for e in self.bus.recorded_events if isinstance(e, AdminAuthenticated)]
        self.assertTrue(len(events) > 0)

    def test_failed_authentication_and_rate_limiting(self) -> None:
        self.auth.initialize_first_password(AdminCredential("correct_password"))

        # 3 failures allowed before lockout
        for _ in range(3):
            bad_res = self.auth.execute(AdminCredential("wrong_password"))
            self.assertTrue(bad_res.is_err())
            self.assertEqual(bad_res.unwrap_err().code, "ADMIN_AUTH_FAILED")

        # 4th failure is rate limited
        locked_res = self.auth.execute(AdminCredential("wrong_password"))
        self.assertTrue(locked_res.is_err())
        self.assertEqual(locked_res.unwrap_err().code, "RATE_LIMIT_EXCEEDED")

        # Advance clock past backoff
        self.clock.advance_seconds(10.0)
        retry_res = self.auth.execute(AdminCredential("correct_password"))
        self.assertTrue(retry_res.is_ok())


class TestChangeAdminPasswordUseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FakeAdminCredentialRepository()
        self.hasher = FakePasswordHasher()
        self.bus = EventBus()
        self.clock = FrozenClock()
        self.auth = AuthenticateAdminUseCase(
            self.repo, self.hasher, self.bus, self.clock
        )
        self.change = ChangeAdminPasswordUseCase(
            self.repo, self.hasher, self.bus, self.clock
        )
        self.session = self.auth.initialize_first_password(
            AdminCredential("initial_password_123")
        ).unwrap()

    def test_change_password_success(self) -> None:
        res = self.change.execute(self.session, AdminCredential("new_strong_pass_456"))
        self.assertTrue(res.is_ok())

        # Verify old password fails and new password succeeds
        self.assertFalse(self.hasher.verify_password("initial_password_123", self.repo.get_verifier()))
        self.assertTrue(self.hasher.verify_password("new_strong_pass_456", self.repo.get_verifier()))

    def test_expired_session_fails(self) -> None:
        expired_session = AdminSession(
            session_id="expired",
            authenticated_at=self.clock.now_utc() - timedelta(minutes=30),
            expires_at=self.clock.now_utc() - timedelta(minutes=1),
        )
        res = self.change.execute(expired_session, AdminCredential("new_strong_pass_456"))
        self.assertTrue(res.is_err())
        self.assertIn("expired", res.unwrap_err().message)


class TestArgon2Infrastructure(unittest.TestCase):
    def test_argon2_password_hasher_real(self) -> None:
        hasher = Argon2PasswordHasher()
        verifier, salt = hasher.hash_password("SuperSecretSchoolPass2026!")
        self.assertTrue(verifier.startswith("$argon2id$"))
        self.assertTrue(hasher.verify_password("SuperSecretSchoolPass2026!", verifier))
        self.assertFalse(hasher.verify_password("WrongPassword!", verifier))

    def test_file_last_user_repo_real(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileLastUserRepository(tmpdir)
            self.assertIsNone(repo.get_last_user())

            dt = datetime(2026, 9, 16, 11, 0, 0, tzinfo=timezone.utc)
            rec = LastUserRecord(email_hash="aabbcc112233", salt="salt123", recorded_at=dt)
            save_res = repo.save_last_user(rec)
            self.assertTrue(save_res.is_ok())

            loaded = repo.get_last_user()
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.email_hash, "aabbcc112233")
            self.assertEqual(loaded.salt, "salt123")


if __name__ == "__main__":
    unittest.main()

