r"""
config.py - User configuration management for Downloadyha.

Stores and loads config.json from the platform-specific app config directory:

  Windows:  %LOCALAPPDATA%\Downloadyha\config.json
  Linux:    ~/.local/share/downloadyha/config.json

The configuration file is intentionally separate from the application
executable so that updates never overwrite user settings.
"""

import json
import os
import platform
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Platform-specific directory helpers
# ---------------------------------------------------------------------------

def get_app_data_dir() -> Path:
    """Return the root application data directory for Downloadyha."""
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Downloadyha"
    else:
        # XDG_DATA_HOME or ~/.local/share
        xdg = os.environ.get("XDG_DATA_HOME", "")
        base = Path(xdg) if xdg else Path.home() / ".local" / "share"
        return base / "downloadyha"


def get_config_dir() -> Path:
    """Return the directory that holds user configuration files."""
    system = platform.system()
    if system == "Windows":
        # On Windows, config lives alongside app data
        return get_app_data_dir()
    else:
        # XDG_CONFIG_HOME or ~/.config
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / "downloadyha"


def get_cache_dir() -> Path:
    """Return the directory used for ephemeral cache data (e.g. update timestamps)."""
    system = platform.system()
    if system == "Windows":
        return get_app_data_dir() / "cache"
    else:
        xdg = os.environ.get("XDG_CACHE_HOME", "")
        base = Path(xdg) if xdg else Path.home() / ".cache"
        return base / "downloadyha"


def get_bin_dir() -> Path:
    """Return the directory where managed binaries (ffmpeg, deno, …) are stored."""
    return get_app_data_dir() / "bin"


def get_logs_dir() -> Path:
    """Return the directory for application log files."""
    return get_app_data_dir() / "logs"


def get_download_dir() -> Path:
    """Return the default download directory (the user's Downloads folder)."""
    return Path.home() / "Downloads"


# ---------------------------------------------------------------------------
# Default configuration values
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG: dict = {
    # Where downloaded files are saved by default.
    "download_directory": str(get_download_dir()),
    # Whether to check for updates in the background.
    "check_updates": True,
}


# ---------------------------------------------------------------------------
# Config file path
# ---------------------------------------------------------------------------

def _config_file_path() -> Path:
    return get_config_dir() / "config.json"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load() -> dict:
    """
    Load the user configuration from disk.

    - Missing keys are filled in with defaults so older config files are
      forward-compatible with new application versions.
    - Parse errors are caught; the defaults are returned so the application
      always starts successfully.

    Returns a mutable dict.  Call ``save(cfg)`` to persist changes.
    """
    path = _config_file_path()

    if not path.exists():
        return dict(_DEFAULT_CONFIG)

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        if not isinstance(data, dict):
            return dict(_DEFAULT_CONFIG)

        # Merge in any keys that are new in this version
        merged = dict(_DEFAULT_CONFIG)
        merged.update(data)
        return merged

    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_CONFIG)


def save(cfg: dict) -> bool:
    """
    Persist *cfg* to disk.

    Creates parent directories as needed.  Returns ``True`` on success.
    """
    path = _config_file_path()

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temp file first so we never leave a half-written config.
        tmp_path = path.with_suffix(".json.tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        # Atomic rename (same filesystem on all supported platforms)
        tmp_path.replace(path)
        return True

    except OSError:
        return False


def get(key: str, default=None):
    """Convenience: load config and return a single key."""
    return load().get(key, default)


def set_value(key: str, value) -> bool:
    """Convenience: load config, update one key, and save."""
    cfg = load()
    cfg[key] = value
    return save(cfg)
