"""
uninstaller.py - Self-uninstall mechanism for Downloadyha.

Responsibilities:
- Remove the executable.
- Remove all user data (config, cache, logs, bundled binaries).
- Ask for confirmation before proceeding.
"""

import platform
import shutil
import sys
from pathlib import Path

from . import config


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
    print()
    print("=" * 55)
    print("       Downloadyha Uninstaller")
    print("=" * 55)
    print()
    print("This will remove:")
    print("  - The Downloadyha executable")
    print("  - Configuration files")
    print("  - Cache data")
    print("  - Log files")
    print("  - Bundled binaries (ffmpeg, deno)")
    print()

    # Ask for confirmation
    response = input("Are you sure you want to uninstall Downloadyha? [y/N]: ").strip().lower()
    if response not in ("y", "yes"):
        print("\nUninstall canceled.")
        return False

    print("\nUninstalling Downloadyha...\n")

    # Get paths to remove
    config_dir = config.get_config_dir()
    cache_dir = config.get_cache_dir()
    logs_dir = config.get_logs_dir()
    app_data_dir = config.get_app_data_dir()
    bin_dir = config.get_bin_dir()
    executable = _get_executable_path()

    errors = []

    # Remove config directory
    if config_dir.exists():
        try:
            shutil.rmtree(config_dir)
            print(f"Removed config: {config_dir}")
        except OSError as e:
            errors.append(f"Failed to remove config directory: {e}")

    # Remove cache directory
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            print(f"Removed cache: {cache_dir}")
        except OSError as e:
            errors.append(f"Failed to remove cache directory: {e}")

    # Remove logs directory
    if logs_dir.exists():
        try:
            shutil.rmtree(logs_dir)
            print(f"Removed logs: {logs_dir}")
        except OSError as e:
            errors.append(f"Failed to remove logs directory: {e}")

    # Remove bin directory (bundled dependencies)
    if bin_dir.exists():
        try:
            shutil.rmtree(bin_dir)
            print(f"Removed binaries: {bin_dir}")
        except OSError as e:
            errors.append(f"Failed to remove bin directory: {e}")

    # Remove app data directory (if empty or only contains removed dirs)
    if app_data_dir.exists():
        try:
            # Try to remove the entire app data dir
            shutil.rmtree(app_data_dir)
            print(f"Removed app data: {app_data_dir}")
        except OSError:
            # Directory might not be empty or have permission issues
            pass

    # Remove executable
    if getattr(sys, "frozen", False):
        try:
            if platform.system() == "Windows":
                # On Windows, we can't delete a running executable directly
                # Mark it for deletion on next restart
                import ctypes
                executable_old = executable.with_suffix(executable.suffix + ".old")
                if executable_old.exists():
                    try:
                        executable_old.unlink()
                    except OSError:
                        pass
                executable.rename(executable_old)

                # Schedule deletion on reboot using Windows API
                ctypes.windll.kernel32.MoveFileExW(
                    str(executable_old),
                    None,
                    0x4  # MOVEFILE_DELAY_UNTIL_REBOOT
                )
                print(f"Executable will be removed on next restart: {executable_old}")
            else:
                # On Linux, we can delete the running executable
                # (the process continues from memory)
                executable.unlink()
                print(f"Removed executable: {executable}")
        except OSError as e:
            errors.append(f"Failed to remove executable: {e}")
    else:
        print("Note: Running in development mode - executable not removed.")

    print()

    if errors:
        print("Some items could not be removed:")
        for error in errors:
            print(f"  - {error}")
        print()
        print("You may need to remove them manually.")
        return False

    print("Downloadyha has been successfully uninstalled.")
    print("Thank you for using Downloadyha!")
    return True


def handle_uninstall_command() -> None:
    """
    Entry point for the 'downloadyha uninstall' command.
    """
    uninstall()
