"""Windows 98 UI Theme and Component Library for Netejator98.

Provides authentic Windows 98 styling, color palette, 3D beveled borders,
gradient title bars, pixel-art retro icons, and TTK widget theming.
"""

from __future__ import annotations

import os
import sys
import time
import tkinter as tk
from tkinter import font as tkfont, ttk
import traceback
from typing import Any, Callable, Optional


def _theme_dlog(msg: str) -> None:
    """Direct unbuffered write to stderr for theme diagnostics."""
    now_str = time.strftime("%H:%M:%S")
    out = f"[{now_str}] [DEBUG-THEME] {msg}\n"
    try:
        os.write(2, out.encode("utf-8", errors="replace"))
    except Exception:
        pass
    try:
        sys.stderr.flush()
    except Exception:
        pass

# ==============================================================================
# Windows 98 Authentic Color Palette
# ==============================================================================
WIN98_TEAL = "#008080"        # Iconic Desktop background
WIN98_GRAY = "#c0c0c0"        # Standard 3D face / window background
WIN98_LIGHT = "#dfdfdf"       # Light 3D highlight
WIN98_WHITE = "#ffffff"       # Pure 3D highlight / text input background
WIN98_DARK = "#808080"        # Dark 3D shadow
WIN98_BLACK = "#000000"       # Darkest 3D border / main text color
WIN98_BLUE_START = "#000080"  # Active title bar gradient left (Navy)
WIN98_BLUE_END = "#1084d0"    # Active title bar gradient right (Cyan/Sky)
WIN98_TITLE_TEXT = "#ffffff"  # Active title bar text
WIN98_SELECTION = "#000080"   # Selected item background
WIN98_SELECTION_TEXT = "#ffffff"  # Selected item text
WIN98_YELLOW = "#ffff00"      # Retro warning yellow
WIN98_RED = "#cc0000"         # Retro critical red
WIN98_GREEN = "#008000"       # Retro success green
WIN98_GOLD = "#d4af37"        # Retro key gold

# Fallback fonts in order of authentic Windows 98 resemblance
_PREFERRED_FONTS = [
    "MS Sans Serif",
    "Tahoma",
    "Segoe UI",
    "DejaVu Sans",
    "Liberation Sans",
    "Arial",
    "Helvetica",
]

_DETECTED_FONT_FAMILY: Optional[str] = None


def get_win98_font(size: int = 9, bold: bool = False, italic: bool = False) -> tuple[str, int, str]:
    """Return a Tk font tuple matching Windows 98 typography on the current system."""
    global _DETECTED_FONT_FAMILY
    if _DETECTED_FONT_FAMILY is None:
        family = "Tahoma"
        try:
            if getattr(tk, "_default_root", None) is not None:
                _theme_dlog("[FONT] Initial font family detection via tkfont.families()...")
                available = set(tkfont.families())
                _theme_dlog(f"[FONT] tkfont.families() found {len(available)} families.")
                for pref in _PREFERRED_FONTS:
                    if pref in available:
                        family = pref
                        _theme_dlog(f"[FONT] Selected preferred font family: '{family}'")
                        break
        except Exception as e:
            _theme_dlog(f"[FONT-WARN] Exception querying tkfont: {e}")
            family = "Tahoma"
        _DETECTED_FONT_FAMILY = family
    else:
        family = _DETECTED_FONT_FAMILY

    style_parts = []
    if bold:
        style_parts.append("bold")
    if italic:
        style_parts.append("italic")
    style_str = " ".join(style_parts) if style_parts else "normal"

    return (family, size, style_str)


# Pre-defined fonts
WIN98_FONT = ("Tahoma", 9)
WIN98_FONT_BOLD = ("Tahoma", 9, "bold")
WIN98_FONT_TITLE = ("Tahoma", 9, "bold")
WIN98_FONT_HEADER = ("Tahoma", 10, "bold")
WIN98_FONT_BRAND = ("Tahoma", 14, "bold")
WIN98_FONT_MONO = ("Courier New", 9)


def apply_win98_ttk_theme(root_or_style: Optional[Any] = None) -> Optional[ttk.Style]:
    """Configure TTK widgets to replicate Windows 98 3D controls."""
    try:
        if isinstance(root_or_style, ttk.Style):
            style = root_or_style
        else:
            style = ttk.Style(master=root_or_style)
    except Exception:
        return None

    try:
        # Use 'classic' or 'default' engine where color/relief overrides are honored
        available_themes = style.theme_names()
        if "classic" in available_themes:
            style.theme_use("classic")
        elif "default" in available_themes:
            style.theme_use("default")

        font_regular = get_win98_font(9)
        font_bold = get_win98_font(9, bold=True)

        # 1. Base settings
        style.configure(".", background=WIN98_GRAY, foreground=WIN98_BLACK, font=font_regular)

        # 2. Tabs (TNotebook & TNotebook.Tab)
        style.configure("TNotebook", background=WIN98_GRAY, borderwidth=2, relief=tk.RAISED)
        style.configure(
            "TNotebook.Tab",
            background=WIN98_GRAY,
            foreground=WIN98_BLACK,
            font=font_regular,
            padding=[12, 4],
            borderwidth=2,
            relief=tk.RAISED,
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", WIN98_WHITE),
                ("active", WIN98_LIGHT),
                ("!selected", WIN98_GRAY),
            ],
            foreground=[
                ("selected", WIN98_BLUE_START),
                ("active", WIN98_BLACK),
                ("!selected", WIN98_BLACK),
            ],
            font=[
                ("selected", font_bold),
                ("!selected", font_regular),
            ],
            relief=[
                ("selected", tk.RAISED),
                ("!selected", tk.GROOVE),
            ],
        )

        # 3. Treeview (Windows 98 Details / ListView)
        style.configure(
            "Treeview",
            background=WIN98_WHITE,
            fieldbackground=WIN98_WHITE,
            foreground=WIN98_BLACK,
            font=font_regular,
            borderwidth=2,
            relief=tk.SUNKEN,
            rowheight=20,
        )
        style.map(
            "Treeview",
            background=[("selected", WIN98_SELECTION)],
            foreground=[("selected", WIN98_SELECTION_TEXT)],
        )
        style.configure(
            "Treeview.Heading",
            background=WIN98_GRAY,
            foreground=WIN98_BLACK,
            font=font_bold,
            relief=tk.RAISED,
            borderwidth=2,
            padding=[4, 2],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", WIN98_LIGHT), ("pressed", WIN98_GRAY)],
            relief=[("pressed", tk.SUNKEN)],
        )

        # 4. Scrollbars (3D Gray with dark arrows)
        style.configure(
            "TScrollbar",
            background=WIN98_GRAY,
            troughcolor=WIN98_LIGHT,
            arrowcolor=WIN98_BLACK,
            borderwidth=2,
            relief=tk.RAISED,
        )
        style.map(
            "TScrollbar",
            background=[("pressed", WIN98_DARK), ("active", WIN98_LIGHT)],
            relief=[("pressed", tk.SUNKEN)],
        )

        # 5. Combobox
        style.configure(
            "TCombobox",
            background=WIN98_GRAY,
            fieldbackground=WIN98_WHITE,
            foreground=WIN98_BLACK,
            font=font_regular,
            relief=tk.SUNKEN,
            borderwidth=2,
        )

        # 6. Progressbar
        style.configure(
            "TProgressbar",
            background=WIN98_BLUE_START,
            troughcolor=WIN98_LIGHT,
            borderwidth=2,
            relief=tk.SUNKEN,
        )
        return style
    except Exception:
        return style


# ==============================================================================
# Canvas-drawn Retro Pixel Art Icons
# ==============================================================================

def _draw_win98_icon_impl(canvas: tk.Canvas, icon_type: str, x: int, y: int, size: int, s: float) -> None:
    if icon_type == "flag":
        # Windows 98 4-color flag (Red, Green, Blue, Yellow)
        # Red top-left, Green top-right, Blue bottom-left, Yellow bottom-right
        w, h = 12 * s, 12 * s
        canvas.create_rectangle(x, y, x + w, y + h, fill="#ff3333", outline=WIN98_BLACK)
        canvas.create_rectangle(x + w + 2 * s, y, x + 2 * w + 2 * s, y + h, fill="#33cc33", outline=WIN98_BLACK)
        canvas.create_rectangle(x, y + h + 2 * s, x + w, y + 2 * h + 2 * s, fill="#3366ff", outline=WIN98_BLACK)
        canvas.create_rectangle(x + w + 2 * s, y + h + 2 * s, x + 2 * w + 2 * s, y + 2 * h + 2 * s, fill="#ffcc00", outline=WIN98_BLACK)

    elif icon_type == "computer":
        # Beige CRT monitor + Computer Tower
        # Monitor outer frame
        canvas.create_rectangle(x + 2 * s, y + 2 * s, x + 24 * s, y + 20 * s, fill="#e0dacb", outline=WIN98_BLACK, width=1)
        # Screen (Cyan / Dark Blue)
        canvas.create_rectangle(x + 5 * s, y + 5 * s, x + 21 * s, y + 17 * s, fill="#008080", outline=WIN98_BLACK, width=1)
        # Screen highlight
        canvas.create_line(x + 6 * s, y + 6 * s, x + 12 * s, y + 6 * s, fill="#00ffff")
        # Stand neck
        canvas.create_rectangle(x + 10 * s, y + 20 * s, x + 16 * s, y + 23 * s, fill="#c0bba8", outline=WIN98_BLACK)
        # Stand base
        canvas.create_rectangle(x + 6 * s, y + 23 * s, x + 20 * s, y + 26 * s, fill="#e0dacb", outline=WIN98_BLACK)
        # Tower box on the side
        canvas.create_rectangle(x + 24 * s, y + 6 * s, x + 31 * s, y + 26 * s, fill="#e0dacb", outline=WIN98_BLACK)
        # CD drive & power button
        canvas.create_line(x + 26 * s, y + 10 * s, x + 29 * s, y + 10 * s, fill="#808080")
        canvas.create_oval(x + 27 * s, y + 21 * s, x + 29 * s, y + 23 * s, fill="#00ff00", outline=WIN98_BLACK)

    elif icon_type == "network":
        # Two connected retro PCs
        # Top-left PC
        canvas.create_rectangle(x + 1 * s, y + 2 * s, x + 17 * s, y + 15 * s, fill="#e0dacb", outline=WIN98_BLACK)
        canvas.create_rectangle(x + 3 * s, y + 4 * s, x + 15 * s, y + 13 * s, fill="#000080", outline="")
        # Bottom-right PC
        canvas.create_rectangle(x + 14 * s, y + 14 * s, x + 30 * s, y + 27 * s, fill="#e0dacb", outline=WIN98_BLACK)
        canvas.create_rectangle(x + 16 * s, y + 16 * s, x + 28 * s, y + 25 * s, fill="#000080", outline="")
        # Connecting cable
        canvas.create_line(x + 9 * s, y + 15 * s, x + 9 * s, y + 20 * s, fill=WIN98_BLACK, width=2)
        canvas.create_line(x + 9 * s, y + 20 * s, x + 22 * s, y + 20 * s, fill=WIN98_BLACK, width=2)
        canvas.create_line(x + 22 * s, y + 20 * s, x + 22 * s, y + 14 * s, fill=WIN98_BLACK, width=2)

    elif icon_type == "recycle_bin":
        # Classic wire-mesh wastebasket
        # Top rim
        canvas.create_oval(x + 4 * s, y + 4 * s, x + 28 * s, y + 10 * s, fill="#a0a0a0", outline=WIN98_BLACK)
        # Body
        canvas.create_polygon(
            x + 4 * s, y + 7 * s,
            x + 8 * s, y + 28 * s,
            x + 24 * s, y + 28 * s,
            x + 28 * s, y + 7 * s,
            fill="#808090", outline=WIN98_BLACK
        )
        # Paper sticking out
        canvas.create_polygon(
            x + 8 * s, y + 2 * s,
            x + 18 * s, y + 4 * s,
            x + 14 * s, y + 12 * s,
            fill="#ffffff", outline=WIN98_BLACK
        )
        # Bottom rim
        canvas.create_oval(x + 8 * s, y + 26 * s, x + 24 * s, y + 30 * s, fill="#606070", outline=WIN98_BLACK)

    elif icon_type == "cleaner":
        # Spray bottle / Broom for Netejator98
        # Spray bottle nozzle
        canvas.create_rectangle(x + 8 * s, y + 4 * s, x + 20 * s, y + 9 * s, fill="#000080", outline=WIN98_BLACK)
        canvas.create_polygon(x + 8 * s, y + 9 * s, x + 4 * s, y + 14 * s, x + 8 * s, y + 12 * s, fill="#000080", outline=WIN98_BLACK)
        # Trigger
        canvas.create_line(x + 12 * s, y + 9 * s, x + 10 * s, y + 16 * s, fill=WIN98_BLACK, width=2)
        # Bottle body
        canvas.create_rectangle(x + 10 * s, y + 12 * s, x + 22 * s, y + 28 * s, fill="#008080", outline=WIN98_BLACK)
        # White label
        canvas.create_rectangle(x + 12 * s, y + 16 * s, x + 20 * s, y + 24 * s, fill="#ffffff", outline=WIN98_BLACK)
        canvas.create_text(x + 16 * s, y + 20 * s, text="98", font=("Tahoma", max(6, int(7 * s)), "bold"), fill="#000080")

    elif icon_type == "key":
        # Golden security key
        # Key head (ring)
        canvas.create_oval(x + 4 * s, y + 4 * s, x + 16 * s, y + 16 * s, fill=WIN98_YELLOW, outline="#806000", width=2)
        canvas.create_oval(x + 8 * s, y + 8 * s, x + 12 * s, y + 12 * s, fill=WIN98_GRAY, outline="#806000")
        # Key shaft
        canvas.create_rectangle(x + 14 * s, y + 8 * s, x + 28 * s, y + 12 * s, fill=WIN98_YELLOW, outline="#806000")
        # Teeth
        canvas.create_rectangle(x + 22 * s, y + 12 * s, x + 25 * s, y + 17 * s, fill=WIN98_YELLOW, outline="#806000")
        canvas.create_rectangle(x + 26 * s, y + 12 * s, x + 28 * s, y + 15 * s, fill=WIN98_YELLOW, outline="#806000")

    elif icon_type == "warning":
        # Yellow triangle with exclamation
        canvas.create_polygon(
            x + 16 * s, y + 2 * s,
            x + 2 * s, y + 28 * s,
            x + 30 * s, y + 28 * s,
            fill=WIN98_YELLOW, outline=WIN98_BLACK, width=2
        )
        canvas.create_rectangle(x + 14 * s, y + 10 * s, x + 18 * s, y + 20 * s, fill=WIN98_BLACK)
        canvas.create_rectangle(x + 14 * s, y + 23 * s, x + 18 * s, y + 26 * s, fill=WIN98_BLACK)

    elif icon_type == "error":
        # Red circle with white X
        canvas.create_oval(x + 2 * s, y + 2 * s, x + 30 * s, y + 30 * s, fill=WIN98_RED, outline=WIN98_BLACK, width=2)
        canvas.create_line(x + 9 * s, y + 9 * s, x + 23 * s, y + 23 * s, fill="#ffffff", width=max(2, int(3 * s)))
        canvas.create_line(x + 23 * s, y + 9 * s, x + 9 * s, y + 23 * s, fill="#ffffff", width=max(2, int(3 * s)))

    elif icon_type == "admin":
        # Retro Computer + Golden Gear / Administrative Tool
        canvas.create_rectangle(x + 2 * s, y + 2 * s, x + 24 * s, y + 20 * s, fill="#e0dacb", outline=WIN98_BLACK, width=1)
        canvas.create_rectangle(x + 5 * s, y + 5 * s, x + 21 * s, y + 17 * s, fill="#000080", outline=WIN98_BLACK, width=1)
        canvas.create_line(x + 6 * s, y + 6 * s, x + 12 * s, y + 6 * s, fill="#00ffff")
        canvas.create_rectangle(x + 10 * s, y + 20 * s, x + 16 * s, y + 23 * s, fill="#c0bba8", outline=WIN98_BLACK)
        canvas.create_rectangle(x + 6 * s, y + 23 * s, x + 20 * s, y + 26 * s, fill="#e0dacb", outline=WIN98_BLACK)
        # Golden Gear on bottom right
        canvas.create_oval(x + 16 * s, y + 14 * s, x + 30 * s, y + 28 * s, fill=WIN98_YELLOW, outline="#806000", width=1)
        canvas.create_oval(x + 20 * s, y + 18 * s, x + 26 * s, y + 24 * s, fill=WIN98_TEAL, outline="#806000")
        for gx, gy in [(22, 13), (22, 29), (15, 20), (31, 20)]:
            canvas.create_rectangle(x + (gx - 1) * s, y + (gy - 1) * s, x + (gx + 2) * s, y + (gy + 2) * s, fill=WIN98_YELLOW, outline="#806000")

    elif icon_type == "info":
        # Blue circle with white "i"
        canvas.create_oval(x + 2 * s, y + 2 * s, x + 30 * s, y + 30 * s, fill="#000080", outline=WIN98_BLACK, width=2)
        canvas.create_rectangle(x + 14 * s, y + 7 * s, x + 18 * s, y + 10 * s, fill="#ffffff")
        canvas.create_rectangle(x + 14 * s, y + 13 * s, x + 18 * s, y + 24 * s, fill="#ffffff")

    else:
        # Default small retro square
        canvas.create_rectangle(x + 4 * s, y + 4 * s, x + 28 * s, y + 28 * s, fill=WIN98_GRAY, outline=WIN98_BLACK)
        _theme_dlog(f"[ICON-DRAW] Successfully rendered icon '{icon_type}'.")
    except Exception as e:
        _theme_dlog(f"[ICON-DRAW-ERR] Failed rendering icon '{icon_type}': {e}")
        _theme_dlog(traceback.format_exc())


# ==============================================================================
# Windows 98 Custom Title Bar Component
# ==============================================================================

class Win98TitleBar(tk.Frame):
    """Authentic Windows 98 title bar with gradient canvas and 3D buttons."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "Netejator 98",
        icon_type: Optional[str] = "cleaner",
        on_close: Optional[Callable[[], None]] = None,
        on_min: Optional[Callable[[], None]] = None,
        on_max: Optional[Callable[[], None]] = None,
        is_dialog: bool = False,
        height: int = 24,
    ) -> None:
        super().__init__(parent, bg=WIN98_BLUE_START, height=height)
        self.pack_propagate(False)
        self.title_text = title
        self.icon_type = icon_type
        self.on_close = on_close
        self.on_min = on_min
        self.on_max = on_max
        self.is_dialog = is_dialog
        self.bar_height = height

        # Control Buttons Container (Fixed Frame on the right, not embedded in Canvas)
        has_buttons = (
            (self.on_close is not None)
            or (self.on_max is not None and not self.is_dialog)
            or (self.on_min is not None and not self.is_dialog)
        )
        if has_buttons:
            self.btn_frame = tk.Frame(self, bg=WIN98_BLUE_END)
            self.btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 3), pady=2)

            # Pack in reverse right-to-left order: Close, Max, Min -> Visual order: [_] [□] [✕]
            if self.on_close is not None:
                close_btn = self._create_title_button(self.btn_frame, "✕", self.on_close, bold=True)
                close_btn.pack(side=tk.RIGHT, padx=(2, 0))

            if self.on_max is not None and not self.is_dialog:
                max_btn = self._create_title_button(self.btn_frame, "□", self.on_max, bold=False)
                max_btn.pack(side=tk.RIGHT, padx=(2, 0))

            if self.on_min is not None and not self.is_dialog:
                min_btn = self._create_title_button(self.btn_frame, "_", self.on_min, bold=True)
                min_btn.pack(side=tk.RIGHT, padx=(2, 0))

        # Gradient Canvas (occupies remaining width on the left)
        self.canvas = tk.Canvas(self, height=height, bg=WIN98_BLUE_START, highlightthickness=0, bd=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<Configure>", self._render_gradient)
        _theme_dlog(f"[TITLEBAR] Initialized '{title}' (icon={icon_type}, is_dialog={is_dialog})")

        # Window Dragging support if parent is a window
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.target_window = self._find_toplevel(parent)
        if self.target_window:
            self.canvas.bind("<Button-1>", self._on_drag_start)
            self.canvas.bind("<B1-Motion>", self._on_drag_motion)
            if has_buttons:
                self.btn_frame.bind("<Button-1>", self._on_drag_start)
                self.btn_frame.bind("<B1-Motion>", self._on_drag_motion)

    def _find_toplevel(self, widget: Any) -> Optional[Any]:
        curr: Optional[Any] = widget
        while curr:
            try:
                # Check for window geometry and winfo_x methods
                if hasattr(curr, "geometry") and hasattr(curr, "winfo_x"):
                    return curr
            except Exception:
                pass
            curr = getattr(curr, "master", None)
        return None

    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_motion(self, event: tk.Event) -> None:
        if not self.target_window:
            return
        # Don't drag if fullscreen
        try:
            if hasattr(self.target_window, "attributes") and self.target_window.attributes("-fullscreen"):
                return
        except Exception:
            pass

        try:
            deltax = event.x - self._drag_start_x
            deltay = event.y - self._drag_start_y
            x = self.target_window.winfo_x() + deltax
            y = self.target_window.winfo_y() + deltay
            self.target_window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def set_title(self, new_title: str) -> None:
        self.title_text = new_title
        self._render_gradient()

    def _render_gradient(self, event: Optional[tk.Event] = None) -> None:
        try:
            width = self.canvas.winfo_width() or (event.width if event else 600)
            if width <= 1:
                width = 600

            _theme_dlog(f"[TITLEBAR-GRAD] _render_gradient starting for '{self.title_text}', width={width}")
            self.canvas.delete("all")

            # Draw smooth horizontal gradient from #000080 to #1084d0
            r1, g1, b1 = 0, 0, 128
            r2, g2, b2 = 16, 132, 208
            steps = min(64, max(8, width // 8))

            step_w = width / steps
            for i in range(steps):
                ratio = i / steps
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                color = f"#{r:02x}{g:02x}{b:02x}"
                x0 = i * step_w
                x1 = (i + 1) * step_w + 1
                self.canvas.create_rectangle(x0, 0, x1, self.bar_height, fill=color, outline=color)

            # Draw icon
            text_x = 6
            if self.icon_type:
                draw_win98_icon(self.canvas, self.icon_type, 4, 3, size=18)
                text_x = 26

            # Draw Title Text (Bold White)
            font = get_win98_font(9, bold=True)
            self.canvas.create_text(
                text_x,
                self.bar_height // 2,
                text=self.title_text,
                anchor=tk.W,
                font=font,
                fill=WIN98_TITLE_TEXT,
            )
            _theme_dlog(f"[TITLEBAR-GRAD] _render_gradient completed for '{self.title_text}'.")
        except Exception as e:
            _theme_dlog(f"[TITLEBAR-GRAD-ERR] Exception in _render_gradient: {e}")
            _theme_dlog(traceback.format_exc())

    def _create_title_button(
        self,
        parent: tk.Widget,
        symbol: str,
        command: Callable[[], None],
        bold: bool = False,
    ) -> tk.Button:
        btn = tk.Button(
            parent,
            text=symbol,
            font=("Tahoma", 7, "bold" if bold else "normal"),
            bg=WIN98_GRAY,
            fg=WIN98_BLACK,
            activebackground=WIN98_GRAY,
            activeforeground=WIN98_BLACK,
            relief=tk.RAISED,
            bd=1,
            padx=2,
            pady=0,
            command=command,
        )
        return btn


# ==============================================================================
# Windows 98 Widget Helpers
# ==============================================================================

def create_win98_window_frame(parent: tk.Widget, bd: int = 3) -> tk.Frame:
    """Create a container frame with authentic Windows 98 raised 3D borders."""
    return tk.Frame(parent, bg=WIN98_GRAY, bd=bd, relief=tk.RAISED)


def create_win98_button(
    parent: tk.Widget,
    text: str,
    command: Optional[Callable[[], None]] = None,
    is_default: bool = False,
    width: Optional[int] = None,
    padx: int = 10,
    pady: int = 3,
    state: str = tk.NORMAL,
    font: Optional[tuple] = None,
) -> tk.Widget:
    """Create an authentic Windows 98 button with 3D raised bevel.

    If is_default is True, creates a 1px black outline frame around the button,
    matching the iconic Windows 98 default dialog button.
    """
    _theme_dlog(f"[BTN] Creating button text='{text}', is_default={is_default}")
    try:
        btn_font = font or get_win98_font(9)

        if is_default:
            # Wrapper frame providing the 1px black outline
            outer = tk.Frame(parent, bg=WIN98_BLACK, bd=1)
            btn = tk.Button(
                outer,
                text=text,
                font=btn_font,
                bg=WIN98_GRAY,
                fg=WIN98_BLACK,
                activebackground=WIN98_GRAY,
                activeforeground=WIN98_BLACK,
                relief=tk.RAISED,
                bd=2,
                padx=padx,
                pady=pady,
                width=width,
                state=state,
                command=command,
            )
            btn.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
            # Expose config methods on the outer wrapper for convenience
            setattr(outer, "config", btn.config)
            setattr(outer, "configure", btn.configure)
            setattr(outer, "btn", btn)
            _theme_dlog(f"[BTN] Default button '{text}' created.")
            return outer
        else:
            b = tk.Button(
                parent,
                text=text,
                font=btn_font,
                bg=WIN98_GRAY,
                fg=WIN98_BLACK,
                activebackground=WIN98_GRAY,
                activeforeground=WIN98_BLACK,
                relief=tk.RAISED,
                bd=2,
                padx=padx,
                pady=pady,
                width=width,
                state=state,
                command=command,
            )
            _theme_dlog(f"[BTN] Regular button '{text}' created.")
            return b
    except Exception as e:
        _theme_dlog(f"[BTN-ERR] Failed creating button '{text}': {e}")
        _theme_dlog(traceback.format_exc())
        raise


def create_win98_entry(
    parent: tk.Widget,
    textvariable: Optional[tk.StringVar] = None,
    width: int = 24,
    show: Optional[str] = None,
    font: Optional[tuple] = None,
) -> tk.Entry:
    """Create an authentic Windows 98 sunken text input field."""
    _theme_dlog(f"[ENTRY] Creating Entry width={width}, show={show}")
    try:
        entry_font = font or get_win98_font(9)
        e = tk.Entry(
            parent,
            textvariable=textvariable,
            font=entry_font,
            width=width,
            show=show,
            bg=WIN98_WHITE,
            fg=WIN98_BLACK,
            insertbackground=WIN98_BLACK,
            selectbackground=WIN98_SELECTION,
            selectforeground=WIN98_SELECTION_TEXT,
            relief=tk.SUNKEN,
            bd=2,
        )
        _theme_dlog(f"[ENTRY] Entry created successfully.")
        return e
    except Exception as err:
        _theme_dlog(f"[ENTRY-ERR] Failed creating Entry: {err}")
        _theme_dlog(traceback.format_exc())
        raise


def create_win98_groupbox(parent: tk.Widget, text: str) -> tk.LabelFrame:
    """Create a Windows 98 group box with etched groove border."""
    return tk.LabelFrame(
        parent,
        text=text,
        font=get_win98_font(9, bold=True),
        fg=WIN98_BLACK,
        bg=WIN98_GRAY,
        relief=tk.GROOVE,
        bd=2,
        padx=10,
        pady=8,
    )


class Win98StatusBar(tk.Frame):
    """Windows 98 Status Bar with multiple sunken panes and sizing grip."""

    def __init__(self, parent: tk.Widget, panes: list[dict[str, Any]]) -> None:
        super().__init__(parent, bg=WIN98_GRAY, bd=1, relief=tk.RAISED)
        self.pack_propagate(False)
        self.configure(height=24)
        self.labels: list[tk.Label] = []

        for p in panes:
            weight = p.get("weight", 0)
            text = p.get("text", "")
            pane_frame = tk.Frame(self, relief=tk.SUNKEN, bd=1, bg=WIN98_GRAY)
            if weight > 0:
                pane_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
            else:
                pane_frame.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)

            lbl = tk.Label(
                pane_frame,
                text=text,
                font=get_win98_font(8),
                bg=WIN98_GRAY,
                fg=WIN98_BLACK,
                anchor=tk.W,
                padx=4,
            )
            lbl.pack(fill=tk.BOTH, expand=True)
            self.labels.append(lbl)

        # Sizing Grip canvas on the right
        grip = tk.Canvas(self, width=14, height=18, bg=WIN98_GRAY, highlightthickness=0, bd=0)
        grip.pack(side=tk.RIGHT, padx=(0, 2), pady=2)
        # 3 diagonal dotted lines
        for offset in [0, 4, 8]:
            grip.create_line(12 - offset, 16, 12, 16 - offset, fill=WIN98_WHITE)
            grip.create_line(11 - offset, 15, 11, 15 - offset, fill=WIN98_DARK)

    def set_pane_text(self, index: int, text: str) -> None:
        if 0 <= index < len(self.labels):
            self.labels[index].config(text=text)
