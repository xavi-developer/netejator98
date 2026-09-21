"""Privileged agent daemon orchestrating access, audit, and sanitisation services."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
from typing import Any, Dict, Optional, Tuple
import yaml

from netejator98.access.application.authenticate_admin import AuthenticateAdminUseCase
from netejator98.access.application.change_admin_password import ChangeAdminPasswordUseCase
from netejator98.access.application.start_session import (
    SessionStartResult,
    StartSessionUseCase,
)
from netejator98.access.domain.admin import AdminCredential, AdminSession
from netejator98.access.domain.detector import UserChangeType
from netejator98.access.domain.policy import DomainPolicy
from netejator98.access.infrastructure.admin_repo import FileAdminCredentialRepository
from netejator98.access.infrastructure.last_user_repo import FileLastUserRepository
from netejator98.access.infrastructure.password_hasher import Argon2PasswordHasher
from netejator98.agent.protocol import IPCCommands, IPCRequest, IPCResponse
from netejator98.audit.application.export_log import ExportAuditLogUseCase
from netejator98.audit.application.query_log import QueryAuditLogUseCase
from netejator98.audit.application.record_login import RecordLoginUseCase
from netejator98.audit.application.record_sanitisation import (
    RecordSanitisationUseCase,
)
from netejator98.audit.application.verify_chain import (
    VerifyChainIntegrityUseCase,
)
from netejator98.audit.infrastructure.key_wrap_adapter import Argon2KeyWrapAdapter
from netejator98.audit.infrastructure.sealed_repo import (
    EncryptedJsonlAuditRepository,
)
from netejator98.audit.infrastructure.x25519_adapter import X25519SealAdapter
from netejator98.sanitisation.application.dry_run import DryRunUseCase
from netejator98.sanitisation.application.execute import (
    ExecuteSanitisationUseCase,
)
from netejator98.sanitisation.application.restore_shortcuts import (
    RestoreGoldenShortcutsUseCase,
)
from netejator98.sanitisation.domain.policy import CleaningPolicy
from netejator98.sanitisation.infrastructure.credential_adapter import (
    RealCredentialStorePort,
)
from netejator98.sanitisation.infrastructure.linux_paths import LinuxPathsAdapter
from netejator98.sanitisation.infrastructure.macos_paths import MacPathsAdapter
from netejator98.sanitisation.infrastructure.process_adapter import RealProcessPort
from netejator98.sanitisation.infrastructure.real_filesystem import RealFileSystem
from netejator98.sanitisation.infrastructure.windows_paths import (
    WindowsPathsAdapter,
)
from netejator98.shared.clock import ClockPort, SystemClock
from netejator98.shared.event_bus import EventBus
from netejator98.shared.machine_id import MachineId


class AgentDaemon:
    """The central privileged daemon service handling IPC requests and security invariants."""

    def __init__(
        self,
        storage_dir: str | Path,
        clock: Optional[ClockPort] = None,
        machine_id: Optional[MachineId] = None,
    ) -> None:
        self.storage_dir = Path(storage_dir).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.clock = clock or SystemClock()
        self.machine_id = machine_id or MachineId.current()
        self.event_bus = EventBus()

        # Filesystem and paths
        self.fs = RealFileSystem()
        self.system_name = platform.system().lower()

        # Storage paths
        self.pubkey_path = self.storage_dir / "log_public.key"
        self.privkey_enc_path = self.storage_dir / "log_private.enc"
        self.config_path = self.storage_dir / "config.yaml"

        # Initialize adapters
        self.last_user_repo = FileLastUserRepository(self.storage_dir)
        self.admin_repo = FileAdminCredentialRepository(self.storage_dir)
        self.hasher = Argon2PasswordHasher()
        self.key_wrapper = Argon2KeyWrapAdapter()
        self.audit_repo = EncryptedJsonlAuditRepository(self.storage_dir)

        # Sealer adapter (lazy loaded when public key exists)
        self._sealer: Optional[X25519SealAdapter] = None
        self._load_or_create_keys_if_initialized()

        # Audit use cases
        self.verify_chain_use_case = VerifyChainIntegrityUseCase(self.audit_repo)

        # Active admin sessions: token -> (AdminSession, unwrapped_private_key_bytes)
        self._active_admin_sessions: Dict[str, Tuple[AdminSession, bytes]] = {}

        # Load policy
        self.policy = self._load_policy()

        # Daemon protection state (disabled by default)
        self.daemon_state_file = self.storage_dir / "daemon_state.json"
        self.daemon_enabled: bool = self._load_daemon_state()

    def _load_daemon_state(self) -> bool:
        if self.daemon_state_file.exists():
            try:
                with open(self.daemon_state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return bool(data.get("enabled", False))
            except Exception:
                pass
        return False

    def _get_platform_paths(self, target_user_home: Optional[str] = None):
        if self.system_name == "windows":
            return WindowsPathsAdapter(target_user_home)
        elif self.system_name == "darwin":
            return MacPathsAdapter(target_user_home)
        else:
            return LinuxPathsAdapter(target_user_home)

    def _load_or_create_keys_if_initialized(self) -> None:
        if self.pubkey_path.exists():
            pub_bytes = self.pubkey_path.read_bytes()
            self._sealer = X25519SealAdapter.from_public_key_bytes(pub_bytes)

    def _create_default_policy(self) -> CleaningPolicy:
        # Try loading from policies/defaults/<system>.yaml
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        policy_file = repo_root / "policies" / "defaults" / f"{self.system_name}.yaml"
        if policy_file.exists():
            try:
                with open(policy_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return CleaningPolicy.from_dict(data)
            except Exception:
                pass

        # Fallback default targets covering all platforms
        from netejator98.sanitisation.domain.path_pattern import PathPattern
        from netejator98.sanitisation.domain.target import CleaningTarget, TargetCategory

        targets = [
            CleaningTarget(
                name="UserDocuments",
                os="Linux",
                category=TargetCategory.USER_DOCUMENTS,
                enabled=False,
                patterns=(
                    PathPattern("Desktop/*"),
                    PathPattern("Documents/*"),
                    PathPattern("Downloads/*"),
                    PathPattern("Pictures/*"),
                    PathPattern("Videos/*"),
                    PathPattern("Music/*"),
                ),
            ),
            CleaningTarget(
                name="CachesAndTemp",
                os="Linux",
                category=TargetCategory.TEMP_AND_CACHE,
                enabled=False,
                patterns=(
                    PathPattern(".cache/*"),
                    PathPattern(".thumbnails/*"),
                ),
            ),
            CleaningTarget(
                name="UserDocuments",
                os="Windows",
                category=TargetCategory.USER_DOCUMENTS,
                enabled=False,
                patterns=(
                    PathPattern("Desktop/*"),
                    PathPattern("Documents/*"),
                    PathPattern("Downloads/*"),
                    PathPattern("Pictures/*"),
                    PathPattern("Videos/*"),
                    PathPattern("Music/*"),
                ),
            ),
            CleaningTarget(
                name="CachesAndTemp",
                os="Windows",
                category=TargetCategory.TEMP_AND_CACHE,
                enabled=False,
                patterns=(
                    PathPattern("AppData/Local/Temp/*"),
                    PathPattern("AppData/Local/CrashDumps/*"),
                ),
            ),
            CleaningTarget(
                name="UserDocuments",
                os="macOS",
                category=TargetCategory.USER_DOCUMENTS,
                enabled=False,
                patterns=(
                    PathPattern("Desktop/*"),
                    PathPattern("Documents/*"),
                    PathPattern("Downloads/*"),
                    PathPattern("Pictures/*"),
                    PathPattern("Movies/*"),
                    PathPattern("Music/*"),
                ),
            ),
            CleaningTarget(
                name="CachesAndTemp",
                os="macOS",
                category=TargetCategory.TEMP_AND_CACHE,
                enabled=False,
                patterns=(
                    PathPattern("Library/Caches/*"),
                ),
            ),
        ]
        return CleaningPolicy(targets=targets, dry_run=True)

    def _load_policy(self) -> CleaningPolicy:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    targets = data.get("targets", [])
                    # Detect legacy configuration without explicit OS or with old partial targets
                    is_legacy = bool(targets) and (
                        all("os" not in t for t in targets)
                        or all(t.get("os") in ("ALL", None) for t in targets)
                        or len(targets) < 25
                    )
                    if not is_legacy:
                        return CleaningPolicy.from_dict(data)
            except Exception:
                pass
        policy = self._create_default_policy()
        try:
            self._save_policy(policy)
        except Exception:
            pass
        return policy

    def _save_policy(self, policy: CleaningPolicy) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(policy.to_dict(), f)
        self.policy = policy

    def _get_record_login(self) -> Optional[RecordLoginUseCase]:
        if self._sealer is None:
            return None
        return RecordLoginUseCase(
            repository=self.audit_repo,
            sealer=self._sealer,
            machine_id=self.machine_id,
            clock=self.clock,
        )

    def _get_record_sanitisation(self) -> Optional[RecordSanitisationUseCase]:
        if self._sealer is None:
            return None
        return RecordSanitisationUseCase(
            repository=self.audit_repo,
            sealer=self._sealer,
            machine_id=self.machine_id,
            clock=self.clock,
        )

    # --------------------------------------------------------------------------
    # Request Dispatcher
    # --------------------------------------------------------------------------

    def dispatch(self, request: IPCRequest) -> IPCResponse:
        cmd = request.command
        payload = request.payload

        if cmd == IPCCommands.GET_STATUS:
            return self.handle_get_status()
        elif cmd == IPCCommands.ADMIN_SETUP_PASSWORD:
            return self.handle_admin_setup_password(payload.get("new_password", ""))
        elif cmd == IPCCommands.ADMIN_AUTH:
            return self.handle_admin_auth(payload.get("password", ""))
        elif cmd == IPCCommands.IDENTIFY_USER:
            return self.handle_identify_user(
                payload.get("email", ""),
                payload.get("target_user_home"),
            )
        elif cmd == IPCCommands.ADMIN_VERIFY_CHAIN:
            return self.handle_admin_verify_chain()
        elif cmd == IPCCommands.ADMIN_GET_LOGS:
            return self.handle_admin_get_logs(
                request.session_token or payload.get("session_token", ""),
                payload.get("limit"),
            )
        elif cmd == IPCCommands.ADMIN_EXPORT_LOGS:
            return self.handle_admin_export_logs(
                request.session_token or payload.get("session_token", ""),
                payload.get("export_path", ""),
            )
        elif cmd == IPCCommands.ADMIN_FORCE_CLEAN:
            return self.handle_admin_force_clean(
                request.session_token or payload.get("session_token", ""),
                payload.get("target_user_home"),
            )
        elif cmd == IPCCommands.ADMIN_GET_POLICY:
            return self.handle_admin_get_policy(
                request.session_token or payload.get("session_token", "")
            )
        elif cmd == IPCCommands.ADMIN_UPDATE_POLICY:
            return self.handle_admin_update_policy(
                request.session_token or payload.get("session_token", ""),
                payload.get("policy", {}),
            )
        elif cmd == IPCCommands.ADMIN_RESET_POLICY:
            return self.handle_admin_reset_policy(
                request.session_token or payload.get("session_token", "")
            )
        elif cmd == IPCCommands.ADMIN_CHANGE_PASSWORD:
            return self.handle_admin_change_password(
                request.session_token or payload.get("session_token", ""),
                payload.get("old_password", ""),
                payload.get("new_password", ""),
            )
        elif cmd == IPCCommands.ADMIN_BYPASS:
            return self.handle_admin_bypass(payload.get("password", ""))
        elif cmd == IPCCommands.SET_DAEMON_STATE:
            return self.handle_set_daemon_state(
                request.session_token or payload.get("session_token", ""),
                payload.get("enabled", False),
            )
        else:
            return IPCResponse.error("UNKNOWN_COMMAND", f"Unrecognized IPC command: {cmd}")

    # --------------------------------------------------------------------------
    # Command Handlers
    # --------------------------------------------------------------------------

    def handle_get_status(self) -> IPCResponse:
        last_rec = self.last_user_repo.get_last_user()
        return IPCResponse.ok(
            {
                "version": "0.1.0",
                "machine_id": str(self.machine_id),
                "platform": self.system_name,
                "has_admin_password": self.admin_repo.has_password(),
                "last_user_timestamp": last_rec.recorded_at.isoformat() if last_rec else None,
                "audit_entries_count": self.audit_repo.count(),
                "always_clean_on_boot": self.policy.always_clean_on_boot,
                "daemon_enabled": self.daemon_enabled,
                "dry_run": self.policy.dry_run,
            }
        )

    def handle_admin_bypass(self, password: str) -> IPCResponse:
        if not self.admin_repo.has_password():
            return IPCResponse.error("NO_ADMIN_PASSWORD", "Admin password has not been configured yet")

        auth_use_case = AuthenticateAdminUseCase(
            credential_repo=self.admin_repo,
            hasher=self.hasher,
            event_bus=self.event_bus,
            clock=self.clock,
        )
        auth_res = auth_use_case.execute(AdminCredential(password))
        if auth_res.is_err():
            err = auth_res.unwrap_err()
            rec_login = self._get_record_login()
            if rec_login:
                rec_login.execute(None, "ADMIN_BYPASS_FAILED", "REJECTED", errors=[err.message])
            return IPCResponse.error(err.code, err.message)

        rec_login = self._get_record_login()
        if rec_login:
            rec_login.execute(None, "ADMIN_BYPASS_SUCCESS", "SUCCESS")

        return IPCResponse.ok(
            {
                "unlocked": True,
                "bypassed": True,
                "sanitised": False,
            }
        )

    def handle_set_daemon_state(self, token: str, enabled: bool) -> IPCResponse:
        session_info = self._validate_session(token)
        if not session_info:
            return IPCResponse.error("UNAUTHORIZED", "Valid administrator session required")

        self.daemon_enabled = bool(enabled)
        try:
            with open(self.daemon_state_file, "w", encoding="utf-8") as f:
                json.dump({"enabled": self.daemon_enabled}, f)
        except Exception:
            pass

        rec_login = self._get_record_login()
        if rec_login:
            rec_login.execute(
                None,
                "DAEMON_ENABLED" if self.daemon_enabled else "DAEMON_DISABLED",
                "SUCCESS",
            )

        return IPCResponse.ok({"daemon_enabled": self.daemon_enabled})

    def handle_admin_setup_password(self, new_password: str) -> IPCResponse:
        if self.admin_repo.has_password():
            return IPCResponse.error("ALREADY_INITIALIZED", "Admin password is already set")

        try:
            cred = AdminCredential(new_password)
            cred.validate_strength(min_length=8)
        except ValueError as e:
            return IPCResponse.error("INVALID_PASSWORD", str(e))

        # 1. Generate X25519 keypair
        pub_bytes, priv_bytes = X25519SealAdapter.generate_keypair()

        # 2. Wrap private key with password
        wrap_res = self.key_wrapper.wrap_key(priv_bytes, new_password)
        if wrap_res.is_err():
            return IPCResponse.error("CRYPTO_ERROR", wrap_res.unwrap_err().message)

        # 3. Save public key in clear and wrapped private key
        self.pubkey_path.write_bytes(pub_bytes)
        self.privkey_enc_path.write_bytes(wrap_res.unwrap())
        self._sealer = X25519SealAdapter.from_public_key_bytes(pub_bytes)

        # 4. Save Argon2id verifier
        verifier, salt = self.hasher.hash_password(new_password)
        save_res = self.admin_repo.save_verifier(verifier, salt)
        if save_res.is_err():
            return IPCResponse.error("STORAGE_ERROR", save_res.unwrap_err().message)

        # 5. Create admin session
        session = AdminSession.create(ttl_minutes=15, current_time=self.clock.now_utc())
        self._active_admin_sessions[session.session_id] = (session, priv_bytes)

        # Record setup in audit log
        rec_login = self._get_record_login()
        if rec_login:
            rec_login.execute(None, "ADMIN_PASSWORD_INITIALIZED", "SUCCESS")

        return IPCResponse.ok(
            {
                "session_token": session.session_id,
                "expires_at": session.expires_at.isoformat(),
            }
        )

    def handle_admin_auth(self, password: str) -> IPCResponse:
        auth_use_case = AuthenticateAdminUseCase(
            credential_repo=self.admin_repo,
            hasher=self.hasher,
            event_bus=self.event_bus,
            clock=self.clock,
        )
        auth_res = auth_use_case.execute(AdminCredential(password))
        if auth_res.is_err():
            err = auth_res.unwrap_err()
            rec_login = self._get_record_login()
            if rec_login:
                rec_login.execute(None, "ADMIN_AUTH_FAILED", "REJECTED", errors=[err.message])
            return IPCResponse.error(err.code, err.message)

        session = auth_res.unwrap()

        # Unwrap private key in memory
        if not self.privkey_enc_path.exists():
            return IPCResponse.error("KEY_MISSING", "Encrypted private key file is missing")

        wrapped_blob = self.privkey_enc_path.read_bytes()
        unwrap_res = self.key_wrapper.unwrap_key(wrapped_blob, password)
        if unwrap_res.is_err():
            return IPCResponse.error("KEY_UNWRAP_FAILED", "Failed to unwrap private key")

        priv_bytes = unwrap_res.unwrap()
        self._active_admin_sessions[session.session_id] = (session, priv_bytes)

        rec_login = self._get_record_login()
        if rec_login:
            rec_login.execute(None, "ADMIN_AUTH_SUCCESS", "SUCCESS")

        return IPCResponse.ok(
            {
                "session_token": session.session_id,
                "expires_at": session.expires_at.isoformat(),
            }
        )

    def _validate_session(self, token: str) -> Optional[Tuple[AdminSession, bytes]]:
        info = self._active_admin_sessions.get(token)
        if not info:
            return None
        session, priv_bytes = info
        if not session.is_valid(self.clock.now_utc()):
            del self._active_admin_sessions[token]
            return None
        return info

    def handle_identify_user(
        self, raw_email: str, target_user_home: Optional[str] = None
    ) -> IPCResponse:
        domain_policy = DomainPolicy("insestatut.cat")
        start_use_case = StartSessionUseCase(
            last_user_repo=self.last_user_repo,
            event_bus=self.event_bus,
            clock=self.clock,
        )

        res = start_use_case.execute(
            raw_email=raw_email,
            policy=domain_policy,
            always_clean_on_boot=self.policy.always_clean_on_boot,
        )

        rec_login = self._get_record_login()
        rec_san = self._get_record_sanitisation()

        if res.is_err():
            err = res.unwrap_err()
            if rec_login:
                rec_login.execute(raw_email, "LOGIN_REJECTED", "REJECTED", errors=[err.message])
            return IPCResponse.error(err.code, err.message)

        session_start = res.unwrap()
        user = session_start.user
        decision = session_start.decision

        if not self.daemon_enabled:
            # Protection is disabled: record user and allow logon without any sanitisation
            start_use_case.commit_sanitised_user(user, decision)
            if rec_login:
                rec_login.execute(user.email.value, "LOGIN_DAEMON_DISABLED", "SUCCESS")
            return IPCResponse.ok(
                {
                    "user": user.email.value,
                    "sanitised": False,
                    "daemon_enabled": False,
                    "unlocked": True,
                    "outcome": {
                        "files_deleted": 0,
                        "bytes_freed": 0,
                        "targets": [],
                        "errors": [],
                    },
                }
            )

        if session_start.requires_sanitisation:
            # Execute sanitisation BEFORE handing over desktop (or DryRun if configured)
            paths_port = self._get_platform_paths(target_user_home)
            proc_port = RealProcessPort()
            cred_port = RealCredentialStorePort()

            if self.policy.dry_run:
                from netejator98.sanitisation.application.dry_run import DryRunUseCase
                dry_runner = DryRunUseCase(fs=self.fs, paths=paths_port, clock=self.clock)
                outcome = dry_runner.execute(self.policy, user_email=user.email.value)
            else:
                executor = ExecuteSanitisationUseCase(
                    fs=self.fs,
                    paths=paths_port,
                    event_bus=self.event_bus,
                    process_port=proc_port,
                    credential_port=cred_port,
                    clock=self.clock,
                )
                outcome = executor.execute(self.policy, user_email=user.email.value)

                # Restore Golden Profile shortcuts if configured
                if not self.policy.dry_run and self.policy.golden_profile_shortcuts:
                    shortcuts_restorer = RestoreGoldenShortcutsUseCase(
                        fs=self.fs,
                        paths=paths_port,
                        platform_name=self.system_name,
                    )
                    shortcuts_restorer.execute(self.policy.golden_profile_shortcuts)

            # Record sanitisation outcome in audit trail
            if rec_san:
                rec_san.execute(
                    event_type="SANITISATION_COMPLETED" if outcome.is_success else "SANITISATION_FAILED",
                    email=user.email.value,
                    outcome="SUCCESS" if outcome.is_success else "FAILED",
                    targets_cleaned=list(outcome.targets_processed),
                    errors=list(outcome.errors),
                )

            # Commit new user record to LastUserRepository
            start_use_case.commit_sanitised_user(user, decision)

            # Record login event
            if rec_login:
                rec_login.execute(user.email.value, "LOGIN_AFTER_SANITISATION", "SUCCESS")

            return IPCResponse.ok(
                {
                    "user": user.email.value,
                    "sanitised": True,
                    "outcome": {
                        "files_deleted": outcome.files_deleted,
                        "bytes_freed": outcome.bytes_freed,
                        "targets": list(outcome.targets_processed),
                        "errors": list(outcome.errors),
                    },
                }
            )
        else:
            # Same user, skipped sanitisation
            if rec_login:
                rec_login.execute(user.email.value, "LOGIN_SAME_USER", "SUCCESS")

            return IPCResponse.ok(
                {
                    "user": user.email.value,
                    "sanitised": False,
                }
            )

    def handle_admin_verify_chain(self) -> IPCResponse:
        """Unauthenticated verification of ciphertext hash chain."""
        verification = self.verify_chain_use_case.execute()
        return IPCResponse.ok(
            {
                "is_valid": verification.is_valid,
                "total_entries": verification.total_entries,
                "tampered_seq": verification.tampered_seq,
                "failure_reason": verification.failure_reason,
            }
        )

    def handle_admin_get_logs(self, token: str, limit: Optional[int] = None) -> IPCResponse:
        session_info = self._validate_session(token)
        if not session_info:
            return IPCResponse.error("UNAUTHORIZED", "Valid administrator session required")

        session, priv_bytes = session_info
        opener = X25519SealAdapter.from_private_key_bytes(priv_bytes)
        query_use_case = QueryAuditLogUseCase(self.audit_repo, opener, self.clock)

        q_res = query_use_case.execute(session, limit=limit)
        if q_res.is_err():
            return IPCResponse.error("DECRYPTION_ERROR", q_res.unwrap_err().message)

        entries = q_res.unwrap()
        serialized = [
            {
                "timestamp": e.timestamp.isoformat(),
                "machine_id": e.machine_id,
                "hostname": e.hostname,
                "event_type": e.event_type,
                "email": e.email,
                "outcome": e.outcome,
                "targets_cleaned": e.targets_cleaned,
                "errors": e.errors,
            }
            for e in entries
        ]
        return IPCResponse.ok({"entries": serialized})

    def handle_admin_export_logs(self, token: str, export_path: str) -> IPCResponse:
        session_info = self._validate_session(token)
        if not session_info:
            return IPCResponse.error("UNAUTHORIZED", "Valid administrator session required")

        if not export_path:
            return IPCResponse.error("INVALID_ARGUMENT", "Export path cannot be empty")

        session, priv_bytes = session_info
        opener = X25519SealAdapter.from_private_key_bytes(priv_bytes)
        export_use_case = ExportAuditLogUseCase(self.audit_repo, opener, self.clock)

        exp_res = export_use_case.execute(session, export_path)
        if exp_res.is_err():
            return IPCResponse.error("EXPORT_FAILED", exp_res.unwrap_err().message)

        return IPCResponse.ok({"export_path": str(export_path)})

    def handle_admin_force_clean(
        self, token: str, target_user_home: Optional[str] = None
    ) -> IPCResponse:
        session_info = self._validate_session(token)
        if not session_info:
            return IPCResponse.error("UNAUTHORIZED", "Valid administrator session required")

        paths_port = self._get_platform_paths(target_user_home)
        if self.policy.dry_run:
            from netejator98.sanitisation.application.dry_run import DryRunUseCase
            dry_runner = DryRunUseCase(fs=self.fs, paths=paths_port, clock=self.clock)
            outcome = dry_runner.execute(self.policy, user_email="admin_forced_dry_run")
        else:
            executor = ExecuteSanitisationUseCase(
                fs=self.fs,
                paths=paths_port,
                event_bus=self.event_bus,
                process_port=RealProcessPort(),
                credential_port=RealCredentialStorePort(),
                clock=self.clock,
            )
            outcome = executor.execute(self.policy, user_email="admin_forced")
            # Restore Golden Profile shortcuts if configured
            if not self.policy.dry_run and self.policy.golden_profile_shortcuts:
                shortcuts_restorer = RestoreGoldenShortcutsUseCase(
                    fs=self.fs,
                    paths=paths_port,
                    platform_name=self.system_name,
                )
                shortcuts_restorer.execute(self.policy.golden_profile_shortcuts)
        rec_san = self._get_record_sanitisation()
        if rec_san:
            rec_san.execute(
                event_type="ADMIN_FORCED_SANITISATION",
                email="admin",
                outcome="SUCCESS" if outcome.is_success else "FAILED",
                targets_cleaned=list(outcome.targets_processed),
                errors=list(outcome.errors),
            )

        return IPCResponse.ok(
            {
                "files_deleted": outcome.files_deleted,
                "bytes_freed": outcome.bytes_freed,
                "targets": list(outcome.targets_processed),
                "errors": list(outcome.errors),
                "log_file_path": outcome.log_file_path,
            }
        )

    def handle_admin_get_policy(self, token: str) -> IPCResponse:
        session_info = self._validate_session(token)
        if not session_info:
            return IPCResponse.error("UNAUTHORIZED", "Valid administrator session required")

        return IPCResponse.ok({"policy": self.policy.to_dict()})

    def handle_admin_update_policy(self, token: str, policy_data: Dict[str, Any]) -> IPCResponse:
        session_info = self._validate_session(token)
        if not session_info:
            return IPCResponse.error("UNAUTHORIZED", "Valid administrator session required")

        try:
            new_policy = CleaningPolicy.from_dict(policy_data)
            new_policy.validate()
        except Exception as e:
            return IPCResponse.error("INVALID_POLICY", str(e))

        self._save_policy(new_policy)
        return IPCResponse.ok({"policy": new_policy.to_dict()})

    def handle_admin_reset_policy(self, token: str) -> IPCResponse:
        session_info = self._validate_session(token)
        if not session_info:
            return IPCResponse.error("UNAUTHORIZED", "Valid administrator session required")

        default_policy = self._create_default_policy()
        self._save_policy(default_policy)
        return IPCResponse.ok({"policy": default_policy.to_dict()})

    def handle_admin_change_password(
        self, token: str, old_password: str, new_password: str
    ) -> IPCResponse:
        session_info = self._validate_session(token)
        if not session_info:
            return IPCResponse.error("UNAUTHORIZED", "Valid administrator session required")

        session, priv_bytes = session_info

        try:
            new_cred = AdminCredential(new_password)
            new_cred.validate_strength(min_length=8)
        except ValueError as e:
            return IPCResponse.error("INVALID_PASSWORD", str(e))

        # Re-wrap private key with new password
        wrap_res = self.key_wrapper.wrap_key(priv_bytes, new_password)
        if wrap_res.is_err():
            return IPCResponse.error("CRYPTO_ERROR", wrap_res.unwrap_err().message)

        new_wrapped = wrap_res.unwrap()

        # Atomic file write
        temp_file = self.storage_dir / "log_private.tmp"
        temp_file.write_bytes(new_wrapped)
        os.replace(temp_file, self.privkey_enc_path)

        # Update Argon2id verifier
        change_use_case = ChangeAdminPasswordUseCase(
            credential_repo=self.admin_repo,
            hasher=self.hasher,
            event_bus=self.event_bus,
            clock=self.clock,
        )
        change_res = change_use_case.execute(session, new_cred)
        if change_res.is_err():
            return IPCResponse.error("UPDATE_FAILED", change_res.unwrap_err().message)

        rec_login = self._get_record_login()
        if rec_login:
            rec_login.execute(None, "ADMIN_PASSWORD_CHANGED", "SUCCESS")

        return IPCResponse.ok({"message": "Password changed successfully"})
