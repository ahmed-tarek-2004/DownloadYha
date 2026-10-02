"""
uninstaller.py - Self-uninstall mechanism for Downloadyha.

Responsibilities:
- Terminate running helper processes (FFmpeg, Deno).
- Release active logging handlers to prevent Windows file locks.
- Safely remove all user data (config, cache, logs, bundled binaries).
- Self-delete running executable on Windows using detached process cleanup and reboot fallback.
- Ask for confirmation before proceeding with modern UI prompts.
- Handle read-only files, permission errors, and locked files gracefully.
"""

import os
import platform
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

from . import config
from .ui import Colors, Symbols, error, info, init_terminal, prompt_confirm, success, warning


def _get_executable_path() -> Path:
    """Return the absolute path to the current running executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    else:
        # Not a frozen executable; return the script path as a fallback
        return Path(__file__).resolve()


def _close_logging_handlers() -> None:
    """
    Close and detach all file handlers across the logging system.
    This releases Windows file locks on active log files (e.g. downloadyha.log).
    """
    import logging

    logger_names = [
        "",
        "downloadyha",
        "downloadyha.cli",
        "downloadyha.download",
        "downloadyha.dependencies",
        "downloadyha.error",
    ]
    for name in logger_names:
        log = logging.getLogger(name)
        for handler in list(log.handlers):
            try:
                handler.flush()
                handler.close()
                log.removeHandler(handler)
            except Exception:
                pass

    try:
        logging.shutdown()
    except Exception:
        pass


def _terminate_helper_processes() -> None:
    """
    Terminate any lingering helper processes (FFmpeg, Deno) on Windows
    that may have been spawned and could hold locks on the bin directory.
    """
    if platform.system() == "Windows":
        for proc_name in ["ffmpeg.exe", "ffprobe.exe", "deno.exe"]:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", proc_name, "/T"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except Exception:
                pass


def _robust_rmtree(path: Path, max_retries: int = 3, retry_delay: float = 0.2) -> Tuple[bool, Optional[str]]:
    """
    Recursively remove a directory tree, handling Windows read-only file attributes
    and transient file locks with retries.

    Returns:
        (True, None) on success.
        (False, error_message) on failure.
    """
    if not path.exists():
        return True, None

    def _handle_remove_readonly(func, file_path, exc_info):
        """Error callback to clear read-only file attributes on Windows and retry."""
        try:
            os.chmod(file_path, stat.S_IWRITE | stat.S_IWUSR | stat.S_IRUSR)
            func(file_path)
        except Exception:
            pass

    for attempt in range(max_retries):
        try:
            if sys.version_info >= (3, 12):
                shutil.rmtree(path, onexc=lambda func, p, exc: _handle_remove_readonly(func, p, exc))
            else:
                shutil.rmtree(path, onerror=_handle_remove_readonly)
            return True, None
        except OSError as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return False, str(e)

    return False, "Directory removal failed after retries."


def _cleanup_stale_backups(executable: Path) -> None:
    """Clean up any leftover .old or .tmp executable files in the target directory."""
    try:
        parent = executable.parent
        stem = executable.stem
        ext = executable.suffix

        patterns = [
            f"{stem}{ext}.old*",
            f"{stem}.old*",
            f"{stem}*.tmp*",
        ]

        for pattern in patterns:
            for item in parent.glob(pattern):
                if item.resolve() != executable.resolve() and item.is_file():
                    try:
                        item.unlink()
                    except OSError:
                        pass
    except Exception:
        pass


def _schedule_windows_self_delete(file_to_delete: Path) -> None:
    """
    Launch a detached background command on Windows that waits for this process to exit
    and deletes the old executable file cleanly without needing admin rights or a reboot.
    Also registers with MoveFileExW as a secondary reboot fallback.
    """
    target = str(file_to_delete.resolve())

    # 1. Detached background deletion process
    cmd = f'ping 127.0.0.1 -n 3 > nul & del /f /q "{target}"'
    creation_flags = 0
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        creation_flags |= subprocess.CREATE_NO_WINDOW
    if hasattr(subprocess, "DETACHED_PROCESS"):
        creation_flags |= subprocess.DETACHED_PROCESS

    try:
        subprocess.Popen(
            ["cmd.exe", "/c", cmd],
            creationflags=creation_flags,
            close_fds=True,
            shell=False,
        )
    except Exception:
        pass

    # 2. Secondary fallback: Schedule deletion on reboot via Windows API
    try:
        import ctypes
        ctypes.windll.kernel32.MoveFileExW(target, None, 0x4)  # MOVEFILE_DELAY_UNTIL_REBOOT
    except Exception:
        pass


def _remove_path_from_windows_registry(target_dir: Path) -> bool:
    """Remove a directory from the Windows user's PATH environment variable."""
    if platform.system() != "Windows":
        return False
    try:
        import winreg
        target_norm = os.path.normpath(str(target_dir.resolve())).lower()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try:
                current_path, val_type = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                return True

            parts = [p.strip() for p in current_path.split(";") if p.strip()]
            new_parts = [p for p in parts if os.path.normpath(p).lower() != target_norm]

            if len(new_parts) != len(parts):
                new_path_val = ";".join(new_parts)
                winreg.SetValueEx(key, "Path", 0, val_type, new_path_val)
                # Broadcast WM_SETTINGCHANGE so other shells pick it up
                try:
                    import ctypes
                    HWND_BROADCAST = 0xFFFF
                    WM_SETTINGCHANGE = 0x001A
                    SMTO_ABORTIFHUNG = 0x0002
                    result = ctypes.c_ulong()
                    ctypes.windll.user32.SendMessageTimeoutW(
                        HWND_BROADCAST,
                        WM_SETTINGCHANGE,
                        0,
                        "Environment",
                        SMTO_ABORTIFHUNG,
                        2000,
                        ctypes.byref(result)
                    )
                except Exception:
                    pass
                return True
    except Exception:
        pass
    return False


def _remove_standalone_installation() -> List[str]:
    """
    Remove standalone installation directories created by installers or scripts
    (e.g., %LOCALAPPDATA%\\Programs\\Downloadyha on Windows).
    """
    removed: List[str] = []
    if platform.system() == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            prog_dir = Path(local_app_data) / "Programs" / "Downloadyha"
            if prog_dir.exists():
                _remove_path_from_windows_registry(prog_dir)
                ok, _ = _robust_rmtree(prog_dir)
                if not ok and prog_dir.exists():
                    for item in list(prog_dir.glob("*")):
                        try:
                            if item.is_file():
                                _schedule_windows_self_delete(item)
                        except Exception:
                            pass
                if ok or not prog_dir.exists():
                    removed.append(str(prog_dir))
    return removed


def _uninstall_pip_package() -> Tuple[bool, Optional[str]]:
    """
    Automatically uninstall the downloadyha package and remove CLI entry points
    when running in a Python environment so non-technical users do not have to
    manually invoke pip.
    """
    try:
        # Schedule script wrappers in Python's Scripts folder for deletion if locked
        scripts_dir = Path(sys.executable).parent / "Scripts"
        if not scripts_dir.exists():
            scripts_dir = Path(sys.executable).parent

        for ep_name in ["downloadyha.exe", "downloadyha", "downloadyha-gui.exe", "downloadyha-gui", "downloadyha-script.py"]:
            ep_file = scripts_dir / ep_name
            if ep_file.exists():
                try:
                    if platform.system() == "Windows":
                        _schedule_windows_self_delete(ep_file)
                    else:
                        ep_file.unlink()
                except Exception:
                    pass

        # Execute pip uninstall -y downloadyha
        cmd = [sys.executable, "-m", "pip", "uninstall", "-y", "downloadyha"]
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False
        )

        return True, None
    except Exception as e:
        return False, str(e)


def uninstall() -> bool:
    """
    Uninstall Downloadyha from the system.

    Removes:
      - Bundled binaries (FFmpeg, FFprobe, Deno).
      - Cache directory.
      - Log directory & files (releasing active logger locks first).
      - Configuration directory & settings.
      - Root application data directory.
      - The executable itself (with Windows file locking safeguards).

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

    # Step 1: Release active file locks and terminate helper processes
    _close_logging_handlers()
    _terminate_helper_processes()

    # Get paths to remove
    config_dir = config.get_config_dir()
    cache_dir = config.get_cache_dir()
    logs_dir = config.get_logs_dir()
    app_data_dir = config.get_app_data_dir()
    bin_dir = config.get_bin_dir()
    executable = _get_executable_path()

    errors_list: List[str] = []

    # Step 2: Remove bin directory (bundled dependencies)
    if bin_dir.exists():
        ok, err = _robust_rmtree(bin_dir)
        if ok:
            success(f"Removed binaries directory: {bin_dir}")
        else:
            errors_list.append(f"Binaries directory ({bin_dir}): {err}")

    # Step 3: Remove cache directory
    if cache_dir.exists():
        ok, err = _robust_rmtree(cache_dir)
        if ok:
            success(f"Removed cache directory: {cache_dir}")
        else:
            errors_list.append(f"Cache directory ({cache_dir}): {err}")

    # Step 4: Remove logs directory
    if logs_dir.exists():
        ok, err = _robust_rmtree(logs_dir)
        if ok:
            success(f"Removed logs directory: {logs_dir}")
        else:
            errors_list.append(f"Logs directory ({logs_dir}): {err}")

    # Step 5: Remove config directory or config file
    if config_dir.exists():
        # On Linux, config_dir (~/.config/downloadyha) is distinct from app_data_dir (~/.local/share/downloadyha)
        if config_dir.resolve() != app_data_dir.resolve():
            ok, err = _robust_rmtree(config_dir)
            if ok:
                success(f"Removed config directory: {config_dir}")
            else:
                errors_list.append(f"Config directory ({config_dir}): {err}")
        else:
            # On Windows, config_dir is app_data_dir; delete config.json explicitly
            config_file = config_dir / "config.json"
            if config_file.exists():
                try:
                    config_file.unlink()
                    success(f"Removed configuration file: {config_file}")
                except OSError as e:
                    errors_list.append(f"Config file ({config_file}): {e}")

    # Step 6: Remove root app data directory if it still exists
    if app_data_dir.exists():
        ok, err = _robust_rmtree(app_data_dir)
        if ok:
            success(f"Removed app data directory: {app_data_dir}")
        else:
            try:
                remaining = list(app_data_dir.iterdir())
                if not remaining:
                    app_data_dir.rmdir()
                    success(f"Removed app data directory: {app_data_dir}")
                else:
                    errors_list.append(f"App data directory ({app_data_dir}): {err}")
            except OSError as e:
                errors_list.append(f"App data directory ({app_data_dir}): {e}")

    # Step 7: Remove standalone installation directory (e.g. Programs\Downloadyha)
    removed_progs = _remove_standalone_installation()
    for prog_dir in removed_progs:
        success(f"Removed application installation directory: {prog_dir}")

    # Step 8: Remove executable / package
    if getattr(sys, "frozen", False):
        try:
            if platform.system() == "Windows":
                # Clean up any previous stale backups first
                _cleanup_stale_backups(executable)

                # Rename the running executable to release the main path
                executable_old = executable.with_name(
                    f"{executable.stem}.old.{os.getpid()}_{int(time.time())}{executable.suffix}"
                )
                try:
                    executable.rename(executable_old)
                except OSError:
                    # Fallback to standard .old
                    executable_old = executable.with_suffix(executable.suffix + ".old")
                    if executable_old.exists():
                        try:
                            executable_old.unlink()
                        except OSError:
                            pass
                    executable.rename(executable_old)

                # Schedule post-exit detached background deletion + MoveFileExW fallback
                _schedule_windows_self_delete(executable_old)
                success("Executable scheduled for immediate deletion.")
            else:
                executable.unlink()
                success("Executable removed successfully.")
        except PermissionError:
            errors_list.append(
                f"Executable removal ({executable}): Permission denied. "
                "Please run uninstaller as Administrator or delete the executable manually."
            )
        except OSError as e:
            errors_list.append(f"Executable removal ({executable}): {e}")
    else:
        # Running under Python / pip: automatically uninstall the pip package
        ok_pip, err_pip = _uninstall_pip_package()
        if ok_pip:
            success("Removed CLI package and command entry points.")
        else:
            errors_list.append(f"Package uninstallation: {err_pip}")

    print()
    if errors_list:
        warning("Some items could not be automatically deleted:")
        for err_msg in errors_list:
            print(f"  - {err_msg}")
        info("\nYou can manually delete any remaining folders listed above.")
        return False

    success("Downloadyha has been completely uninstalled.")
    print(f"\n{c.CYAN}Thank you for using Downloadyha!{c.RESET}\n")
    return True


def handle_uninstall_command() -> None:
    """Entry point for the 'downloadyha uninstall' command."""
    uninstall()
