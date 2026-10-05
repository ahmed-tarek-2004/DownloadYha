"""
validators.py - Comprehensive input validation and parser utilities for Downloadyha API.
Supports timestamp parsing, clipping range validation, platform detection, URL validation,
quality resolution, and subtitle/container format validation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

from .models import ClipValidationResponse, UrlValidationResponse


# ---------------------------------------------------------------------------
# Supported Platforms Constant
# ---------------------------------------------------------------------------

SUPPORTED_PLATFORMS: List[str] = [
    "YouTube",
    "YouTube Shorts",
    "YouTube Music",
    "TikTok",
    "Instagram",
    "Facebook",
    "Twitter/X",
    "Reddit",
    "Vimeo",
    "SoundCloud",
    "Twitch",
    "Dailymotion",
    "Pinterest",
    "Threads",
    "Generic Media URL",
]

SUPPORTED_VIDEO_RESOLUTIONS: List[int] = [
    4320,  # 8K UHD
    2160,  # 4K UHD
    1440,  # 2K QHD
    1080,  # Full HD
    720,   # HD
    480,   # SD
    360,   # Low
    240,   # Extra Low
    144,   # Mobile Minimal
]

SUPPORTED_AUDIO_BITRATES: List[str] = [
    "320",
    "256",
    "192",
    "128",
    "96",
    "64",
    "0",   # Best VBR
]

SUPPORTED_SUBTITLE_FORMATS: List[str] = ["srt", "vtt", "ass", "lrc"]

SUPPORTED_VIDEO_CONTAINERS: List[str] = ["mp4", "mkv", "webm"]
SUPPORTED_AUDIO_CONTAINERS: List[str] = ["mp3", "m4a", "aac", "opus", "wav", "flac"]


# ---------------------------------------------------------------------------
# Formatting Utilities
# ---------------------------------------------------------------------------

def format_bytes(bytes_count: Optional[Union[int, float]]) -> str:
    """
    Format bytes count into human-readable string (e.g., '14.2 MB', '1.5 GB').
    """
    if bytes_count is None or bytes_count <= 0:
        return "N/A"
    units = ["B", "KB", "MB", "GB", "TB"]
    val = float(bytes_count)
    unit_idx = 0
    while val >= 1024.0 and unit_idx < len(units) - 1:
        val /= 1024.0
        unit_idx += 1
    return f"{val:.1f} {units[unit_idx]}"


def format_seconds(seconds: Optional[Union[int, float]]) -> str:
    """
    Format total seconds into HH:MM:SS or MM:SS string representation.
    """
    if seconds is None or seconds < 0:
        return "00:00"
    s = int(seconds)
    hrs = s // 3600
    mins = (s % 3600) // 60
    secs = s % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def sanitize_filename(name: str, fallback: str = "download") -> str:
    """
    Sanitize a string so it can safely be used as a filename across all operating systems.
    Removes illegal filesystem characters (/ \\ : * ? " < > | \0) and trims spaces.
    """
    if not name:
        return fallback
    clean = re.sub(r'[\\/*?:"<>|\x00-\x1f]+', '_', str(name))
    clean = clean.strip('. _')
    clean = re.sub(r'_+', '_', clean)
    return clean or fallback


def sanitize_folder_name(name: str, fallback: str = "Media_Download") -> str:
    """
    Sanitize a string for safe use as a directory or album name.
    """
    if not name:
        return fallback
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '_', str(name)).strip('. _')
    clean = re.sub(r'_+', '_', clean)
    return clean if clean else fallback


# ---------------------------------------------------------------------------
# Timestamp Parsing & Validation
# ---------------------------------------------------------------------------

def parse_time_str(val: Optional[Union[str, int, float]]) -> Optional[float]:
    """
    Parse a timestamp string or numeric value into total seconds as a float.

    Supported formats:
    - None or empty string -> None
    - int or float -> float seconds (e.g., 90 -> 90.0, must be >= 0)
    - "SS" or "SS.s" or "90s" (e.g., "90", "90.5", "90s")
    - "MM:SS" or "MM:SS.s" (e.g., "01:30", "1:30", "01:30.5")
    - "HH:MM:SS" or "HH:MM:SS.s" (e.g., "01:15:30", "1:00:00")

    Args:
        val: Time string or numeric seconds.

    Returns:
        Float seconds or None if empty/None.

    Raises:
        ValueError: If format is invalid, timestamp is negative, or time components out of range.
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
        # Seconds only (e.g. "90", "90.5")
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
                raise ValueError(f"Invalid minutes/seconds in timestamp: '{val}'. Seconds must be between 0 and 59.")
            return mins * 60.0 + secs
        except ValueError as e:
            if "Invalid minutes/seconds" in str(e):
                raise
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
                raise ValueError(f"Invalid hours/minutes/seconds in timestamp: '{val}'. Minutes and seconds must be 0-59.")
            return hrs * 3600.0 + mins * 60.0 + secs
        except ValueError as e:
            if "Invalid hours/minutes/seconds" in str(e):
                raise
            raise ValueError(
                f"Invalid timestamp format: '{val}'. Expected MM:SS, HH:MM:SS, or seconds (e.g., '01:30' or '90')."
            )

    else:
        raise ValueError(
            f"Invalid timestamp format: '{val}'. Expected MM:SS, HH:MM:SS, or seconds (e.g., '01:30' or '90')."
        )


def validate_clip_range(
    start_time: Optional[Union[str, int, float]],
    end_time: Optional[Union[str, int, float]],
    media_duration: Optional[Union[str, int, float]] = None
) -> ClipValidationResponse:
    """
    Validate start and end clipping timestamps against optional total media duration.

    Validates:
    - Non-negative start and end timestamps.
    - Start time must be strictly less than end time.
    - Start time must be strictly less than media duration (if provided).
    - Clamps or notes end time if it exceeds total media duration.

    Args:
        start_time: Start timestamp ("MM:SS", "HH:MM:SS", seconds).
        end_time: End timestamp ("MM:SS", "HH:MM:SS", seconds).
        media_duration: Optional total media duration in seconds or timestamp.

    Returns:
        ClipValidationResponse instance with calculated offsets and validation status.
    """
    try:
        start_sec = parse_time_str(start_time)
        end_sec = parse_time_str(end_time)
        duration_sec = parse_time_str(media_duration)
    except ValueError as e:
        return ClipValidationResponse(
            is_valid=False,
            error_message=str(e)
        )

    # Validate start < end
    if start_sec is not None and end_sec is not None and end_sec <= start_sec:
        s_fmt = format_seconds(start_sec)
        e_fmt = format_seconds(end_sec)
        return ClipValidationResponse(
            is_valid=False,
            start_seconds=start_sec,
            end_seconds=end_sec,
            start_time=s_fmt,
            end_time=e_fmt,
            error_message=f"End time ({e_fmt}) must be greater than start time ({s_fmt})."
        )

    # Validate against total media duration if provided
    if duration_sec is not None and duration_sec > 0:
        if start_sec is not None and start_sec >= duration_sec:
            s_fmt = format_seconds(start_sec)
            d_fmt = format_seconds(duration_sec)
            return ClipValidationResponse(
                is_valid=False,
                start_seconds=start_sec,
                end_seconds=end_sec,
                duration=duration_sec,
                start_time=s_fmt,
                error_message=f"Start time ({s_fmt}) cannot exceed total media duration ({d_fmt})."
            )
        # Clamping end time to duration if beyond
        if end_sec is not None and end_sec > duration_sec:
            end_sec = duration_sec

    # Calculate effective clip duration
    effective_start = start_sec if start_sec is not None else 0.0
    effective_end = end_sec if end_sec is not None else duration_sec
    clip_dur = (effective_end - effective_start) if effective_end is not None else None

    return ClipValidationResponse(
        is_valid=True,
        start_time=format_seconds(start_sec) if start_sec is not None else None,
        end_time=format_seconds(end_sec) if end_sec is not None else None,
        duration=duration_sec,
        start_seconds=start_sec,
        end_seconds=end_sec,
        clip_duration_seconds=clip_dur,
        clip_duration_formatted=format_seconds(clip_dur) if clip_dur is not None else None,
        error_message=None
    )


# ---------------------------------------------------------------------------
# Platform Detection & URL Validation
# ---------------------------------------------------------------------------

def detect_platform(url: str) -> str:
    """
    Detect the media platform name from a given URL string.

    Supports:
    - YouTube, YouTube Shorts, YouTube Music
    - TikTok
    - Instagram
    - Facebook
    - Twitter/X
    - Reddit
    - Vimeo
    - SoundCloud
    - Twitch
    - Dailymotion
    - Pinterest
    - Threads
    - Generic Media URL
    """
    if not url:
        return "Unknown"

    url_str = str(url).strip()
    if not url_str.startswith("http://") and not url_str.startswith("https://"):
        url_str = "https://" + url_str

    try:
        parsed = urlparse(url_str)
        netloc = (parsed.netloc or "").lower().split(":")[0]
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = (parsed.path or "").lower()
    except Exception:
        netloc = url_str.lower()
        path = ""

    # YouTube variants
    if netloc in ("music.youtube.com",):
        return "YouTube Music"
    if netloc in ("youtube.com", "m.youtube.com", "youtu.be") or netloc.endswith(".youtube.com"):
        if "/shorts" in path:
            return "YouTube Shorts"
        return "YouTube"

    # TikTok
    if netloc in ("tiktok.com", "vm.tiktok.com", "vt.tiktok.com") or netloc.endswith(".tiktok.com"):
        return "TikTok"

    # Instagram
    if netloc in ("instagram.com", "instagr.am") or netloc.endswith(".instagram.com"):
        return "Instagram"

    # Facebook
    if netloc in ("facebook.com", "m.facebook.com", "fb.watch", "fb.com", "web.facebook.com") or netloc.endswith(".facebook.com"):
        return "Facebook"

    # Twitter / X
    if netloc in ("twitter.com", "x.com", "t.co", "mobile.twitter.com") or netloc.endswith(".twitter.com") or netloc.endswith(".x.com"):
        return "Twitter/X"

    # Reddit
    if netloc in ("reddit.com", "old.reddit.com", "v.redd.it", "redd.it") or netloc.endswith(".reddit.com"):
        return "Reddit"

    # Vimeo
    if netloc in ("vimeo.com", "player.vimeo.com") or netloc.endswith(".vimeo.com"):
        return "Vimeo"

    # SoundCloud
    if netloc in ("soundcloud.com", "m.soundcloud.com") or netloc.endswith(".soundcloud.com"):
        return "SoundCloud"

    # Twitch
    if netloc in ("twitch.tv", "clips.twitch.tv") or netloc.endswith(".twitch.tv"):
        return "Twitch"

    # Dailymotion
    if netloc in ("dailymotion.com", "dai.ly") or netloc.endswith(".dailymotion.com"):
        return "Dailymotion"

    # Pinterest
    if netloc in ("pinterest.com", "pin.it") or netloc.endswith(".pinterest.com"):
        return "Pinterest"

    # Threads
    if netloc in ("threads.net",) or netloc.endswith(".threads.net"):
        return "Threads"

    return "Generic Media URL"


def is_playlist_url(url: str) -> bool:
    """
    Check if a URL represents a playlist, album, or collection.

    Handles:
    - https://www.youtube.com/playlist?list=...
    - https://www.youtube.com/watch?v=...&list=... (excluding watch-later or likes)
    - SoundCloud sets / albums
    """
    if not url:
        return False

    url_str = str(url).strip()
    url_lower = url_str.lower()

    if "/playlist" in url_lower:
        return True

    try:
        parsed = urlparse(url_str)
        params = parse_qs(parsed.query)
        if "list" in params and params["list"]:
            list_id = params["list"][0]
            # Exclude special user mixes like 'LL' (Liked) or 'WL' (Watch Later)
            if list_id not in ("LL", "WL"):
                return True
    except Exception:
        pass

    if "/sets/" in url_lower or "/album/" in url_lower or "/series/" in url_lower:
        return True

    return False


def validate_media_url(url: str) -> UrlValidationResponse:
    """
    Validate URL syntax, domain name structure, and detect media platform.

    Args:
        url: URL string to inspect.

    Returns:
        UrlValidationResponse instance.
    """
    if not url or not isinstance(url, str):
        return UrlValidationResponse(
            url=str(url),
            is_valid=False,
            platform="Unknown",
            is_playlist=False,
            error_message="URL is empty or not a valid string."
        )

    clean_url = url.strip()

    # Prepend https:// if protocol is missing but domain exists
    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        if "." in clean_url and "/" in clean_url:
            clean_url = "https://" + clean_url
        else:
            return UrlValidationResponse(
                url=url,
                is_valid=False,
                platform="Unknown",
                is_playlist=False,
                error_message="URL must start with http:// or https://"
            )

    try:
        parsed = urlparse(clean_url)
        if not parsed.netloc or "." not in parsed.netloc:
            return UrlValidationResponse(
                url=clean_url,
                is_valid=False,
                platform="Unknown",
                is_playlist=False,
                error_message="Invalid domain name in URL."
            )
    except Exception as e:
        return UrlValidationResponse(
            url=clean_url,
            is_valid=False,
            platform="Unknown",
            is_playlist=False,
            error_message=f"Malformed URL: {e}"
        )

    platform = detect_platform(clean_url)
    is_pl = is_playlist_url(clean_url)

    return UrlValidationResponse(
        url=clean_url,
        is_valid=True,
        platform=platform,
        is_playlist=is_pl,
        normalized_url=clean_url,
        error_message=None
    )


# ---------------------------------------------------------------------------
# Quality & Format Validators
# ---------------------------------------------------------------------------

def validate_video_quality(quality: Optional[Union[str, int]]) -> int:
    """
    Normalize video quality parameter to standard integer height.
    Returns 0 for 'best' / 'max' / 'auto'.

    Examples:
        - "1080p" -> 1080
        - "4K" -> 2160
        - "best" -> 0
        - 720 -> 720
    """
    if quality is None:
        return 0

    if isinstance(quality, int):
        return quality if quality >= 0 else 0

    q_str = str(quality).lower().strip()
    if q_str in ("0", "best", "max", "highest", "auto", "b"):
        return 0
    if q_str in ("8k", "4320", "4320p"):
        return 4320
    if q_str in ("4k", "2160", "2160p", "uhd"):
        return 2160
    if q_str in ("2k", "1440", "1440p", "qhd"):
        return 1440
    if q_str in ("1080", "1080p", "fhd", "fullhd"):
        return 1080
    if q_str in ("720", "720p", "hd"):
        return 720
    if q_str in ("480", "480p", "sd"):
        return 480
    if q_str in ("360", "360p"):
        return 360
    if q_str in ("240", "240p"):
        return 240
    if q_str in ("144", "144p"):
        return 144

    # Extract digits
    digits = re.findall(r"\d+", q_str)
    if digits:
        parsed_val = int(digits[0])
        return parsed_val if parsed_val >= 0 else 0

    return 0


def validate_audio_bitrate(quality: Optional[Union[str, int]]) -> str:
    """
    Normalize audio quality to standardized bitrate string ("320", "192", "128", "0").
    Returns "0" for best VBR quality.

    Examples:
        - "320k" -> "320"
        - "best" -> "0"
        - 192 -> "192"
    """
    if quality is None:
        return "0"

    q_str = str(quality).lower().rstrip("k").rstrip("kbps").strip()
    if q_str in ("320", "256", "192", "128", "96", "64"):
        return q_str
    if q_str in ("0", "best", "highest", "vbr", "max", "auto", "b"):
        return "0"

    # Digits matching
    digits = re.findall(r"\d+", q_str)
    if digits and digits[0] in ("320", "256", "192", "128", "96", "64"):
        return digits[0]

    return "0"


def validate_subtitle_format(sub_format: Optional[str]) -> str:
    """
    Validate subtitle container format ('srt', 'vtt', 'ass', 'lrc').
    Defaults to 'srt' if omitted or unsupported.
    """
    if not sub_format:
        return "srt"
    s = str(sub_format).lower().strip().lstrip(".")
    if s in SUPPORTED_SUBTITLE_FORMATS:
        return s
    return "srt"


def validate_output_format(output_format: Optional[str], media_type: str = "video") -> str:
    """
    Validate container output format for video or audio media types.
    """
    media_type = media_type.lower().strip()
    if not output_format:
        return "mp3" if media_type == "audio" else "mp4"

    fmt = str(output_format).lower().strip().lstrip(".")

    if media_type == "audio":
        if fmt in SUPPORTED_AUDIO_CONTAINERS:
            return fmt
        return "mp3"

    if fmt in SUPPORTED_VIDEO_CONTAINERS:
        return fmt
    return "mp4"

# ---------------------------------------------------------------------------
# Aliases & Exports
# ---------------------------------------------------------------------------

resolve_video_height = validate_video_quality
resolve_audio_bitrate = validate_audio_bitrate

