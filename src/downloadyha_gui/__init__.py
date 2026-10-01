"""
Downloadyha GUI - Modern Desktop Application for YouTube Downloads

A cross-platform desktop GUI built with CustomTkinter that provides:
- Beautiful dark/light theme support with system auto-detection
- Download tab with URL input, quality selection, and real-time progress
- Queue management for multiple downloads
- Settings configuration panel
- Integration with the downloadyha core engine
"""

__version__ = "1.0.0"
__author__ = "Ahmed Tarek Zaher"

from .app import DownloadyhaGUI, main

__all__ = ["DownloadyhaGUI", "main"]
