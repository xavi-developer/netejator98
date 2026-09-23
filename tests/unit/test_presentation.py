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

    def test_policy_thorough_log_translations(self) -> None:
        set_language("ca")
        self.assertIn("clean_trace.log", t("policy_thorough_log"))
        self.assertIn("exhaustiu", t("policy_thorough_log"))

        set_language("es")
        self.assertIn("clean_trace.log", t("policy_thorough_log"))
        self.assertIn("exhaustivo", t("policy_thorough_log"))

        set_language("en")
        self.assertIn("clean_trace.log", t("policy_thorough_log"))
        self.assertIn("Thorough", t("policy_thorough_log"))


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

    def test_admin_view_has_thorough_log_var(self) -> None:
        from unittest.mock import MagicMock
        from netejator98.presentation.admin_view import AdminView

        mock_vm = MagicMock()
        mock_parent = MagicMock()
        av = AdminView(mock_vm, parent=mock_parent)
        self.assertTrue(hasattr(av, "policy_thorough_log_var"))
        self.assertIsNone(av.policy_thorough_log_var)
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


    def test_win98_theme_notebook_tab_highlight(self) -> None:
        from unittest.mock import MagicMock
        from netejator98.presentation.win98_theme import (
            WIN98_BLUE_START,
            WIN98_WHITE,
            apply_win98_ttk_theme,
        )

        from tkinter import ttk
        mock_style = MagicMock(spec=ttk.Style)
        mock_style.theme_names.return_value = ["classic", "default"]
        apply_win98_ttk_theme(mock_style)

        # Verify style.map was called for TNotebook.Tab with highlight styling
        tab_map_calls = [
            call for call in mock_style.map.call_args_list if call[0] and call[0][0] == "TNotebook.Tab"
        ]
        self.assertTrue(len(tab_map_calls) > 0)
        _, kwargs = tab_map_calls[0]
        self.assertIn("background", kwargs)
        self.assertIn("foreground", kwargs)
        # Verify selected background is white and foreground is navy blue
        bg_map = dict(kwargs["background"])
        fg_map = dict(kwargs["foreground"])
        self.assertEqual(bg_map.get("selected"), WIN98_WHITE)
        self.assertEqual(fg_map.get("selected"), WIN98_BLUE_START)

    def test_admin_view_policy_tab_immediate_auto_save_and_buttons(self) -> None:
        from unittest.mock import MagicMock, patch
        from netejator98.presentation.admin_view import AdminView

        mock_vm = MagicMock()
        mock_vm.fetch_policy.return_value = {
            "dry_run": True,
            "always_clean_on_boot": False,
            "secure_delete": False,
            "thorough_logging": False,
            "retention_days": 365,
            "targets": [{"name": "Downloads", "enabled": True}],
            "protected_paths": [],
        }
        mock_vm.save_policy.return_value = True

        mock_parent = MagicMock()
        av = AdminView(mock_vm, parent=mock_parent)

        button_texts = []

        def fake_create_button(parent, text="", command=None, **kwargs):
            button_texts.append(text)
            btn = MagicMock()
            return btn

        checkbutton_commands = []

        def fake_checkbutton(*args, **kwargs):
            if "command" in kwargs and kwargs["command"]:
                checkbutton_commands.append(kwargs["command"])
            return MagicMock()

        spinbox_instances = []

        def fake_spinbox(*args, **kwargs):
            sp = MagicMock()
            if "command" in kwargs and kwargs["command"]:
                checkbutton_commands.append(kwargs["command"])
            spinbox_instances.append(sp)
            return sp

        with patch("netejator98.presentation.admin_view.create_win98_button", side_effect=fake_create_button), \
             patch("tkinter.Checkbutton", side_effect=fake_checkbutton), \
             patch("tkinter.Spinbox", side_effect=fake_spinbox), \
             patch("tkinter.Frame"), patch("tkinter.Canvas"), patch("tkinter.Label"), \
             patch("tkinter.ttk.Treeview"), patch("tkinter.ttk.Scrollbar"), \
             patch("tkinter.BooleanVar"), patch("tkinter.StringVar"):
            mock_frame = MagicMock()
            av._build_policy_tab(mock_frame)

            # 1. Verify "desar politica", "recarregar", and "restablir per defecte" buttons are NOT present
            lower_button_texts = [str(b).lower() for b in button_texts]
            self.assertFalse(any("desar política" in bt or "desar politica" in bt for bt in lower_button_texts))
            self.assertFalse(any("recarregar" in bt for bt in lower_button_texts))
            self.assertFalse(any("restablir per defecte" in bt for bt in lower_button_texts))

            # 2. Verify Add, Delete, and Edit target buttons ARE present and in order
            self.assertTrue(any(t("policy_add_btn") in bt for bt in button_texts))
            self.assertTrue(any(t("policy_delete_btn") in bt for bt in button_texts))
            self.assertTrue(any(t("policy_edit_btn") in bt for bt in button_texts))
            add_idx = next(i for i, bt in enumerate(button_texts) if t("policy_add_btn") in bt)
            del_idx = next(i for i, bt in enumerate(button_texts) if t("policy_delete_btn") in bt)
            self.assertLess(add_idx, del_idx)

            # 3. Verify all 4 Checkbuttons wired auto_save
            self.assertGreaterEqual(len(checkbutton_commands), 4)

            # 4. Trigger auto_save via _save_current_policy and verify immediate persistence
            self.assertTrue(hasattr(av, "_save_current_policy"))
            saved = av._save_current_policy(quiet=True)
            self.assertTrue(saved)
            mock_vm.save_policy.assert_called()

    def test_admin_view_policy_tab_packing_order_and_delete_binding(self) -> None:
        from unittest.mock import MagicMock, patch
        from netejator98.presentation.admin_view import AdminView

        mock_vm = MagicMock()
        mock_vm.fetch_policy.return_value = {
            "dry_run": True,
            "targets": [{"name": "Downloads", "enabled": True}],
        }
        mock_parent = MagicMock()
        av = AdminView(mock_vm, parent=mock_parent)

        mock_tree = MagicMock()
        bound_tree_events = {}
        mock_tree.bind.side_effect = lambda evt, cb: bound_tree_events.update({evt: cb})

        pack_calls = []
        def fake_frame(*args, **kwargs):
            f = MagicMock()
            f.pack.side_effect = lambda **p_kwargs: pack_calls.append((f, p_kwargs))
            return f

        with patch("netejator98.presentation.admin_view.create_win98_button"), \
             patch("tkinter.Checkbutton"), patch("tkinter.Spinbox"), \
             patch("tkinter.Frame", side_effect=fake_frame), \
             patch("tkinter.Canvas"), patch("tkinter.Label"), \
             patch("tkinter.ttk.Treeview", return_value=mock_tree), \
             patch("tkinter.ttk.Scrollbar"), \
             patch("tkinter.BooleanVar"), patch("tkinter.StringVar"):
            mock_frame = MagicMock()
            av._build_policy_tab(mock_frame)

            # Verify <Delete> is bound on policy treeview
            self.assertIn("<Delete>", bound_tree_events)
            self.assertIn("<Double-1>", bound_tree_events)
            self.assertIn("<space>", bound_tree_events)

            # Verify that in targets frame, side=RIGHT is packed before side=LEFT
            side_packings = [p_kwargs.get("side") for _, p_kwargs in pack_calls if "side" in p_kwargs]
            # Find the index of the first RIGHT packing for buttons and LEFT packing for tree
            right_indices = [i for i, s in enumerate(side_packings) if str(s) == "right"]
            left_indices = [i for i, s in enumerate(side_packings) if str(s) == "left"]
            self.assertTrue(len(right_indices) > 0)
            self.assertTrue(len(left_indices) > 0)
            # The button panel (side=RIGHT) must be packed before the expanding treeview (side=LEFT)
            self.assertLess(right_indices[0], left_indices[-1])


    def test_admin_dashboard_active_tab_highlight(self) -> None:
        from unittest.mock import MagicMock, patch
        from netejator98.presentation.admin_view import AdminView

        mock_vm = MagicMock()
        mock_vm.is_authenticated = True
        mock_parent = MagicMock()
        av = AdminView(mock_vm, parent=mock_parent)

        mock_notebook = MagicMock()
        mock_notebook.tabs.return_value = ["tab0", "tab1", "tab2", "tab3"]

        frames_added = []
        def fake_add(frame, **kwargs):
            frames_added.append(frame)

        mock_notebook.add.side_effect = fake_add

        tab_texts = {}
        def fake_tab(idx, **kwargs):
            if "text" in kwargs:
                tab_texts[idx] = kwargs["text"]
            return {"text": tab_texts.get(idx, "")}

        mock_notebook.tab.side_effect = fake_tab

        bound_events = {}
        def fake_bind(evt, cb):
            bound_events[evt] = cb

        mock_notebook.bind.side_effect = fake_bind

        with patch("tkinter.Toplevel"), patch("netejator98.presentation.admin_view.create_win98_window_frame"), \
             patch("netejator98.presentation.admin_view.Win98TitleBar"), \
             patch("tkinter.Frame", side_effect=lambda *args, **kwargs: MagicMock()), \
             patch("tkinter.ttk.Notebook", return_value=mock_notebook), \
             patch("tkinter.BooleanVar"), patch("tkinter.StringVar"), \
             patch.object(av, "_build_audit_tab"), patch.object(av, "_build_policy_tab"), \
             patch.object(av, "_build_golden_tab"), patch.object(av, "_build_maintenance_tab"), \
             patch("netejator98.presentation.admin_view.create_win98_button"):
            # Set selected tab to match the second tab (Cleaning Policy)
            def fake_select():
                return str(frames_added[1]) if len(frames_added) > 1 else ""
            mock_notebook.select.side_effect = fake_select

            av._show_dashboard()

            self.assertIn("<<NotebookTabChanged>>", bound_events)
            cb = bound_events["<<NotebookTabChanged>>"]
            cb()
            # Active tab (index 1) has "▶" highlight
            self.assertIn("▶", tab_texts[1])
            self.assertNotIn("▶", tab_texts[0])


if __name__ == "__main__":
    unittest.main()


