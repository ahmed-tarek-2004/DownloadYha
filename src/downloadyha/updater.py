"""
updater.py - Self-update mechanism for Downloadyha.

Responsibilities:
- Check GitHub Releases API for newer versions.
- Cache update checks (once per 24 hours).
- Download, verify (SHA-256), and atomically replace the running executable.
- Preserve user configuration during updates.
- Handle OS and architecture detection.

User consent is ALWAYS required. This module never auto-updates.
"""

import hashlib
import json
import os
import platform
import stat
import sys
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple

from . import __version__
from . import config


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# GitHub repository (REPLACE with actual owner/repo)
GITHUB_OWNER = "ahmed-tarek-2004"
GITHUB_REPO = "DownloadYha"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_RELEASE_BASE = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download"

# Update check cache duration in seconds (24 hours)
UPDATE_CHECK_INTERVAL = 24 * 60 * 60

# Timeout for network requests (seconds)
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
      - "windows-x64"
      - "linux-x64"
      - "linux-arm64"

    Returns None if the platform is unsupported.
    """
    system = platform.system()
    machine = platform.machine().lower()

    # Normalize architecture names
    if machine in ("x86_64", "amd64"):
        arch = "x64"
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
      downloadyha-1.0.0-windows-x64.exe
      downloadyha-1.0.0-linux-x64
    """
    ext = ".exe" if "windows" in platform_id else ""
    return f"downloadyha-{version}-{platform_id}{ext}"


# ---------------------------------------------------------------------------
# GitHub API
# ---------------------------------------------------------------------------

def _fetch_latest_release() -> Optional[dict]:
    """
    Fetch the latest release metadata from GitHub.

    Returns a dict with keys: 'tag_name', 'assets'.
    Returns None on error.
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
        - The new version string (e.g., "v1.1.0") if an update is available.
        - None if no update is available or if an error occurred.

    Side effect: updates the check timestamp cache.
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
    """
    Download a file from *url* to *dest_path*.

    Returns True on success, False on error.
    """
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
    for *artifact_name*.

    Returns the hex digest string on success, None on error.
    """
    # Example URL:
    # https://github.com/OWNER/REPO/releases/download/v1.0.0/SHA256SUMS
    url = f"{GITHUB_RELEASE_BASE}/{version}/SHA256SUMS"

    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", f"Downloadyha/{__version__}")

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            content = resp.read().decode("utf-8")

        # SHA256SUMS format: <hash>  <filename>
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            checksum, filename = parts
            if filename == artifact_name:
                return checksum.lower()

        return None

    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return None


# ---------------------------------------------------------------------------
# Update execution
# ---------------------------------------------------------------------------

def _get_executable_path() -> Path:
    """Return the absolute path to the current running executable."""
    # sys.executable points to the Python interpreter if running as a script,
    # or to the bundled executable if packaged (PyInstaller, etc.)
    #
    # For a PyInstaller bundle, sys.executable is the downloadyha.exe path.
    # For development, it's the python interpreter; in that case we can't
    # self-update. Check for frozen state.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    else:
        # Not a frozen executable; return the script path as a fallback
        # (self-update won't work in this mode)
        return Path(__file__).resolve()


def perform_update(new_version: str) -> bool:
    """
    Download and install the update for *new_version*.

    Steps:
      1. Detect platform.
      2. Build artifact name.
      3. Download artifact to a temporary file.
      4. Fetch and verify SHA-256 checksum.
      5. Atomically replace the current executable.
      6. Preserve user configuration (it lives in a separate directory).

    Returns True on success, False on error.

    Prints progress messages to stdout.
    """
    print(f"\nUpdating Downloadyha to {new_version}...\n")

    platform_id = _detect_platform()
    if platform_id is None:
        print("Error: Unsupported platform for auto-update.")
        return False

    artifact_name = _build_artifact_name(new_version, platform_id)
    print(f"Platform: {platform_id}")
    print(f"Artifact: {artifact_name}\n")

    # Download URL
    download_url = f"{GITHUB_RELEASE_BASE}/{new_version}/{artifact_name}"

    # Create a temporary directory for the download
    temp_dir = Path(tempfile.mkdtemp(prefix="downloadyha-update-"))

    try:
        temp_artifact = temp_dir / artifact_name

        # Step 1: Download the new executable
        print("Downloading update...")
        if not _download_file(download_url, temp_artifact):
            print("Error: Failed to download the update.")
            return False
        print("Download complete.\n")

        # Step 2: Fetch checksum
        print("Verifying checksum...")
        expected_checksum = _fetch_checksum(new_version, artifact_name)
        if expected_checksum is None:
            print("Error: Could not retrieve SHA-256 checksum.")
            return False

        # Step 3: Compute actual checksum
        actual_checksum = _compute_sha256(temp_artifact)

        if actual_checksum != expected_checksum:
            print("Error: Checksum verification failed.")
            print(f"  Expected: {expected_checksum}")
            print(f"  Got:      {actual_checksum}")
            return False
        print("Checksum verified.\n")

        # Step 4: Replace the current executable atomically
        print("Installing update...")
        current_exe = _get_executable_path()

        # On Windows, we can't overwrite a running .exe directly.
        # Strategy: rename current to .old, move new to original name.
        # On Linux, we can overwrite directly (running process keeps old inode).

        if platform.system() == "Windows":
            old_backup = current_exe.with_suffix(current_exe.suffix + ".old")
            # Remove any previous .old file
            if old_backup.exists():
                try:
                    old_backup.unlink()
                except OSError:
                    pass

            try:
                current_exe.rename(old_backup)
                temp_artifact.rename(current_exe)
            except OSError as e:
                print(f"Error: Failed to replace executable: {e}")
                return False

        else:
            # Linux: overwrite directly
            try:
                temp_artifact.replace(current_exe)
                # Ensure executable bit is set
                current_exe.chmod(current_exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            except OSError as e:
                print(f"Error: Failed to replace executable: {e}")
                return False

        print("Update installed successfully.\n")
        print(f"Downloadyha has been updated to {new_version}.")
        print("\nPlease restart the application to use the new version.")

        return True

    finally:
        # Clean up temp directory
        try:
            for item in temp_dir.iterdir():
                item.unlink()
            temp_dir.rmdir()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Non-intrusive update notification on app start
# ---------------------------------------------------------------------------

def notify_update_available() -> None:
    """
    Check for updates in the background (respects 24-hour cache).
    If a new version is available, print a non-intrusive message.

    Call this at application startup before the main menu.
    """
    new_version = check_for_updates(force=False)
    if new_version is not None:
        print()
        print("=" * 55)
        print(" A new version of Downloadyha is available!")
        print("=" * 55)
        print(f"  Current version: {__version__}")
        print(f"  Latest version:  {new_version}")
        print()
        print("  Run the following command to update:")
        print()
        print("      downloadyha update")
        print()
        print("=" * 55)
        print()


# ---------------------------------------------------------------------------
# CLI command: downloadyha update
# ---------------------------------------------------------------------------

def handle_update_command() -> None:
    """
    Entry point for the 'downloadyha update' command.

    Checks for updates (ignoring cache) and performs the update if available.
    """
    print()
    print("=" * 55)
    print("           Downloadyha Update")
    print("=" * 55)
    print()

    print("Checking for updates...")
    new_version = check_for_updates(force=True)

    if new_version is None:
        print(f"\nYou are already running the latest version ({__version__}).")
        return

    print(f"\nCurrent version: {__version__}")
    print(f"Latest version:  {new_version}")
    print()

    # Ask for confirmation
    response = input("Do you want to update now? [y/N]: ").strip().lower()
    if response not in ("y", "yes"):
        print("\nUpdate canceled.")
        return

    success = perform_update(new_version)
    if not success:
        print("\nUpdate failed. Please try again later or download manually from:")
        print(f"  https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases")
