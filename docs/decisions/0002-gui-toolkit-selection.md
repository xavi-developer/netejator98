# ADR 0002: GUI Toolkit Selection — Decoupled Presentation with Tkinter & PySide6 Architecture

## Status
Accepted

## Context
Netejator98 requires a full-screen, frameless, always-on-top kiosk prompt at user session login, as well as a password-protected administrative interface. The specification allows PySide6 or Tkinter with justification.

Key constraints:
1. The software must function reliably on educational workstations (often thin clients or constrained Linux/Windows/macOS machines) without heavy external C-library dependency chains.
2. The user environment in many institutional settings (and containerized or base Python installations) includes standard Python with Tkinter built-in, whereas PySide6 / Qt6 requires substantial binary downloads (>100MB) and specific graphics driver / Wayland / X11 stack bindings.
3. The Presentation layer must be strictly decoupled from domain logic via View-Models and Controllers.

## Decision
1. We design the presentation layer following the Model-View-ViewModel (MVVM) pattern, exposing `KioskViewModel` and `AdminViewModel`.
2. The primary default UI is implemented using Python's built-in `tkinter` / `ttk`, providing native, zero-dependency, out-of-the-box execution across Windows, Linux, and macOS.
3. The kiosk view uses borderless, topmost, grab-enabled windows that prevent desktop interaction until validation succeeds, with emergency escape chords (`Ctrl+Alt+A`).
4. The architecture defines a clean abstract UI interface (`KioskViewInterface`, `AdminViewInterface`), allowing a PySide6 implementation to be plugged in seamlessly when `pyside6` is installed in the target environment.

## Consequences
- **Positive**: Zero external GUI library dependencies; runs immediately on any standard Python 3.11+ distribution across Windows, macOS, and Linux.
- **Positive**: Small disk footprint and rapid startup time (crucial during user session boot).
- **Negative**: Tkinter styling requires deliberate configuration to look modern across platforms compared to Qt's rich widget stylesheets. We address this with clean TTK theming.

