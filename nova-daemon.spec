# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Nova Cathedral Daemon
Produces: dist/nova-daemon/nova-daemon  (onedir, no UPX)
"""

from pathlib import Path

ROOT = Path(SPECPATH)
NOVA = ROOT / "Cathedral" / "nova"

VOSK_DIR = Path.home() / ".local/lib/python3.12/site-packages/vosk"

a = Analysis(
    [str(NOVA / "daemon" / "nova_cathedral_daemon.py")],
    pathex=[
        str(NOVA / "modules"),
        str(NOVA / "plugins"),
        str(NOVA / "nuclear" / "memory"),
        str(NOVA / "nuclear" / "monitoring"),
    ],
    binaries=[
        # vosk STT — libvosk.so is loaded via ctypes, not picked up automatically
        (str(VOSK_DIR / "libvosk.so"), "vosk"),
    ],
    datas=[
        # bundle vosk Python files alongside the native lib
        (str(VOSK_DIR / "__init__.py"),    "vosk"),
        (str(VOSK_DIR / "vosk_cffi.py"),   "vosk"),
        (str(NOVA / "nova_foundation.yaml"), "."),
    ],
    hiddenimports=[
        # stdlib that PyInstaller sometimes misses
        "sqlite3",
        "urllib.request",
        "urllib.error",
        "hashlib",
        "asyncio",
        # third-party
        "yaml",
        "psutil",
        "psutil._pslinux",
        "psutil._common",
        # Nova modules (loaded via try/import at top of daemon)
        "evolution_engine",
        "code_sandbox",
        "filesystem",
        "voice",
        "web_search",
        "nova_self_builder",
        "nova_system",
        # Nuclear memory layer
        "mega_brain_core",
        "nova_memory",
        # Plugins (optional — imported with try/except)
        "oracle_module",
        "echo_module",
        "consciousness_plugins",
        "real_claude_bridge",
        "all_seeing_core",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt6", "tkinter", "matplotlib", "numpy",
        "PIL", "cv2", "scipy",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="nova-daemon",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="nova-daemon",
)
