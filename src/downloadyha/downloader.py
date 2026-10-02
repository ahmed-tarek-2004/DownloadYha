"""
downloader.py - Robust video, audio, and playlist downloader using yt-dlp.

Supports:
- Single video downloads (custom resolution up to 4K, audio/video stream merging into MP4/MKV).
- Single audio downloads (MP3 extraction with customizable bitrate: 320k, 192k, 128k, best).
- Full Playlist downloads (video or audio, indexed filenames, organized folder hierarchy).
- Automatic detection of single media vs playlist URLs.
- Multi-platform support (YouTube, TikTok, Facebook, Instagram, Twitter/X, and more).
- Real-time progress reporting hooks and structured DownloadResult return types.
- Per-item error tolerance (ignoreerrors) so single broken videos don't fail a playlist.
- Cross-platform dependency integration (bundled FFmpeg and Deno runtimes).
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import parse_qs, urlparse

import yt_dlp

from .dependencies import get_deno_path, get_ffmpeg_path
from .logging import get_logger

# Optional UI rendering integration
try:
    from .ui import render_progress
except ImportError:
    render_progress = None


# ---------------------------------------------------------------------------
# Constants & Quality Definitions
# ---------------------------------------------------------------------------

AUDIO_QUALITY_MAP: Dict[str, str] = {
    "1": "0",       # Best quality (VBR ~256-320 kbps)
    "2": "320",     # 320 kbps (CBR High)
    "3": "192",     # 192 kbps (CBR Standard)
    "4": "128",     # 128 kbps (CBR Compact)
}

VIDEO_QUALITY_PRESETS: List[Tuple[str, int, str]] = [
    ("1", 0, "Best Available (Maximum Quality)"),
    ("2", 2160, "2160p (4K UHD)"),
    ("3", 1440, "1440p (2K QHD)"),
    ("4", 1080, "1080p (Full HD)"),
    ("5", 720, "720p (HD)"),
    ("6", 480, "480p (SD)"),
    ("7", 360, "360p (Low)"),
]


# ---------------------------------------------------------------------------
# Data Classes & Result Structures
# ---------------------------------------------------------------------------

@dataclass
class DownloadResult:
    """
    Structured summary returned after completing a download operation.

    Supports:
    - Boolean evaluation (if download_video(...): ...)
    - Dictionary-like access (result["success"], result.get("output_dir"))
    - Direct attribute access (result.completed_items, result.errors)
    """
    success: bool
    message: str = ""
    download_type: str = "video"  # "video" or "audio"
    is_playlist: bool = False
    total_items: int = 1
    completed_items: int = 0
    failed_items: int = 0
    files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    download_directory: str = ""
    playlist_title: Optional[str] = None

    def __bool__(self) -> bool:
        """Evaluate truthiness based on overall operation success."""
        return self.success

    @property
    def output_dir(self) -> str:
        """Alias for download_directory for backwards compatibility."""
        return self.download_directory

    def to_dict(self) -> Dict[str, Any]:
        """Convert result into a serializable dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "download_type": self.download_type,
            "is_playlist": self.is_playlist,
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "failed_items": self.failed_items,
            "files": self.files,
            "errors": self.errors,
            "download_directory": self.download_directory,
            "output_dir": self.download_directory,
            "playlist_title": self.playlist_title,
        }

    def __getitem__(self, item: str) -> Any:
        return self.to_dict()[item]

    def get(self, item: str, default: Any = None) -> Any:
        return self.to_dict().get(item, default)

    def __contains__(self, item: str) -> bool:
        return item in self.to_dict()


# ---------------------------------------------------------------------------
# Filename & URL Helpers
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    """
    Sanitize a string so it can be safely used as a filename across all OSes.

    Removes or replaces invalid characters (/ \\ : * ? " < > | \0) and trims whitespace.
    """
    if not name:
        return "download"
    # Replace illegal filesystem characters with underscore
    sanitized = re.sub(r'[\\/*?:"<>|\x00-\x1f]+', '_', str(name))
    # Strip leading and trailing periods, spaces, and underscores
    sanitized = sanitized.strip('. _')
    # Collapse multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized or "download"


def sanitize_folder_name(name: str) -> str:
    """
    Sanitize a string for safe use as a directory name on Windows and Linux.
    """
    if not name:
        return "Media_Download"
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '_', str(name)).strip('. _')
    clean = re.sub(r'_+', '_', clean)
    return clean if clean else "Media_Download"


def is_playlist_url(url: str) -> bool:
    """
    Check if a given URL represents a playlist or collection.

    Handles:
    - https://www.youtube.com/playlist?list=...
    - https://www.youtube.com/watch?v=...&list=...
    - Channel playlists, tabs, albums, and sets.
    """
    if not url:
        return False

    url_str = str(url).strip()
    url_lower = url_str.lower()

    # Direct playlist paths
    if "/playlist" in url_lower:
        return True

    # Check query parameters for playlist ID
    try:
        parsed = urlparse(url_str)
        params = parse_qs(parsed.query)
        if "list" in params and params["list"]:
            return True
    except Exception:
        pass

    # Generic sets or albums
    if "/sets/" in url_lower or "/album/" in url_lower:
        return True

    return False


def is_playlist(info: Optional[Dict[str, Any]]) -> bool:
    """
    Check whether an extracted yt-dlp metadata dictionary represents a playlist.
    """
    if not info or not isinstance(info, dict):
        return False

    if info.get("_type") in ("playlist", "multi_video"):
        return True

    # Has entries key with list/generator
    if "entries" in info and info.get("entries") is not None:
        return True

    # Explicit playlist count without single video formats
    if info.get("playlist_count") and not info.get("formats"):
        return True

    return False


def get_playlist_entries(info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract list of non-null entries from playlist info.
    """
    if not is_playlist(info):
        return [info]
    entries = info.get("entries", [])
    if isinstance(entries, list):
        return [e for e in entries if e is not None]
    try:
        return [e for e in list(entries) if e is not None]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Unit & Progress Formatting Helpers
# ---------------------------------------------------------------------------

def format_bytes(bytes_count: Optional[Union[int, float]]) -> str:
    """Format bytes count into human-readable string (e.g., '14.2 MB')."""
    if bytes_count is None or bytes_count <= 0:
        return "N/A"
    units = ["B", "KB", "MB", "GB", "TB"]
    val = float(bytes_count)
    unit_idx = 0
    while val >= 1024.0 and unit_idx < len(units) - 1:
        val /= 1024.0
        unit_idx += 1
    return f"{val:.1f} {units[unit_idx]}"


def format_speed(speed: Optional[Union[int, float]]) -> str:
    """Format download speed in bytes/s into human-readable string."""
    if speed is None or speed <= 0:
        return "N/A"
    return f"{format_bytes(speed)}/s"


def format_eta(seconds: Optional[Union[int, float]]) -> str:
    """Format ETA seconds into MM:SS or HH:MM:SS."""
    if seconds is None or seconds < 0:
        return "N/A"
    s = int(seconds)
    hrs = s // 3600
    mins = (s % 3600) // 60
    secs = s % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


# ---------------------------------------------------------------------------
# yt-dlp Options & Logging
# ---------------------------------------------------------------------------

class YtDlpMessageCollector:
    """
    Custom logger that intercepts yt-dlp messages, capturing errors and warnings
    while routing them to the downloadyha logger.
    """

    def __init__(self, logger_name: str = "downloader"):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self._logger = get_logger(logger_name)

    def debug(self, msg: str) -> None:
        self._logger.debug(msg)

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def warning(self, msg: str) -> None:
        self.warnings.append(str(msg))
        self._logger.warning(msg)

    def error(self, msg: str) -> None:
        self.errors.append(str(msg))
        self._logger.error(msg)


def get_yt_dlp_options(
    extra_options: Optional[Dict[str, Any]] = None,
    logger_instance: Optional[Any] = None,
    auto_download_deps: bool = False
) -> Dict[str, Any]:
    """
    Get common yt-dlp options configured with bundled dependencies.

    Configures:
    - Quiet mode and warning suppression.
    - Bundled/system Deno JavaScript runtime if available.
    - Bundled/system FFmpeg directory for media conversion and muxing.
    - Clean options without remote components.

    Args:
        extra_options: Optional extra parameters to merge into options.
        logger_instance: Optional custom logger instance.
        auto_download_deps: Whether to auto-download missing dependencies.

    Returns:
        Dictionary of yt-dlp options.
    """
    options: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": False,
        "ignoreerrors": False,
        "logtostderr": False,
    }

    # Configure Deno runtime for yt-dlp JS execution
    deno_path = get_deno_path(auto_download=auto_download_deps)
    if deno_path and deno_path.exists():
        options["js_runtimes"] = {
            "deno": {
                "path": str(deno_path)
            }
        }
    else:
        options["js_runtimes"] = {
            "deno": {}
        }

    # Configure FFmpeg location
    ffmpeg_path = get_ffmpeg_path(auto_download=auto_download_deps)
    if ffmpeg_path and ffmpeg_path.exists():
        options["ffmpeg_location"] = str(ffmpeg_path.parent)

    # Attach logger if provided
    if logger_instance:
        options["logger"] = logger_instance

    # Merge caller options
    if extra_options:
        options.update(extra_options)

    return options


# ---------------------------------------------------------------------------
# Metadata Extraction
# ---------------------------------------------------------------------------

def get_media_info(
    url: str,
    extract_flat: Union[bool, str] = "in_playlist",
    process: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Extract video or playlist information from a media URL.

    Args:
        url: Media video or playlist URL.
        extract_flat: 'in_playlist' (fast playlist entries), True, or False.
        process: Whether to fully process video info.

    Returns:
        Media information dictionary, or None if extraction failed.
    """
    logger = get_logger("downloader")
    options = get_yt_dlp_options({
        "extract_flat": extract_flat,
    })

    try:
        logger.info(f"Extracting media info for URL: {url}")
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False, process=process)

        if not info:
            logger.warning(f"No media info returned for: {url}")
            return None

        # Materialize entries list if returned as iterator/generator
        if "entries" in info and info["entries"] is not None:
            if not isinstance(info["entries"], list):
                try:
                    info["entries"] = [e for e in info["entries"] if e is not None]
                except Exception as e:
                    logger.warning(f"Error materializing playlist entries: {e}")
                    info["entries"] = []

        # Tag playlist status
        info["is_playlist"] = is_playlist(info)
        return info

    except Exception as e:
        logger.error(f"Failed to get media information: {e}")
        return None


def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract video or playlist information from a media URL.

    Maintains full backward compatibility.

    Args:
        url: Media URL.

    Returns:
        Information dictionary, or None if extraction failed.
    """
    return get_media_info(url, extract_flat="in_playlist")


def get_playlist_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract playlist information from a media URL.

    Args:
        url: Media playlist URL.

    Returns:
        Playlist information dictionary, or None if not a playlist or failed.
    """
    info = get_media_info(url, extract_flat="in_playlist")
    if info and is_playlist(info):
        return info
    return None


# ---------------------------------------------------------------------------
# Quality Selection
# ---------------------------------------------------------------------------

def get_video_qualities(info: Dict[str, Any]) -> List[int]:
    """
    Extract available video qualities from video info.

    Args:
        info: Video or playlist information dictionary from yt-dlp.

    Returns:
        Sorted list of available video heights descending (e.g., [1080, 720, 480, 360]).
    """
    formats = info.get("formats", [])
    heights: Set[int] = set()

    for fmt in formats:
        height = fmt.get("height")
        if height and isinstance(height, int) and height >= 144:
            heights.add(height)

    if heights:
        return sorted(heights, reverse=True)

    # Default resolution list for playlists or flat extraction
    return [1080, 720, 480, 360]


def choose_video_quality(info: Optional[Dict[str, Any]] = None) -> Optional[int]:
    """
    Prompt user to select video quality.

    Args:
        info: Optional media information dictionary.

    Returns:
        Selected video height (e.g., 1080, 720, 0 for best), or None if invalid.
    """
    # Single video with specific available formats
    if info and not is_playlist(info) and info.get("formats"):
        heights = get_video_qualities(info)
        if not heights:
            print("\nNo specific video qualities found. Defaulting to Best.")
            return 0

        print("\nAvailable video qualities:")
        print("0. Best Available (Maximum Quality)")
        for index, height in enumerate(heights, start=1):
            print(f"{index}. {height}p")

        choice = input("\nChoose quality [0 for Best]: ").strip()

        if choice in ("0", "", "best", "b"):
            return 0

        try:
            index = int(choice) - 1
            if 0 <= index < len(heights):
                return heights[index]
            print("Invalid choice.")
            return None
        except ValueError:
            print("Invalid choice.")
            return None

    # Preset menu for playlists or generic selections
    print("\nAvailable video qualities:")
    for key, height, label in VIDEO_QUALITY_PRESETS:
        print(f"{key}. {label}")

    choice = input(f"\nChoose quality [1-{len(VIDEO_QUALITY_PRESETS)}]: ").strip()

    preset_map = {k: h for k, h, _ in VIDEO_QUALITY_PRESETS}

    if choice in preset_map:
        return preset_map[choice]
    elif choice == "" or choice.lower() == "best":
        return 0

    print("Invalid choice.")
    return None


def choose_audio_quality() -> Optional[str]:
    """
    Prompt user to select audio quality for MP3 conversion.

    Returns:
        Selected audio quality string for FFmpeg ("0", "320", "192", "128"), or None.
    """
    print("\nAvailable audio qualities:")
    print("1. Best (Variable Bitrate ~256-320 kbps)")
    print("2. 320 kbps (High Quality)")
    print("3. 192 kbps (Standard Quality)")
    print("4. 128 kbps (Compact Size)")

    choice = input("\nChoose quality [1-4]: ").strip()

    quality = AUDIO_QUALITY_MAP.get(choice)

    if quality is None and (choice == "" or choice.lower() == "best"):
        return "0"
    elif quality is None:
        print("Invalid choice.")
        return None

    return quality


def resolve_video_format(height: Optional[int] = None, has_ffmpeg: bool = True) -> str:
    """
    Build yt-dlp format selector string for video downloads.

    Args:
        height: Maximum video height resolution (e.g., 1080, 720, 0 for best).
        has_ffmpeg: Whether FFmpeg is available to mux separate video and audio streams.

    Returns:
        yt-dlp format string.
    """
    if not has_ffmpeg:
        # Fallback to single-file progressive streams with audio if FFmpeg is absent
        if height and height > 0:
            return f"best[height<={height}][acodec!=none]/best[acodec!=none]/best"
        return "best[acodec!=none]/best"

    if height and height > 0:
        return (
            f"bestvideo[height<={height}]+bestaudio/"
            f"best[height<={height}]/"
            f"bestvideo+bestaudio/best"
        )
    return "bestvideo+bestaudio/best"


def resolve_audio_quality(quality: Optional[Union[str, int]] = None) -> str:
    """
    Normalize audio quality input to valid FFmpeg quality value.

    Args:
        quality: Audio quality parameter ("best", "0", "320", "320k", "192", 128, etc.)

    Returns:
        Normalized quality string ("0", "128", "192", "320").
    """
    if not quality or quality in ("0", "best", "bestaudio"):
        return "0"

    q_str = str(quality).lower().rstrip("k").strip()
    if q_str in ("320", "192", "128", "256", "96", "64"):
        return q_str

    return "0"


# ---------------------------------------------------------------------------
# Progress Hooks & Statistics Tracking
# ---------------------------------------------------------------------------

def create_progress_hook(
    custom_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    stats_tracker: Optional[Dict[str, Any]] = None
) -> Callable[[Dict[str, Any]], None]:
    """
    Create a robust progress hook for yt-dlp downloads.

    Args:
        custom_callback: Optional user callback receiving parsed progress dict.
        stats_tracker: Optional dictionary tracking files and completion metrics.

    Returns:
        Callable hook compatible with yt-dlp's progress_hooks.
    """
    def hook(data: Dict[str, Any]) -> None:
        status = data.get("status")
        info_dict = data.get("info_dict", {}) or {}

        # Extract playlist metrics
        pl_index = data.get("playlist_index") or info_dict.get("playlist_index")
        pl_count = data.get("playlist_count") or data.get("n_entries") or info_dict.get("playlist_count")
        item_title = info_dict.get("title") or ""
        filename = data.get("filename") or ""

        # Update stats tracker
        if stats_tracker is not None:
            if pl_count and "total_items" in stats_tracker:
                stats_tracker["total_items"] = max(stats_tracker.get("total_items", 1), pl_count)
            if status == "finished" and filename:
                files_list = stats_tracker.setdefault("files", [])
                if filename not in files_list:
                    files_list.append(filename)
                    stats_tracker["completed_items"] = stats_tracker.get("completed_items", 0) + 1

        # Dispatch to custom callback if present
        if custom_callback:
            try:
                downloaded = data.get("downloaded_bytes", 0) or 0
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                percent = (downloaded / total * 100.0) if total > 0 else 0.0
                speed = data.get("speed")
                eta = data.get("eta")

                event = {
                    "status": status,
                    "percent": percent,
                    "percent_str": data.get("_percent_str", f"{percent:.1f}%").strip(),
                    "downloaded_bytes": downloaded,
                    "total_bytes": total,
                    "size_str": f"{format_bytes(downloaded)}/{format_bytes(total)}" if total else format_bytes(downloaded),
                    "speed": speed,
                    "speed_str": data.get("_speed_str", format_speed(speed)).strip(),
                    "eta": eta,
                    "eta_str": data.get("_eta_str", format_eta(eta)).strip(),
                    "filename": filename,
                    "item_title": item_title,
                    "playlist_index": pl_index,
                    "playlist_count": pl_count,
                    "raw_data": data,
                }
                custom_callback(event)
            except Exception:
                pass

        # Progress rendering: prefer UI renderer if available, else stdout
        if render_progress is not None and not custom_callback:
            render_progress(data, playlist_index=pl_index, playlist_total=pl_count)
        elif not custom_callback:
            if status == "downloading":
                percentage = data.get("_percent_str", "").strip()
                speed = data.get("_speed_str", "").strip()
                eta = data.get("_eta_str", "").strip()

                pl_prefix = f"[{pl_index}/{pl_count}] " if (pl_index and pl_count) else ""
                out = f"\rDownloading {pl_prefix}{percentage} | Speed: {speed} | ETA: {eta}"
                sys.stdout.write(out)
                sys.stdout.flush()

            elif status == "finished":
                pl_suffix = f" (Item {pl_index}/{pl_count})" if (pl_index and pl_count) else ""
                sys.stdout.write(f"\nProcessing file{pl_suffix}...\n")
                sys.stdout.flush()

    return hook


def progress_hook(data: Dict[str, Any]) -> None:
    """
    Default progress hook for backward compatibility.
    """
    default_hook = create_progress_hook()
    default_hook(data)


# ---------------------------------------------------------------------------
# Core Download Operations
# ---------------------------------------------------------------------------

def download_media(
    url: str,
    download_path: str,
    media_type: str = "video",
    quality: Any = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    output_format: str = "mp4"
) -> DownloadResult:
    """
    Download media (single video, audio, or entire playlist) from a URL.

    Handles:
    - Automatic detection and handling of playlists.
    - Saving playlists in organized subfolders with indexed filenames.
    - Merging video and audio into MP4/MKV.
    - Converting audio to MP3 with chosen quality/bitrate.
    - Graceful error tolerance for individual failed playlist items.

    Args:
        url: Video, audio, or playlist URL (YouTube, TikTok, Social Media, etc.).
        download_path: Target root download directory.
        media_type: "video" or "audio".
        quality: Video height (int/preset) or Audio bitrate string ("0", "320", "192", "128").
        progress_callback: Optional callback for UI progress updates.
        output_format: Video container format (default: "mp4").

    Returns:
        DownloadResult instance containing status and statistics.
    """
    logger = get_logger("downloader")
    media_type = media_type.lower().strip()

    # Extract media metadata
    logger.info(f"Checking media info for download: url={url}, type={media_type}")
    info = get_media_info(url, extract_flat="in_playlist")
    is_pl = is_playlist(info) or is_playlist_url(url)

    # Determine destination folder and filename template
    if is_pl:
        pl_title = (info.get("title") if info else None) or "Playlist"
        safe_pl_title = sanitize_folder_name(pl_title)
        target_dir = os.path.join(download_path, safe_pl_title)
        outtmpl = os.path.join(
            target_dir,
            "%(playlist_index&{:02d} - |)s%(title)s.%(ext)s"
        )
        entries = info.get("entries") if info else []
        entries_count = len(entries) if entries else (info.get("playlist_count") or 1 if info else 1)
    else:
        pl_title = None
        target_dir = download_path
        outtmpl = os.path.join(target_dir, "%(title)s.%(ext)s")
        entries_count = 1

    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory {target_dir}: {e}")
        return DownloadResult(
            success=False,
            message=f"Failed to create target folder: {e}",
            download_type=media_type,
            is_playlist=is_pl,
            errors=[str(e)],
            download_directory=target_dir
        )

    # Ensure dependencies (FFmpeg for stream merging / MP3 extraction, Deno for JS solver)
    ffmpeg_path = get_ffmpeg_path(auto_download=True)
    has_ffmpeg = ffmpeg_path is not None and ffmpeg_path.exists()

    # Set up progress and stats tracking
    stats_tracker: Dict[str, Any] = {
        "total_items": entries_count,
        "completed_items": 0,
        "files": [],
    }
    hook = create_progress_hook(progress_callback, stats_tracker)
    collector = YtDlpMessageCollector("downloader")

    # Build yt-dlp options based on media type
    extra_options: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "ignoreerrors": True,
        "progress_hooks": [hook],
    }

    if media_type == "audio":
        audio_quality = resolve_audio_quality(quality)
        extra_options.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": audio_quality,
                }
            ],
        })
        desc_str = f"audio (MP3, quality: {audio_quality})"
    else:
        # Video download
        height = int(quality) if (quality is not None and str(quality).isdigit()) else 0
        video_format = resolve_video_format(height, has_ffmpeg=has_ffmpeg)
        extra_options.update({
            "format": video_format,
            "merge_output_format": output_format,
        })
        desc_str = f"video (format: {output_format}, max height: {height or 'best'}p)"

    options = get_yt_dlp_options(extra_options, logger_instance=collector, auto_download_deps=True)
    if has_ffmpeg and "ffmpeg_location" not in options:
        options["ffmpeg_location"] = str(ffmpeg_path.parent)

    try:
        logger.info(f"Starting download: url={url}, type={desc_str}, is_playlist={is_pl}")
        print(f"\nDownloading {desc_str}...\n")

        with yt_dlp.YoutubeDL(options) as ydl:
            exit_code = ydl.download([url])

        completed = stats_tracker["completed_items"]
        total = max(stats_tracker["total_items"], completed)
        errors = collector.errors

        # For single items without explicit hook finish increment
        if exit_code == 0 and completed == 0 and not is_pl:
            completed = 1

        failed = max(0, total - completed)
        success = completed > 0 or (exit_code == 0 and len(errors) == 0)

        if is_pl:
            summary_msg = f"Playlist download finished: {completed}/{total} items completed successfully."
        else:
            summary_msg = "Download completed successfully."

        result = DownloadResult(
            success=success,
            message=summary_msg,
            download_type=media_type,
            is_playlist=is_pl,
            total_items=total,
            completed_items=completed,
            failed_items=failed,
            files=stats_tracker["files"],
            errors=errors,
            download_directory=target_dir,
            playlist_title=pl_title
        )

        if success:
            logger.info(summary_msg)
            print(f"\n{summary_msg}")
        else:
            logger.error(f"Download failed with errors: {errors}")
            print("\nDownload failed.")

        return result

    except Exception as e:
        logger.error(f"Download exception occurred: {e}")
        print(f"\nDownload failed:")
        print(e)
        return DownloadResult(
            success=False,
            message=str(e),
            download_type=media_type,
            is_playlist=is_pl,
            total_items=entries_count,
            completed_items=0,
            failed_items=entries_count,
            errors=[str(e)],
            download_directory=target_dir,
            playlist_title=pl_title
        )


def download_audio(
    url: str,
    download_path: str,
    quality: str = "0",
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> DownloadResult:
    """
    Download audio (single media or playlist) as MP3.

    Args:
        url: Video, audio, or playlist URL.
        download_path: Directory to save the downloaded audio file(s).
        quality: Audio quality for MP3 conversion ("0", "320", "192", "128").
        progress_callback: Optional UI progress callback.

    Returns:
        DownloadResult instance (evaluates as True on success).
    """
    return download_media(
        url=url,
        download_path=download_path,
        media_type="audio",
        quality=quality,
        progress_callback=progress_callback
    )


def download_video(
    url: str,
    download_path: str,
    height: Optional[int] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    output_format: str = "mp4"
) -> DownloadResult:
    """
    Download video (single video or playlist) with FFmpeg muxing into MP4/MKV.

    Args:
        url: Video or playlist URL.
        download_path: Directory to save the downloaded video file(s).
        height: Maximum video height resolution (e.g., 1080, 720, 0 for best).
        progress_callback: Optional UI progress callback.
        output_format: Container format ("mp4" or "mkv").

    Returns:
        DownloadResult instance (evaluates as True on success).
    """
    return download_media(
        url=url,
        download_path=download_path,
        media_type="video",
        quality=height,
        progress_callback=progress_callback,
        output_format=output_format
    )


def download_playlist(
    url: str,
    download_path: str,
    media_type: str = "video",
    quality: Any = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    output_format: str = "mp4"
) -> DownloadResult:
    """
    Download an entire playlist as video or audio.

    Args:
        url: Media playlist URL.
        download_path: Root folder for the playlist subfolder.
        media_type: "video" or "audio".
        quality: Video height or audio bitrate.
        progress_callback: Optional UI progress callback.
        output_format: Video container format ("mp4" or "mkv").

    Returns:
        DownloadResult instance with full completion statistics.
    """
    return download_media(
        url=url,
        download_path=download_path,
        media_type=media_type,
        quality=quality,
        progress_callback=progress_callback,
        output_format=output_format
    )


def download_playlist_video(
    url: str,
    download_path: str,
    height: Optional[int] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    output_format: str = "mp4"
) -> DownloadResult:
    """
    Download an entire playlist as video files.
    """
    return download_video(
        url=url,
        download_path=download_path,
        height=height,
        progress_callback=progress_callback,
        output_format=output_format
    )


def download_playlist_audio(
    url: str,
    download_path: str,
    quality: str = "0",
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> DownloadResult:
    """
    Download an entire playlist as audio MP3 files.
    """
    return download_audio(
        url=url,
        download_path=download_path,
        quality=quality,
        progress_callback=progress_callback
    )
