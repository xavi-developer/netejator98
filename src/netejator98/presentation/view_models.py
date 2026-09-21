"""View-Models for Kiosk and Administration presentation components."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from netejator98.presentation.i18n import t
from netejator98.presentation.ipc_client import IPCClient


class KioskViewModel:
    """Manages state and operations for the full-screen kiosk login prompt."""

    def __init__(self, ipc_client: IPCClient) -> None:
        self.client = ipc_client
        self.is_loading = False
        self.is_unlocked = False
        self.status_message = ""
        self.error_message = ""
        self.daemon_enabled = False
        self.on_state_changed: Optional[Callable[[], None]] = None
        self.check_daemon_status()

    def _notify(self) -> None:
        if self.on_state_changed:
            self.on_state_changed()

    def check_daemon_status(self) -> bool:
        """Check if daemon is reachable and whether protection is enabled."""
        res = self.client.get_status()
        if res.is_ok():
            self.daemon_enabled = res.unwrap().get("daemon_enabled", False)
        else:
            self.daemon_enabled = False
        self._notify()
        return self.daemon_enabled

    def bypass_with_admin_password(self, admin_password: str) -> bool:
        """Bypass the login prompt and unlock desktop without cleaning if admin password matches."""
        cleaned = admin_password.strip()
        if not cleaned:
            self.error_message = t("admin_password_required")
            self._notify()
            return False

        self.is_loading = True
        self.error_message = ""
        self._notify()

        res = self.client.admin_bypass(cleaned)
        self.is_loading = False

        if res.is_err():
            self.error_message = res.unwrap_err().message
            self.status_message = ""
            self._notify()
            return False

        self.is_unlocked = True
        self.status_message = t("bypass_success")
        self._notify()
        return True

    def submit_email(self, email_input: str) -> bool:
        cleaned = email_input.strip()
        if not cleaned or "@" not in cleaned:
            self.error_message = t("invalid_email")
            self._notify()
            return False

        self.is_loading = True
        self.error_message = ""
        self.status_message = t("sanitising_status")
        self._notify()

        res = self.client.identify_user(cleaned)

        self.is_loading = False
        if res.is_err():
            self.error_message = res.unwrap_err().message
            self.status_message = ""
            self._notify()
            return False

        data = res.unwrap()
        self.is_unlocked = True
        self.status_message = t("status_success")
        self._notify()
        return True


class AdminViewModel:
    """Manages state and operations for the system administration dashboard."""

    def __init__(self, ipc_client: IPCClient) -> None:
        self.client = ipc_client
        self.session_token: Optional[str] = None
        self.is_authenticated = False
        self.error_message = ""
        self.status_message = ""
        self.on_state_changed: Optional[Callable[[], None]] = None

    def _notify(self) -> None:
        if self.on_state_changed:
            self.on_state_changed()

    def is_first_run(self) -> bool:
        status_res = self.client.get_status()
        if status_res.is_ok():
            return not status_res.unwrap().get("has_admin_password", False)
        return False

    def authenticate(self, password: str) -> bool:
        self.error_message = ""
        if self.is_first_run():
            res = self.client.admin_setup_password(password)
        else:
            res = self.client.admin_auth(password)

        if res.is_err():
            self.error_message = res.unwrap_err().message
            self._notify()
            return False

        self.session_token = res.unwrap().get("session_token")
        self.is_authenticated = True
        self._notify()
        return True

    def logout(self) -> None:
        self.session_token = None
        self.is_authenticated = False
        self._notify()

    def fetch_logs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self.session_token:
            return []
        res = self.client.admin_get_logs(self.session_token, limit=limit)
        return res.unwrap() if res.is_ok() else []

    def export_logs(self, path: str) -> bool:
        if not self.session_token:
            return False
        res = self.client.admin_export_logs(self.session_token, path)
        return res.is_ok()

    def verify_chain(self) -> Dict[str, Any]:
        res = self.client.admin_verify_chain()
        return res.unwrap() if res.is_ok() else {"is_valid": False, "total_entries": 0}

    def fetch_policy(self) -> Dict[str, Any]:
        if not self.session_token:
            return {}
        res = self.client.admin_get_policy(self.session_token)
        return res.unwrap() if res.is_ok() else {}

    def save_policy(self, policy_data: Dict[str, Any]) -> bool:
        if not self.session_token:
            return False
        res = self.client.admin_update_policy(self.session_token, policy_data)
        return res.is_ok()

    def reset_policy(self) -> Dict[str, Any]:
        if not self.session_token:
            return {}
        res = self.client.admin_reset_policy(self.session_token)
        return res.unwrap() if res.is_ok() else {}

    def force_clean(self) -> Optional[Dict[str, Any]]:
        if not self.session_token:
            return None
        res = self.client.admin_force_clean(self.session_token)
        return res.unwrap() if res.is_ok() else None

    def change_password(self, old_pass: str, new_pass: str) -> bool:
        if not self.session_token:
            return False
        res = self.client.admin_change_password(self.session_token, old_pass, new_pass)
        return res.is_ok()

    def get_daemon_enabled(self) -> bool:
        status_res = self.client.get_status()
        if status_res.is_ok():
            return status_res.unwrap().get("daemon_enabled", False)
        return False

    def set_daemon_enabled(self, enabled: bool) -> bool:
        if not self.session_token:
            self.error_message = "No authenticated session"
            self._notify()
            return False
        res = self.client.set_daemon_state(self.session_token, enabled)
        if res.is_err():
            self.error_message = res.unwrap_err().message
            self._notify()
            return False
        self.status_message = t("status_success")
        self._notify()
        return True

