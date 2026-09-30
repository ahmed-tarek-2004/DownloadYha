"""
updater.py - Self-update mechanism for Downloadyha.

Responsibilities:
- Check GitHub Releases API for newer versions.
- Cache update checks (once per 24 hours).
- Download, verify (SHA-256), and atomically replace the running executable.
- Preserve user configuration during updates.
- Handle OS and architecture detection.
- Cross-platform styled UI for update notices and progress.
"""

import hashlib
import json
import os
import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, Tuple

from . import __version__
from . import config
from .ui import Colors, Symbols, error, info, init_terminal, prompt_confirm, success, wait, warning


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_OWNER = "ahmed-tarek-2004"
GITHUB_REPO = "DownloadYha"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_RELEASE_BASE = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download"

UPDATE_CHECK_INTERVAL = 24 * 60 * 60
REQUEST_TIMEOUT = 30


# ---------------------------------------------------------------------------
# Update check timestamp storage
# ---------------------------------------------------------------------------

def _update_check_cache_path() -> Path:
    """Path to the file storing the last update check timestamp."""
    cache_dir = config.get_cache_dir()
    return cache_dir / "last_update_check"


def _get_last_check_time() -> float:
    """
    Return the Unix timestamp of the last update check.
    Returns 0 if never checked.
    """
    path = _update_check_cache_path()
    if not path.exists():
        return 0.0

    try:
        with path.open("r", encoding="utf-8") as fh:
            return float(fh.read().strip())
    except (OSError, ValueError):
        return 0.0


def _set_last_check_time(timestamp: float) -> None:
    """Persist the given Unix timestamp as the last check time."""
    path = _update_check_cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            fh.write(f"{timestamp}\n")
    except OSError:
        pass


def _should_check_for_updates() -> bool:
    """
    Return True if enough time has passed since the last check.
    Respects the user's config setting 'check_updates'.
    """
    cfg = config.load()
    if not cfg.get("check_updates", True):
        return False

    last_check = _get_last_check_time()
    now = time.time()
    return (now - last_check) >= UPDATE_CHECK_INTERVAL


# ---------------------------------------------------------------------------
# Version comparison
# ---------------------------------------------------------------------------

def _parse_version(version_str: str) -> Tuple[int, ...]:
    """
    Parse a semantic version string like '1.2.3' or 'v1.2.3' into (1, 2, 3).
    Returns (0,) on parse failure.
    """
    version_str = version_str.lstrip("v")
    parts = version_str.split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return (0,)


def _is_newer_version(current: str, remote: str) -> bool:
    """Return True if remote version is newer than current."""
    current_tuple = _parse_version(current)
    remote_tuple = _parse_version(remote)
    return remote_tuple > current_tuple


# ---------------------------------------------------------------------------
# OS and architecture detection
# ---------------------------------------------------------------------------

def _detect_platform() -> Optional[str]:
    """
    Detect the current OS and architecture.

    Returns a platform identifier like:
      - "windows-x86_64"
      - "linux-x86_64"
      - "linux-arm64"

    Returns None if the platform is unsupported.
    """
    system = platform.system()
    machine = platform.machine().lower()

    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    else:
        return None

    if system == "Windows":
        return f"windows-{arch}"
    elif system == "Linux":
        return f"linux-{arch}"
    else:
        return None


def _build_artifact_name(version: str, platform_id: str) -> str:
    """
    Build the expected artifact name for the given version and platform.

    Examples:
      downloadyha-v1.0.0-windows-x86_64.zip
      downloadyha-v1.0.0-linux-x86_64.tar.gz
    """
    if "windows" in platform_id:
        ext = ".zip"
    else:
        ext = ".tar.gz"

    return f"downloadyha-{version}-{platform_id}{ext}"


# ---------------------------------------------------------------------------
# GitHub API
# ---------------------------------------------------------------------------

def _fetch_latest_release() -> Optional[dict]:
    """
    Fetch the latest release metadata from GitHub.
    """
    url = f"{GITHUB_API_BASE}/releases/latest"

    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", f"Downloadyha/{__version__}")

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        return data

    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
        return None


def check_for_updates(force: bool = False) -> Optional[str]:
    """
    Check GitHub Releases for a newer version.

    Args:
        force: If True, bypass the 24-hour cache and check immediately.

    Returns:
        The new version string (e.g. "v1.0.5") if an update is available, else None.
    """
    if not force and not _should_check_for_updates():
        return None

    release = _fetch_latest_release()
    _set_last_check_time(time.time())

    if release is None:
        return None

    remote_version = release.get("tag_name", "")
    if not remote_version:
        return None

    if _is_newer_version(__version__, remote_version):
        return remote_version

    return None


# ---------------------------------------------------------------------------
# SHA-256 verification
# ---------------------------------------------------------------------------

def _download_file(url: str, dest_path: Path) -> bool:
    """Download a file from url to dest_path."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", f"Downloadyha/{__version__}")

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with dest_path.open("wb") as fh:
                fh.write(resp.read())

        return True

    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return False


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of the given file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def _fetch_checksum(version: str, artifact_name: str) -> Optional[str]:
    """
    Download SHA256SUMS for the given version and extract the checksum
    for artifact_name.
    """
    url = f"{GITHUB_RELEASE_BASE}/{version}/SHA256SUMS"

    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", f"Downloadyha/{__version__}")

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            content = resp.read().decode("utf-8")

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            checksum, filename = parts
            if filename.lstrip("*") == artifact_name:
                return checksum.lower()

        return None

    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return None


# ---------------------------------------------------------------------------
# Update execution
# ---------------------------------------------------------------------------

def _get_executable_path() -> Path:
    """Return the absolute path to the current running executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    else:
        return Path(__file__).resolve()


def perform_update(new_version: str) -> bool:
    """
    Download and install the update for new_version.

    Returns True on success, False on error.
    """
    c = Colors
    init_terminal()

    info(f"Preparing update to {c.BOLD}{new_version}{c.RESET}...")

    platform_id = _detect_platform()
    if platform_id is None:
        error("Unsupported operating system or architecture for auto-update.")
        return False

    artifact_name = _build_artifact_name(new_version, platform_id)
    download_url = f"{GITHUB_RELEASE_BASE}/{new_version}/{artifact_name}"
    temp_dir = Path(tempfile.mkdtemp(prefix="downloadyha-update-"))

    try:
        temp_artifact = temp_dir / artifact_name

        # Step 1: Download
        wait("Downloading update package from GitHub Releases...")
        if not _download_file(download_url, temp_artifact):
            error("Failed to download update package.")
            return False
        success("Download complete.")

        # Step 2: Checksum verification
        wait("Verifying SHA-256 integrity checksum...")
        expected_checksum = _fetch_checksum(new_version, artifact_name)
        if expected_checksum is None:
            error("Could not retrieve SHA256SUMS from GitHub.")
            return False

        actual_checksum = _compute_sha256(temp_artifact)
        if actual_checksum != expected_checksum:
            error("Integrity check failed: Checksum mismatch.")
            return False
        success("Checksum verified.")

        # Step 3: Extract
        wait("Extracting update files...")
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        if artifact_name.endswith(".zip"):
            with zipfile.ZipFile(temp_artifact, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
        elif artifact_name.endswith(".tar.gz"):
            with tarfile.open(temp_artifact, "r:gz") as tar_ref:
                tar_ref.extractall(extract_dir)
        else:
            error("Unsupported archive format.")
            return False

        exe_name = "downloadyha.exe" if platform.system() == "Windows" else "downloadyha"
        new_exe = None
        for item in extract_dir.rglob(exe_name):
            if item.is_file():
                new_exe = item
                break

        if new_exe is None:
            error(f"Could not find '{exe_name}' inside the update archive.")
            return False

        # Step 4: Replace executable
        wait("Applying update to current installation...")
        current_exe = _get_executable_path()

        if platform.system() == "Windows":
            old_backup = current_exe.with_suffix(current_exe.suffix + ".old")
            if old_backup.exists():
                try:
                    old_backup.unlink()
                except OSError:
                    pass

            try:
                current_exe.rename(old_backup)
                shutil.copy2(new_exe, current_exe)
            except OSError as e:
                error(f"Failed to replace executable: {e}")
                return False
        else:
            try:
                shutil.copy2(new_exe, current_exe)
                current_exe.chmod(current_exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            except OSError as e:
                error(f"Failed to replace executable: {e}")
                return False

        success(f"Downloadyha has been updated to {new_version}!")
        print(f"\n{c.BRIGHT_GREEN}Please restart the application to use the updated version.{c.RESET}\n")
        return True

    finally:
        try:
            shutil.rmtree(temp_dir)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Non-intrusive update notification on app start
# ---------------------------------------------------------------------------

def notify_update_available() -> None:
    """
    Check for updates in the background (respects 24-hour cache).
    If a new version is available, print a stylish notification badge.
    """
    new_version = check_for_updates(force=False)
    if new_version is not None:
        c = Colors
        print(f"{c.BRIGHT_YELLOW}╭────────────────────────────────────────────────────────╮{c.RESET}")
        print(f"{c.BRIGHT_YELLOW}│{c.RESET}  {Symbols.SPARKLE} {c.BOLD}A new version of Downloadyha is available!{c.RESET} ({c.CYAN}{new_version}{c.RESET})  {c.BRIGHT_YELLOW}│{c.RESET}")
        print(f"{c.BRIGHT_YELLOW}│{c.RESET}  Run {c.BOLD}{c.BRIGHT_WHITE}downloadyha update{c.RESET} to install the latest features.   {c.BRIGHT_YELLOW}│{c.RESET}")
        print(f"{c.BRIGHT_YELLOW}╰────────────────────────────────────────────────────────╯{c.RESET}\n")


# ---------------------------------------------------------------------------
# CLI command: downloadyha update
# ---------------------------------------------------------------------------

def handle_update_command() -> None:
    """Entry point for the 'downloadyha update' command."""
    init_terminal()
    c = Colors

    print()
    print(f"{c.BRIGHT_CYAN}╭────────────────────────────────────────────────────────╮{c.RESET}")
    print(f"{c.BRIGHT_CYAN}│{c.RESET} {c.BOLD}{c.BRIGHT_WHITE}                Downloadyha Updater                     {c.RESET} {c.BRIGHT_CYAN}│{c.RESET}")
    print(f"{c.BRIGHT_CYAN}╰────────────────────────────────────────────────────────╯{c.RESET}")
    print()

    wait("Checking for updates on GitHub...")
    new_version = check_for_updates(force=True)

    if new_version is None:
        success(f"You are already running the latest version ({__version__}).")
        return

    info(f"Current version : {Colors.BOLD}{__version__}{Colors.RESET}")
    info(f"Latest version  : {Colors.BOLD}{Colors.BRIGHT_GREEN}{new_version}{Colors.RESET}")

    if not prompt_confirm("Do you want to download and install this update now?", default=True):
        info("Update canceled.")
        return

    success_status = perform_update(new_version)
    if not success_status:
        warning(f"Update could not be completed automatically. Download manually from:\n  https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases")
