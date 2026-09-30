"""
uninstaller.py - Self-uninstall mechanism for Downloadyha.

Responsibilities:
- Remove the executable.
- Remove all user data (config, cache, logs, bundled binaries).
- Ask for confirmation before proceeding with modern UI prompts.
"""

import platform
import shutil
import sys
from pathlib import Path

from . import config
from .ui import Colors, Symbols, error, info, init_terminal, prompt_confirm, success, warning


def _get_executable_path() -> Path:
    """Return the absolute path to the current running executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    else:
        # Not a frozen executable; return the script path as a fallback
        return Path(__file__).resolve()


def uninstall() -> bool:
    """
    Uninstall Downloadyha from the system.

    Removes:
      - The executable itself.
      - Configuration directory.
      - Cache directory.
      - Logs directory.
      - Bundled binaries (ffmpeg, deno).

    Returns:
        True on success, False on error.
    """
    init_terminal()
    c = Colors

    print()
    print(f"{c.BRIGHT_RED}╭────────────────────────────────────────────────────────╮{c.RESET}")
    print(f"{c.BRIGHT_RED}│{c.RESET} {c.BOLD}{c.BRIGHT_WHITE}              Downloadyha Uninstaller                  {c.RESET} {c.BRIGHT_RED}│{c.RESET}")
    print(f"{c.BRIGHT_RED}╰────────────────────────────────────────────────────────╯{c.RESET}")
    print()
    print(f"{c.DIM}This will permanently remove:{c.RESET}")
    print(f"  {c.RED}•{c.RESET} Downloadyha application executable")
    print(f"  {c.RED}•{c.RESET} Configuration files")
    print(f"  {c.RED}•{c.RESET} Cache & log files")
    print(f"  {c.RED}•{c.RESET} Bundled binaries (FFmpeg, Deno)")
    print()

    # Ask for confirmation
    if not prompt_confirm("Are you sure you want to completely uninstall Downloadyha?", default=False):
        info("Uninstall canceled.")
        return False

    info("Uninstalling Downloadyha...")

    # Get paths to remove
    config_dir = config.get_config_dir()
    cache_dir = config.get_cache_dir()
    logs_dir = config.get_logs_dir()
    app_data_dir = config.get_app_data_dir()
    bin_dir = config.get_bin_dir()
    executable = _get_executable_path()

    errors_list = []

    # Remove config directory
    if config_dir.exists():
        try:
            shutil.rmtree(config_dir)
            success(f"Removed config directory: {config_dir}")
        except OSError as e:
            errors_list.append(f"Config directory: {e}")

    # Remove cache directory
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            success(f"Removed cache directory: {cache_dir}")
        except OSError as e:
            errors_list.append(f"Cache directory: {e}")

    # Remove logs directory
    if logs_dir.exists():
        try:
            shutil.rmtree(logs_dir)
            success(f"Removed logs directory: {logs_dir}")
        except OSError as e:
            errors_list.append(f"Logs directory: {e}")

    # Remove bin directory (bundled dependencies)
    if bin_dir.exists():
        try:
            shutil.rmtree(bin_dir)
            success(f"Removed binaries directory: {bin_dir}")
        except OSError as e:
            errors_list.append(f"Binaries directory: {e}")

    # Remove app data directory if empty or remaining
    if app_data_dir.exists():
        try:
            shutil.rmtree(app_data_dir)
            success(f"Removed app data directory: {app_data_dir}")
        except OSError:
            pass

    # Remove executable
    if getattr(sys, "frozen", False):
        try:
            if platform.system() == "Windows":
                import ctypes
                executable_old = executable.with_suffix(executable.suffix + ".old")
                if executable_old.exists():
                    try:
                        executable_old.unlink()
                    except OSError:
                        pass
                executable.rename(executable_old)

                # Schedule deletion on reboot
                ctypes.windll.kernel32.MoveFileExW(
                    str(executable_old),
                    None,
                    0x4  # MOVEFILE_DELAY_UNTIL_REBOOT
                )
                success("Executable scheduled for deletion on next reboot.")
            else:
                executable.unlink()
                success("Executable removed successfully.")
        except OSError as e:
            errors_list.append(f"Executable removal: {e}")
    else:
        info("Running in development mode — local source files preserved.")

    print()
    if errors_list:
        warning("Some items could not be automatically deleted:")
        for err_msg in errors_list:
            print(f"  - {err_msg}")
        return False

    success("Downloadyha has been completely uninstalled.")
    print(f"\n{c.CYAN}Thank you for using Downloadyha!{c.RESET}\n")
    return True


def handle_uninstall_command() -> None:
    """Entry point for the 'downloadyha uninstall' command."""
    uninstall()
