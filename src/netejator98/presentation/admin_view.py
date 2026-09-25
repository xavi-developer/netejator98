"""Administration area presentation view with authentic Windows 98 UX/UI."""

from __future__ import annotations

import copy
import json
import os
import platform
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import traceback
from typing import Any, Optional
import yaml

from netejator98.presentation.i18n import t
from netejator98.presentation.view_models import AdminViewModel
from netejator98.presentation.win98_theme import (
    WIN98_BLACK,
    WIN98_BLUE_START,
    WIN98_DARK,
    WIN98_GRAY,
    WIN98_GREEN,
    WIN98_LIGHT,
    WIN98_RED,
    WIN98_WHITE,
    WIN98_YELLOW,
    Win98StatusBar,
    Win98TitleBar,
    apply_win98_ttk_theme,
    create_win98_button,
    create_win98_entry,
    create_win98_groupbox,
    create_win98_window_frame,
    draw_win98_icon,
    get_win98_font,
)


def _dlog(msg: str) -> None:
    """Direct, unbuffered write to stderr fd 2 to prevent losing logs upon native SIGSEGV."""
    now_str = time.strftime("%H:%M:%S")
    out = f"[{now_str}] [DEBUG-ADMIN] {msg}\n"
    try:
        os.write(2, out.encode("utf-8", errors="replace"))
    except Exception:
        pass
    try:
        sys.stderr.flush()
    except Exception:
        pass


def _safe_modal_grab(window: tk.Toplevel) -> None:
    """Safely acquire modal grab, ignoring or deferring if X11 pointer is temporarily grabbed."""
    def _apply() -> None:
        _dlog("[STEP GRAB-TIMER] _safe_modal_grab timer fired.")
        try:
            if window.winfo_exists():
                _dlog("[STEP GRAB-APPLY] window exists, calling grab_set()...")
                window.grab_set()
                _dlog("[STEP GRAB-OK] window.grab_set() succeeded.")
            else:
                _dlog("[STEP GRAB-SKIP] window no longer exists.")
        except tk.TclError as e:
            _dlog(f"[STEP GRAB-WARN] TclError during grab_set: {e}")
        except Exception as e:
            _dlog(f"[STEP GRAB-ERR] Exception during grab_set: {e}")

    try:
        _dlog("[STEP GRAB-SCHED] Scheduling window.after(50, _apply)...")
        window.after(50, _apply)
        _dlog("[STEP GRAB-SCHED-OK] window.after(50) scheduled.")
    except Exception as e:
        _dlog(f"[STEP GRAB-SCHED-ERR] Failed to schedule window.after: {e}")


class AdminView:
    """Password-protected administration dialog for system administrators in Windows 98 aesthetic."""

    def __init__(self, view_model: AdminViewModel, parent: Optional[tk.Tk | tk.Toplevel] = None) -> None:
        _dlog("[STEP INIT-001] AdminView.__init__ started.")
        self.vm = view_model
        self.parent = parent
        self.window: Optional[tk.Toplevel] = None
        self._standalone_root: Optional[tk.Tk] = None

        if self.parent is None:
            _dlog("[STEP INIT-002] self.parent is None, inspecting tk._default_root...")
            if getattr(tk, "_default_root", None) is not None:
                _dlog("[STEP INIT-003] Attached to existing tk._default_root.")
                self.parent = tk._default_root
                self._is_standalone = False
            else:
                _dlog("[STEP INIT-004] No root found. Creating new tk.Tk() for _standalone_root...")
                try:
                    self._standalone_root = tk.Tk()
                    _dlog(f"[STEP INIT-005] tk.Tk() instance created: {self._standalone_root}")
                    self._standalone_root.withdraw()
                    _dlog("[STEP INIT-006] _standalone_root.withdraw() executed.")
                except Exception as e:
                    _dlog(f"[ERROR INIT-004] Failed creating tk.Tk(): {e}")
                    raise
                self.parent = self._standalone_root
                self._is_standalone = True
        else:
            _dlog(f"[STEP INIT-007] Using provided parent window: {self.parent}")
            self._is_standalone = False

        if self.parent:
            _dlog("[STEP INIT-008] Calling apply_win98_ttk_theme(self.parent)...")
            try:
                apply_win98_ttk_theme(self.parent)
                _dlog("[STEP INIT-009] apply_win98_ttk_theme completed.")
            except Exception as e:
                _dlog(f"[ERROR INIT-008] apply_win98_ttk_theme raised: {e}")

        self.policy_dry_run_var: Optional[tk.BooleanVar] = None
        self.policy_clean_boot_var: Optional[tk.BooleanVar] = None
        self.policy_secure_del_var: Optional[tk.BooleanVar] = None
        self.policy_thorough_log_var: Optional[tk.BooleanVar] = None
        self.policy_retention_var: Optional[tk.StringVar] = None
        self.golden_shortcuts: list[dict[str, str]] = []
        _dlog("[STEP INIT-010] AdminView.__init__ finished successfully.")

    def show(self) -> None:
        """Prompt for admin authentication or open dashboard if already authenticated."""
        _dlog("[STEP SHOW-100] Entering AdminView.show()...")
        try:
            _dlog("[STEP SHOW-101] Evaluating self.vm.is_authenticated...")
            is_auth = self.vm.is_authenticated
            _dlog(f"[STEP SHOW-102] self.vm.is_authenticated = {is_auth}")
        except Exception as e:
            _dlog(f"[ERROR SHOW-101] Exception checking is_authenticated: {e}")
            is_auth = False

        if not is_auth:
            _dlog("[STEP SHOW-103] Not authenticated. Calling self._show_login_dialog()...")
            try:
                self._show_login_dialog()
                _dlog("[STEP SHOW-104] self._show_login_dialog() returned normally.")
            except Exception as e:
                _dlog(f"[ERROR SHOW-103] Exception in _show_login_dialog: {e}")
                _dlog(traceback.format_exc())
                raise
        else:
            _dlog("[STEP SHOW-105] Authenticated. Calling self._show_dashboard()...")
            try:
                self._show_dashboard()
                _dlog("[STEP SHOW-106] self._show_dashboard() returned normally.")
            except Exception as e:
                _dlog(f"[ERROR SHOW-105] Exception in _show_dashboard: {e}")
                _dlog(traceback.format_exc())
                raise

        _dlog(f"[STEP SHOW-107] Checking standalone mainloop condition: _is_standalone={self._is_standalone}, root={self._standalone_root}")
        if self._is_standalone and self._standalone_root:
            _dlog("[STEP SHOW-108] Calling self._standalone_root.mainloop() -> Entering Tk event dispatch...")
            try:
                self._standalone_root.mainloop()
                _dlog("[STEP SHOW-109] self._standalone_root.mainloop() exited.")
            except Exception as e:
                _dlog(f"[ERROR SHOW-108] Exception inside mainloop(): {e}")
                _dlog(traceback.format_exc())
                raise
        else:
            _dlog("[STEP SHOW-110] Standalone mainloop not started (non-standalone or no root).")

    # ==========================================================================
    # Admin Authentication Dialog (Windows 98 Security Prompt)
    # ==========================================================================

    def _show_login_dialog(self) -> None:
        _dlog("[STEP DLG-200] Entering _show_login_dialog()...")

        _dlog("[STEP DLG-201] Creating tk.Toplevel(self.parent)...")
        try:
            dlg = tk.Toplevel(self.parent)
            _dlog(f"[STEP DLG-202] tk.Toplevel created: {dlg}")
        except Exception as e:
            _dlog(f"[ERROR DLG-201] Failed creating tk.Toplevel: {e}")
            raise

        _dlog("[STEP DLG-203] Setting dialog title...")
        try:
            dlg.title(t("admin_title"))
            _dlog("[STEP DLG-204] Title set.")
        except Exception as e:
            _dlog(f"[ERROR DLG-203] Failed setting title: {e}")

        _dlog("[STEP DLG-205] Setting dialog geometry 460x280...")
        try:
            dlg.geometry("460x280")
            _dlog("[STEP DLG-206] Geometry set.")
        except Exception as e:
            _dlog(f"[ERROR DLG-205] Failed setting geometry: {e}")

        _dlog("[STEP DLG-207] Setting resizable(False, False)...")
        try:
            dlg.resizable(False, False)
            _dlog("[STEP DLG-208] Resizable set.")
        except Exception as e:
            _dlog(f"[ERROR DLG-207] Failed setting resizable: {e}")

        _dlog(f"[STEP DLG-209] Setting configure(bg={WIN98_GRAY})...")
        try:
            dlg.configure(bg=WIN98_GRAY)
            _dlog("[STEP DLG-210] Background configured.")
        except Exception as e:
            _dlog(f"[ERROR DLG-209] Failed setting configure bg: {e}")

        _dlog("[STEP DLG-211] Setting dlg.attributes('-topmost', True)...")
        try:
            dlg.attributes("-topmost", True)
            _dlog("[STEP DLG-212] Topmost attribute set successfully.")
        except Exception as e:
            _dlog(f"[WARN DLG-211] dlg.attributes('-topmost') failed (ignored for safety): {e}")

        def on_dlg_close() -> None:
            _dlog("[STEP DLG-CLOSE] on_dlg_close callback triggered.")
            try:
                dlg.destroy()
                _dlog("[STEP DLG-CLOSE-1] dlg.destroy() called.")
            except Exception as e:
                _dlog(f"[WARN DLG-CLOSE-1] dlg.destroy() failed: {e}")

            if self._is_standalone and not self.vm.is_authenticated:
                if self._standalone_root:
                    try:
                        _dlog("[STEP DLG-CLOSE-2] Destroying _standalone_root...")
                        self._standalone_root.destroy()
                        _dlog("[STEP DLG-CLOSE-3] _standalone_root destroyed.")
                    except Exception as e:
                        _dlog(f"[WARN DLG-CLOSE-2] _standalone_root.destroy() failed: {e}")

        _dlog("[STEP DLG-213] Binding WM_DELETE_WINDOW protocol...")
        try:
            dlg.protocol("WM_DELETE_WINDOW", on_dlg_close)
            _dlog("[STEP DLG-214] Protocol WM_DELETE_WINDOW bound.")
        except Exception as e:
            _dlog(f"[ERROR DLG-213] Failed binding protocol: {e}")

        # Outer 3D raised border
        _dlog("[STEP DLG-215] Creating outer 3D window frame via create_win98_window_frame...")
        try:
            frame = create_win98_window_frame(dlg, bd=3)
            _dlog(f"[STEP DLG-216] Outer frame created: {frame}. Packing...")
            frame.pack(fill=tk.BOTH, expand=True)
            _dlog("[STEP DLG-217] Outer frame packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-215] Failed creating/packing outer frame: {e}")
            raise

        _dlog("[STEP DLG-218] Querying self.vm.is_first_run()...")
        try:
            is_first = self.vm.is_first_run()
            _dlog(f"[STEP DLG-219] is_first_run result = {is_first}")
        except Exception as e:
            _dlog(f"[ERROR DLG-218] Exception in is_first_run(): {e}")
            is_first = False

        _dlog("[STEP DLG-220] Querying self.vm.client.get_status()...")
        try:
            status_res = self.vm.client.get_status()
            is_offline = status_res.is_err()
            _dlog(f"[STEP DLG-221] client.get_status() returned: is_err={is_offline}")
        except Exception as e:
            _dlog(f"[ERROR DLG-220] Exception in client.get_status(): {e}")
            is_offline = True

        title_text = "Configuració Inicial Administrador" if is_first else t("admin_title")
        sub_text = (
            "Estableix la contrasenya d'administrador (mínim 8 caràcters):"
            if is_first
            else t("admin_password_prompt")
        )
        _dlog(f"[STEP DLG-222] Dialog text prepared: title='{title_text}', sub_text_len={len(sub_text)}")

        # Title bar with blue gradient
        _dlog("[STEP DLG-223] Creating Win98TitleBar...")
        try:
            title_bar = Win98TitleBar(
                frame,
                title="Seguretat de Netejator 98",
                icon_type="key",
                on_close=on_dlg_close,
                is_dialog=True,
                height=22,
            )
            _dlog(f"[STEP DLG-224] Win98TitleBar instantiated: {title_bar}. Packing...")
            title_bar.pack(fill=tk.X)
            _dlog("[STEP DLG-225] Win98TitleBar packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-223] Failed creating/packing Win98TitleBar: {e}")
            _dlog(traceback.format_exc())
            raise

        _dlog("[STEP DLG-226] Creating body Frame...")
        try:
            body = tk.Frame(frame, bg=WIN98_GRAY, padx=16, pady=12)
            body.pack(fill=tk.BOTH, expand=True)
            _dlog("[STEP DLG-227] Body Frame packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-226] Failed body Frame: {e}")
            raise

        _dlog("[STEP DLG-228] Creating top_f Frame...")
        try:
            top_f = tk.Frame(body, bg=WIN98_GRAY)
            top_f.pack(fill=tk.X, pady=(0, 10))
            _dlog("[STEP DLG-229] top_f Frame packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-228] Failed top_f Frame: {e}")
            raise

        _dlog("[STEP DLG-230] Creating key_cv Canvas (36x36)...")
        try:
            key_cv = tk.Canvas(top_f, width=36, height=36, bg=WIN98_GRAY, highlightthickness=0, bd=0)
            key_cv.pack(side=tk.LEFT, padx=(0, 12))
            _dlog("[STEP DLG-231] key_cv packed. Drawing 'key' icon...")
            draw_win98_icon(key_cv, "key", 2, 2, size=32)
            _dlog("[STEP DLG-232] 'key' icon drawn successfully.")
        except Exception as e:
            _dlog(f"[ERROR DLG-230] Failed key_cv / draw_win98_icon: {e}")

        _dlog("[STEP DLG-233] Creating hdr_col Frame...")
        try:
            hdr_col = tk.Frame(top_f, bg=WIN98_GRAY)
            hdr_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            _dlog("[STEP DLG-234] hdr_col packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-233] Failed hdr_col: {e}")
            raise

        _dlog("[STEP DLG-235] Creating Title Label...")
        try:
            font_title = get_win98_font(10, bold=True)
            _dlog(f"[STEP DLG-236] Font for title: {font_title}")
            lbl_title = tk.Label(
                hdr_col,
                text=title_text,
                font=font_title,
                fg=WIN98_BLACK,
                bg=WIN98_GRAY,
                anchor=tk.W,
            )
            lbl_title.pack(fill=tk.X)
            _dlog("[STEP DLG-237] Title Label packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-235] Failed Title Label: {e}")

        _dlog("[STEP DLG-238] Creating Subtext Label...")
        try:
            font_sub = get_win98_font(9)
            _dlog(f"[STEP DLG-239] Font for subtext: {font_sub}")
            lbl_sub = tk.Label(
                hdr_col,
                text=sub_text,
                font=font_sub,
                fg=WIN98_BLACK,
                bg=WIN98_GRAY,
                wraplength=330,
                justify=tk.LEFT,
                anchor=tk.W,
            )
            lbl_sub.pack(fill=tk.X, pady=(2, 0))
            _dlog("[STEP DLG-240] Subtext Label packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-238] Failed Subtext Label: {e}")

        # Password input
        _dlog("[STEP DLG-241] Creating pwd_f Frame...")
        try:
            pwd_f = tk.Frame(body, bg=WIN98_GRAY)
            pwd_f.pack(fill=tk.X, pady=(4, 8))
            _dlog("[STEP DLG-242] pwd_f packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-241] Failed pwd_f: {e}")
            raise

        _dlog("[STEP DLG-243] Creating 'Contrasenya:' Label...")
        try:
            font_pwd_lbl = get_win98_font(9, bold=True)
            lbl_pwd = tk.Label(
                pwd_f,
                text="Contrasenya:",
                font=font_pwd_lbl,
                fg=WIN98_BLACK,
                bg=WIN98_GRAY,
            )
            lbl_pwd.pack(anchor=tk.W, pady=(0, 2))
            _dlog("[STEP DLG-244] 'Contrasenya:' Label packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-243] Failed 'Contrasenya:' Label: {e}")

        _dlog("[STEP DLG-245] Creating pwd_var and Entry...")
        try:
            pwd_var = tk.StringVar(master=dlg)
            font_entry = get_win98_font(10)
            _dlog(f"[STEP DLG-246] Entry font: {font_entry}. Calling create_win98_entry...")
            pwd_entry = create_win98_entry(
                pwd_f,
                textvariable=pwd_var,
                show="*",
                width=32,
                font=font_entry,
            )
            _dlog(f"[STEP DLG-247] Entry created: {pwd_entry}. Packing...")
            pwd_entry.pack(fill=tk.X, ipady=2)
            _dlog("[STEP DLG-248] Entry packed. Setting focus...")
            pwd_entry.focus_set()
            _dlog("[STEP DLG-249] Entry focus_set() completed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-245] Failed Entry creation/focus: {e}")
            raise

        # Status / Offline indicator (sunken pane)
        _dlog("[STEP DLG-250] Creating status_pane Frame...")
        try:
            status_pane = tk.Frame(body, relief=tk.SUNKEN, bd=1, bg=WIN98_GRAY, padx=6, pady=3)
            status_pane.pack(fill=tk.X, pady=(0, 8))
            _dlog("[STEP DLG-251] status_pane packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-250] Failed status_pane: {e}")
            raise

        _dlog("[STEP DLG-252] Creating err_label...")
        try:
            initial_hint = (
                "ℹ️ Mode autònom actiu (Sense dimoni de fons)"
                if getattr(self.vm.client, "is_in_process", False)
                else ("⚠️ Dimoni agent fora de línia." if is_offline else "A punt per a l'autenticació.")
            )
            font_err = get_win98_font(8)
            err_label = tk.Label(
                status_pane,
                text=initial_hint,
                font=font_err,
                fg=WIN98_RED if is_offline else WIN98_BLACK,
                bg=WIN98_GRAY,
                anchor=tk.W,
            )
            err_label.pack(fill=tk.X)
            _dlog("[STEP DLG-253] err_label packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-252] Failed err_label: {e}")
            raise

        # Action Buttons
        _dlog("[STEP DLG-254] Creating btn_frame...")
        try:
            btn_frame = tk.Frame(body, bg=WIN98_GRAY)
            btn_frame.pack(anchor=tk.E)
            _dlog("[STEP DLG-255] btn_frame packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-254] Failed btn_frame: {e}")
            raise

        def do_login() -> None:
            _dlog("[STEP BTN-300] >>> do_login() triggered! (User clicked button or hit Return) <<<")
            try:
                _dlog("[STEP BTN-301] Reading password from pwd_entry / pwd_var...")
                pwd = pwd_entry.get() or pwd_var.get()
                _dlog(f"[STEP BTN-302] Password retrieved. Length = {len(pwd)}")
                if not pwd:
                    _dlog("[STEP BTN-303] Password is empty. Setting error prompt.")
                    err_label.config(text="La contrasenya no pot estar buida", fg=WIN98_RED)
                    return

                _dlog("[STEP BTN-304] Calling self.vm.authenticate(pwd)...")
                success = self.vm.authenticate(pwd)
                _dlog(f"[STEP BTN-305] self.vm.authenticate result = {success}")
                if success:
                    _dlog("[STEP BTN-306] Authentication success! Destroying login dialog and opening dashboard...")
                    dlg.destroy()
                    self._show_dashboard()
                    _dlog("[STEP BTN-307] Dashboard opened.")
                else:
                    _dlog(f"[STEP BTN-308] Authentication failed. Error message: {self.vm.error_message}")
                    err_label.config(text=self.vm.error_message or "Autenticació fallida", fg=WIN98_RED)
            except Exception as e:
                _dlog(f"[ERROR BTN-300] Exception inside do_login: {e}")
                _dlog(traceback.format_exc())

        _dlog("[STEP DLG-256] Binding events (<Return>, <Escape>)...")
        try:
            pwd_entry.bind("<Return>", lambda e: do_login())
            dlg.bind("<Escape>", lambda e: on_dlg_close())
            _dlog("[STEP DLG-257] Key bindings bound.")
        except Exception as e:
            _dlog(f"[ERROR DLG-256] Failed key bindings: {e}")

        _dlog("[STEP DLG-258] Creating Login button via create_win98_button...")
        try:
            btn_login = create_win98_button(
                btn_frame,
                text=t("admin_login_button"),
                command=do_login,
                is_default=True,
                padx=16,
            )
            _dlog(f"[STEP DLG-259] Login button created: {btn_login}. Packing...")
            btn_login.pack(side=tk.LEFT, padx=6)
            _dlog("[STEP DLG-260] Login button packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-258] Failed Login button: {e}")
            raise

        _dlog("[STEP DLG-261] Creating Cancel button via create_win98_button...")
        try:
            btn_cancel = create_win98_button(
                btn_frame,
                text=t("admin_cancel_button"),
                command=on_dlg_close,
                is_default=False,
                padx=12,
            )
            _dlog(f"[STEP DLG-262] Cancel button created: {btn_cancel}. Packing...")
            btn_cancel.pack(side=tk.LEFT)
            _dlog("[STEP DLG-263] Cancel button packed.")
        except Exception as e:
            _dlog(f"[ERROR DLG-261] Failed Cancel button: {e}")
            raise

        _dlog("[STEP DLG-264] Calling _safe_modal_grab(dlg)...")
        try:
            _safe_modal_grab(dlg)
            _dlog("[STEP DLG-265] _safe_modal_grab called.")
        except Exception as e:
            _dlog(f"[WARN DLG-264] _safe_modal_grab raised: {e}")

        _dlog("[STEP DLG-266] _show_login_dialog setup COMPLETE. Dialog is active and awaiting user input.")

    # ==========================================================================
    # Admin Dashboard Window (Windows 98 "System Properties" Style)
    # ==========================================================================

    def _show_dashboard(self) -> None:
        _dlog("[STEP DASH-400] Entering _show_dashboard()...")
        try:
            self.window = tk.Toplevel(self.parent)
            self.window.title(t("admin_title"))
            self.window.geometry("920x640")
            self.window.configure(bg=WIN98_GRAY)
            _dlog("[STEP DASH-401] Dashboard window created, geometry set.")
        except Exception as e:
            _dlog(f"[ERROR DASH-400] Failed creating dashboard window: {e}")
            raise

        try:
            _dlog("[STEP DASH-402] Setting dashboard topmost attribute...")
            self.window.attributes("-topmost", True)
            _dlog("[STEP DASH-403] Dashboard topmost set.")
        except Exception as e:
            _dlog(f"[WARN DASH-402] Dashboard attributes -topmost failed: {e}")

        try:
            _dlog("[STEP DASH-404] Applying TTK theme to dashboard window...")
            apply_win98_ttk_theme(self.window)
            _dlog("[STEP DASH-405] Dashboard TTK theme applied.")
        except Exception as e:
            _dlog(f"[WARN DASH-404] Failed apply_win98_ttk_theme: {e}")

        def on_dashboard_close() -> None:
            if self.window:
                self.window.destroy()
            if self._is_standalone and self._standalone_root:
                self._standalone_root.destroy()

        self.window.protocol("WM_DELETE_WINDOW", on_dashboard_close)

        # Outer 3D raised border
        main_frame = create_win98_window_frame(self.window, bd=3)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Windows 98 Title bar
        self.title_bar = Win98TitleBar(
            main_frame,
            title="Netejator 98 - Administració del Sistema",
            icon_type="computer",
            on_close=on_dashboard_close,
            is_dialog=False,
            height=24,
        )
        self.title_bar.pack(fill=tk.X)

        # Tabbed Property Sheet Notebook
        content_frame = tk.Frame(main_frame, bg=WIN98_GRAY, padx=8, pady=8)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Initialize Policy & Golden Profile form variables
        self.policy_dry_run_var = tk.BooleanVar(value=True)
        self.policy_clean_boot_var = tk.BooleanVar(value=False)
        self.policy_secure_del_var = tk.BooleanVar(value=False)
        self.policy_thorough_log_var = tk.BooleanVar(value=False)
        self.policy_retention_var = tk.StringVar(value="365")
        self.golden_shortcuts = [
            {"name": "insestatut.cat", "url": "https://insestatut.cat"}
        ]

        _dlog("[STEP DASH-406] Creating ttk.Notebook...")
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        _dlog("[STEP DASH-407] ttk.Notebook created and packed.")

        # Tab 1: Audit Log
        _dlog("[STEP DASH-408] Building Tab 1: Audit Log frame...")
        log_frame = tk.Frame(self.notebook, bg=WIN98_GRAY, padx=6, pady=6)
        self.notebook.add(log_frame, text=f"  {t('admin_tab_logs')}  ")
        _dlog("[STEP DASH-409] Calling _build_audit_tab(log_frame)...")
        self._build_audit_tab(log_frame)
        _dlog("[STEP DASH-410] Tab 1: Audit Log built successfully.")

        # Tab 2: Cleaning Policy
        _dlog("[STEP DASH-411] Building Tab 2: Cleaning Policy frame...")
        policy_frame = tk.Frame(self.notebook, bg=WIN98_GRAY, padx=6, pady=6)
        self.notebook.add(policy_frame, text=f"  {t('admin_tab_policy')}  ")
        _dlog("[STEP DASH-412] Calling _build_policy_tab(policy_frame)...")
        self._build_policy_tab(policy_frame)
        _dlog("[STEP DASH-413] Tab 2: Cleaning Policy built successfully.")

        # Tab 3: Golden Profile
        _dlog("[STEP DASH-414] Building Tab 3: Golden Profile frame...")
        golden_frame = tk.Frame(self.notebook, bg=WIN98_GRAY, padx=6, pady=6)
        self.notebook.add(golden_frame, text=f"  {t('admin_tab_golden')}  ")
        _dlog("[STEP DASH-415] Calling _build_golden_tab(golden_frame)...")
        self._build_golden_tab(golden_frame)
        _dlog("[STEP DASH-416] Tab 3: Golden Profile built successfully.")

        # Tab 4: Maintenance
        _dlog("[STEP DASH-417] Building Tab 4: Maintenance frame...")
        maint_frame = tk.Frame(self.notebook, bg=WIN98_GRAY, padx=6, pady=6)
        self.notebook.add(maint_frame, text=f"  {t('admin_tab_maintenance')}  ")
        _dlog("[STEP DASH-418] Calling _build_maintenance_tab(maint_frame)...")
        self._build_maintenance_tab(maint_frame)
        _dlog("[STEP DASH-419] Tab 4: Maintenance built successfully.")

        tab_entries = [
            (log_frame, t("admin_tab_logs")),
            (policy_frame, t("admin_tab_policy")),
            (golden_frame, t("admin_tab_golden")),
            (maint_frame, t("admin_tab_maintenance")),
        ]

        def update_active_tab_highlight(event: Any = None) -> None:
            try:
                selected_tab = self.notebook.select()
                if not selected_tab:
                    return
                for idx, (frame, title) in enumerate(tab_entries):
                    if str(frame) == str(selected_tab):
                        self.notebook.tab(idx, text=f"  ▶ {title}  ")
                    else:
                        self.notebook.tab(idx, text=f"    {title}    ")
            except Exception as e:
                _dlog(f"[WARN DASH] update_active_tab_highlight error: {e}")

        self.notebook.bind("<<NotebookTabChanged>>", update_active_tab_highlight)
        update_active_tab_highlight()

        # Bottom Property Sheet Control Bar (D'acord, Cancel·la, Aplica)
        _dlog("[STEP DASH-420] Creating bottom property sheet control bar...")
        bottom_bar = tk.Frame(main_frame, bg=WIN98_GRAY, padx=10, pady=8)
        bottom_bar.pack(fill=tk.X)

        def do_apply() -> None:
            if hasattr(self, "_save_current_policy"):
                self._save_current_policy(quiet=True)

        def do_ok() -> None:
            do_apply()
            on_dashboard_close()

        create_win98_button(bottom_bar, text="D'acord", command=do_ok, is_default=True, padx=16).pack(side=tk.RIGHT, padx=4)
        create_win98_button(bottom_bar, text="Cancel·la", command=on_dashboard_close, is_default=False, padx=14).pack(side=tk.RIGHT, padx=4)
        create_win98_button(bottom_bar, text="Aplica", command=do_apply, is_default=False, padx=14).pack(side=tk.RIGHT, padx=4)
        _dlog("[STEP DASH-421] Dashboard initialization complete. Window displayed.")

    def _show_about_dialog(self) -> None:
        dlg = tk.Toplevel(self.window)
        dlg.title("Quant a Netejator 98")
        dlg.geometry("420x260")
        dlg.resizable(False, False)
        dlg.configure(bg=WIN98_GRAY)
        dlg.attributes("-topmost", True)

        frame = create_win98_window_frame(dlg, bd=2)
        frame.pack(fill=tk.BOTH, expand=True)

        Win98TitleBar(frame, title="Quant a Netejator 98", icon_type="cleaner", on_close=dlg.destroy, is_dialog=True).pack(fill=tk.X)

        body = tk.Frame(frame, bg=WIN98_GRAY, padx=20, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        top_f = tk.Frame(body, bg=WIN98_GRAY)
        top_f.pack(fill=tk.X, pady=(0, 10))

        flag_cv = tk.Canvas(top_f, width=36, height=36, bg=WIN98_GRAY, highlightthickness=0, bd=0)
        flag_cv.pack(side=tk.LEFT, padx=(0, 12))
        draw_win98_icon(flag_cv, "cleaner", 0, 0, size=36)

        title_col = tk.Frame(top_f, bg=WIN98_GRAY)
        title_col.pack(side=tk.LEFT, fill=tk.BOTH)

        tk.Label(title_col, text="Netejator 98", font=get_win98_font(13, bold=True), fg=WIN98_BLUE_START, bg=WIN98_GRAY).pack(anchor=tk.W)
        tk.Label(title_col, text="Versió 1.0 (Administració)", font=get_win98_font(9), fg=WIN98_BLACK, bg=WIN98_GRAY).pack(anchor=tk.W)

        tk.Frame(body, height=2, relief=tk.SUNKEN, bd=1, bg=WIN98_GRAY).pack(fill=tk.X, pady=8)

        desc = (
            "Netejator 98 - Eina d'administració per a estacions compartides.\n\n"
            "Arquitectura DDD Hexagonal amb registre criptogràfic asimètric (X25519) i cadena SHA-256."
        )
        tk.Label(body, text=desc, font=get_win98_font(8), fg=WIN98_BLACK, bg=WIN98_GRAY, justify=tk.LEFT, wraplength=360).pack(fill=tk.X, pady=(0, 12))

        btn_box = tk.Frame(body, bg=WIN98_GRAY)
        btn_box.pack(anchor=tk.CENTER)
        create_win98_button(btn_box, text="D'acord", command=dlg.destroy, is_default=True, padx=20).pack()

        _safe_modal_grab(dlg)

    # --------------------------------------------------------------------------
    # Tab 1: Audit Log
    # --------------------------------------------------------------------------

    def _build_audit_tab(self, parent: tk.Frame) -> None:
        _dlog("[STEP AUDIT-500] Entering _build_audit_tab()...")
        toolbar = tk.Frame(parent, bg=WIN98_GRAY, pady=6)
        toolbar.pack(fill=tk.X)
        _dlog("[STEP AUDIT-501] Toolbar packed.")

        create_win98_button(
            toolbar,
            text="🔄 Refrescar",
            command=self._refresh_logs,
            padx=10,
        ).pack(side=tk.LEFT, padx=4)
        _dlog("[STEP AUDIT-502] 'Refrescar' button packed.")

        create_win98_button(
            toolbar,
            text=f"🛡 {t('admin_verify_button')}",
            command=self._verify_chain,
            padx=10,
        ).pack(side=tk.LEFT, padx=4)
        _dlog("[STEP AUDIT-503] 'Verificar' button packed.")

        create_win98_button(
            toolbar,
            text=f"📁 {t('admin_export_button')}",
            command=self._export_csv,
            padx=10,
        ).pack(side=tk.LEFT, padx=4)
        _dlog("[STEP AUDIT-504] 'Exportar' button packed.")

        _dlog("[STEP AUDIT-505] Creating tree_frame for Audit Log...")
        tree_frame = tk.Frame(parent, bg=WIN98_GRAY, relief=tk.SUNKEN, bd=2)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        _dlog("[STEP AUDIT-506] tree_frame created and packed.")

        columns = ("seq", "timestamp", "event", "email", "outcome", "targets")
        _dlog("[STEP AUDIT-507] Instantiating ttk.Treeview...")
        try:
            self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
            _dlog(f"[STEP AUDIT-508] ttk.Treeview instantiated: {self.tree}")
        except Exception as e:
            _dlog(f"[ERROR AUDIT-507] Failed instantiating ttk.Treeview: {e}")
            raise

        _dlog("[STEP AUDIT-509] Setting headings on ttk.Treeview...")
        self.tree.heading("seq", text="#")
        self.tree.heading("timestamp", text="Data/Hora (UTC)")
        self.tree.heading("event", text="Esdeveniment")
        self.tree.heading("email", text="Usuari")
        self.tree.heading("outcome", text="Resultat")
        self.tree.heading("targets", text="Objectius Netejats")
        _dlog("[STEP AUDIT-510] Headings set.")

        _dlog("[STEP AUDIT-511] Setting columns on ttk.Treeview...")
        self.tree.column("seq", width=40, anchor=tk.CENTER)
        self.tree.column("timestamp", width=160)
        self.tree.column("event", width=160)
        self.tree.column("email", width=180)
        self.tree.column("outcome", width=90, anchor=tk.CENTER)
        self.tree.column("targets", width=240)
        _dlog("[STEP AUDIT-512] Columns set.")

        _dlog("[STEP AUDIT-513] Creating scrollbar...")
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        _dlog("[STEP AUDIT-514] Scrollbar and Treeview packed.")

        # Multi-pane Windows 98 Status Bar
        _dlog("[STEP AUDIT-515] Creating Win98StatusBar...")
        self.audit_status_bar = Win98StatusBar(
            parent,
            panes=[
                {"text": "Total entrades carregades: 0", "weight": 1},
                {"text": "Integritat SHA-256: Verificada", "weight": 0},
                {"text": "INS Estatut", "weight": 0},
            ],
        )
        self.audit_status_bar.pack(fill=tk.X, pady=(2, 0))
        _dlog("[STEP AUDIT-516] Win98StatusBar created and packed.")

        _dlog("[STEP AUDIT-517] Triggering initial self._refresh_logs()...")
        self._refresh_logs()
        _dlog("[STEP AUDIT-518] _build_audit_tab() completed.")

    def _refresh_logs(self) -> None:
        _dlog("[STEP REFRESH-600] Entering _refresh_logs()...")
        try:
            children = self.tree.get_children()
            _dlog(f"[STEP REFRESH-601] Existing tree children: {len(children)}")
            for item in children:
                self.tree.delete(item)
            _dlog("[STEP REFRESH-602] Existing items deleted safely.")
        except Exception as e:
            _dlog(f"[WARN REFRESH-601] Error clearing tree children: {e}")

        _dlog("[STEP REFRESH-603] Querying self.vm.fetch_logs()...")
        try:
            entries = self.vm.fetch_logs()
            _dlog(f"[STEP REFRESH-604] self.vm.fetch_logs() returned {len(entries)} entries.")
        except Exception as e:
            _dlog(f"[ERROR REFRESH-603] Exception in self.vm.fetch_logs(): {e}")
            entries = []

        _dlog(f"[STEP REFRESH-605] Inserting {len(entries)} entries into tree...")
        try:
            for i, e in enumerate(entries, start=1):
                targets_str = ", ".join(e.get("targets_cleaned", []))
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        i,
                        e.get("timestamp", "")[:19].replace("T", " "),
                        e.get("event_type", ""),
                        e.get("email") or "(anònim/agent)",
                        e.get("outcome", ""),
                        targets_str,
                    ),
                )
            _dlog("[STEP REFRESH-606] Treeview items inserted successfully.")
        except Exception as e:
            _dlog(f"[ERROR REFRESH-605] Failed inserting entries into treeview: {e}")

        if hasattr(self, "audit_status_bar"):
            try:
                self.audit_status_bar.set_pane_text(0, f"Total entrades carregades: {len(entries)}")
                _dlog("[STEP REFRESH-607] Status bar pane 0 updated.")
            except Exception as e:
                _dlog(f"[WARN REFRESH-607] Failed updating status bar: {e}")
        _dlog("[STEP REFRESH-608] _refresh_logs() finished.")

    def _verify_chain(self) -> None:
        res = self.vm.verify_chain()
        if res.get("is_valid"):
            messagebox.showinfo(
                "Verificació d'Integritat",
                f"{t('integrity_valid')}\nTotal registres verificats: {res.get('total_entries', 0)}",
                parent=self.window,
            )
            if hasattr(self, "audit_status_bar"):
                self.audit_status_bar.set_pane_text(1, "Integritat SHA-256: Correcta ✓")
        else:
            messagebox.showerror(
                "Alerta d'Integritat",
                f"{t('integrity_invalid')}\nSeqüència: {res.get('tampered_seq')}\nMotiu: {res.get('failure_reason')}",
                parent=self.window,
            )
            if hasattr(self, "audit_status_bar"):
                self.audit_status_bar.set_pane_text(1, "Integritat: ALERTA DE MANIPULACIÓ ✗")

    def _export_csv(self) -> None:
        dest = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title=t("admin_export_button"),
            parent=self.window,
        )
        if dest:
            if self.vm.export_logs(dest):
                messagebox.showinfo("Exportació", "Registre exportat correctament!", parent=self.window)
            else:
                messagebox.showerror("Error", "No s'ha pogut exportar el registre", parent=self.window)

    # --------------------------------------------------------------------------
    # Tab 2: Cleaning Policy
    # --------------------------------------------------------------------------

    def _build_policy_tab(self, parent: tk.Frame) -> None:
        _dlog("[STEP POLICY-700] Entering _build_policy_tab()...")
        self.targets_list: list[dict[str, Any]] = []
        self._current_policy_raw: dict[str, Any] = {}

        if not hasattr(self, "policy_dry_run_var") or self.policy_dry_run_var is None:
            self.policy_dry_run_var = tk.BooleanVar(value=True)
            self.policy_clean_boot_var = tk.BooleanVar(value=False)
            self.policy_secure_del_var = tk.BooleanVar(value=False)
            self.policy_thorough_log_var = tk.BooleanVar(value=False)
            self.policy_retention_var = tk.StringVar(value="365")
            self.golden_shortcuts = [
                {"name": "insestatut.cat", "url": "https://insestatut.cat"}
            ]

        def save_policy_data(quiet: bool = True) -> bool:
            ret_days = 365
            if self.policy_retention_var is not None:
                try:
                    ret_days = int(self.policy_retention_var.get().strip())
                except ValueError:
                    pass

            data = {
                "dry_run": bool(self.policy_dry_run_var.get()) if self.policy_dry_run_var else True,
                "always_clean_on_boot": bool(self.policy_clean_boot_var.get()) if self.policy_clean_boot_var else False,
                "secure_delete": bool(self.policy_secure_del_var.get()) if self.policy_secure_del_var else False,
                "thorough_logging": bool(self.policy_thorough_log_var.get()) if self.policy_thorough_log_var else False,
                "reset_to_golden_profile": bool(self.golden_shortcuts),
                "golden_profile_path": "/etc/skel",
                "golden_profile_shortcuts": self.golden_shortcuts,
                "retention_days": ret_days,
                "targets": self.targets_list,
                "protected_paths": self._current_policy_raw.get("protected_paths", []),
            }

            saved = self.vm.save_policy(data)
            if saved:
                if hasattr(self, "policy_status_label") and self.policy_status_label:
                    self.policy_status_label.config(text="✓ Canvis desats immediatament", fg=WIN98_GREEN)
            else:
                messagebox.showerror("Error", self.vm.error_message or "Error al desar la configuració", parent=self.window)
            return saved

        self._save_current_policy = save_policy_data

        def auto_save() -> None:
            save_policy_data(quiet=True)

        def view_yaml_popup() -> None:
            ret_days = 365
            if self.policy_retention_var is not None:
                try:
                    ret_days = int(self.policy_retention_var.get().strip())
                except ValueError:
                    pass

            preview_dict = {
                "dry_run": bool(self.policy_dry_run_var.get()) if self.policy_dry_run_var else True,
                "always_clean_on_boot": bool(self.policy_clean_boot_var.get()) if self.policy_clean_boot_var else False,
                "secure_delete": bool(self.policy_secure_del_var.get()) if self.policy_secure_del_var else False,
                "thorough_logging": bool(self.policy_thorough_log_var.get()) if self.policy_thorough_log_var else False,
                "reset_to_golden_profile": bool(self.golden_shortcuts),
                "golden_profile_path": "/etc/skel",
                "golden_profile_shortcuts": self.golden_shortcuts,
                "retention_days": ret_days,
                "targets": self.targets_list,
                "protected_paths": self._current_policy_raw.get("protected_paths", []),
            }

            dlg = tk.Toplevel(self.window)
            dlg.title("Vista Prèvia YAML")
            dlg.geometry("560x420")
            dlg.configure(bg=WIN98_GRAY)
            dlg.attributes("-topmost", True)

            dlg_frame = create_win98_window_frame(dlg, bd=2)
            dlg_frame.pack(fill=tk.BOTH, expand=True)

            Win98TitleBar(
                dlg_frame,
                title="Vista Prèvia de la Política (YAML)",
                icon_type="info",
                on_close=dlg.destroy,
                is_dialog=True,
                height=22,
            ).pack(fill=tk.X)

            txt_box = tk.Frame(dlg_frame, bg=WIN98_GRAY, padx=12, pady=10)
            txt_box.pack(fill=tk.BOTH, expand=True)

            txt = tk.Text(
                txt_box, font=get_win98_font(9), bg=WIN98_WHITE, fg=WIN98_BLACK,
                relief=tk.SUNKEN, bd=2, wrap=tk.NONE
            )
            txt.pack(fill=tk.BOTH, expand=True)
            txt.insert("1.0", yaml.safe_dump(preview_dict, indent=2, sort_keys=False))
            txt.config(state=tk.DISABLED)

            btn_f = tk.Frame(dlg_frame, bg=WIN98_GRAY, pady=8)
            btn_f.pack(anchor=tk.CENTER)
            create_win98_button(btn_f, text="Tancar", command=dlg.destroy, is_default=True, padx=20).pack()

        # 1. Top toolbar
        toolbar = tk.Frame(parent, bg=WIN98_GRAY, pady=4)
        toolbar.pack(fill=tk.X, pady=(0, 4))

        create_win98_button(
            toolbar,
            text=f"🔍 {t('admin_dry_run')}",
            command=self._dry_run,
            is_default=False,
            padx=10,
        ).pack(side=tk.LEFT, padx=4)

        self.policy_status_label = tk.Label(
            toolbar,
            text="💾 Desat automàtic",
            font=get_win98_font(8),
            fg=WIN98_DARK,
            bg=WIN98_GRAY,
        )
        self.policy_status_label.pack(side=tk.LEFT, padx=12)

        create_win98_button(
            toolbar,
            text=f"👁️ {t('policy_view_yaml_btn')}",
            command=view_yaml_popup,
            is_default=False,
            padx=10,
        ).pack(side=tk.RIGHT, padx=4)

        # 2. General Settings Frame (Etched groove Win98 GroupBox)
        general_frame = create_win98_groupbox(parent, t("policy_general_title"))
        general_frame.pack(fill=tk.X, pady=4)

        cb1 = tk.Checkbutton(
            general_frame,
            text=t("policy_dry_run"),
            variable=self.policy_dry_run_var,
            font=get_win98_font(9),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
            selectcolor=WIN98_WHITE,
            activebackground=WIN98_GRAY,
            command=auto_save,
        )
        cb1.grid(row=0, column=0, sticky=tk.W, padx=8, pady=2)

        cb2 = tk.Checkbutton(
            general_frame,
            text=t("policy_always_clean_boot"),
            variable=self.policy_clean_boot_var,
            font=get_win98_font(9),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
            selectcolor=WIN98_WHITE,
            activebackground=WIN98_GRAY,
            command=auto_save,
        )
        cb2.grid(row=0, column=1, sticky=tk.W, padx=8, pady=2)

        cb3 = tk.Checkbutton(
            general_frame,
            text=t("policy_secure_delete"),
            variable=self.policy_secure_del_var,
            font=get_win98_font(9),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
            selectcolor=WIN98_WHITE,
            activebackground=WIN98_GRAY,
            command=auto_save,
        )
        cb3.grid(row=1, column=0, sticky=tk.W, padx=8, pady=2)

        ret_frame = tk.Frame(general_frame, bg=WIN98_GRAY)
        ret_frame.grid(row=1, column=1, sticky=tk.W, padx=8, pady=2)

        tk.Label(
            ret_frame,
            text=t("policy_retention_days"),
            font=get_win98_font(9),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
        ).pack(side=tk.LEFT)

        ret_spinbox = tk.Spinbox(
            ret_frame,
            from_=1,
            to_=3650,
            textvariable=self.policy_retention_var,
            width=6,
            font=get_win98_font(9),
            bg=WIN98_WHITE,
            fg=WIN98_BLACK,
            insertbackground=WIN98_BLACK,
            relief=tk.SUNKEN,
            bd=2,
            command=auto_save,
        )
        ret_spinbox.pack(side=tk.LEFT, padx=6)
        ret_spinbox.bind("<FocusOut>", lambda e: auto_save())
        ret_spinbox.bind("<Return>", lambda e: auto_save())

        cb4 = tk.Checkbutton(
            general_frame,
            text=t("policy_thorough_log"),
            variable=self.policy_thorough_log_var,
            font=get_win98_font(9),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
            selectcolor=WIN98_WHITE,
            activebackground=WIN98_GRAY,
            command=auto_save,
        )
        cb4.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=8, pady=2)

        # 3. Targets List Frame (Etched groove Win98 GroupBox)
        targets_frame = create_win98_groupbox(parent, t("policy_targets_title"))
        targets_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        # 4. Target Action Buttons Panel (packed FIRST with side=RIGHT so it is always allocated space)
        btn_box = tk.Frame(targets_frame, bg=WIN98_GRAY)
        btn_box.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))

        tree_box = tk.Frame(targets_frame, bg=WIN98_GRAY, relief=tk.SUNKEN, bd=2)
        tree_box.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        columns = ("enabled", "os", "name", "category", "strategy", "patterns", "description")
        self.policy_tree = ttk.Treeview(tree_box, columns=columns, show="headings", height=8)

        self.policy_tree.heading("enabled", text=t("policy_col_status"))
        self.policy_tree.heading("os", text=t("policy_col_os"))
        self.policy_tree.heading("name", text=t("policy_col_name"))
        self.policy_tree.heading("category", text=t("policy_col_category"))
        self.policy_tree.heading("strategy", text=t("policy_col_strategy"))
        self.policy_tree.heading("patterns", text=t("policy_col_patterns"))
        self.policy_tree.heading("description", text=t("policy_col_desc"))

        self.policy_tree.column("enabled", width=65, minwidth=50, anchor=tk.CENTER)
        self.policy_tree.column("os", width=60, minwidth=50, anchor=tk.CENTER)
        self.policy_tree.column("name", width=115, minwidth=80)
        self.policy_tree.column("category", width=120, minwidth=90)
        self.policy_tree.column("strategy", width=80, minwidth=70, anchor=tk.CENTER)
        self.policy_tree.column("patterns", width=140, minwidth=100)
        self.policy_tree.column("description", width=110, minwidth=80)

        p_scrolly = ttk.Scrollbar(tree_box, orient=tk.VERTICAL, command=self.policy_tree.yview)
        p_scrollx = ttk.Scrollbar(tree_box, orient=tk.HORIZONTAL, command=self.policy_tree.xview)
        self.policy_tree.configure(yscrollcommand=p_scrolly.set, xscrollcommand=p_scrollx.set)

        self.policy_tree.grid(row=0, column=0, sticky="nsew")
        p_scrolly.grid(row=0, column=1, sticky="ns")
        p_scrollx.grid(row=1, column=0, sticky="ew")
        tree_box.grid_rowconfigure(0, weight=1)
        tree_box.grid_columnconfigure(0, weight=1)

        def refresh_policy_tree() -> None:
            for item in self.policy_tree.get_children():
                self.policy_tree.delete(item)
            for idx, target in enumerate(self.targets_list):
                status_text = "🟢 Actiu" if target.get("enabled", False) else "⚪ Inactiu"
                pats = target.get("patterns", [])
                pats_str = ", ".join(pats) if isinstance(pats, list) else str(pats)
                self.policy_tree.insert(
                    "",
                    tk.END,
                    iid=str(idx),
                    values=(
                        status_text,
                        target.get("os", "ALL"),
                        target.get("name", ""),
                        target.get("category", ""),
                        target.get("strategy", "STANDARD"),
                        pats_str,
                        target.get("description", ""),
                    ),
                )

        def get_selected_target_index() -> int | None:
            selected = self.policy_tree.selection()
            if not selected:
                messagebox.showwarning("Atenció", "Cal seleccionar un objectiu de la llista.", parent=self.window)
                return None
            try:
                return int(selected[0])
            except ValueError:
                return None

        def toggle_selected_target() -> None:
            idx = get_selected_target_index()
            if idx is not None and 0 <= idx < len(self.targets_list):
                cur = self.targets_list[idx].get("enabled", False)
                self.targets_list[idx]["enabled"] = not cur
                refresh_policy_tree()
                auto_save()

        def enable_all_targets() -> None:
            for target in self.targets_list:
                target["enabled"] = True
            refresh_policy_tree()
            auto_save()

        def disable_all_targets() -> None:
            for target in self.targets_list:
                target["enabled"] = False
            refresh_policy_tree()
            auto_save()

        def delete_selected_target() -> None:
            idx = get_selected_target_index()
            if idx is not None and 0 <= idx < len(self.targets_list):
                target_name = self.targets_list[idx].get("name", "")
                if messagebox.askyesno("Confirmació", f"Vols eliminar l'objectiu '{target_name}'?", parent=self.window):
                    del self.targets_list[idx]
                    refresh_policy_tree()
                    auto_save()

        def open_target_editor(edit_idx: int | None = None) -> None:
            is_edit = edit_idx is not None and 0 <= edit_idx < len(self.targets_list)
            target_data = self.targets_list[edit_idx] if is_edit else {}

            dlg = tk.Toplevel(self.window)
            dlg.title("Editar Objectiu de Neteja" if is_edit else "Afegir Nou Objectiu")
            dlg.geometry("490x475")
            dlg.resizable(False, False)
            dlg.configure(bg=WIN98_GRAY)
            dlg.attributes("-topmost", True)

            dlg_frame = create_win98_window_frame(dlg, bd=2)
            dlg_frame.pack(fill=tk.BOTH, expand=True)

            Win98TitleBar(
                dlg_frame,
                title="Editar Objectiu" if is_edit else "Nou Objectiu de Neteja",
                icon_type="cleaner",
                on_close=dlg.destroy,
                is_dialog=True,
                height=22,
            ).pack(fill=tk.X)

            form = tk.Frame(dlg_frame, bg=WIN98_GRAY, padx=16, pady=12)
            form.pack(fill=tk.BOTH, expand=True)

            # Name
            tk.Label(form, text="Nom:", font=get_win98_font(9, bold=True), fg=WIN98_BLACK, bg=WIN98_GRAY).grid(
                row=0, column=0, sticky=tk.W, pady=4
            )
            name_var = tk.StringVar(value=target_data.get("name", ""))
            create_win98_entry(form, textvariable=name_var, width=32).grid(
                row=0, column=1, sticky=tk.W, pady=4, padx=5
            )

            # OS (Dropdown)
            tk.Label(form, text="OS:", font=get_win98_font(9, bold=True), fg=WIN98_BLACK, bg=WIN98_GRAY).grid(
                row=1, column=0, sticky=tk.W, pady=4
            )
            os_options = ["Linux", "Windows", "macOS", "ALL"]
            os_var = tk.StringVar(value=target_data.get("os", "Linux"))
            os_combo = ttk.Combobox(form, textvariable=os_var, values=os_options, state="readonly", width=30)
            os_combo.grid(row=1, column=1, sticky=tk.W, pady=4, padx=5)

            # Category (Dropdown)
            tk.Label(form, text="Categoria:", font=get_win98_font(9, bold=True), fg=WIN98_BLACK, bg=WIN98_GRAY).grid(
                row=2, column=0, sticky=tk.W, pady=4
            )
            cat_categories = [
                "USER_DOCUMENTS",
                "BROWSER_PROFILES",
                "TEMP_AND_CACHE",
                "RECENT_FILES",
                "CREDENTIALS",
                "SHELL_HISTORY",
                "DESKTOP_SHORTCUTS",
                "RECYCLE_BIN",
                "CLOUD_SYNC",
                "GOLDEN_PROFILE",
                "CUSTOM",
            ]
            cat_var = tk.StringVar(value=target_data.get("category", "USER_DOCUMENTS"))
            cat_combo = ttk.Combobox(form, textvariable=cat_var, values=cat_categories, state="readonly", width=30)
            cat_combo.grid(row=2, column=1, sticky=tk.W, pady=4, padx=5)

            # Strategy (Dropdown)
            tk.Label(form, text="Estratègia:", font=get_win98_font(9, bold=True), fg=WIN98_BLACK, bg=WIN98_GRAY).grid(
                row=3, column=0, sticky=tk.W, pady=4
            )
            from netejator98.sanitisation.domain.strategy import DeletionStrategy
            strat_options = [s.value for s in DeletionStrategy]
            strat_var = tk.StringVar(value=target_data.get("strategy", "STANDARD"))
            strat_combo = ttk.Combobox(form, textvariable=strat_var, values=strat_options, state="readonly", width=30)
            strat_combo.grid(row=3, column=1, sticky=tk.W, pady=4, padx=5)

            # Enabled (Checkbox)
            enabled_var = tk.BooleanVar(value=target_data.get("enabled", True))
            tk.Checkbutton(
                form,
                text="Objectiu actiu per a la neteja",
                variable=enabled_var,
                font=get_win98_font(9),
                fg=WIN98_BLACK,
                bg=WIN98_GRAY,
                selectcolor=WIN98_WHITE,
                activebackground=WIN98_GRAY,
            ).grid(row=4, column=1, sticky=tk.W, pady=4, padx=5)

            # Description
            tk.Label(form, text="Descripció:", font=get_win98_font(9), fg=WIN98_BLACK, bg=WIN98_GRAY).grid(
                row=5, column=0, sticky=tk.W, pady=4
            )
            desc_var = tk.StringVar(value=target_data.get("description", ""))
            create_win98_entry(form, textvariable=desc_var, width=32).grid(
                row=5, column=1, sticky=tk.W, pady=4, padx=5
            )

            # Patterns (Text area)
            tk.Label(form, text="Patrons (1/línia):", font=get_win98_font(9, bold=True), fg=WIN98_BLACK, bg=WIN98_GRAY).grid(
                row=6, column=0, sticky=tk.NW, pady=4
            )
            pat_text = tk.Text(
                form, height=4, width=32, bg=WIN98_WHITE, fg=WIN98_BLACK,
                insertbackground=WIN98_BLACK, wrap=tk.NONE, relief=tk.SUNKEN, bd=2
            )
            pat_text.grid(row=6, column=1, sticky=tk.W, pady=4, padx=5)
            existing_pats = target_data.get("patterns", [])
            if isinstance(existing_pats, list):
                pat_text.insert("1.0", "\n".join(existing_pats))
            else:
                pat_text.insert("1.0", str(existing_pats))

            def save_target() -> None:
                name = name_var.get().strip()
                if not name:
                    messagebox.showerror("Error", "El nom de l'objectiu no pot estar buit.", parent=dlg)
                    return
                raw_pats = [p.strip() for p in pat_text.get("1.0", tk.END).strip().splitlines() if p.strip()]
                if not raw_pats:
                    messagebox.showerror("Error", "Cal indicar almenys un patró de ruta (ex. Desktop/*).", parent=dlg)
                    return

                new_entry = {
                    "name": name,
                    "os": os_var.get(),
                    "category": cat_var.get(),
                    "strategy": strat_var.get(),
                    "enabled": enabled_var.get(),
                    "description": desc_var.get().strip(),
                    "patterns": raw_pats,
                }

                if is_edit and edit_idx is not None:
                    self.targets_list[edit_idx] = new_entry
                else:
                    self.targets_list.append(new_entry)

                refresh_policy_tree()
                auto_save()
                dlg.destroy()

            btn_f = tk.Frame(dlg_frame, bg=WIN98_GRAY, pady=8)
            btn_f.pack(anchor=tk.E, padx=16)
            create_win98_button(btn_f, text="Desar Objectiu", command=save_target, is_default=True, padx=14).pack(side=tk.LEFT, padx=6)
            create_win98_button(btn_f, text="Cancel·lar", command=dlg.destroy, is_default=False, padx=12).pack(side=tk.LEFT)

            _safe_modal_grab(dlg)

        # Right-side action buttons: Add and Delete placed prominently at the top
        create_win98_button(btn_box, text=t("policy_add_btn"), command=lambda: open_target_editor(None), width=16).pack(pady=2)
        create_win98_button(btn_box, text=t("policy_delete_btn"), command=delete_selected_target, width=16).pack(pady=2)
        create_win98_button(btn_box, text=t("policy_edit_btn"), command=lambda: open_target_editor(get_selected_target_index()), width=16).pack(pady=2)
        create_win98_button(btn_box, text=t("policy_toggle_btn"), command=toggle_selected_target, width=16).pack(pady=2)

        # Separator line
        tk.Frame(btn_box, height=2, relief=tk.SUNKEN, bd=1, bg=WIN98_GRAY).pack(fill=tk.X, pady=6)

        create_win98_button(btn_box, text=t("policy_enable_all_btn"), command=enable_all_targets, width=16).pack(pady=2)
        create_win98_button(btn_box, text=t("policy_disable_all_btn"), command=disable_all_targets, width=16).pack(pady=2)

        self.policy_tree.bind("<Double-1>", lambda e: open_target_editor(get_selected_target_index()))
        self.policy_tree.bind("<space>", lambda e: toggle_selected_target())
        self.policy_tree.bind("<Delete>", lambda e: delete_selected_target())

        # 5. Core Policy Load
        def load_policy_data() -> None:
            _dlog("[STEP POLICY-750] Entering load_policy_data()...")
            try:
                policy_data = self.vm.fetch_policy()
                _dlog(f"[STEP POLICY-751] fetch_policy returned {len(policy_data)} keys.")
            except Exception as e:
                _dlog(f"[ERROR POLICY-750] fetch_policy exception: {e}")
                policy_data = {}
            self._current_policy_raw = policy_data
            self.policy_dry_run_var.set(policy_data.get("dry_run", True))
            self.policy_clean_boot_var.set(policy_data.get("always_clean_on_boot", False))
            self.policy_secure_del_var.set(policy_data.get("secure_delete", False))
            self.policy_thorough_log_var.set(policy_data.get("thorough_logging", False))
            self.policy_retention_var.set(str(policy_data.get("retention_days", 365)))
            self.golden_shortcuts = copy.deepcopy(
                policy_data.get(
                    "golden_profile_shortcuts",
                    [{"name": "insestatut.cat", "url": "https://insestatut.cat"}]
                )
            )
            if hasattr(self, "_refresh_golden_tree"):
                self._refresh_golden_tree()

            self.targets_list = copy.deepcopy(policy_data.get("targets", []))
            _dlog(f"[STEP POLICY-752] Refreshing policy tree with {len(self.targets_list)} targets...")
            refresh_policy_tree()
            _dlog("[STEP POLICY-753] Policy tree refreshed successfully.")

        self._load_policy_data = load_policy_data

        load_policy_data()
        _dlog("[STEP POLICY-754] _build_policy_tab completed.")

    def _dry_run(self) -> None:
        res = self.vm.force_clean()
        if res:
            log_info = f"\n\nRegistre detallat guardat a:\n{res.get('log_file_path')}" if res.get('log_file_path') else ""
            msg = (
                f"Resultat de la neteja / simulació:\n\n"
                f"Fitxers eliminats / simulats: {res.get('files_deleted', 0)}\n"
                f"Bytes alliberats: {res.get('bytes_freed', 0)}\n"
                f"Objectius: {', '.join(res.get('targets', []))}"
                f"{log_info}"
            )
            messagebox.showinfo(t("admin_dry_run"), msg, parent=self.window)

    # --------------------------------------------------------------------------
    # Tab 3: Golden Profile (Desktop Web Shortcuts Micro-CRUD)
    # --------------------------------------------------------------------------

    def _build_golden_tab(self, parent: tk.Frame) -> None:
        _dlog("[STEP GOLDEN-800] Entering _build_golden_tab()...")
        container = tk.Frame(parent, bg=WIN98_GRAY, padx=12, pady=10)
        container.pack(fill=tk.BOTH, expand=True)

        # 1. Header with icon and descriptive text
        header_frame = tk.Frame(container, bg=WIN98_GRAY)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        icon_canvas = tk.Canvas(header_frame, width=32, height=32, bg=WIN98_GRAY, highlightthickness=0)
        icon_canvas.pack(side=tk.LEFT, padx=(0, 10))
        draw_win98_icon(icon_canvas, "key", 0, 0, size=32)

        desc_frame = tk.Frame(header_frame, bg=WIN98_GRAY)
        desc_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            desc_frame,
            text=t("golden_heading"),
            font=get_win98_font(10, bold=True),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
        ).pack(anchor=tk.W)

        tk.Label(
            desc_frame,
            text=t("golden_desc"),
            font=get_win98_font(9),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(2, 0))

        # 2. GroupBox with Treeview and Actions
        crud_box = create_win98_groupbox(container, text="Dreceres Web per a l'Escriptori")
        crud_box.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        content_box = tk.Frame(crud_box, bg=WIN98_GRAY, padx=8, pady=8)
        content_box.pack(fill=tk.BOTH, expand=True)

        # Action buttons on right side (packed FIRST with side=RIGHT)
        btn_box = tk.Frame(content_box, bg=WIN98_GRAY, padx=10)
        btn_box.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview (ListView in Details mode)
        tree_frame = tk.Frame(content_box, bg=WIN98_GRAY)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        columns = ("name", "url")
        self.golden_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.golden_tree.heading("name", text=t("golden_col_name"))
        self.golden_tree.heading("url", text=t("golden_col_url"))
        self.golden_tree.column("name", width=220, minwidth=140, stretch=False)
        self.golden_tree.column("url", width=420, minwidth=240, stretch=True)

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.golden_tree.yview)
        self.golden_tree.configure(yscrollcommand=tree_scroll.set)
        self.golden_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        def refresh_golden_tree() -> None:
            for item in self.golden_tree.get_children():
                self.golden_tree.delete(item)
            for idx, sc in enumerate(self.golden_shortcuts):
                self.golden_tree.insert("", tk.END, iid=str(idx), values=(sc.get("name", ""), sc.get("url", "")))

        self._refresh_golden_tree = refresh_golden_tree

        def get_selected_shortcut_index() -> Optional[int]:
            sel = self.golden_tree.selection()
            if not sel:
                return None
            try:
                return int(sel[0])
            except ValueError:
                return None

        def open_shortcut_editor(idx: Optional[int] = None) -> None:
            is_edit = idx is not None and 0 <= idx < len(self.golden_shortcuts)
            cur_name = self.golden_shortcuts[idx]["name"] if is_edit else ""
            cur_url = self.golden_shortcuts[idx]["url"] if is_edit else "https://"

            dlg = tk.Toplevel(self.window)
            dlg.title(t("golden_dlg_edit_title") if is_edit else t("golden_dlg_add_title"))
            dlg.geometry("450x210")
            dlg.resizable(False, False)
            dlg.configure(bg=WIN98_GRAY)
            dlg.attributes("-topmost", True)

            dlg_frame = create_win98_window_frame(dlg, bd=2)
            dlg_frame.pack(fill=tk.BOTH, expand=True)

            Win98TitleBar(
                dlg_frame,
                title=t("golden_dlg_edit_title") if is_edit else t("golden_dlg_add_title"),
                icon_type="key",
                on_close=dlg.destroy,
                is_dialog=True,
                height=22,
            ).pack(fill=tk.X)

            form = tk.Frame(dlg_frame, bg=WIN98_GRAY, padx=16, pady=12)
            form.pack(fill=tk.BOTH, expand=True)

            tk.Label(
                form,
                text=t("golden_dlg_name"),
                font=get_win98_font(9),
                fg=WIN98_BLACK,
                bg=WIN98_GRAY,
            ).grid(row=0, column=0, sticky=tk.W, pady=6)
            name_var = tk.StringVar(value=cur_name)
            name_entry = create_win98_entry(form, textvariable=name_var, width=32)
            name_entry.grid(row=0, column=1, pady=6, padx=8, sticky=tk.W)

            tk.Label(
                form,
                text=t("golden_dlg_url"),
                font=get_win98_font(9),
                fg=WIN98_BLACK,
                bg=WIN98_GRAY,
            ).grid(row=1, column=0, sticky=tk.W, pady=6)
            url_var = tk.StringVar(value=cur_url)
            url_entry = create_win98_entry(form, textvariable=url_var, width=32)
            url_entry.grid(row=1, column=1, pady=6, padx=8, sticky=tk.W)

            btn_row = tk.Frame(dlg_frame, bg=WIN98_GRAY, pady=10)
            btn_row.pack(anchor=tk.E, padx=16)

            def save_shortcut() -> None:
                n_val = name_var.get().strip()
                u_val = url_var.get().strip()
                if not n_val or not u_val:
                    messagebox.showerror("Error", "Cal indicar un nom i una adreça URL vàlids.", parent=dlg)
                    return
                if not (u_val.startswith("http://") or u_val.startswith("https://")):
                    u_val = f"https://{u_val}"

                new_sc = {"name": n_val, "url": u_val}
                if is_edit and idx is not None:
                    self.golden_shortcuts[idx] = new_sc
                else:
                    self.golden_shortcuts.append(new_sc)

                refresh_golden_tree()
                if hasattr(self, "_save_current_policy"):
                    self._save_current_policy(quiet=True)
                dlg.destroy()

            create_win98_button(btn_row, text="D'acord", command=save_shortcut, is_default=True, padx=16).pack(side=tk.LEFT, padx=4)
            create_win98_button(btn_row, text="Cancel·la", command=dlg.destroy, is_default=False, padx=14).pack(side=tk.LEFT)

            _safe_modal_grab(dlg)

        def delete_selected_shortcut() -> None:
            idx = get_selected_shortcut_index()
            if idx is None:
                messagebox.showwarning("Atenció", "Selecciona una drecera per eliminar.", parent=self.window)
                return
            confirm = messagebox.askyesno("Confirmació", t("golden_confirm_delete"), parent=self.window)
            if confirm:
                self.golden_shortcuts.pop(idx)
                refresh_golden_tree()
                if hasattr(self, "_save_current_policy"):
                    self._save_current_policy(quiet=True)

        create_win98_button(
            btn_box,
            text=t("golden_add_btn"),
            command=lambda: open_shortcut_editor(None),
            width=16,
        ).pack(pady=3)

        create_win98_button(
            btn_box,
            text=t("golden_edit_btn"),
            command=lambda: open_shortcut_editor(get_selected_shortcut_index()),
            width=16,
        ).pack(pady=3)

        create_win98_button(
            btn_box,
            text=t("golden_delete_btn"),
            command=delete_selected_shortcut,
            width=16,
        ).pack(pady=3)

        self.golden_tree.bind("<Double-1>", lambda e: open_shortcut_editor(get_selected_shortcut_index()))

        refresh_golden_tree()
        _dlog("[STEP GOLDEN-801] _build_golden_tab completed.")

    # --------------------------------------------------------------------------
    # Tab 4: Maintenance
    # --------------------------------------------------------------------------

    def _build_maintenance_tab(self, parent: tk.Frame) -> None:
        _dlog("[STEP MAINT-900] Entering _build_maintenance_tab()...")
        container = tk.Frame(parent, bg=WIN98_GRAY, padx=12, pady=12)
        container.pack(fill=tk.BOTH, expand=True)

        # 1. Daemon & Protection state section
        daemon_frame = create_win98_groupbox(container, t("daemon_state_title"))
        daemon_frame.pack(fill=tk.X, pady=(0, 14))

        current_daemon_enabled = self.vm.get_daemon_enabled()

        daemon_lbl = tk.Label(
            daemon_frame,
            text=t("daemon_status_enabled") if current_daemon_enabled else t("daemon_status_disabled"),
            font=get_win98_font(9, bold=True),
            fg=WIN98_GREEN if current_daemon_enabled else WIN98_RED,
            bg=WIN98_GRAY,
        )
        daemon_lbl.pack(anchor=tk.W, pady=(4, 8))

        def do_toggle_daemon() -> None:
            new_state = not self.vm.get_daemon_enabled()
            if self.vm.set_daemon_enabled(new_state):
                daemon_lbl.config(
                    text=t("daemon_status_enabled") if new_state else t("daemon_status_disabled"),
                    fg=WIN98_GREEN if new_state else WIN98_RED,
                )
                toggle_btn.config(
                    text=t("daemon_disable_btn") if new_state else t("daemon_enable_btn"),
                )
                messagebox.showinfo("Èxit", "Estat del dimoni actualitzat!", parent=self.window)
            else:
                messagebox.showerror("Error", self.vm.error_message or "Error en canviar l'estat del dimoni", parent=self.window)

        toggle_btn = create_win98_button(
            daemon_frame,
            text=t("daemon_disable_btn") if current_daemon_enabled else t("daemon_enable_btn"),
            command=do_toggle_daemon,
            padx=14,
            pady=4,
        )
        toggle_btn.pack(anchor=tk.W, pady=(0, 4))

        # 2. Immediate Actions section
        fc_frame = create_win98_groupbox(container, "Accions Immediates")
        fc_frame.pack(fill=tk.X, pady=(0, 14))

        create_win98_button(
            fc_frame,
            text=f"🧹 {t('admin_force_clean_button')}",
            command=self._force_clean_action,
            padx=16,
            pady=5,
        ).pack(anchor=tk.W, pady=4)

        # 3. Change password section
        pwd_frame = create_win98_groupbox(container, t("admin_change_pwd_button"))
        pwd_frame.pack(fill=tk.X)

        tk.Label(pwd_frame, text=t("admin_old_pwd"), font=get_win98_font(9), fg=WIN98_BLACK, bg=WIN98_GRAY).grid(
            row=0, column=0, sticky=tk.W, pady=4
        )
        old_pwd_var = tk.StringVar(master=pwd_frame)
        old_pwd_entry = create_win98_entry(pwd_frame, textvariable=old_pwd_var, show="*", width=28)
        old_pwd_entry.grid(row=0, column=1, pady=4, padx=10, sticky=tk.W)

        tk.Label(pwd_frame, text=t("admin_new_pwd"), font=get_win98_font(9), fg=WIN98_BLACK, bg=WIN98_GRAY).grid(
            row=1, column=0, sticky=tk.W, pady=4
        )
        new_pwd_var = tk.StringVar(master=pwd_frame)
        new_pwd_entry = create_win98_entry(pwd_frame, textvariable=new_pwd_var, show="*", width=28)
        new_pwd_entry.grid(row=1, column=1, pady=4, padx=10, sticky=tk.W)

        def do_change_pwd() -> None:
            old_p = old_pwd_entry.get() or old_pwd_var.get()
            new_p = new_pwd_entry.get() or new_pwd_var.get()
            if not old_p or not new_p:
                messagebox.showerror("Error", "Cal emplenar ambdues contrasenyes", parent=self.window)
                return
            if len(new_p) < 8:
                messagebox.showerror("Error", "La nova contrasenya ha de tenir almenys 8 caràcters", parent=self.window)
                return

            if self.vm.change_password(old_p, new_p):
                messagebox.showinfo("Èxit", "Contrasenya d'administrador actualitzada amb èxit!", parent=self.window)
                old_pwd_var.set("")
                new_pwd_var.set("")
            else:
                messagebox.showerror("Error", self.vm.error_message or "Error en canviar la contrasenya", parent=self.window)

        create_win98_button(
            pwd_frame,
            text=t("admin_change_pwd_button"),
            command=do_change_pwd,
            padx=12,
            pady=3,
        ).grid(row=2, column=1, sticky=tk.W, pady=8, padx=10)
        _dlog("[STEP MAINT-901] _build_maintenance_tab completed.")

    def _force_clean_action(self) -> None:
        confirm = messagebox.askyesno(
            "Confirmar neteja",
            "Estàs segur que vols executar la neteja immediata de les dades d'usuari?",
            parent=self.window,
        )
        if confirm:
            res = self.vm.force_clean()
            if res:
                log_info = f"\n\nRegistre detallat guardat a:\n{res.get('log_file_path')}" if res.get('log_file_path') else ""
                messagebox.showinfo(
                    "Neteja completada",
                    f"Fitxers esborrats: {res.get('files_deleted')}\nBytes alliberats: {res.get('bytes_freed')}{log_info}",
                    parent=self.window,
                )
            else:
                messagebox.showerror("Error", "Ha fallat la neteja forçada", parent=self.window)
