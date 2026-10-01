# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec file for downloadyha-gui (Desktop GUI version)
#
# Build commands:
#   Windows:  pyinstaller downloadyha-gui.spec
#   Linux:    pyinstaller downloadyha-gui.spec
#
# Or use the platform-specific build scripts:
#   Windows:  .\build-gui-windows.ps1
#   Linux:    ./build-gui-linux.sh

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all customtkinter assets (themes, fonts, images)
customtkinter_datas = collect_data_files("customtkinter")
# Collect all PIL/Pillow assets
pil_datas = collect_data_files("PIL")

a = Analysis(
    # Entry point for GUI - use launcher.py which launches the modern CustomTkinter GUI
    ["src/downloadyha_gui/launcher.py"],

    pathex=["src"],

    binaries=[],

    # Include:
    # - yt-dlp data files (extractors, JS snippets)
    # - customtkinter assets (themes, images, fonts)
    # - PIL/Pillow assets (images, fonts)
    # - downloadyha versions manifest
    datas=[
        ("src/downloadyha/versions.json", "downloadyha"),
    ] + collect_data_files("yt_dlp") + customtkinter_datas + pil_datas,

    hiddenimports=[
        # yt-dlp dynamic imports
        "yt_dlp.extractor",
        "yt_dlp.extractor._extractors",
        "yt_dlp.extractor.common",
        "yt_dlp.networking",
        "yt_dlp.networking.common",
        "yt_dlp.networking._urllib",
        "yt_dlp.postprocessor",
        "yt_dlp.postprocessor.common",
        "yt_dlp.postprocessor.ffmpeg",
        # Standard library modules for yt-dlp
        "urllib",
        "urllib.request",
        "urllib.parse",
        "urllib.error",
        "http",
        "http.client",
        "http.cookiejar",
        "email",
        "email.message",
        "xml",
        "xml.etree",
        "xml.etree.ElementTree",
        # customtkinter and tkinter
        "customtkinter",
        "customtkinter.windows",
        "customtkinter.windows.widgets",
        "customtkinter.windows.widgets.ctk_canvas",
        "customtkinter.windows.widgets.ctk_entry",
        "customtkinter.windows.widgets.ctk_button",
        "customtkinter.windows.widgets.ctk_label",
        "customtkinter.windows.widgets.ctk_frame",
        "customtkinter.windows.widgets.ctk_progressbar",
        "customtkinter.windows.widgets.ctk_slider",
        "customtkinter.windows.widgets.ctk_optionmenu",
        "customtkinter.windows.widgets.ctk_combobox",
        "customtkinter.windows.widgets.ctk_checkbox",
        "customtkinter.windows.widgets.ctk_radiobutton",
        "customtkinter.windows.widgets.ctk_switch",
        "customtkinter.windows.widgets.ctk_scrollbar",
        "customtkinter.windows.widgets.ctk_textbox",
        "customtkinter.windows.widgets.ctk_tabview",
        "customtkinter.windows.widgets.ctk_segmentedbutton",
        "customtkinter.windows.widgets.ctk_toplevel",
        "customtkinter.windows.widgets.ctk_toplevel",
        "customtkinter.windows.widgets.ctk_font",
        "customtkinter.windows.widgets.ctk_image",
        "customtkinter.windows.widgets.ctk_canvas",
        "customtkinter.windows.widgets.ctk_tkinter",
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.ttk",
        "PIL",
        "PIL._tkinter_finder",
        "PIL.Image",
        "PIL.ImageTk",
        "PIL.ImageFont",
        "PIL.ImageDraw",
        # downloadyha_gui modules
        "downloadyha_gui",
        "downloadyha_gui.app",
        # downloadyha core modules
        "downloadyha.config",
        "downloadyha.downloader",
        "downloadyha.paths",
        "downloadyha.platform",
        "downloadyha.platform_utils",
        "downloadyha.dependencies",
        "downloadyha.logging",
        "downloadyha.ui",
        "downloadyha.uninstaller",
        "downloadyha.updater",
    ] + collect_submodules("customtkinter"),

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # Exclude unnecessary packages
    excludes=[
        "test",
        "unittest",
        "distutils",
        "setuptools",
        "pip",
        # Exclude matplotlib and other heavy packages if not needed
        "matplotlib",
        "numpy",
        "pandas",
    ],

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

    # Output executable name
    name="downloadyha-gui",

    debug=False,
    bootloader_ignore_signals=False,
    strip=False,

    # upx=True compresses the executable
    upx=True,
    upx_exclude=[],

    # Single-file executable (onefile mode)
    runtime_tmpdir=None,

    console=False,   # GUI application — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    # Windows-specific icon (uncomment when icon is available)
    # icon="assets/icon.ico",
)
