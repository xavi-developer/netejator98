# -*- mode: python ; coding: utf-8 -*-
# ==============================================================================
# PyInstaller Spec for Netejator98
# Builds single-binary executable for cross-platform distribution.
# ==============================================================================

import os
from pathlib import Path

block_cipher = None

# Root paths
spec_root = Path(SPECPATH).resolve()
repo_root = spec_root.parent
src_dir = repo_root / "src"
policies_dir = repo_root / "policies"

added_datas = [
    (str(policies_dir / "defaults"), "policies/defaults"),
]

a = Analysis(
    [str(src_dir / "netejator98" / "main.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=added_datas,
    hiddenimports=[
        "nacl",
        "nacl.bindings",
        "nacl.pwhash",
        "nacl.public",
        "nacl.secret",
        "cryptography",
        "yaml",
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "tkinter.filedialog",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "unittest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="netejator98",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

