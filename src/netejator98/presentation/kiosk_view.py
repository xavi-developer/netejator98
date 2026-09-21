"""Full-screen, frameless, always-on-top Kiosk view with authentic Windows 98 UX/UI."""

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from netejator98.presentation.i18n import get_language, set_language, t
from netejator98.presentation.view_models import KioskViewModel
from netejator98.presentation.win98_theme import (
    WIN98_BLACK,
    WIN98_BLUE_START,
    WIN98_DARK,
    WIN98_GRAY,
    WIN98_LIGHT,
    WIN98_RED,
    WIN98_TEAL,
    WIN98_WHITE,
    WIN98_YELLOW,
    Win98TitleBar,
    apply_win98_ttk_theme,
    create_win98_button,
    create_win98_entry,
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


class KioskView:
    """Full-screen non-closable kiosk prompt blocking desktop with Windows 98 UX/UI."""

    def __init__(
        self,
        view_model: KioskViewModel,
        on_admin_requested: Optional[Callable[[], None]] = None,
        root: Optional[tk.Tk] = None,
    ) -> None:
        self.vm = view_model
        self.on_admin_requested = on_admin_requested
        self.root = root or tk.Tk()

        # Apply Windows 98 styling
        apply_win98_ttk_theme(self.root)

        self._clock_timer_id: Optional[str] = None

        self._configure_window()
        self._build_ui()
        self.vm.on_state_changed = self._on_vm_changed

    def _configure_window(self) -> None:
        self.root.title(t("app_title"))
        # Frameless and full-screen on desktop
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=WIN98_TEAL)

        # Disable closing via window manager
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        # Intercept Alt+F4 / Escape
        self.root.bind("<Alt-F4>", lambda e: "break")
        self.root.bind("<Escape>", lambda e: "break")

        # Admin emergency escape shortcut (Ctrl+Alt+A)
        self.root.bind("<Control-Alt-a>", lambda e: self._trigger_admin())
        self.root.bind("<Control-Alt-A>", lambda e: self._trigger_admin())

    # ==========================================================================
    # Main UI Construction
    # ==========================================================================

    def _build_ui(self) -> None:
        # 1. Desktop background & Admin Desktop Icon on left side
        self._build_desktop_icons()

        # 2. Windows 98 Taskbar at bottom
        self._build_taskbar()

        # 3. Centered "Log On to Windows 98" dialog box
        self._build_logon_dialog()

    # --------------------------------------------------------------------------
    # Desktop Icon: Access to Admin Window (Left margin of screen)
    # --------------------------------------------------------------------------

    def _build_desktop_icons(self) -> None:
        icons_frame = tk.Frame(self.root, bg=WIN98_TEAL)
        icons_frame.place(x=20, y=20)

        admin_item_frame = tk.Frame(icons_frame, bg=WIN98_TEAL, cursor="hand2", padx=4, pady=4)
        admin_item_frame.pack(anchor=tk.W)

        cv = tk.Canvas(admin_item_frame, width=40, height=40, bg=WIN98_TEAL, highlightthickness=0, bd=0, cursor="hand2")
        cv.pack()
        draw_win98_icon(cv, "admin", 4, 4, size=32)

        lbl = tk.Label(
            admin_item_frame,
            text=f"{t('admin_button')}\n(Ctrl+Alt+A)",
            font=get_win98_font(8, bold=True),
            fg=WIN98_WHITE,
            bg=WIN98_TEAL,
            wraplength=100,
            justify=tk.CENTER,
            cursor="hand2",
        )
        lbl.pack(pady=(2, 0))

        # Clicking or double-clicking launches the Admin window
        admin_item_frame.bind("<Button-1>", lambda e: self._trigger_admin())
        cv.bind("<Button-1>", lambda e: self._trigger_admin())
        lbl.bind("<Button-1>", lambda e: self._trigger_admin())
        admin_item_frame.bind("<Double-Button-1>", lambda e: self._trigger_admin())
        cv.bind("<Double-Button-1>", lambda e: self._trigger_admin())
        lbl.bind("<Double-Button-1>", lambda e: self._trigger_admin())

    # --------------------------------------------------------------------------
    # Bottom Windows 98 Taskbar
    # --------------------------------------------------------------------------

    def _build_taskbar(self) -> None:
        # Taskbar container (28px height, raised 3D border)
        self.taskbar = tk.Frame(self.root, bg=WIN98_GRAY, height=28, bd=2, relief=tk.RAISED)
        self.taskbar.pack_propagate(False)
        self.taskbar.place(relx=0, rely=1.0, relwidth=1.0, anchor=tk.SW)

        # Active Window Taskbar Button (Sunken tab for Logon window)
        active_tab = tk.Frame(self.taskbar, relief=tk.SUNKEN, bd=2, bg=WIN98_LIGHT, padx=8)
        active_tab.pack(side=tk.LEFT, fill=tk.Y, pady=2, padx=4)

        tab_icon = tk.Canvas(active_tab, width=16, height=16, bg=WIN98_LIGHT, highlightthickness=0, bd=0)
        tab_icon.pack(side=tk.LEFT, padx=(0, 4))
        draw_win98_icon(tab_icon, "key", 0, 0, size=16)

        tab_lbl = tk.Label(
            active_tab,
            text="Inici de sessió a Netejator 98",
            font=get_win98_font(8, bold=True),
            bg=WIN98_LIGHT,
            fg=WIN98_BLACK,
        )
        tab_lbl.pack(side=tk.LEFT)

        # System Tray (Sunken pane on right)
        tray_frame = tk.Frame(self.taskbar, relief=tk.SUNKEN, bd=1, bg=WIN98_GRAY, padx=6)
        tray_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=4, pady=2)

        # Language indicator badge (CA / ES / EN)
        self.lang_badge = tk.Label(
            tray_frame,
            text=get_language().upper(),
            font=get_win98_font(8, bold=True),
            bg=WIN98_GRAY,
            fg=WIN98_BLACK,
            cursor="hand2",
            padx=4,
        )
        self.lang_badge.pack(side=tk.LEFT, padx=3)
        self.lang_badge.bind("<Button-1>", lambda e: self._cycle_language())

        # Real-time digital clock
        self.clock_lbl = tk.Label(
            tray_frame,
            text="",
            font=get_win98_font(8),
            bg=WIN98_GRAY,
            fg=WIN98_BLACK,
            padx=4,
        )
        self.clock_lbl.pack(side=tk.LEFT)
        self._update_clock()

    def _update_clock(self) -> None:
        now = datetime.datetime.now().strftime("%H:%M")
        if hasattr(self, "clock_lbl") and self.clock_lbl.winfo_exists():
            self.clock_lbl.config(text=now)
            self._clock_timer_id = self.root.after(1000, self._update_clock)

    def _cycle_language(self) -> None:
        current = get_language()
        next_lang = "es" if current == "ca" else ("en" if current == "es" else "ca")
        set_language(next_lang)
        self.lang_badge.config(text=next_lang.upper())
        self._refresh_translations()

    def _refresh_translations(self) -> None:
        self.root.title(t("app_title"))
        if hasattr(self, "title_bar"):
            self.title_bar.set_title(t("app_title"))
        if hasattr(self, "heading_lbl"):
            self.heading_lbl.config(text=t("kiosk_heading"))
        if hasattr(self, "sub_lbl"):
            self.sub_lbl.config(text=t("kiosk_subheading"))
        if hasattr(self, "submit_btn") and hasattr(self.submit_btn, "btn"):
            self.submit_btn.btn.config(text=t("enter_button"))
        elif hasattr(self, "submit_btn"):
            self.submit_btn.config(text=t("enter_button"))
        if hasattr(self, "bypass_btn"):
            self.bypass_btn.config(text=f"🔑 {t('bypass_button')}")

    # --------------------------------------------------------------------------
    # Centered "Log On to Windows 98" Dialog Box
    # --------------------------------------------------------------------------

    def _build_logon_dialog(self) -> None:
        # Window frame (3D raised outer border)
        self.dialog_frame = create_win98_window_frame(self.root, bd=3)
        self.dialog_frame.place(relx=0.5, rely=0.46, anchor=tk.CENTER, width=540)

        # Windows 98 Title Bar
        self.title_bar = Win98TitleBar(
            self.dialog_frame,
            title=t("app_title"),
            icon_type="key",
            on_close=None,  # Not closable directly on kiosk
            is_dialog=True,
            height=22,
        )
        self.title_bar.pack(fill=tk.X)

        # Dialog Inner Container
        inner = tk.Frame(self.dialog_frame, bg=WIN98_GRAY, padx=16, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        # Layout: Left side retro graphic banner, Right side form
        body_frame = tk.Frame(inner, bg=WIN98_GRAY)
        body_frame.pack(fill=tk.BOTH, expand=True)

        # Left Banner Graphic (Padlock / Key / Netejator 98 emblem)
        left_banner = tk.Canvas(body_frame, width=90, height=180, bg=WIN98_GRAY, highlightthickness=0, bd=0)
        left_banner.pack(side=tk.LEFT, padx=(0, 16), anchor=tk.N)

        # Draw retro graphic: Computer + Key
        draw_win98_icon(left_banner, "computer", 28, 10, size=34)
        draw_win98_icon(left_banner, "key", 32, 50, size=28)
        left_banner.create_text(
            45, 95, text="Netejator", font=get_win98_font(10, bold=True), fill=WIN98_BLUE_START
        )
        left_banner.create_text(
            45, 112, text="98", font=get_win98_font(16, bold=True), fill=WIN98_RED
        )
        left_banner.create_line(10, 130, 80, 130, fill=WIN98_DARK)
        left_banner.create_line(10, 131, 80, 131, fill=WIN98_WHITE)

        # Right Form Area
        right_form = tk.Frame(body_frame, bg=WIN98_GRAY)
        right_form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Heading & Subheading
        self.heading_lbl = tk.Label(
            right_form,
            text=t("kiosk_heading"),
            font=get_win98_font(10, bold=True),
            bg=WIN98_GRAY,
            fg=WIN98_BLACK,
            anchor=tk.W,
        )
        self.heading_lbl.pack(fill=tk.X, pady=(0, 4))

        self.sub_lbl = tk.Label(
            right_form,
            text=t("kiosk_subheading"),
            font=get_win98_font(9),
            bg=WIN98_GRAY,
            fg=WIN98_BLACK,
            wraplength=380,
            justify=tk.LEFT,
            anchor=tk.W,
        )
        self.sub_lbl.pack(fill=tk.X, pady=(0, 12))

        # Email entry prompt
        prompt_frame = tk.Frame(right_form, bg=WIN98_GRAY)
        prompt_frame.pack(fill=tk.X, pady=(0, 8))

        lbl_email = tk.Label(
            prompt_frame,
            text="Nom d'usuari / Correu:",
            font=get_win98_font(9, bold=True),
            bg=WIN98_GRAY,
            fg=WIN98_BLACK,
            anchor=tk.W,
        )
        lbl_email.pack(anchor=tk.W, pady=(0, 3))

        self.email_var = tk.StringVar(master=self.root)
        self.email_entry = create_win98_entry(
            prompt_frame,
            textvariable=self.email_var,
            width=36,
            font=get_win98_font(10),
        )
        self.email_entry.pack(fill=tk.X, ipady=3)
        self.email_entry.focus_set()
        self.email_entry.bind("<Return>", lambda e: self._on_submit())

        # Etched groove line above buttons
        tk.Frame(right_form, height=2, bd=1, relief=tk.SUNKEN, bg=WIN98_GRAY).pack(fill=tk.X, pady=(12, 12))

        # Action Buttons Row (D'acord [default with black border], Ometre, Administració)
        btn_row = tk.Frame(right_form, bg=WIN98_GRAY)
        btn_row.pack(fill=tk.X)

        # Default submit button [ D'acord ]
        self.submit_btn = create_win98_button(
            btn_row,
            text=t("enter_button"),
            command=self._on_submit,
            is_default=True,
            padx=16,
            pady=3,
        )
        self.submit_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Bypass button [ Ometre... ]
        self.bypass_btn = create_win98_button(
            btn_row,
            text=f"🔑 {t('bypass_button')}",
            command=self._on_bypass,
            is_default=False,
            padx=8,
            pady=3,
        )
        self.bypass_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Discreet Admin button [ Administració... ]
        admin_btn = create_win98_button(
            btn_row,
            text=f"⚙ {t('admin_button')}",
            command=self._trigger_admin,
            is_default=False,
            padx=8,
            pady=3,
        )
        admin_btn.pack(side=tk.RIGHT)

        # Status and Error Message Bar (Sunken retro pane)
        self.status_pane = tk.Frame(self.dialog_frame, bg=WIN98_GRAY, bd=1, relief=tk.SUNKEN, padx=6, pady=4)
        self.status_pane.pack(fill=tk.X, padx=4, pady=(0, 4))

        self.status_lbl = tk.Label(
            self.status_pane,
            text="",
            font=get_win98_font(8),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
            anchor=tk.W,
            wraplength=480,
        )
        self.status_lbl.pack(fill=tk.X)

        # Daemon disabled indicator
        self.daemon_badge = tk.Label(
            self.dialog_frame,
            text=t("daemon_disabled_badge") if not self.vm.daemon_enabled else "",
            font=get_win98_font(8, italic=True),
            fg=WIN98_RED,
            bg=WIN98_GRAY,
        )
        self.daemon_badge.pack(pady=(0, 4))

    # ==========================================================================
    # Handlers & Actions
    # ==========================================================================

    def _on_submit(self) -> None:
        email = self.email_entry.get() if hasattr(self, "email_entry") else self.email_var.get()
        if not email:
            email = self.email_var.get()

        # Disable button during submission
        if hasattr(self.submit_btn, "config"):
            self.submit_btn.config(state=tk.DISABLED)
        self.root.update()

        success = self.vm.submit_email(email)

        if hasattr(self.submit_btn, "config"):
            self.submit_btn.config(state=tk.NORMAL)

        if success:
            # Unlock workstation and destroy kiosk window
            if self._clock_timer_id:
                try:
                    self.root.after_cancel(self._clock_timer_id)
                except Exception:
                    pass
            self.root.destroy()

    def _on_bypass(self) -> None:
        """Prompt for admin password with Windows 98 dialog to access PC without cleaning."""
        dlg = tk.Toplevel(self.root)
        dlg.title(t("bypass_title"))
        dlg.geometry("440x220")
        dlg.resizable(False, False)
        dlg.configure(bg=WIN98_GRAY)
        dlg.attributes("-topmost", True)

        # 3D raised window border
        frame = create_win98_window_frame(dlg, bd=2)
        frame.pack(fill=tk.BOTH, expand=True)

        title_bar = Win98TitleBar(
            frame,
            title=t("bypass_title"),
            icon_type="key",
            on_close=dlg.destroy,
            is_dialog=True,
            height=22,
        )
        title_bar.pack(fill=tk.X)

        body = tk.Frame(frame, bg=WIN98_GRAY, padx=16, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        top_row = tk.Frame(body, bg=WIN98_GRAY)
        top_row.pack(fill=tk.X, pady=(0, 8))

        key_cv = tk.Canvas(top_row, width=32, height=32, bg=WIN98_GRAY, highlightthickness=0, bd=0)
        key_cv.pack(side=tk.LEFT, padx=(0, 10))
        draw_win98_icon(key_cv, "key", 0, 0, size=32)

        tk.Label(
            top_row,
            text=t("bypass_prompt"),
            font=get_win98_font(9),
            fg=WIN98_BLACK,
            bg=WIN98_GRAY,
            wraplength=340,
            justify=tk.LEFT,
        ).pack(side=tk.LEFT, fill=tk.X)

        pwd_var = tk.StringVar(master=dlg)
        pwd_entry = create_win98_entry(body, textvariable=pwd_var, show="*", width=28, font=get_win98_font(10))
        pwd_entry.pack(fill=tk.X, pady=(4, 8), ipady=2)
        pwd_entry.focus_set()

        dlg_err = tk.Label(body, text="", font=get_win98_font(8), fg=WIN98_RED, bg=WIN98_GRAY)
        dlg_err.pack(fill=tk.X, pady=(0, 6))

        btn_row = tk.Frame(body, bg=WIN98_GRAY)
        btn_row.pack(anchor=tk.E)

        def do_bypass() -> None:
            pwd = pwd_entry.get() or pwd_var.get()
            if not pwd:
                dlg_err.config(text=t("admin_password_required"))
                return

            success = self.vm.bypass_with_admin_password(pwd)
            if success:
                dlg.destroy()
                if self._clock_timer_id:
                    try:
                        self.root.after_cancel(self._clock_timer_id)
                    except Exception:
                        pass
                self.root.destroy()
            else:
                dlg_err.config(text=self.vm.error_message or "Autenticació fallida")

        pwd_entry.bind("<Return>", lambda e: do_bypass())
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        create_win98_button(btn_row, text="D'acord", command=do_bypass, is_default=True, padx=16).pack(side=tk.LEFT, padx=6)
        create_win98_button(btn_row, text=t("admin_cancel_button"), command=dlg.destroy, is_default=False, padx=12).pack(side=tk.LEFT)

        _safe_modal_grab(dlg)

    def _show_about_dialog(self) -> None:
        """Show classic Windows 98 About dialog."""
        dlg = tk.Toplevel(self.root)
        dlg.title("Quant a Netejator 98")
        dlg.geometry("400x260")
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
        tk.Label(title_col, text="Versió 1.0 (Edició Institucional)", font=get_win98_font(9), fg=WIN98_BLACK, bg=WIN98_GRAY).pack(anchor=tk.W)

        tk.Frame(body, height=2, relief=tk.SUNKEN, bd=1, bg=WIN98_GRAY).pack(fill=tk.X, pady=8)

        desc = (
            "Sistema de neteja automàtica d'equips compartits per a centres educatius.\n\n"
            "Arquitectura DDD Hexagonal amb registre criptogràfic asimètric (X25519) i cadena SHA-256."
        )
        tk.Label(body, text=desc, font=get_win98_font(8), fg=WIN98_BLACK, bg=WIN98_GRAY, justify=tk.LEFT, wraplength=350).pack(fill=tk.X, pady=(0, 12))

        btn_box = tk.Frame(body, bg=WIN98_GRAY)
        btn_box.pack(anchor=tk.CENTER)
        create_win98_button(btn_box, text="D'acord", command=dlg.destroy, is_default=True, padx=20).pack()

        _safe_modal_grab(dlg)

    def _on_vm_changed(self) -> None:
        if self.vm.error_message:
            self.status_lbl.config(text=f"⚠️ {self.vm.error_message}", fg=WIN98_RED)
        elif self.vm.status_message:
            self.status_lbl.config(text=f"ℹ️ {self.vm.status_message}", fg=WIN98_BLACK)
        else:
            self.status_lbl.config(text="")

        if hasattr(self, "daemon_badge"):
            if not self.vm.daemon_enabled:
                self.daemon_badge.config(text=t("daemon_disabled_badge"))
            else:
                self.daemon_badge.config(text="")

        self.root.update_idletasks()

    def _trigger_admin(self) -> None:
        if self.on_admin_requested:
            self.on_admin_requested()

    def show(self) -> None:
        self.root.mainloop()
