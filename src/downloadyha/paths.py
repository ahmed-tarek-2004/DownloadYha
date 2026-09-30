"""
Platform-specific path management for Downloadyha.

Provides cross-platform paths for application data, configuration,
cache, logs, binaries, and downloads.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .platform import get_platform, get_architecture


def get_app_name() -> str:
    """
    Get the application name for directory paths.

    Returns:
        Application name (lowercase for consistency).
    """
    return "downloadyha"


def get_app_data_dir() -> Path:
    """
    Get the application data directory.

    Windows: %LOCALAPPDATA%\\Downloadyha
    Linux: ~/.local/share/downloadyha

    Returns:
        Path to the application data directory.
    """
    app_name = get_app_name()

    if get_platform() == "windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base = Path(local_app_data)
        else:
            base = Path.home() / "AppData" / "Local"
        return base / "Downloadyha"
    else:
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            base = Path(xdg_data_home)
        else:
            base = Path.home() / ".local" / "share"
        return base / app_name


def get_bin_dir() -> Path:
    """
    Get the directory for bundled/downloaded binaries.

    Returns:
        Path to the bin directory within app data.
    """
    return get_app_data_dir() / "bin"


def get_config_dir() -> Path:
    """
    Get the configuration directory.

    Windows: %LOCALAPPDATA%\\Downloadyha\\config
    Linux: ~/.config/downloadyha

    Returns:
        Path to the configuration directory.
    """
    app_name = get_app_name()

    if get_platform() == "windows":
        return get_app_data_dir() / "config"
    else:
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            base = Path(xdg_config_home)
        else:
            base = Path.home() / ".config"
        return base / app_name


def get_cache_dir() -> Path:
    """
    Get the cache directory.

    Windows: %LOCALAPPDATA%\\Downloadyha\\cache
    Linux: ~/.cache/downloadyha

    Returns:
        Path to the cache directory.
    """
    app_name = get_app_name()

    if get_platform() == "windows":
        return get_app_data_dir() / "cache"
    else:
        xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache_home:
            base = Path(xdg_cache_home)
        else:
            base = Path.home() / ".cache"
        return base / app_name


def get_log_dir() -> Path:
    """
    Get the log directory.

    Windows: %LOCALAPPDATA%\\Downloadyha\\logs
    Linux: ~/.local/share/downloadyha/logs

    Returns:
        Path to the log directory.
    """
    return get_app_data_dir() / "logs"


def get_download_dir() -> Path:
    """
    Get the default download directory.

    Returns:
        Path to the user's Downloads folder.
    """
    return Path.home() / "Downloads"


def ensure_directories() -> None:
    """
    Ensure all required application directories exist.
    """
    directories = [
        get_app_data_dir(),
        get_bin_dir(),
        get_config_dir(),
        get_cache_dir(),
        get_log_dir(),
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_ffmpeg_executable_name() -> str:
    """
    Get the FFmpeg executable name for the current platform.

    Returns:
        "ffmpeg.exe" on Windows, "ffmpeg" on Linux.
    """
    return "ffmpeg.exe" if get_platform() == "windows" else "ffmpeg"


def get_ffprobe_executable_name() -> str:
    """
    Get the FFprobe executable name for the current platform.

    Returns:
        "ffprobe.exe" on Windows, "ffprobe" on Linux.
    """
    return "ffprobe.exe" if get_platform() == "windows" else "ffprobe"


def get_deno_executable_name() -> str:
    """
    Get the Deno executable name for the current platform.

    Returns:
        "deno.exe" on Windows, "deno" on Linux.
    """
    return "deno.exe" if get_platform() == "windows" else "deno"
