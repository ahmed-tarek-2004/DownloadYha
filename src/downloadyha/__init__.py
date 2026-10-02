"""
Downloadyha - Video, Audio & Playlist Downloader CLI and Desktop GUI.

A standalone downloader that supports audio and video downloads from YouTube,
TikTok, Instagram, Facebook, Twitter/X, and more with customizable quality options,
available in both CLI and Desktop GUI versions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _resolve_version() -> str:
    """
    Dynamically resolve the application version from bundled versions.json
    (including PyInstaller frozen environments), installed package metadata, or manifest.
    """
    # 1. Try PyInstaller frozen bundle location
    if hasattr(sys, "_MEIPASS"):
        try:
            meipass_json = Path(sys._MEIPASS) / "downloadyha" / "versions.json"
            if meipass_json.exists():
                with open(meipass_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "downloadyha" in data and data["downloadyha"]:
                        return str(data["downloadyha"])
            root_json = Path(sys._MEIPASS) / "versions.json"
            if root_json.exists():
                with open(root_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "downloadyha" in data and data["downloadyha"]:
                        return str(data["downloadyha"])
        except Exception:
            pass

    # 2. Try package-level versions.json
    try:
        versions_file = Path(__file__).parent / "versions.json"
        if versions_file.exists():
            with open(versions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "downloadyha" in data and data["downloadyha"]:
                    return str(data["downloadyha"])
    except Exception:
        pass

    # 3. Try importlib.metadata for installed distribution
    try:
        import importlib.metadata
        return importlib.metadata.version("downloadyha")
    except Exception:
        pass

    # 4. Fallback default
    return "2.0.0"


__version__ = _resolve_version()
__author__ = "Ahmed Tarek Zaher"
__app_name__ = "Downloadyha"

