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

__author__ = "Ahmed Tarek Zaher"
__copyright__ = "Copyright 2026, Ahmed Tarek Zaher"
__license__ = "MIT"

# BOOKMARK: Ahmed Tarek Zaher - Owner

import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import yt_dlp
try:
    from yt_dlp.utils import DownloadCancelled, download_range_func
except ImportError:
    class DownloadCancelled(Exception):
        """Fallback exception if yt_dlp.utils.DownloadCancelled is unavailable."""
        pass

    def download_range_func(chapters, ranges):
        def _range_func(info_dict, ydl=None):
            for start, end in ranges:
                yield {"start_time": start, "end_time": end}
        return _range_func

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


def has_video_id(url: str) -> bool:
    """
    Check if a given URL directly points to a specific video ID or video endpoint.

    Identifies:
    - YouTube: /watch?v=..., youtu.be/..., /shorts/..., /embed/..., /v/..., /live/...
    - TikTok: /video/... or /v/...
    - Instagram: /reel/..., /p/..., /tv/...
    - Facebook: /videos/..., /watch/?v=..., fb.watch/...
    - Twitter/X: /status/...
    """
    if not url:
        return False

    url_str = str(url).strip()
    try:
        parsed = urlparse(url_str)
        netloc = (parsed.netloc or "").lower()
        path = parsed.path or ""
        params = parse_qs(parsed.query)

        # YouTube / YouTube Music
        if "youtube.com" in netloc or "youtu.be" in netloc:
            # Shortened youtu.be/<video_id>
            if "youtu.be" in netloc and path.strip("/"):
                return True
            # Standard /watch?v=<video_id>
            if "v" in params and params["v"] and params["v"][0].strip():
                return True
            # Embedded or direct video endpoints
            for prefix in ("/shorts/", "/embed/", "/v/", "/live/"):
                if prefix in path:
                    sub = path.split(prefix)[-1].strip("/").split("/")[0]
                    if sub:
                        return True
            return False

        # TikTok (/video/<id>)
        if "tiktok.com" in netloc and ("/video/" in path or "/v/" in path):
            return True

        # Instagram (/reel/<id>, /p/<id>, /tv/<id>)
        if "instagram.com" in netloc and any(x in path for x in ("/reel/", "/p/", "/tv/")):
            return True

        # Facebook (/watch/?v=..., /videos/..., fb.watch)
        if "facebook.com" in netloc or "fb.watch" in netloc:
            if "v" in params and params["v"]:
                return True
            if "/videos/" in path or "/reel/" in path or "fb.watch" in netloc:
                return True

        # Twitter/X (/status/<id>)
        if ("twitter.com" in netloc or "x.com" in netloc) and "/status/" in path:
            return True

    except Exception:
        pass

    return False


def is_pure_playlist_url(url: str) -> bool:
    """
    Check if a URL represents a dedicated playlist or collection without a specific video target.

    Returns True for:
    - https://www.youtube.com/playlist?list=...
    - https://soundcloud.com/artist/sets/...
    - https://music.youtube.com/playlist?list=...
    - URLs with list= param that do NOT contain a video ID (has_video_id is False).
    """
    if not url:
        return False

    url_str = str(url).strip()
    url_lower = url_str.lower()

    # If it contains a specific video ID, it is NOT a pure playlist URL
    if has_video_id(url_str):
        return False

    if "/playlist" in url_lower:
        return True

    if "/sets/" in url_lower or "/album/" in url_lower or "/series/" in url_lower:
        return True

    try:
        parsed = urlparse(url_str)
        params = parse_qs(parsed.query)
        if "list" in params and params["list"] and params["list"][0].strip():
            return True
    except Exception:
        pass

    return False


def is_video_in_playlist_url(url: str) -> bool:
    """
    Check if a URL represents a specific video embedded inside a playlist or mix.

    Examples:
    - https://www.youtube.com/watch?v=kQzf4SsFMxs&list=RDQp3GVg_rC_M&index=17 -> True
    - https://youtu.be/kQzf4SsFMxs?list=PL1234567890 -> True
    - https://www.youtube.com/playlist?list=PL1234567890 -> False (pure playlist)
    - https://www.youtube.com/watch?v=kQzf4SsFMxs -> False (pure single video)
    """
    if not url:
        return False

    url_str = str(url).strip()
    if not has_video_id(url_str):
        return False

    try:
        parsed = urlparse(url_str)
        params = parse_qs(parsed.query)
        if "list" in params and params["list"] and params["list"][0].strip():
            return True
    except Exception:
        pass

    return False


def strip_playlist_params(url: str) -> str:
    """
    Strip playlist/mix query parameters (list, index, start_radio, etc.) from a video URL,
    returning the clean single-video URL.

    Example:
    'https://www.youtube.com/watch?v=kQzf4SsFMxs&list=RDQp3GVg_rC_M&index=17'
    -> 'https://www.youtube.com/watch?v=kQzf4SsFMxs'
    """
    if not url:
        return ""

    url_str = str(url).strip()
    try:
        parsed = urlparse(url_str)
        params = parse_qs(parsed.query, keep_blank_values=True)
        strip_keys = {"list", "index", "start_radio", "pp", "si"}
        cleaned_params = {k: v for k, v in params.items() if k.lower() not in strip_keys}
        new_query = urlencode(cleaned_params, doseq=True)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    except Exception:
        return url_str


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


def parse_time_str(val: Optional[Union[str, int, float]]) -> Optional[float]:
    """
    Parse a timestamp string or numeric value into total seconds as a float.

    Supported formats:
    - None or empty string -> None
    - int or float -> float seconds (e.g., 90 -> 90.0, must be >= 0)
    - "SS" or "SS.s" (e.g., "90", "90.5", "90s")
    - "MM:SS" or "MM:SS.s" (e.g., "01:30", "1:30", "01:30.5")
    - "HH:MM:SS" or "HH:MM:SS.s" (e.g., "01:15:30", "1:00:00")

    Args:
        val: Time string or numeric seconds.

    Returns:
        Float seconds or None if empty/None.

    Raises:
        ValueError: If format is invalid or timestamp is negative.
    """
    if val is None:
        return None

    if isinstance(val, (int, float)):
        if val < 0:
            raise ValueError(f"Timestamp cannot be negative: {val}")
        return float(val)

    s = str(val).strip().rstrip("sS").strip()
    if not s:
        return None

    if s.startswith("-"):
        raise ValueError(f"Timestamp cannot be negative: '{val}'")

    parts = s.split(":")
    if len(parts) == 1:
        # Seconds only
        try:
            sec = float(parts[0])
            if sec < 0:
                raise ValueError(f"Timestamp cannot be negative: '{val}'")
            return sec
        except ValueError:
            raise ValueError(
                f"Invalid timestamp format: '{val}'. Expected MM:SS, HH:MM:SS, or seconds (e.g., '01:30' or '90')."
            )

    elif len(parts) == 2:
        # MM:SS
        try:
            mins = int(parts[0])
            secs = float(parts[1])
            if mins < 0 or secs < 0 or secs >= 60:
                raise ValueError(f"Invalid minutes/seconds in timestamp: '{val}'")
            return mins * 60.0 + secs
        except ValueError:
            raise ValueError(
                f"Invalid timestamp format: '{val}'. Expected MM:SS, HH:MM:SS, or seconds (e.g., '01:30' or '90')."
            )

    elif len(parts) == 3:
        # HH:MM:SS
        try:
            hrs = int(parts[0])
            mins = int(parts[1])
            secs = float(parts[2])
            if hrs < 0 or mins < 0 or mins >= 60 or secs < 0 or secs >= 60:
                raise ValueError(f"Invalid hours/minutes/seconds in timestamp: '{val}'")
            return hrs * 3600.0 + mins * 60.0 + secs
        except ValueError:
            raise ValueError(
                f"Invalid timestamp format: '{val}'. Expected MM:SS, HH:MM:SS, or seconds (e.g., '01:30' or '90')."
            )

    else:
        raise ValueError(
            f"Invalid timestamp format: '{val}'. Expected MM:SS, HH:MM:SS, or seconds (e.g., '01:30' or '90')."
        )


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
    process: bool = True,
    noplaylist: Optional[bool] = None
) -> Optional[Dict[str, Any]]:
    """
    Extract video or playlist information from a media URL.

    Args:
        url: Media video or playlist URL.
        extract_flat: 'in_playlist' (fast playlist entries), True, or False.
        process: Whether to fully process video info.
        noplaylist: Suppress playlist extraction (defaults to True if URL has a video ID).

    Returns:
        Media information dictionary, or None if extraction failed.
    """
    logger = get_logger("downloader")

    # Smart default for noplaylist: if URL contains a specific video ID (like /watch?v=...&list=...),
    # default to single video extraction so users inspect the targeted video rather than the full playlist/mix.
    if noplaylist is None:
        if has_video_id(url):
            noplaylist = True
        elif is_pure_playlist_url(url):
            noplaylist = False

    extra_opts: Dict[str, Any] = {
        "extract_flat": extract_flat,
    }
    if noplaylist is not None:
        extra_opts["noplaylist"] = noplaylist

    options = get_yt_dlp_options(extra_opts)

    try:
        logger.info(f"Extracting media info for URL: {url} (noplaylist={noplaylist})")
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

        # Tag playlist and video-in-playlist status
        info["is_playlist"] = is_playlist(info)
        info["is_video_in_playlist"] = is_video_in_playlist_url(url)
        info["clean_url"] = strip_playlist_params(url) if is_video_in_playlist_url(url) else url
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


def parse_video_height(quality: Optional[Union[str, int]]) -> int:
    """
    Parse video quality parameter into an integer height resolution.

    Supports integer heights, string numbers ('1080', '720'), quality presets ('1080p', '4k', '1440p', '8k'),
    and returns 0 for 'best' / '0' / None / unparseable values.

    Args:
        quality: Video quality string or integer (e.g., 1080, "1080", "1080p", "4k", "1440p", "8k", "best", 0).

    Returns:
        Integer height (e.g., 1080, 720, 1440, 2160, 4320) or 0 for best/default.
    """
    if quality is None:
        return 0
    if isinstance(quality, int):
        return max(0, quality)
    q_str = str(quality).strip().lower()
    if q_str in ("", "0", "best", "max", "default", "none"):
        return 0
    if q_str in ("4k", "2160", "2160p", "uhd", "4k uhd"):
        return 2160
    if q_str in ("2k", "1440", "1440p", "qhd", "2k qhd"):
        return 1440
    if q_str in ("8k", "4320", "4320p", "fuhd", "8k uhd"):
        return 4320
    clean = q_str.rstrip("p").strip()
    if clean.isdigit():
        return int(clean)
    return 0


def resolve_video_format(height: Optional[Union[int, str]] = None, has_ffmpeg: bool = True) -> str:
    """
    Build yt-dlp format selector string with smart codec prioritization.

    Smart Logic:
    - For qualities 1080p and below (or default 'video' / height=0):
      Strictly prioritize native H.264 (avc) video and M4A (aac) audio directly from YouTube:
      'bestvideo[vcodec^=avc]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
    - For Ultra-HD qualities (1440p, 4K, 8K, i.e. height > 1080):
      Allow yt-dlp to fetch the default best codecs (VP9/AV1) using standard format string:
      'bestvideo+bestaudio/best'

    Args:
        height: Maximum video height resolution (e.g., 1080, 720, 1440, 2160, 0 for best/default).
        has_ffmpeg: Whether FFmpeg is available to mux separate video and audio streams.

    Returns:
        yt-dlp format string.
    """
    h = parse_video_height(height)

    if not has_ffmpeg:
        # Fallback to single-file progressive streams with audio if FFmpeg is absent
        if h > 1080:
            return f"best[height<={h}][acodec!=none]/best[acodec!=none]/best"
        elif h > 0:
            return f"best[height<={h}][vcodec^=avc][acodec!=none]/best[height<={h}][acodec!=none]/best[acodec!=none]/best"
        return "best[vcodec^=avc][acodec!=none]/best[acodec!=none]/best"

    if h > 1080:
        # Ultra-HD qualities (1440p, 4K, 8K): YouTube does not provide H.264 at these resolutions,
        # so allow yt-dlp to fetch the default best codecs (VP9/AV1).
        return (
            f"bestvideo[height<={h}]+bestaudio/"
            f"best[height<={h}]/"
            f"bestvideo+bestaudio/best"
        )
    elif h > 0:
        # 1080p and below with specific height: strictly prioritize native H.264 (avc) and M4A (aac)
        return (
            f"bestvideo[height<={h}][vcodec^=avc]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={h}]+bestaudio/"
            f"best[height<={h}]/"
            f"bestvideo[vcodec^=avc]+bestaudio[ext=m4a]/"
            f"bestvideo+bestaudio/best"
        )

    # Default 'video' / Best available (height == 0 / None)
    return "bestvideo[vcodec^=avc]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"


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
            except (DownloadCancelled, KeyboardInterrupt):
                raise
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
                if sys.stdout is not None and hasattr(sys.stdout, "write"):
                    sys.stdout.write(out)
                    if hasattr(sys.stdout, "flush"):
                        sys.stdout.flush()

            elif status == "finished":
                pl_suffix = f" (Item {pl_index}/{pl_count})" if (pl_index and pl_count) else ""
                if sys.stdout is not None and hasattr(sys.stdout, "write"):
                    sys.stdout.write(f"\nProcessing file{pl_suffix}...\n")
                    if hasattr(sys.stdout, "flush"):
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
    output_format: str = "mp4",
    start_time: Optional[Union[str, int, float]] = None,
    end_time: Optional[Union[str, int, float]] = None,
    write_subtitles: bool = False,
    write_auto_subs: bool = False,
    sub_langs: Optional[str] = None,
    sub_format: str = "srt",
    embed_subs: bool = False,
    convert_subs: Optional[str] = None,
    is_playlist_mode: Optional[bool] = None
) -> DownloadResult:
    """
    Download media (single video, audio, or entire playlist) from a URL.

    Handles:
    - Automatic detection and handling of playlists vs single video with playlist params.
    - Saving playlists in organized subfolders with indexed filenames.
    - Merging video and audio into MP4/MKV.
    - Converting audio to MP3 with chosen quality/bitrate.
    - Partial media clipping via start_time and end_time range selection.
    - Graceful error tolerance for individual failed playlist items.

    Args:
        url: Video, audio, or playlist URL (YouTube, TikTok, Social Media, etc.).
        download_path: Target root download directory.
        media_type: "video" or "audio".
        quality: Video height (int/preset) or Audio bitrate string ("0", "320", "192", "128").
        progress_callback: Optional callback for UI progress updates.
        output_format: Video container format (default: "mp4").
        start_time: Optional start timestamp (e.g., "01:30", "90", 90.0).
        end_time: Optional end timestamp (e.g., "04:15", "255", 255.0).
        write_subtitles: Whether to write subtitle files alongside the media.
        write_auto_subs: Whether to write auto-generated subtitles.
        sub_langs: Comma-separated subtitle language codes (e.g., "en,ar") or "all".
        sub_format: Subtitle container format (e.g., "srt", "vtt", "ass").
        embed_subs: Whether to embed subtitles into the video file.
        convert_subs: Optional subtitle format conversion target (e.g., "srt").
        is_playlist_mode: Explicit flag to force playlist batch download or single item.

    Returns:
        DownloadResult instance containing status and statistics.
    """
    logger = get_logger("downloader")
    media_type = media_type.lower().strip()

    # Parse and validate section timestamps if provided
    try:
        start_sec = parse_time_str(start_time)
        end_sec = parse_time_str(end_time)
    except ValueError as e:
        logger.error(f"Timestamp validation error: {e}")
        return DownloadResult(
            success=False,
            message=str(e),
            download_type=media_type,
            is_playlist=False,
            total_items=1,
            completed_items=0,
            failed_items=1,
            errors=[str(e)],
            download_directory=download_path
        )

    if start_sec is not None and end_sec is not None and end_sec <= start_sec:
        err_msg = f"End time ({end_time}) must be greater than start time ({start_time})."
        logger.error(err_msg)
        return DownloadResult(
            success=False,
            message=err_msg,
            download_type=media_type,
            is_playlist=False,
            total_items=1,
            completed_items=0,
            failed_items=1,
            errors=[err_msg],
            download_directory=download_path
        )

    # Determine if this operation targets a playlist batch or a single media item
    if is_playlist_mode is not None:
        is_pl = bool(is_playlist_mode)
    elif is_pure_playlist_url(url):
        is_pl = True
    elif has_video_id(url):
        # Specific video link (even with list= query parameter) defaults to single video
        is_pl = False
    else:
        info_peek = get_media_info(url, extract_flat="in_playlist", noplaylist=None)
        is_pl = is_playlist(info_peek)

    # Extract media metadata
    logger.info(f"Checking media info for download: url={url}, type={media_type}, is_playlist={is_pl}")
    info = get_media_info(url, extract_flat="in_playlist", noplaylist=not is_pl)

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
        "postprocessor_hooks": [hook],
        "noplaylist": not is_pl,
    }

    # Configure partial download range if specified
    if start_sec is not None or end_sec is not None:
        s_val = start_sec if start_sec is not None else 0.0
        e_val = end_sec if end_sec is not None else float("inf")
        extra_options["download_ranges"] = download_range_func(None, [(s_val, e_val)])
        extra_options["force_keyframes_at_cuts"] = True

    clip_desc = ""
    if start_sec is not None or end_sec is not None:
        s_disp = str(start_time) if start_time is not None else "00:00"
        e_disp = str(end_time) if end_time is not None else "end"
        clip_desc = f" [section: {s_disp} - {e_disp}]"

    # Configure subtitle options if requested
    sub_desc = ""
    if media_type in ("subtitles", "subtitle", "subs"):
        # Subtitle-only download mode (skips video/audio media download entirely)
        effective_sub_langs = sub_langs or "all"
        clean_langs = [part.strip().split()[0] for part in effective_sub_langs.split(",") if part.strip()]
        if not clean_langs or "all" in [c.lower() for c in clean_langs]:
            sub_langs_list = ["all"]
        else:
            sub_langs_list = clean_langs

        extra_options.update({
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": write_auto_subs if write_auto_subs is not None else True,
            "subtitleslangs": sub_langs_list,
            "subtitlesformat": sub_format or "srt",
        })
        if convert_subs:
            extra_options["postprocessors"] = extra_options.get("postprocessors", []) + [
                {
                    "key": "FFmpegSubtitlesConvertor",
                    "format": convert_subs,
                }
            ]
        desc_str = f"subtitles only (format: {sub_format or 'srt'}, languages: {','.join(sub_langs_list)})"

    elif media_type == "audio":
        if write_subtitles or write_auto_subs or embed_subs or convert_subs:
            effective_write_subs = write_subtitles or write_auto_subs or embed_subs or convert_subs
            effective_write_auto_subs = write_subtitles or write_auto_subs or embed_subs or convert_subs

            if effective_write_subs:
                extra_options["writesubtitles"] = True
            if effective_write_auto_subs:
                extra_options["writeautomaticsub"] = True
            if sub_langs:
                extra_options["subtitleslangs"] = [lang.strip() for lang in sub_langs.split(",") if lang.strip()]
            if sub_format:
                extra_options["subtitlesformat"] = sub_format
            if embed_subs:
                extra_options["embedsubs"] = True
            if convert_subs:
                extra_options["postprocessors"] = extra_options.get("postprocessors", []) + [
                    {
                        "key": "FFmpegSubtitlesConvertor",
                        "format": convert_subs,
                    }
                ]
            sub_desc = " + subtitles" + (" (embedded)" if embed_subs else "")

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
        desc_str = f"audio (MP3, quality: {audio_quality}){clip_desc}{sub_desc}"
    else:
        # Video download
        if write_subtitles or write_auto_subs or embed_subs or convert_subs:
            effective_write_subs = write_subtitles or write_auto_subs or embed_subs or convert_subs
            effective_write_auto_subs = write_subtitles or write_auto_subs or embed_subs or convert_subs

            if effective_write_subs:
                extra_options["writesubtitles"] = True
            if effective_write_auto_subs:
                extra_options["writeautomaticsub"] = True
            if sub_langs:
                extra_options["subtitleslangs"] = [lang.strip() for lang in sub_langs.split(",") if lang.strip()]
            if sub_format:
                extra_options["subtitlesformat"] = sub_format
            if embed_subs:
                extra_options["embedsubs"] = True
            if convert_subs:
                extra_options["postprocessors"] = extra_options.get("postprocessors", []) + [
                    {
                        "key": "FFmpegSubtitlesConvertor",
                        "format": convert_subs,
                    }
                ]
            sub_desc = " + subtitles" + (" (embedded)" if embed_subs else "")

        height = parse_video_height(quality)
        is_ultra_hd = height > 1080
        video_format = resolve_video_format(height, has_ffmpeg=has_ffmpeg)

        # Smart format & container selection:
        # - For 1080p and below (or default 'video'): strictly prioritize H.264 + M4A and set merge_output_format to mp4
        # - For Ultra-HD (1440p, 4K, 8K): allow VP9/AV1 with .mkv or .webm container (do not force .mp4)
        if is_ultra_hd:
            if output_format and output_format.lower() in ("webm", "mkv"):
                merge_fmt = output_format.lower()
            else:
                merge_fmt = "mkv"
        else:
            if output_format and output_format.lower() in ("mkv", "webm"):
                merge_fmt = output_format.lower()
            else:
                merge_fmt = "mp4"

        extra_options.update({
            "format": video_format,
            "merge_output_format": merge_fmt,
        })
        desc_str = f"video (format: {merge_fmt}, max height: {height or 'best'}p){clip_desc}{sub_desc}"

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

    except (DownloadCancelled, KeyboardInterrupt) as e:
        logger.info(f"Download was cancelled: {e}")
        print("\nDownload cancelled by user.")
        return DownloadResult(
            success=False,
            message="Download cancelled by user.",
            download_type=media_type,
            is_playlist=is_pl,
            total_items=entries_count,
            completed_items=stats_tracker.get("completed_items", 0),
            failed_items=0,
            errors=["Download cancelled by user."],
            download_directory=target_dir,
            playlist_title=pl_title
        )
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
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    start_time: Optional[Union[str, int, float]] = None,
    end_time: Optional[Union[str, int, float]] = None,
    write_subtitles: bool = False,
    write_auto_subs: bool = False,
    sub_langs: Optional[str] = None,
    sub_format: str = "srt",
    embed_subs: bool = False,
    convert_subs: Optional[str] = None
) -> DownloadResult:
    """
    Download audio (single media or playlist) as MP3.

    Args:
        url: Video, audio, or playlist URL.
        download_path: Directory to save the downloaded audio file(s).
        quality: Audio quality for MP3 conversion ("0", "320", "192", "128").
        progress_callback: Optional UI progress callback.
        start_time: Optional start timestamp (e.g., "01:30", "90").
        end_time: Optional end timestamp (e.g., "04:15", "255").

    Returns:
        DownloadResult instance (evaluates as True on success).
    """
    return download_media(
        url=url,
        download_path=download_path,
        media_type="audio",
        quality=quality,
        progress_callback=progress_callback,
        start_time=start_time,
        end_time=end_time,
        write_subtitles=write_subtitles,
        write_auto_subs=write_auto_subs,
        sub_langs=sub_langs,
        sub_format=sub_format,
        embed_subs=embed_subs,
        convert_subs=convert_subs
    )


def download_video(
    url: str,
    download_path: str,
    height: Optional[int] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    output_format: str = "mp4",
    start_time: Optional[Union[str, int, float]] = None,
    end_time: Optional[Union[str, int, float]] = None,
    write_subtitles: bool = False,
    write_auto_subs: bool = False,
    sub_langs: Optional[str] = None,
    sub_format: str = "srt",
    embed_subs: bool = False,
    convert_subs: Optional[str] = None
) -> DownloadResult:
    """
    Download video (single video or playlist) with FFmpeg muxing into MP4/MKV.

    Args:
        url: Video or playlist URL.
        download_path: Directory to save the downloaded video file(s).
        height: Maximum video height resolution (e.g., 1080, 720, 0 for best).
        progress_callback: Optional UI progress callback.
        output_format: Container format ("mp4" or "mkv").
        start_time: Optional start timestamp (e.g., "01:30", "90").
        end_time: Optional end timestamp (e.g., "04:15", "255").
        write_subtitles: Whether to write subtitle files alongside the media.
        write_auto_subs: Whether to write auto-generated subtitles.
        sub_langs: Comma-separated subtitle language codes (e.g., "en,ar") or "all".
        sub_format: Subtitle container format (e.g., "srt", "vtt", "ass").
        embed_subs: Whether to embed subtitles into the video file.
        convert_subs: Optional subtitle format conversion target (e.g., "srt").

    Returns:
        DownloadResult instance (evaluates as True on success).
    """
    return download_media(
        url=url,
        download_path=download_path,
        media_type="video",
        quality=height,
        progress_callback=progress_callback,
        output_format=output_format,
        start_time=start_time,
        end_time=end_time,
        write_subtitles=write_subtitles,
        write_auto_subs=write_auto_subs,
        sub_langs=sub_langs,
        sub_format=sub_format,
        embed_subs=embed_subs,
        convert_subs=convert_subs
    )


def download_playlist(
    url: str,
    download_path: str,
    media_type: str = "video",
    quality: Any = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    output_format: str = "mp4",
    start_time: Optional[Union[str, int, float]] = None,
    end_time: Optional[Union[str, int, float]] = None,
    write_subtitles: bool = False,
    write_auto_subs: bool = False,
    sub_langs: Optional[str] = None,
    sub_format: str = "srt",
    embed_subs: bool = False,
    convert_subs: Optional[str] = None
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
        start_time: Optional start timestamp.
        end_time: Optional end timestamp.
        write_subtitles: Whether to write subtitle files alongside the media.
        write_auto_subs: Whether to write auto-generated subtitles.
        sub_langs: Comma-separated subtitle language codes (e.g., "en,ar") or "all".
        sub_format: Subtitle container format (e.g., "srt", "vtt", "ass").
        embed_subs: Whether to embed subtitles into the video file.
        convert_subs: Optional subtitle format conversion target (e.g., "srt").

    Returns:
        DownloadResult instance with full completion statistics.
    """
    return download_media(
        url=url,
        download_path=download_path,
        media_type=media_type,
        quality=quality,
        progress_callback=progress_callback,
        output_format=output_format,
        start_time=start_time,
        end_time=end_time,
        write_subtitles=write_subtitles,
        write_auto_subs=write_auto_subs,
        sub_langs=sub_langs,
        sub_format=sub_format,
        embed_subs=embed_subs,
        convert_subs=convert_subs,
        is_playlist_mode=True
    )


def download_playlist_video(
    url: str,
    download_path: str,
    height: Optional[int] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    output_format: str = "mp4",
    start_time: Optional[Union[str, int, float]] = None,
    end_time: Optional[Union[str, int, float]] = None,
    write_subtitles: bool = False,
    write_auto_subs: bool = False,
    sub_langs: Optional[str] = None,
    sub_format: str = "srt",
    embed_subs: bool = False,
    convert_subs: Optional[str] = None
) -> DownloadResult:
    """
    Download an entire playlist as video files.
    """
    return download_playlist(
        url=url,
        download_path=download_path,
        media_type="video",
        quality=height,
        progress_callback=progress_callback,
        output_format=output_format,
        start_time=start_time,
        end_time=end_time,
        write_subtitles=write_subtitles,
        write_auto_subs=write_auto_subs,
        sub_langs=sub_langs,
        sub_format=sub_format,
        embed_subs=embed_subs,
        convert_subs=convert_subs
    )


def download_playlist_audio(
    url: str,
    download_path: str,
    quality: str = "0",
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    start_time: Optional[Union[str, int, float]] = None,
    end_time: Optional[Union[str, int, float]] = None,
    write_subtitles: bool = False,
    write_auto_subs: bool = False,
    sub_langs: Optional[str] = None,
    sub_format: str = "srt",
    embed_subs: bool = False,
    convert_subs: Optional[str] = None
) -> DownloadResult:
    """
    Download an entire playlist as audio MP3 files.
    """
    return download_playlist(
        url=url,
        download_path=download_path,
        media_type="audio",
        quality=quality,
        progress_callback=progress_callback,
        start_time=start_time,
        end_time=end_time,
        write_subtitles=write_subtitles,
        write_auto_subs=write_auto_subs,
        sub_langs=sub_langs,
        sub_format=sub_format,
        embed_subs=embed_subs,
        convert_subs=convert_subs
    )


def download_subtitles(
    url: str,
    download_path: str,
    sub_langs: Optional[str] = None,
    sub_format: str = "srt",
    write_auto_subs: bool = True,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    convert_subs: Optional[str] = None,
    is_playlist_mode: Optional[bool] = None
) -> DownloadResult:
    """
    Download subtitle/transcript files only without downloading video or audio media.

    Args:
        url: Video or playlist URL.
        download_path: Directory to save the subtitle files.
        sub_langs: Subtitle language code(s) (e.g. 'en', 'ar', 'all', or 'en,ar').
        sub_format: Preferred subtitle format (default: 'srt').
        write_auto_subs: Whether to fetch auto-generated subtitles if manual are absent.
        progress_callback: Optional progress callback.
        convert_subs: Optional target conversion format.
        is_playlist_mode: Whether to process as a playlist batch.

    Returns:
        DownloadResult instance.
    """
    return download_media(
        url=url,
        download_path=download_path,
        media_type="subtitles",
        sub_langs=sub_langs,
        sub_format=sub_format,
        write_subtitles=True,
        write_auto_subs=write_auto_subs,
        progress_callback=progress_callback,
        convert_subs=convert_subs,
        is_playlist_mode=is_playlist_mode
    )

