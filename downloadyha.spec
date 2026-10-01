# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec file for downloadyha
#
# Build commands:
#   Windows:  pyinstaller downloadyha.spec
#   Linux:    pyinstaller downloadyha.spec
#
# Or use the platform-specific build scripts:
#   Windows:  .\build-windows.ps1
#   Linux:    ./build-linux.sh

import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(
    # Entry point — __main__.py calls cli.main()
    ["src/downloadyha/__main__.py"],

    pathex=["src"],

    binaries=[],

    # yt-dlp ships internal extractors and JS snippets as package data;
    # collect_data_files pulls them all in so the frozen executable can
    # still discover and use every extractor.
    # Also include the dependency versions manifest.
    datas=[
        ("src/downloadyha/versions.json", "downloadyha"),
    ] + collect_data_files("yt_dlp"),

    hiddenimports=[
        # yt-dlp dynamically loads its extractor plug-ins at runtime via
        # importlib; PyInstaller cannot see these imports statically.
        "yt_dlp.extractor",
        "yt_dlp.extractor._extractors",
        "yt_dlp.extractor.common",
        "yt_dlp.networking",
        "yt_dlp.networking.common",
        "yt_dlp.networking._urllib",
        "yt_dlp.postprocessor",
        "yt_dlp.postprocessor.common",
        "yt_dlp.postprocessor.ffmpeg",
        # Standard library modules that yt-dlp uses via lazy imports
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
    ],

    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],

    # yt-dlp pulls in many optional packages (mutagen, websockets, brotli,
    # certifi, …).  Exclude the ones that are definitely not needed to keep
    # the executable lean while still being safe.
    excludes=[
        "tkinter",
        "test",
        "unittest",
        "distutils",
        "setuptools",
        "pip",
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

    # Output executable name — no .exe suffix needed; PyInstaller adds it
    # automatically on Windows.
    name="downloadyha",

    debug=False,
    bootloader_ignore_signals=False,
    strip=False,

    # upx=True compresses the executable.  Set to False if UPX is not
    # installed or if you prefer a faster cold-start.
    upx=True,
    upx_exclude=[],

    # Single-file executable (onefile mode).
    # All Python bytecode and data are packed into this one binary.
    runtime_tmpdir=None,

    console=True,   # CLI tool — keep the console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    # Windows-specific version / icon metadata.
    # Uncomment and adjust as needed:
    icon="assets/icons/downloadyha.ico",
    # version="version_info.txt",
)
