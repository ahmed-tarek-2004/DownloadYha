#!/usr/bin/env python3
"""
launcher.py - Cross-platform launcher script for Downloadyha GUI

Provides a simple entry point that ensures all dependencies are available
and launches the main GUI application with proper error handling.
"""

import sys
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import tkinter
    except ImportError:
        print("ERROR: Python Tkinter support is missing!")
        if sys.platform.startswith("linux"):
            print("\nPlease install Tkinter via your Linux package manager:")
            print("  Debian/Ubuntu: sudo apt install python3-tk")
            print("  Fedora/RHEL:   sudo dnf install python3-tkinter")
            print("  Arch Linux:    sudo pacman -S tk")
        else:
            print("\nPlease reinstall Python with Tcl/Tk support enabled.")
        return False

    missing = []

    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")

    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")

    if missing:
        print("ERROR: Missing required dependencies!")
        print("\nPlease install the following packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nInstall command:")
        print(f"  pip install {' '.join(missing)}")
        return False

    return True


def main():
    """Main launcher entry point."""
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)

    # Import and launch the GUI
    try:
        from downloadyha_gui.app import DownloadyhaGUI

        print("Launching Downloadyha GUI...")
        app = DownloadyhaGUI()
        app.mainloop()

    except KeyboardInterrupt:
        print("\nApplication closed by user.")
        sys.exit(0)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
