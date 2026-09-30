"""
Dependency management for Downloadyha.

Handles resolution, verification, automatic downloading, and SHA-256
integrity checks of bundled dependencies (FFmpeg, FFprobe, Deno)
and provides yt-dlp configuration.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .paths import (
    ensure_directories,
    get_bin_dir,
    get_deno_executable_name,
    get_ffmpeg_executable_name,
    get_ffprobe_executable_name,
    get_log_dir,
)
from .platform import get_architecture, get_platform, is_linux, is_windows


class DependencyError(Exception):
    """Base exception for dependency-related errors."""
    pass


class DownloadError(DependencyError):
    """Raised when a dependency download fails."""
    pass


class VerificationError(DependencyError):
    """Raised when dependency checksum verification fails."""
    pass


class ExtractionError(DependencyError):
    """Raised when archive extraction fails."""
    pass


def load_versions() -> Dict[str, Any]:
    """
    Load the versions manifest from versions.json.

    Returns:
        Dictionary containing dependency version information.
    """
    versions_file = Path(__file__).parent / "versions.json"

    try:
        with open(versions_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_dependency_versions() -> Dict[str, str]:
    """
    Get human-readable versions of dependencies from the manifest.

    Returns:
        Dictionary of dependency names to version strings.
    """
    versions = load_versions()
    result: Dict[str, str] = {}

    if "downloadyha" in versions:
        result["downloadyha"] = str(versions["downloadyha"])

    if "yt_dlp" in versions:
        result["yt-dlp"] = str(versions["yt_dlp"])

    if "ffmpeg" in versions and isinstance(versions["ffmpeg"], dict):
        result["ffmpeg"] = str(versions["ffmpeg"].get("version", "unknown"))

    if "deno" in versions and isinstance(versions["deno"], dict):
        result["deno"] = str(versions["deno"].get("version", "unknown"))

    return result


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal SHA-256 checksum string in lowercase.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def _make_executable(file_path: Path) -> None:
    """
    Ensure a file has executable permissions on POSIX / Linux platforms.

    Args:
        file_path: Path to the executable file.
    """
    if not is_windows() and file_path.exists():
        current_mode = file_path.stat().st_mode
        file_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _download_file(url: str, dest_path: Path) -> None:
    """
    Download a file from a URL over HTTPS to destination path atomically.

    Args:
        url: URL to download from.
        dest_path: Final destination path.

    Raises:
        DownloadError: If the download fails.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dest = dest_path.with_suffix(dest_path.suffix + ".download.tmp")

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Downloadyha-Dependency-Resolver/1.0"}
        )
        with urllib.request.urlopen(request, timeout=300) as response:
            with open(temp_dest, "wb") as f:
                shutil.copyfileobj(response, f)

        if temp_dest.exists():
            if dest_path.exists():
                dest_path.unlink()
            temp_dest.rename(dest_path)
    except urllib.error.URLError as e:
        if temp_dest.exists():
            temp_dest.unlink()
        raise DownloadError(f"Failed to download {url}: {e}") from e
    except Exception as e:
        if temp_dest.exists():
            temp_dest.unlink()
        raise DownloadError(f"Error while downloading {url}: {e}") from e


def _extract_archive(archive_path: Path, extract_dir: Path, archive_type: str) -> None:
    """
    Extract an archive safely into a directory.

    Args:
        archive_path: Path to the archive file.
        extract_dir: Destination directory.
        archive_type: "zip", "tar.xz", "tar.gz", etc.

    Raises:
        ExtractionError: If extraction fails.
    """
    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        if archive_type == "zip" or archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(extract_dir)
        elif "tar" in archive_type or archive_path.name.endswith((".tar.xz", ".tar.gz", ".tar.bz2", ".txz")):
            mode = "r:xz" if archive_path.name.endswith((".tar.xz", ".txz")) else "r:*"
            with tarfile.open(archive_path, mode) as tf:
                tf.extractall(extract_dir)
        else:
            raise ExtractionError(f"Unsupported archive format: {archive_type}")
    except Exception as e:
        raise ExtractionError(f"Failed to extract {archive_path}: {e}") from e


def download_and_install_dependency(dep_name: str) -> bool:
    """
    Download and install a dependency (ffmpeg or deno) according to versions.json.

    Args:
        dep_name: "ffmpeg" or "deno"

    Returns:
        True if successfully downloaded and installed, False otherwise.
    """
    versions = load_versions()
    platform_name = get_platform()
    arch_name = get_architecture()

    dep_config = versions.get(dep_name, {})
    platform_config = dep_config.get(platform_name, {})
    target_config = platform_config.get(arch_name)

    if not target_config:
        print(f"No download configuration for {dep_name} on {platform_name} ({arch_name}).")
        return False

    url = target_config.get("url")
    expected_sha256 = target_config.get("sha256")
    archive_type = target_config.get("archive_type", "zip")
    bin_path_in_archive = target_config.get("bin_path_in_archive")
    probe_path_in_archive = target_config.get("probe_path_in_archive")

    if not url or not bin_path_in_archive:
        print(f"Invalid configuration for {dep_name}.")
        return False

    ensure_directories()
    bin_dir = get_bin_dir()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        archive_dest = temp_dir_path / f"{dep_name}_archive"

        print(f"Downloading {dep_name}...")
        try:
            _download_file(url, archive_dest)
        except DownloadError as e:
            print(f"Download failed: {e}")
            return False

        # Verify SHA-256 if specified
        if expected_sha256:
            actual_sha256 = calculate_sha256(archive_dest)
            if actual_sha256.lower() != expected_sha256.lower():
                print(f"Verification failed for {dep_name}: SHA-256 checksum mismatch.")
                print(f"Expected: {expected_sha256}")
                print(f"Actual:   {actual_sha256}")
                return False

        # Extract archive
        extract_dir = temp_dir_path / "extracted"
        try:
            _extract_archive(archive_dest, extract_dir, archive_type)
        except ExtractionError as e:
            print(f"Extraction failed: {e}")
            return False

        # Copy primary binary
        src_bin = extract_dir / bin_path_in_archive
        if not src_bin.exists():
            # Search if nested differently
            candidates = list(extract_dir.glob(f"**/{Path(bin_path_in_archive).name}"))
            if candidates:
                src_bin = candidates[0]
            else:
                print(f"Could not locate {bin_path_in_archive} in extracted archive.")
                return False

        if dep_name == "ffmpeg":
            final_bin_name = get_ffmpeg_executable_name()
        elif dep_name == "deno":
            final_bin_name = get_deno_executable_name()
        else:
            final_bin_name = Path(bin_path_in_archive).name

        target_bin_path = bin_dir / final_bin_name
        if target_bin_path.exists():
            try:
                target_bin_path.unlink()
            except Exception:
                pass

        shutil.copy2(src_bin, target_bin_path)
        _make_executable(target_bin_path)

        # Handle secondary binary (e.g. ffprobe in ffmpeg archive)
        if probe_path_in_archive:
            src_probe = extract_dir / probe_path_in_archive
            if not src_probe.exists():
                probe_candidates = list(extract_dir.glob(f"**/{Path(probe_path_in_archive).name}"))
                if probe_candidates:
                    src_probe = probe_candidates[0]

            if src_probe.exists():
                target_probe_name = get_ffprobe_executable_name()
                target_probe_path = bin_dir / target_probe_name
                if target_probe_path.exists():
                    try:
                        target_probe_path.unlink()
                    except Exception:
                        pass
                shutil.copy2(src_probe, target_probe_path)
                _make_executable(target_probe_path)

        print(f"Installed {dep_name} successfully.")
        return True


def get_ffmpeg_path(auto_download: bool = True) -> Optional[Path]:
    """
    Get the path to the FFmpeg executable.
    Checks bundled/app binary directory first, then falls back to system PATH.
    Automatically downloads if missing when auto_download is True.

    Args:
        auto_download: Whether to attempt downloading if missing.

    Returns:
        Path to FFmpeg executable, or None if unavailable.
    """
    bin_dir = get_bin_dir()
    ffmpeg_name = get_ffmpeg_executable_name()
    ffmpeg_path = bin_dir / ffmpeg_name

    if ffmpeg_path.exists():
        _make_executable(ffmpeg_path)
        return ffmpeg_path

    # Fall back to system FFmpeg
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return Path(system_ffmpeg)

    # Auto download if permitted
    if auto_download:
        if download_and_install_dependency("ffmpeg"):
            if ffmpeg_path.exists():
                return ffmpeg_path

    return None


def get_ffprobe_path(auto_download: bool = True) -> Optional[Path]:
    """
    Get the path to the FFprobe executable.
    Checks bundled/app binary directory first, then falls back to system PATH.
    Automatically downloads if missing when auto_download is True.

    Args:
        auto_download: Whether to attempt downloading if missing.

    Returns:
        Path to FFprobe executable, or None if unavailable.
    """
    bin_dir = get_bin_dir()
    ffprobe_name = get_ffprobe_executable_name()
    ffprobe_path = bin_dir / ffprobe_name

    if ffprobe_path.exists():
        _make_executable(ffprobe_path)
        return ffprobe_path

    # Fall back to system FFprobe
    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        return Path(system_ffprobe)

    # Auto download if permitted (ffprobe is packaged with ffmpeg)
    if auto_download:
        if download_and_install_dependency("ffmpeg"):
            if ffprobe_path.exists():
                return ffprobe_path

    return None


def get_deno_path(auto_download: bool = True) -> Optional[Path]:
    """
    Get the path to the Deno executable.
    Checks bundled/app binary directory first, then falls back to system PATH.
    Automatically downloads if missing when auto_download is True.

    Args:
        auto_download: Whether to attempt downloading if missing.

    Returns:
        Path to Deno executable, or None if unavailable.
    """
    bin_dir = get_bin_dir()
    deno_name = get_deno_executable_name()
    deno_path = bin_dir / deno_name

    if deno_path.exists():
        _make_executable(deno_path)
        return deno_path

    # Fall back to system Deno
    system_deno = shutil.which("deno")
    if system_deno:
        return Path(system_deno)

    # Auto download if permitted
    if auto_download:
        if download_and_install_dependency("deno"):
            if deno_path.exists():
                return deno_path

    return None


def get_yt_dlp() -> Any:
    """
    Get the yt-dlp module.

    Returns:
        The imported yt_dlp module.

    Raises:
        DependencyError: If yt-dlp cannot be imported.
    """
    try:
        import yt_dlp
        return yt_dlp
    except ImportError as e:
        raise DependencyError(
            "yt-dlp is not available. Please ensure the package is properly installed."
        ) from e


def check_ffmpeg() -> Tuple[bool, Optional[Path]]:
    """
    Check if FFmpeg is available (without auto-downloading).

    Returns:
        Tuple of (is_available, path).
    """
    ffmpeg_path = get_ffmpeg_path(auto_download=False)
    return (ffmpeg_path is not None, ffmpeg_path)


def check_ffprobe() -> Tuple[bool, Optional[Path]]:
    """
    Check if FFprobe is available (without auto-downloading).

    Returns:
        Tuple of (is_available, path).
    """
    ffprobe_path = get_ffprobe_path(auto_download=False)
    return (ffprobe_path is not None, ffprobe_path)


def check_deno() -> Tuple[bool, Optional[Path]]:
    """
    Check if Deno is available (without auto-downloading).

    Returns:
        Tuple of (is_available, path).
    """
    deno_path = get_deno_path(auto_download=False)
    return (deno_path is not None, deno_path)


def check_dependencies(auto_download: bool = True) -> bool:
    """
    Check if all required dependencies are available, downloading them if needed.

    Args:
        auto_download: Whether to attempt auto-downloading missing binaries.

    Returns:
        True if all dependencies are ready, False otherwise.
    """
    ensure_directories()
    missing: List[str] = []

    ffmpeg_path = get_ffmpeg_path(auto_download=auto_download)
    if not ffmpeg_path:
        missing.append("FFmpeg")

    ffprobe_path = get_ffprobe_path(auto_download=auto_download)
    if not ffprobe_path:
        missing.append("FFprobe")

    deno_path = get_deno_path(auto_download=auto_download)
    if not deno_path:
        missing.append("Deno")

    try:
        get_yt_dlp()
    except DependencyError:
        missing.append("yt-dlp")

    if not missing:
        return True

    print("\nMissing dependencies:")
    for dependency in missing:
        print(f"  - {dependency}")

    print(
        "\nPlease run 'downloadyha repair' or install the missing dependencies "
        "before using Downloadyha."
    )
    return False


def verify_dependencies() -> bool:
    """
    Verify all dependencies and print their locations.

    Returns:
        True if all dependencies are available, False otherwise.
    """
    all_available = True

    # Check FFmpeg
    ffmpeg_available, ffmpeg_path = check_ffmpeg()
    if ffmpeg_available:
        print(f"FFmpeg: {ffmpeg_path}")
    else:
        print("FFmpeg: NOT FOUND")
        all_available = False

    # Check FFprobe
    ffprobe_available, ffprobe_path = check_ffprobe()
    if ffprobe_available:
        print(f"FFprobe: {ffprobe_path}")
    else:
        print("FFprobe: NOT FOUND")
        all_available = False

    # Check Deno
    deno_available, deno_path = check_deno()
    if deno_available:
        print(f"Deno: {deno_path}")
    else:
        print("Deno: NOT FOUND")
        all_available = False

    # Check yt-dlp
    try:
        yt = get_yt_dlp()
        print(f"yt-dlp: available ({getattr(yt, '__version__', 'unknown')})")
    except DependencyError:
        print("yt-dlp: NOT FOUND")
        all_available = False

    return all_available


def repair_dependencies() -> bool:
    """
    Force re-download and verification of all managed dependencies.

    Returns:
        True if all dependencies were successfully repaired.
    """
    print("Repairing dependencies...")
    ffmpeg_ok = download_and_install_dependency("ffmpeg")
    deno_ok = download_and_install_dependency("deno")

    success = ffmpeg_ok and deno_ok
    if success:
        print("\nAll dependencies repaired successfully.")
    else:
        print("\nSome dependencies could not be repaired.")
    return success
