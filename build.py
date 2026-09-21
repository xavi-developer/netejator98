#!/usr/bin/env bash
""":"
# Polyglot wrapper allowing direct execution on bash/sh as well as python
if command -v python3 >/dev/null 2>&1; then
    exec python3 "$0" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$0" "$@"
else
    echo "Error: Python 3 is required but not found on PATH." >&2
    exit 1
fi
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def print_banner(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def check_python_version() -> None:
    if sys.version_info < (3, 10):
        print(
            f"Error: Python 3.10+ is required (found Python {sys.version_info.major}.{sys.version_info.minor})",
            file=sys.stderr,
        )
        sys.exit(1)


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
        print("✓ PyInstaller is available.")
    except ImportError:
        print("[*] PyInstaller not found. Installing PyInstaller...")
        pip_cmd = [sys.executable, "-m", "pip", "install", "pyinstaller"]
        # If running outside venv on newer Debian/Ubuntu, append break-system-packages
        is_venv = sys.prefix != sys.base_prefix
        if not is_venv:
            pip_cmd.append("--break-system-packages")
        try:
            subprocess.check_call(pip_cmd)
            print("✓ PyInstaller installed successfully.")
        except subprocess.CalledProcessError as e:
            # Retry without break-system-packages if it failed
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pyinstaller"])
                print("✓ PyInstaller installed to user site-packages.")
            except subprocess.CalledProcessError:
                print(f"Error: Failed to install PyInstaller: {e}", file=sys.stderr)
                print("Please install it manually: pip install pyinstaller", file=sys.stderr)
                sys.exit(1)


def build_executable(repo_root: Path, clean: bool = False, test: bool = True) -> Path:
    system = platform.system().lower()
    machine = platform.machine().lower()
    spec_file = repo_root / "packaging" / "netejator98.spec"
    dist_dir = repo_root / "dist"
    build_dir = repo_root / "build"

    if not spec_file.exists():
        print(f"Error: Spec file not found at {spec_file}", file=sys.stderr)
        sys.exit(1)

    if clean:
        print("[*] Cleaning build artifacts...")
        if build_dir.exists():
            shutil.rmtree(build_dir, ignore_errors=True)
        print("✓ Build artifacts cleaned.")

    print_banner(f"Building Netejator98 standalone binary for {platform.system()} ({machine})")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        str(spec_file),
    ]

    print(f"[*] Running: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=str(repo_root))

    # Expected output binary
    binary_name = "netejator98.exe" if system == "windows" else "netejator98"
    output_binary = dist_dir / binary_name

    if not output_binary.exists():
        print(f"Error: Expected binary not found at {output_binary}", file=sys.stderr)
        sys.exit(1)

    # Ensure executable permissions on Unix
    if system != "windows":
        os.chmod(output_binary, 0o755)

    size_mb = output_binary.stat().st_size / (1024 * 1024)
    print_banner(f"Build Succeeded! Binary: {output_binary} ({size_mb:.2f} MB)")

    # Verification smoke test
    if test:
        print("[*] Running verification test (--help)...")
        try:
            smoke_proc = subprocess.run(
                [str(output_binary), "--help"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
            )
            if smoke_proc.returncode == 0:
                print("✓ Binary self-test passed: executable runs and displays help successfully!")
            else:
                print(f"⚠️ Warning: Binary exited with code {smoke_proc.returncode}")
                if smoke_proc.stderr:
                    print(smoke_proc.stderr)
        except Exception as e:
            print(f"⚠️ Smoke test could not be completed: {e}")

    return output_binary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Netejator98 standalone executable for the current operating system."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean previous build artifacts before building",
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip post-build executable smoke test",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent

    check_python_version()
    ensure_pyinstaller()
    output_binary = build_executable(repo_root, clean=args.clean, test=not args.no_test)

    print("\nNext steps:")
    system = platform.system().lower()
    if system == "windows":
        print("  • Run directly:       .\\dist\\netejator98.exe admin")
        print("  • Deploy service:     .\\packaging\\windows\\install-service.ps1")
        print("  • Deploy logon task:  .\\packaging\\windows\\setup-logon-task.ps1")
    elif system == "darwin":
        print("  • Run directly:       ./dist/netejator98 admin")
        print("  • Deploy agent:       sudo ./packaging/macos/install.sh")
    else:
        print("  • Run directly:       ./dist/netejator98 admin")
        print("  • Deploy agent:       sudo ./packaging/linux/install.sh")


if __name__ == "__main__":
    main()

