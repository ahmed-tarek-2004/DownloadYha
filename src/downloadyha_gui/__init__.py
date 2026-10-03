"""
Downloadyha GUI - Modern Desktop Application for Video & Media Downloads

A cross-platform desktop GUI built with CustomTkinter that provides:
- Support for YouTube, TikTok, Instagram, Facebook, Twitter/X, and more
- Beautiful dark/light theme support with system auto-detection
- Download tab with URL input, quality selection, and real-time progress
- Queue management for multiple downloads
- Settings configuration panel
- Integration with the downloadyha core engine
"""

from __future__ import annotations

try:
    from downloadyha import __version__
except Exception:
    import importlib.metadata
    try:
        __version__ = importlib.metadata.version("downloadyha")
    except Exception:
        __version__ = "2.0.0"

__author__ = "Ahmed Tarek Zaher"
__copyright__ = "Copyright 2026, Ahmed Tarek Zaher"
__license__ = "MIT"

# BOOKMARK: Ahmed Tarek Zaher - Owner

def __getattr__(name: str):
    if name in ("DownloadyhaGUI", "main"):
        from .app import DownloadyhaGUI, main
        return {"DownloadyhaGUI": DownloadyhaGUI, "main": main}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["DownloadyhaGUI", "main", "__version__"]
