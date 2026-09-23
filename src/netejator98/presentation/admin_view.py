"""Administration area presentation view with authentic Windows 98 UX/UI."""

from __future__ import annotations

import copy
import json
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
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


def _safe_modal_grab(window: tk.Toplevel) -> None:
    """Safely acquire modal grab, ignoring or deferring if X11 pointer is temporarily grabbed."""
    def _apply() -> None:
        try:
            if window.winfo_exists():
                window.grab_set()
        except tk.TclError:
            pass

    try:
        window.after(50, _apply)
    except Exception:
        pass


class AdminView:
    """Password-protected administration dialog for system administrators in Windows 98 aesthetic."""

    def __init__(self, view_model: AdminViewModel, parent: Optional[tk.Tk | tk.Toplevel] = None) -> None:
        self.vm = view_model
        self.parent = parent
        self.window: Optional[tk.Toplevel] = None
        self._standalone_root: Optional[tk.Tk] = None

        if self.parent is None:
            if getattr(tk, "_default_root", None) is not None:
                self.parent = tk._default_root
                self._is_standalone = False
            else:
                self._standalone_root = tk.Tk()
                self._standalone_root.withdraw()
                self.parent = self._standalone_root
                self._is_standalone = True
        else:
            self._is_standalone = False

        if self.parent:
            apply_win98_ttk_theme(self.parent)

        self.policy_dry_run_var: Optional[tk.BooleanVar] = None
        self.policy_clean_boot_var: Optional[tk.BooleanVar] = None
        self.policy_secure_del_var: Optional[tk.BooleanVar] = None
        self.policy_thorough_log_var: Optional[tk.BooleanVar] = None
        self.policy_retention_var: Optional[tk.StringVar] = None
        self.golden_shortcuts: list[dict[str, str]] = []

    def show(self) -> None:
        """Prompt for admin authentication or open dashboard if already authenticated."""
        if not self.vm.is_authenticated:
            self._show_login_dialog()
        else:
            self._show_dashboard()

        if self._is_standalone and self._standalone_root:
            self._standalone_root.mainloop()

    # ==========================================================================
    # Admin Authentication Dialog (Windows 98 Security Prompt)
    # ==========================================================================

    def _show_login_dialog(self) -> None:
        dlg = tk.Toplevel(self.parent)
        dlg.title(t("admin_title"))
        dlg.geometry("460x280")
        dlg.resizable(False, False)
        dlg.configure(bg=WIN98_GRAY)
        dlg.attributes("-topmost", True)

        def on_dlg_close() -> None:
            dlg.destroy()
            if self._is_standalone and not self.vm.is_authenticated:
                if self._standalone_root:
                    self._standalone_root.destroy()

        dlg.protocol("WM_DELETE_WINDOW", on_dlg_close)

        # Outer 3D raised border
        frame = create_win98_window_frame(dlg, bd=3)
        frame.pack(fill=tk.BOTH, expand=True)

        is_first = self.vm.is_first_run()
        status_res = self.vm.client.get_status()
        is_offline = status_res.is_err()

        title_text = "Configuració Inicial Administrador" if is_first else t("admin_title")
        sub_text = (
            "Estableix la contrasenya d'administrador (mínim 8 caràcters):"
            if is_first
            else t("admin_password_prompt")
        )

        # Title bar with blue gradient
        Win98TitleBar(
            frame,
            title="Seguretat de Netejator 98",
            icon_type="key",
            on_close=on_dlg_close,
            is_dialog=True,
            height=22,
        ).pack(fill=tk.X)

        body = tk.Frame(frame, bg=WIN98_GRAY, padx=16, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        top_f = tk.Frame(body, bg=WIN98_GRAY)
        top_f.pack(fill=tk.X, pady=(0, 10))

        key_cv = tk.Canvas(top_f, width=36, height=36, bg=WIN98_GRAY, highlightthickness=0, bd=0)
        key_cv.pack(side=tk.LEFT, padx=(0, 12))
        draw_win98_icon(key_cv, "key", 2, 2, size=32)

        hdr_col = tk.Frame(top_f, bg=WIN98_GRAY)
        hdr_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            hdr_col,
            text=title_text,
            font=get_win98_font(10, bold=True),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
            anchor=tk.W,
        ).pack(fill=tk.X)

        tk.Label(
            hdr_col,
            text=sub_text,
            font=get_win98_font(9),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
            wraplength=330,
            justify=tk.LEFT,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(2, 0))

        # Password input
        pwd_f = tk.Frame(body, bg=WIN98_GRAY)
        pwd_f.pack(fill=tk.X, pady=(4, 8))

        tk.Label(
            pwd_f,
            text="Contrasenya:",
            font=get_win98_font(9, bold=True),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
        ).pack(anchor=tk.W, pady=(0, 2))

        pwd_var = tk.StringVar(master=dlg)
        pwd_entry = create_win98_entry(
            pwd_f,
            textvariable=pwd_var,
            show="*",
            width=32,
            font=get_win98_font(10),
        )
        pwd_entry.pack(fill=tk.X, ipady=2)
        pwd_entry.focus_set()

        # Status / Offline indicator (sunken pane)
        status_pane = tk.Frame(body, relief=tk.SUNKEN, bd=1, bg=WIN98_GRAY, padx=6, pady=3)
        status_pane.pack(fill=tk.X, pady=(0, 8))

        initial_hint = (
            "ℹ️ Mode autònom actiu (Sense dimoni de fons)"
            if getattr(self.vm.client, "is_in_process", False)
            else ("⚠️ Dimoni agent fora de línia." if is_offline else "A punt per a l'autenticació.")
        )
        err_label = tk.Label(
            status_pane,
            text=initial_hint,
            font=get_win98_font(8),
            fg=WIN98_RED if is_offline else WIN98_BLACK,
            bg=WIN98_GRAY,
            anchor=tk.W,
        )
        err_label.pack(fill=tk.X)

        # Action Buttons
        btn_frame = tk.Frame(body, bg=WIN98_GRAY)
        btn_frame.pack(anchor=tk.E)

        def do_login() -> None:
            pwd = pwd_entry.get() or pwd_var.get()
            if not pwd:
                err_label.config(text="La contrasenya no pot estar buida", fg=WIN98_RED)
                return

            success = self.vm.authenticate(pwd)
            if success:
                dlg.destroy()
                self._show_dashboard()
            else:
                err_label.config(text=self.vm.error_message or "Autenticació fallida", fg=WIN98_RED)

        pwd_entry.bind("<Return>", lambda e: do_login())
        dlg.bind("<Escape>", lambda e: on_dlg_close())

        create_win98_button(
            btn_frame,
            text=t("admin_login_button"),
            command=do_login,
            is_default=True,
            padx=16,
        ).pack(side=tk.LEFT, padx=6)

        create_win98_button(
            btn_frame,
            text=t("admin_cancel_button"),
            command=on_dlg_close,
            is_default=False,
            padx=12,
        ).pack(side=tk.LEFT)

        _safe_modal_grab(dlg)

    # ==========================================================================
    # Admin Dashboard Window (Windows 98 "System Properties" Style)
    # ==========================================================================

    def _show_dashboard(self) -> None:
        self.window = tk.Toplevel(self.parent)
        self.window.title(t("admin_title"))
        self.window.geometry("920x640")
        self.window.configure(bg=WIN98_GRAY)
        self.window.attributes("-topmost", True)

        apply_win98_ttk_theme(self.window)

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

        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Audit Log
        log_frame = tk.Frame(self.notebook, bg=WIN98_GRAY, padx=6, pady=6)
        self.notebook.add(log_frame, text=f"  {t('admin_tab_logs')}  ")
        self._build_audit_tab(log_frame)

        # Tab 2: Cleaning Policy
        policy_frame = tk.Frame(self.notebook, bg=WIN98_GRAY, padx=6, pady=6)
        self.notebook.add(policy_frame, text=f"  {t('admin_tab_policy')}  ")
        self._build_policy_tab(policy_frame)

        # Tab 3: Golden Profile
        golden_frame = tk.Frame(self.notebook, bg=WIN98_GRAY, padx=6, pady=6)
        self.notebook.add(golden_frame, text=f"  {t('admin_tab_golden')}  ")
        self._build_golden_tab(golden_frame)

        # Tab 4: Maintenance
        maint_frame = tk.Frame(self.notebook, bg=WIN98_GRAY, padx=6, pady=6)
        self.notebook.add(maint_frame, text=f"  {t('admin_tab_maintenance')}  ")
        self._build_maintenance_tab(maint_frame)

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
            except Exception:
                pass

        self.notebook.bind("<<NotebookTabChanged>>", update_active_tab_highlight)
        update_active_tab_highlight()

        # Bottom Property Sheet Control Bar (D'acord, Cancel·la, Aplica)
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
        toolbar = tk.Frame(parent, bg=WIN98_GRAY, pady=6)
        toolbar.pack(fill=tk.X)

        create_win98_button(
            toolbar,
            text="🔄 Refrescar",
            command=self._refresh_logs,
            padx=10,
        ).pack(side=tk.LEFT, padx=4)

        create_win98_button(
            toolbar,
            text=f"🛡 {t('admin_verify_button')}",
            command=self._verify_chain,
            padx=10,
        ).pack(side=tk.LEFT, padx=4)

        create_win98_button(
            toolbar,
            text=f"📁 {t('admin_export_button')}",
            command=self._export_csv,
            padx=10,
        ).pack(side=tk.LEFT, padx=4)

        tree_frame = tk.Frame(parent, bg=WIN98_GRAY, relief=tk.SUNKEN, bd=2)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ("seq", "timestamp", "event", "email", "outcome", "targets")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        self.tree.heading("seq", text="#")
        self.tree.heading("timestamp", text="Data/Hora (UTC)")
        self.tree.heading("event", text="Esdeveniment")
        self.tree.heading("email", text="Usuari")
        self.tree.heading("outcome", text="Resultat")
        self.tree.heading("targets", text="Objectius Netejats")

        self.tree.column("seq", width=40, anchor=tk.CENTER)
        self.tree.column("timestamp", width=160)
        self.tree.column("event", width=160)
        self.tree.column("email", width=180)
        self.tree.column("outcome", width=90, anchor=tk.CENTER)
        self.tree.column("targets", width=240)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Multi-pane Windows 98 Status Bar
        self.audit_status_bar = Win98StatusBar(
            parent,
            panes=[
                {"text": "Total entrades carregades: 0", "weight": 1},
                {"text": "Integritat SHA-256: Verificada", "weight": 0},
                {"text": "INS Estatut", "weight": 0},
            ],
        )
        self.audit_status_bar.pack(fill=tk.X, pady=(2, 0))

        self._refresh_logs()

    def _refresh_logs(self) -> None:
        self.tree.delete(*self.tree.get_children())
        entries = self.vm.fetch_logs()
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
        if hasattr(self, "audit_status_bar"):
            self.audit_status_bar.set_pane_text(0, f"Total entrades carregades: {len(entries)}")

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
            policy_data = self.vm.fetch_policy()
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
            refresh_policy_tree()

        self._load_policy_data = load_policy_data

        load_policy_data()

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

    # --------------------------------------------------------------------------
    # Tab 4: Maintenance
    # --------------------------------------------------------------------------

    def _build_maintenance_tab(self, parent: tk.Frame) -> None:
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
