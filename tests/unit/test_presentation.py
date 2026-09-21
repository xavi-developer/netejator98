"""Unit tests for presentation View-Models and i18n localization."""

import unittest
from unittest.mock import MagicMock

from netejator98.presentation.i18n import get_language, set_language, t
from netejator98.presentation.ipc_client import IPCClient
from netejator98.presentation.view_models import AdminViewModel, KioskViewModel
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Err, Ok


class TestPresentationI18n(unittest.TestCase):
    def setUp(self) -> None:
        set_language("ca")

    def test_default_is_catalan(self) -> None:
        self.assertEqual(get_language(), "ca")
        self.assertIn("Benvingut/da", t("kiosk_heading"))
        self.assertEqual(t("enter_button"), "Començar sessió")

    def test_switch_language_to_spanish(self) -> None:
        set_language("es")
        self.assertEqual(get_language(), "es")
        self.assertIn("Bienvenido/a", t("kiosk_heading"))
        self.assertEqual(t("enter_button"), "Iniciar sesión")

    def test_switch_language_to_english(self) -> None:
        set_language("en")
        self.assertEqual(get_language(), "en")
        self.assertIn("Welcome", t("kiosk_heading"))
        self.assertEqual(t("enter_button"), "Start session")

    def test_eines_per_defecte_nomenclature(self) -> None:
        set_language("ca")
        self.assertEqual(t("admin_tab_golden"), "Eines per defecte")
        self.assertIn("Eines per defecte", t("golden_heading"))
        self.assertEqual(t("policy_reset_golden"), "Restablir eines per defecte")

        set_language("es")
        self.assertEqual(t("admin_tab_golden"), "Herramientas por defecto")
        self.assertIn("Herramientas por defecto", t("golden_heading"))

        set_language("en")
        self.assertEqual(t("admin_tab_golden"), "Default Tools")
        self.assertIn("Default Tools", t("golden_heading"))

    def test_policy_os_applies_translations(self) -> None:
        set_language("ca")
        self.assertEqual(t("policy_os_applies"), "Aplica al sistema operatiu")
        self.assertEqual(t("policy_col_os"), "OS")
        self.assertEqual(t("policy_target_os"), "Sistema Operatiu (OS):")

        set_language("es")
        self.assertEqual(t("policy_os_applies"), "Aplica al sistema operativo")
        self.assertEqual(t("policy_col_os"), "OS")
        self.assertEqual(t("policy_target_os"), "Sistema Operativo (SO):")

        set_language("en")
        self.assertEqual(t("policy_os_applies"), "Applies to operating system")
        self.assertEqual(t("policy_col_os"), "OS")
        self.assertEqual(t("policy_target_os"), "Operating System (OS):")


class TestKioskViewModel(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_client = MagicMock(spec=IPCClient)
        self.vm = KioskViewModel(self.mock_client)

    def test_invalid_email_sets_error(self) -> None:
        success = self.vm.submit_email("notanemail")
        self.assertFalse(success)
        self.assertFalse(self.vm.is_unlocked)
        self.assertTrue(len(self.vm.error_message) > 0)
        self.mock_client.identify_user.assert_not_called()

    def test_successful_identification_unlocks(self) -> None:
        self.mock_client.identify_user.return_value = Ok(
            {"user": "student1@insestatut.cat", "sanitised": True}
        )
        notified = False

        def on_change() -> None:
            nonlocal notified
            notified = True

        self.vm.on_state_changed = on_change

        success = self.vm.submit_email("student1@insestatut.cat")
        self.assertTrue(success)
        self.assertTrue(self.vm.is_unlocked)
        self.assertEqual(self.vm.error_message, "")
        self.assertTrue(notified)

    def test_daemon_error_sets_error_message(self) -> None:
        self.mock_client.identify_user.return_value = Err(
            DomainError("Institutional domain required", code="INVALID_DOMAIN")
        )
        success = self.vm.submit_email("student@gmail.com")
        self.assertFalse(success)
        self.assertFalse(self.vm.is_unlocked)
        self.assertIn("Institutional domain", self.vm.error_message)

    def test_bypass_empty_password(self) -> None:
        success = self.vm.bypass_with_admin_password("   ")
        self.assertFalse(success)
        self.assertFalse(self.vm.is_unlocked)
        self.assertIn("Cal introduir", self.vm.error_message)
        self.mock_client.admin_bypass.assert_not_called()

    def test_bypass_failed_authentication(self) -> None:
        self.mock_client.admin_bypass.return_value = Err(
            DomainError("Contrasenya d'administrador incorrecta.", code="ADMIN_AUTH_FAILED")
        )
        success = self.vm.bypass_with_admin_password("WrongPassword123")
        self.assertFalse(success)
        self.assertFalse(self.vm.is_unlocked)
        self.assertIn("incorrecta", self.vm.error_message)
        self.mock_client.admin_bypass.assert_called_once_with("WrongPassword123")

    def test_bypass_success_unlocks_desktop(self) -> None:
        self.mock_client.admin_bypass.return_value = Ok(
            {"unlocked": True, "bypassed": True, "sanitised": False}
        )
        notified = False

        def on_change() -> None:
            nonlocal notified
            notified = True

        self.vm.on_state_changed = on_change

        success = self.vm.bypass_with_admin_password("CorrectAdminPass123!")
        self.assertTrue(success)
        self.assertTrue(self.vm.is_unlocked)
        self.assertEqual(self.vm.error_message, "")
        self.assertIn("Accés concedit", self.vm.status_message)
        self.assertTrue(notified)
        self.mock_client.admin_bypass.assert_called_once_with("CorrectAdminPass123!")

    def test_check_daemon_status(self) -> None:
        self.mock_client.get_status.return_value = Ok({"daemon_enabled": True})
        enabled = self.vm.check_daemon_status()
        self.assertTrue(enabled)
        self.assertTrue(self.vm.daemon_enabled)

        self.mock_client.get_status.return_value = Ok({"daemon_enabled": False})
        enabled = self.vm.check_daemon_status()
        self.assertFalse(enabled)
        self.assertFalse(self.vm.daemon_enabled)


class TestAdminViewModel(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_client = MagicMock(spec=IPCClient)
        self.vm = AdminViewModel(self.mock_client)

    def test_first_run_setup(self) -> None:
        self.mock_client.get_status.return_value = Ok({"has_admin_password": False})
        self.assertTrue(self.vm.is_first_run())

        self.mock_client.admin_setup_password.return_value = Ok({"session_token": "token123"})
        success = self.vm.authenticate("SuperAdminPass2026!")
        self.assertTrue(success)
        self.assertTrue(self.vm.is_authenticated)
        self.assertEqual(self.vm.session_token, "token123")

    def test_existing_password_auth_success(self) -> None:
        self.mock_client.get_status.return_value = Ok({"has_admin_password": True})
        self.assertFalse(self.vm.is_first_run())

        self.mock_client.admin_auth.return_value = Ok({"session_token": "auth_token_456"})
        success = self.vm.authenticate("CorrectPass123!")
        self.assertTrue(success)
        self.assertEqual(self.vm.session_token, "auth_token_456")

    def test_fetch_logs_and_verify_chain(self) -> None:
        self.vm.session_token = "valid_token"
        self.vm.is_authenticated = True

        self.mock_client.admin_get_logs.return_value = Ok([{"event": "LOGIN"}])
        logs = self.vm.fetch_logs()
        self.assertEqual(len(logs), 1)

        self.mock_client.admin_verify_chain.return_value = Ok({"is_valid": True, "total_entries": 5})
        verify = self.vm.verify_chain()
        self.assertTrue(verify["is_valid"])

    def test_policy_and_maintenance_operations(self) -> None:
        self.vm.session_token = "valid_token"
        self.vm.is_authenticated = True

        self.mock_client.admin_get_policy.return_value = Ok({"secure_delete": False})
        self.assertEqual(self.vm.fetch_policy(), {"secure_delete": False})

        self.mock_client.admin_update_policy.return_value = Ok({})
        self.assertTrue(self.vm.save_policy({"secure_delete": True}))

        self.mock_client.admin_reset_policy.return_value = Ok({"targets": [{"name": "UserDocuments"}]})
        self.assertEqual(self.vm.reset_policy(), {"targets": [{"name": "UserDocuments"}]})

        self.mock_client.admin_force_clean.return_value = Ok({"files_deleted": 10})
        self.assertEqual(self.vm.force_clean(), {"files_deleted": 10})

        self.mock_client.admin_change_password.return_value = Ok({})
        self.assertTrue(self.vm.change_password("Old12345", "New123456"))

    def test_get_and_set_daemon_enabled(self) -> None:
        self.mock_client.get_status.return_value = Ok({"daemon_enabled": False})
        self.assertFalse(self.vm.get_daemon_enabled())

        # Unauthenticated toggle fails
        self.vm.session_token = None
        self.assertFalse(self.vm.set_daemon_enabled(True))

        # Authenticated toggle succeeds
        self.vm.session_token = "valid_token"
        self.mock_client.set_daemon_state.return_value = Ok({"daemon_enabled": True})
        self.assertTrue(self.vm.set_daemon_enabled(True))
        self.mock_client.set_daemon_state.assert_called_once_with("valid_token", True)


class TestIPCClientInProcessFallback(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile
        from pathlib import Path
        self.tmp = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.tmp.name)
        self.non_existent_sock = self.storage_dir / "does_not_exist.sock"
        self.client = IPCClient(
            socket_path=self.non_existent_sock,
            storage_dir=self.storage_dir,
            allow_in_process_fallback=True,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_get_status_succeeds_without_daemon(self) -> None:
        res = self.client.get_status()
        self.assertTrue(res.is_ok())
        status = res.unwrap()
        self.assertFalse(status["has_admin_password"])
        self.assertTrue(self.client.is_in_process)

    def test_setup_and_auth_succeeds_without_daemon(self) -> None:
        setup_res = self.client.admin_setup_password("MasterPass123!")
        self.assertTrue(setup_res.is_ok())
        self.assertTrue(self.client.is_in_process)

        auth_res = self.client.admin_auth("MasterPass123!")
        self.assertTrue(auth_res.is_ok())
        self.assertIn("session_token", auth_res.unwrap())


class TestPresentationWiring(unittest.TestCase):
    def test_create_kiosk_app_wires_admin_parent(self) -> None:
        from unittest.mock import MagicMock, patch
        from netejator98.composition_root import create_kiosk_app

        mock_client = MagicMock()
        mock_root = MagicMock()

        with patch("tkinter.Tk", return_value=mock_root), patch("tkinter.StringVar"):
            kiosk = create_kiosk_app(mock_client)
            with patch("netejator98.composition_root.AdminView") as mock_admin_view:
                kiosk.on_admin_requested()
                mock_admin_view.assert_called_once()
                _, kwargs = mock_admin_view.call_args
                self.assertEqual(kwargs.get("parent"), kiosk.root)

    def test_admin_view_parent_and_standalone_resolution(self) -> None:
        from unittest.mock import MagicMock, patch
        import tkinter as tk
        from netejator98.presentation.admin_view import AdminView

        mock_vm = MagicMock()
        mock_parent = MagicMock()

        # When parent is explicitly passed
        av1 = AdminView(mock_vm, parent=mock_parent)
        self.assertEqual(av1.parent, mock_parent)
        self.assertFalse(av1._is_standalone)

        # When parent is None but tk._default_root is set
        with patch.object(tk, "_default_root", mock_parent):
            av2 = AdminView(mock_vm, parent=None)
            self.assertEqual(av2.parent, mock_parent)
            self.assertFalse(av2._is_standalone)

        # When parent is None and tk._default_root is None
        with patch.object(tk, "_default_root", None), patch("tkinter.Tk") as mock_tk:
            mock_tk_inst = MagicMock()
            mock_tk.return_value = mock_tk_inst
            av3 = AdminView(mock_vm, parent=None)
            self.assertEqual(av3.parent, mock_tk_inst)
            self.assertTrue(av3._is_standalone)

    def test_admin_view_golden_profile_attributes_and_tab(self) -> None:
        from unittest.mock import MagicMock, patch
        from netejator98.presentation.admin_view import AdminView

        mock_vm = MagicMock()
        mock_parent = MagicMock()
        av = AdminView(mock_vm, parent=mock_parent)
        self.assertEqual(av.golden_shortcuts, [])

        with patch("tkinter.Frame"), patch("tkinter.Canvas"), patch("tkinter.Label"), \
             patch("tkinter.ttk.Treeview"), patch("tkinter.ttk.Scrollbar"):
            mock_frame = MagicMock()
            av.golden_shortcuts = [{"name": "insestatut.cat", "url": "https://insestatut.cat"}]
            av._build_golden_tab(mock_frame)
            self.assertEqual(len(av.golden_shortcuts), 1)
            self.assertEqual(av.golden_shortcuts[0]["name"], "insestatut.cat")

    def test_admin_view_policy_tree_has_os_column(self) -> None:
        from unittest.mock import MagicMock, patch
        from netejator98.presentation.admin_view import AdminView

        mock_vm = MagicMock()
        mock_parent = MagicMock()
        av = AdminView(mock_vm, parent=mock_parent)

        with patch("tkinter.Frame"), patch("tkinter.Canvas"), patch("tkinter.Label"), \
             patch("tkinter.ttk.Treeview") as mock_treeview, patch("tkinter.ttk.Scrollbar"), \
             patch("tkinter.Checkbutton"), patch("tkinter.Spinbox"), patch("tkinter.Button"), \
             patch("tkinter.BooleanVar"), patch("tkinter.IntVar"), patch("tkinter.StringVar"):
            mock_frame = MagicMock()
            av._build_policy_tab(mock_frame)
            mock_treeview.assert_called_once()
            _, kwargs = mock_treeview.call_args
            self.assertIn("columns", kwargs)
            self.assertIn("os", kwargs["columns"])
            self.assertEqual(kwargs["columns"], ("enabled", "os", "name", "category", "strategy", "patterns", "description"))




class TestWin98Theme(unittest.TestCase):
    def test_palette_constants(self) -> None:
        from netejator98.presentation.win98_theme import (
            WIN98_TEAL,
            WIN98_GRAY,
            WIN98_WHITE,
            WIN98_BLACK,
            WIN98_BLUE_START,
            WIN98_BLUE_END,
        )
        self.assertEqual(WIN98_TEAL, "#008080")
        self.assertEqual(WIN98_GRAY, "#c0c0c0")
        self.assertEqual(WIN98_WHITE, "#ffffff")
        self.assertEqual(WIN98_BLACK, "#000000")
        self.assertEqual(WIN98_BLUE_START, "#000080")
        self.assertEqual(WIN98_BLUE_END, "#1084d0")

    def test_get_win98_font(self) -> None:
        from netejator98.presentation.win98_theme import get_win98_font
        regular = get_win98_font(9)
        self.assertEqual(len(regular), 3)
        self.assertEqual(regular[1], 9)
        self.assertEqual(regular[2], "normal")

        bold = get_win98_font(10, bold=True)
        self.assertEqual(bold[1], 10)
        self.assertEqual(bold[2], "bold")

    def test_draw_win98_icon_all_types(self) -> None:
        from unittest.mock import MagicMock
        from netejator98.presentation.win98_theme import draw_win98_icon
        mock_canvas = MagicMock()

        for icon in ["flag", "computer", "network", "recycle_bin", "cleaner", "key", "admin", "warning", "error", "info", "other"]:
            draw_win98_icon(mock_canvas, icon, 0, 0, size=32)
            self.assertTrue(mock_canvas.create_rectangle.called or mock_canvas.create_oval.called or mock_canvas.create_polygon.called)

    def test_apply_win98_ttk_theme_handles_none_or_mock(self) -> None:
        from unittest.mock import MagicMock
        from netejator98.presentation.win98_theme import apply_win98_ttk_theme

        # None or mock root should not raise uncaught exception
        res = apply_win98_ttk_theme(None)
        # Should return None or a style safely without exception
        mock_root = MagicMock()
        res2 = apply_win98_ttk_theme(mock_root)


if __name__ == "__main__":
    unittest.main()


