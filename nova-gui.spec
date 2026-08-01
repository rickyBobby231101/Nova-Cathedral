# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Nova Cathedral GUI
Produces: dist/nova-gui/nova-gui  (onedir, no UPX)

GTK + WebKit2 are system libraries; the binary bundles only the Python
layer and gi bindings, then links against the host system's GTK stack.
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

ROOT = Path(SPECPATH)
NOVA = ROOT / "Cathedral" / "nova"

TYPELIB_DIR = Path("/usr/lib/x86_64-linux-gnu/girepository-1.0")

# typelibs needed at runtime for GTK 3 + WebKit2 4.1
TYPELIBS = [
    "GLib-2.0.typelib",
    "GLibUnix-2.0.typelib",
    "GObject-2.0.typelib",
    "Gio-2.0.typelib",
    "GioUnix-2.0.typelib",
    "Gtk-3.0.typelib",
    "WebKit2-4.1.typelib",
    "WebKit2WebExtension-4.1.typelib",
    "Atk-1.0.typelib",
    "Gdk-3.0.typelib",
    "GdkX11-3.0.typelib",
    "Pango-1.0.typelib",
    "PangoCairo-1.0.typelib",
    "cairo-1.0.typelib",
    "GdkPixbuf-2.0.typelib",
    "HarfBuzz-0.0.typelib",
]

typelib_datas = [
    (str(TYPELIB_DIR / t), "gi/overrides/data/typelibs")
    for t in TYPELIBS
    if (TYPELIB_DIR / t).exists()
]

gi_submodules = collect_submodules("gi")

a = Analysis(
    [str(NOVA / "gui" / "nova_app.py")],
    pathex=[str(NOVA / "gui")],
    binaries=[],
    datas=[
        (str(NOVA / "gui" / "nova_gui.html"), "."),
        *typelib_datas,
    ],
    hiddenimports=[
        *gi_submodules,
        "gi.repository.Gtk",
        "gi.repository.GLib",
        "gi.repository.GObject",
        "gi.repository.Gio",
        "gi.repository.WebKit2",
        "urllib.request",
        "urllib.error",
        "http.server",
        "socketserver",
        "json",
        "threading",
        "subprocess",
    ],
    hookspath=[],
    hooksconfig={
        "gi": {
            "collect_glib_schemas": False,
            "languages":            [],
        },
    },
    runtime_hooks=[],
    excludes=[
        "tkinter", "matplotlib", "numpy", "scipy",
        "PyQt5", "PyQt6", "PySide2", "PySide6",
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
    name="nova-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="nova-gui",
)
