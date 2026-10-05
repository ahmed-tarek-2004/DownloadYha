"""
ytdlp_service.py - Serverless-optimized media metadata extraction and stream resolution service.
Designed for high concurrency, fast cold starts, and resilience in serverless environments (Vercel, AWS Lambda, etc.).
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import yt_dlp

from ..models import (
    ClipInfo,
    DownloadRequest,
    DownloadStreamResponse,
    FormatInfo,
    HealthResponse,
    MediaInfoResponse,
    PlaylistEntry,
    PlaylistInfoResponse,
    PlaylistResolvedEntry,
    PlaylistResolveResponse,
    SubtitleTrack,
)
from ..validators import (
    SUPPORTED_PLATFORMS,
    detect_platform,
    format_bytes,
    format_seconds,
    is_playlist_url,
    parse_time_str,
    sanitize_filename,
    sanitize_folder_name,
    validate_audio_bitrate,
    validate_clip_range,
    validate_media_url,
    validate_output_format,
    validate_subtitle_format,
    validate_video_quality,
)

logger = logging.getLogger("downloadyha.api.service")
_SERVICE_START_TIME = time.time()


# ---------------------------------------------------------------------------
# Custom Exception Classes
# ---------------------------------------------------------------------------

class DownloadyhaException(Exception):
    """Base exception for all Downloadyha API errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "DOWNLOADYHA_ERROR",
        status_code: int = 500,
        detail: Optional[str] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.detail = detail or message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": False,
            "error_code": self.error_code,
            "message": self.message,
            "detail": self.detail,
            "status_code": self.status_code,
        }


# Backwards-compatible / shorthand alias
ApiException = DownloadyhaException


class InvalidUrlError(DownloadyhaException):
    """Raised when an invalid, malformed, or unsupported URL is provided."""

    def __init__(self, message: str = "Invalid or unsupported media URL.", detail: Optional[str] = None) -> None:
        super().__init__(message=message, error_code="INVALID_URL", status_code=400, detail=detail)


class MediaNotFoundError(DownloadyhaException):
    """Raised when the requested media does not exist, was deleted, or is unavailable."""

    def __init__(self, message: str = "Media not found or is currently unavailable.", detail: Optional[str] = None) -> None:
        super().__init__(message=message, error_code="MEDIA_NOT_FOUND", status_code=404, detail=detail)


class ValidationError(DownloadyhaException):
    """Raised when input parameters (e.g. clip ranges or quality options) fail validation."""

    def __init__(self, message: str = "Input parameter validation failed.", detail: Optional[str] = None) -> None:
        super().__init__(message=message, error_code="VALIDATION_ERROR", status_code=400, detail=detail)


class AgeRestrictedError(DownloadyhaException):
    """Raised when content is age-restricted and requires sign-in authentication."""

    def __init__(self, message: str = "Media is age-restricted and cannot be extracted.", detail: Optional[str] = None) -> None:
        super().__init__(message=message, error_code="AGE_RESTRICTED", status_code=403, detail=detail)


class GeoBlockedError(DownloadyhaException):
    """Raised when content is blocked in the server's geographic region."""

    def __init__(self, message: str = "Media is not available in the server's geographic location.", detail: Optional[str] = None) -> None:
        super().__init__(message=message, error_code="GEO_BLOCKED", status_code=403, detail=detail)


class PrivateMediaError(DownloadyhaException):
    """Raised when media is private or restricted to authorized viewers."""

    def __init__(self, message: str = "Media is private or restricted to authorized users.", detail: Optional[str] = None) -> None:
        super().__init__(message=message, error_code="PRIVATE_MEDIA", status_code=403, detail=detail)


class RateLimitError(DownloadyhaException):
    """Raised when the upstream platform rate-limits or challenges with bot verification (HTTP 429)."""

    def __init__(self, message: str = "Upstream media platform rate limit reached. Please try again later.", detail: Optional[str] = None) -> None:
        super().__init__(message=message, error_code="RATE_LIMITED", status_code=429, detail=detail)


class ExtractionError(DownloadyhaException):
    """Raised when yt-dlp fails to extract media metadata or streams."""

    def __init__(self, message: str = "Failed to extract media information.", detail: Optional[str] = None) -> None:
        super().__init__(message=message, error_code="EXTRACTION_ERROR", status_code=502, detail=detail)


# ---------------------------------------------------------------------------
# Exception Mapping & Error Parsing
# ---------------------------------------------------------------------------

def map_ytdlp_exception(e: Exception, url: str) -> DownloadyhaException:
    """
    Inspect a yt-dlp or generic exception and map it to a specific, informative DownloadyhaException.

    Strips internal yt-dlp traceback prefixes to provide clean, readable error descriptions.
    """
    if isinstance(e, DownloadyhaException):
        return e

    err_str = str(e).strip()

    # Clean yt-dlp prefix: 'ERROR: [youtube] 12345: ' -> '...'
    clean_msg = re.sub(r"^ERROR:\s*(\[[^\]]+\]\s*[^:]*:\s*)?", "", err_str).strip()
    clean_lower = clean_msg.lower()

    # Detect specific error scenarios
    if any(k in clean_lower for k in ("video unavailable", "this video has been removed", "does not exist", "not found", "404")):
        return MediaNotFoundError(
            message="The requested video or media is unavailable, deleted, or does not exist.",
            detail=clean_msg
        )

    if any(k in clean_lower for k in ("private video", "sign in if you've been granted access", "account is private")):
        return PrivateMediaError(
            message="This media is private and cannot be accessed without authorization.",
            detail=clean_msg
        )

    if any(k in clean_lower for k in ("sign in to confirm your age", "age-restricted", "inappropriate for some users")):
        return AgeRestrictedError(
            message="This video is age-restricted and requires account verification.",
            detail=clean_msg
        )

    if any(k in clean_lower for k in ("not available in your country", "geoblocked", "geographic restriction", "blocked in your country")):
        return GeoBlockedError(
            message="This media is not available in the server's geographic location.",
            detail=clean_msg
        )

    if any(k in clean_lower for k in ("http error 429", "too many requests", "rate-limited", "bot verification", "sign in to confirm you're not a bot")):
        return RateLimitError(
            message="The upstream platform has temporarily rate-limited access. Please try again in a few moments.",
            detail=clean_msg
        )

    if any(k in clean_lower for k in ("is not a valid url", "unsupported url", "no suitable extractor")):
        return InvalidUrlError(
            message=f"The URL '{url}' is not a valid or supported media link.",
            detail=clean_msg
        )

    return ExtractionError(
        message=f"Extraction failed: {clean_msg or 'Unknown error occurred while processing URL.'}",
        detail=clean_msg
    )


# ---------------------------------------------------------------------------
# Serverless yt-dlp Option Builder
# ---------------------------------------------------------------------------

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

DEFAULT_HTTP_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Mode": "navigate",
}


def build_serverless_ytdlp_options(
    extract_flat: Union[bool, str] = False,
    socket_timeout: int = 15,
    custom_opts: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build yt-dlp configuration options optimized for serverless environments.

    Features:
    - Pure metadata/stream resolution without writing media files.
    - Read-only filesystem resilience (cache disabled / cachedir=False).
    - SSL certificate tolerance for serverless container environments.
    - Realistic browser headers to prevent basic anti-bot challenges.
    - Strict socket timeouts to avoid exceeding serverless function limits.
    - Zero remote binary execution requirements for pure stream resolution.
    """
    options: Dict[str, Any] = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "socket_timeout": socket_timeout,
        "cachedir": False,
        "extract_flat": extract_flat,
        "ignoreerrors": False,
        "no_color": True,
        "logtostderr": False,
        "http_headers": DEFAULT_HTTP_HEADERS.copy(),
        # Don't force format_sort - let yt-dlp choose available formats
        # "format_sort": ["res", "fps", "codec:h264", "size", "br"],
        # YouTube-specific options for better extraction
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "player_skip": ["webpage", "configs"],
            }
        },
        # Prevent yt-dlp from trying to select a default format for download
        "format": "bestvideo+bestaudio/best",
    }

    # If local Deno is present in runtime environment, hook it for JS solving
    deno_executable = os.environ.get("DENO_PATH") or (
        "deno.exe" if os.name == "nt" else "deno"
    )
    # Check if Deno is available on PATH
    try:
        from shutil import which
        found_deno = which(deno_executable)
        if found_deno:
            options["js_runtimes"] = {
                "deno": {
                    "path": found_deno
                }
            }
    except Exception:
        pass

    # Merge caller custom options
    if custom_opts:
        options.update(custom_opts)

    return options


# ---------------------------------------------------------------------------
# Core Metadata Extraction
# ---------------------------------------------------------------------------

def raw_extract_info(
    target_url: str,
    options: Optional[Dict[str, Any]] = None,
    process: bool = True
) -> Dict[str, Any]:
    """
    Perform direct yt-dlp extraction call.
    Separated for unit testing and direct backend overrides.
    """
    opts = options or build_serverless_ytdlp_options()
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(target_url, download=False, process=process)


def extract_info(
    url: str,
    extract_flat: Union[bool, str] = False,
    process: bool = True,
    custom_opts: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract raw media or playlist dictionary from a media URL using yt-dlp.

    Args:
        url: Media video or playlist URL.
        extract_flat: False (full extraction), True (flat metadata), or 'in_playlist'.
        process: Whether to fully parse video stream formats.
        custom_opts: Optional extra options for yt-dlp.

    Returns:
        Extracted yt-dlp metadata dictionary.

    Raises:
        InvalidUrlError: If URL is malformed or invalid.
        MediaNotFoundError: If media does not exist.
        ExtractionError: If metadata extraction failed.
    """
    # Pre-validate URL
    val_res = validate_media_url(url)
    if not val_res.is_valid:
        raise InvalidUrlError(
            message=f"Invalid URL: {val_res.error_message or 'URL format is not recognized.'}",
            detail=val_res.error_message
        )

    target_url = val_res.normalized_url or url.strip()
    options = build_serverless_ytdlp_options(
        extract_flat=extract_flat,
        custom_opts=custom_opts
    )

    try:
        logger.info("Extracting media info for URL: %s (flat=%s)", target_url, extract_flat)
        info = raw_extract_info(target_url, options, process=process)

        if not info:
            raise MediaNotFoundError(f"No media information could be retrieved for URL: {target_url}")

        # Materialize entries list if generator
        if "entries" in info and info["entries"] is not None:
            if not isinstance(info["entries"], list):
                try:
                    info["entries"] = [e for e in info["entries"] if e is not None]
                except Exception as e:
                    logger.warning("Error materializing playlist entries: %s", e)
                    info["entries"] = []

        # Tag playlist status
        is_pl = (
            info.get("_type") in ("playlist", "multi_video")
            or ("entries" in info and info.get("entries") is not None)
            or bool(info.get("playlist_count") and not info.get("formats"))
        )
        info["is_playlist"] = is_pl

        return info

    except Exception as e:
        logger.error("Extraction error for %s: %s", target_url, e)
        raise map_ytdlp_exception(e, target_url)


# ---------------------------------------------------------------------------
# Subtitle Extraction Helper
# ---------------------------------------------------------------------------

def get_subtitles_info_from_dict(info: Dict[str, Any]) -> List[SubtitleTrack]:
    """
    Parse subtitles and auto captions from an extracted yt-dlp info dictionary.
    """
    manual_subs = info.get("subtitles") or {}
    auto_subs = info.get("automatic_captions") or {}

    subtitle_tracks: List[SubtitleTrack] = []
    seen_keys: Set[Tuple[str, bool]] = set()

    # 1. Manual Subtitles
    for lang, track_list in sorted(manual_subs.items()):
        if not track_list or not isinstance(track_list, list):
            continue
        formats = [sub.get("ext") for sub in track_list if sub.get("ext")]
        formats = list(dict.fromkeys(formats))  # Preserve order deduplication
        first_track = track_list[0] if track_list else {}
        name = first_track.get("name")
        url = first_track.get("url")
        ext = first_track.get("ext") or (formats[0] if formats else "srt")

        key = (lang, False)
        if key not in seen_keys:
            seen_keys.add(key)
            subtitle_tracks.append(
                SubtitleTrack(
                    lang=lang,
                    name=name,
                    is_auto=False,
                    ext=ext,
                    url=url,
                    formats=formats,
                )
            )

    # 2. Automatic Captions
    for lang, track_list in sorted(auto_subs.items()):
        if not track_list or not isinstance(track_list, list):
            continue
        formats = [sub.get("ext") for sub in track_list if sub.get("ext")]
        formats = list(dict.fromkeys(formats))
        first_track = track_list[0] if track_list else {}
        name = first_track.get("name")
        url = first_track.get("url")
        ext = first_track.get("ext") or (formats[0] if formats else "srt")

        key = (lang, True)
        if key not in seen_keys:
            seen_keys.add(key)
            subtitle_tracks.append(
                SubtitleTrack(
                    lang=lang,
                    name=name,
                    is_auto=True,
                    ext=ext,
                    url=url,
                    formats=formats,
                )
            )

    return subtitle_tracks


def get_subtitles_info(url: str) -> List[SubtitleTrack]:
    """
    Extract all available subtitle and caption tracks for a media URL.

    Args:
        url: Media video URL.

    Returns:
        List of SubtitleTrack instances.
    """
    info = extract_info(url, extract_flat=False, process=True)
    return get_subtitles_info_from_dict(info)


# ---------------------------------------------------------------------------
# Format Parsing & Breakdown
# ---------------------------------------------------------------------------

def parse_format_item(fmt: Dict[str, Any]) -> FormatInfo:
    """
    Convert a raw yt-dlp format dictionary into a structured FormatInfo model.
    """
    fmt_id = str(fmt.get("format_id") or fmt.get("id") or "")
    ext = fmt.get("ext") or "mp4"
    resolution = fmt.get("resolution") or (f"{fmt.get('width')}x{fmt.get('height')}" if fmt.get("width") and fmt.get("height") else None)
    height = fmt.get("height")
    width = fmt.get("width")
    fps = fmt.get("fps")
    filesize = fmt.get("filesize") or fmt.get("filesize_approx")
    vcodec = fmt.get("vcodec")
    acodec = fmt.get("acodec")
    tbr = fmt.get("tbr")
    abr = fmt.get("abr")
    vbr = fmt.get("vbr")
    url = fmt.get("url")
    note = fmt.get("format_note") or fmt.get("note")
    protocol = fmt.get("protocol")
    http_headers = fmt.get("http_headers")

    has_video = bool(vcodec and str(vcodec).lower() != "none") or bool(height and height > 0)
    has_audio = bool(acodec and str(acodec).lower() != "none") or bool(abr and abr > 0)

    # Human-formatted filesize
    filesize_fmt = format_bytes(filesize) if filesize else None

    return FormatInfo(
        id=fmt_id,
        format_id=fmt_id,
        ext=ext,
        resolution=resolution,
        height=height,
        width=width,
        fps=fps,
        filesize=filesize,
        filesize_formatted=filesize_fmt,
        vcodec=vcodec,
        acodec=acodec,
        tbr=tbr,
        abr=abr,
        vbr=vbr,
        url=url,
        note=note,
        has_video=has_video,
        has_audio=has_audio,
        protocol=protocol,
        http_headers=http_headers,
    )


def get_formats_breakdown(url: str) -> Dict[str, Any]:
    """
    Extract and categorize available media formats for a URL.

    Returns:
        Dictionary containing:
        - 'video_only': list of video-only formats
        - 'audio_only': list of audio-only formats
        - 'combined': list of progressive combined streams
        - 'best_video': best quality video stream
        - 'best_audio': best quality audio stream
        - 'best_combined': best progressive stream
        - 'available_resolutions': list of available video heights descending
        - 'available_audio_bitrates': list of standard bitrates
    """
    info = extract_info(url, extract_flat=False, process=True)
    raw_formats = info.get("formats") or []

    video_only: List[FormatInfo] = []
    audio_only: List[FormatInfo] = []
    combined: List[FormatInfo] = []
    heights_set: Set[int] = set()

    for rf in raw_formats:
        item = parse_format_item(rf)
        if item.height and item.height >= 144:
            heights_set.add(item.height)

        if item.has_video and item.has_audio:
            combined.append(item)
        elif item.has_video:
            video_only.append(item)
        elif item.has_audio:
            audio_only.append(item)

    # Sort formats
    video_only.sort(key=lambda x: (x.height or 0, x.tbr or 0.0, x.fps or 0.0), reverse=True)
    audio_only.sort(key=lambda x: (x.abr or 0.0, x.tbr or 0.0), reverse=True)
    combined.sort(key=lambda x: (x.height or 0, x.tbr or 0.0), reverse=True)

    sorted_heights = sorted(heights_set, reverse=True) if heights_set else [1080, 720, 480, 360]

    return {
        "title": info.get("title") or "Unknown Media",
        "id": info.get("id") or "",
        "video_only": video_only,
        "audio_only": audio_only,
        "combined": combined,
        "video_formats": video_only,
        "audio_formats": audio_only,
        "progressive_formats": combined,
        "best_video": video_only[0] if video_only else (combined[0] if combined else None),
        "best_audio": audio_only[0] if audio_only else (combined[0] if combined else None),
        "best_combined": combined[0] if combined else None,
        "available_resolutions": sorted_heights,
        "available_audio_bitrates": ["320", "256", "192", "128", "96", "64", "0"],
    }


# ---------------------------------------------------------------------------
# Structured Media Information
# ---------------------------------------------------------------------------

def get_structured_media_info(url: str, include_subtitles: bool = True) -> MediaInfoResponse:
    """
    Retrieve comprehensive, validated media information structured for the REST API.

    Args:
        url: Media video or playlist URL.
        include_subtitles: Whether to extract and include subtitle tracks.

    Returns:
        MediaInfoResponse instance.

    Raises:
        InvalidUrlError: If URL is invalid.
        MediaNotFoundError: If media is unavailable.
        ExtractionError: If extraction fails.
    """
    info = extract_info(url, extract_flat=False, process=True)

    media_id = str(info.get("id") or "")
    title = str(info.get("title") or "Untitled Media")
    uploader = info.get("uploader") or info.get("artist") or info.get("creator")
    channel = info.get("channel") or info.get("uploader")
    channel_url = info.get("channel_url") or info.get("uploader_url")
    duration = float(info["duration"]) if info.get("duration") is not None else None
    duration_fmt = format_seconds(duration) if duration else None
    thumbnail = info.get("thumbnail")
    thumbnails = info.get("thumbnails") or []
    description = info.get("description")
    view_count = info.get("view_count")
    like_count = info.get("like_count")
    upload_date = info.get("upload_date")
    tags = info.get("tags") or []
    webpage_url = info.get("webpage_url") or url
    is_pl = bool(info.get("is_playlist", False))
    pl_count = info.get("playlist_count") or (len(info.get("entries")) if info.get("entries") else None)

    # Parse stream formats
    raw_formats = info.get("formats") or []
    formats_list: List[FormatInfo] = []
    heights_set: Set[int] = set()

    for rf in raw_formats:
        f_item = parse_format_item(rf)
        formats_list.append(f_item)
        if f_item.height and f_item.height >= 144:
            heights_set.add(f_item.height)

    available_resolutions = sorted(heights_set, reverse=True) if heights_set else [1080, 720, 480, 360]

    # Subtitles
    subtitles = get_subtitles_info_from_dict(info) if include_subtitles else []

    return MediaInfoResponse(
        success=True,
        url=url,
        id=media_id,
        title=title,
        uploader=uploader,
        channel=channel,
        channel_url=channel_url,
        duration=duration,
        duration_formatted=duration_fmt,
        thumbnail=thumbnail,
        thumbnails=thumbnails,
        description=description,
        view_count=view_count,
        like_count=like_count,
        upload_date=upload_date,
        is_playlist=is_pl,
        playlist_count=pl_count,
        formats=formats_list,
        available_resolutions=available_resolutions,
        available_audio_qualities=[
            "320 kbps (High Quality)",
            "192 kbps (Standard Quality)",
            "128 kbps (Compact Size)",
            "Best Available (VBR)",
        ],
        subtitles=subtitles,
        tags=tags,
        webpage_url=webpage_url,
    )


# ---------------------------------------------------------------------------
# Direct Stream Resolution
# ---------------------------------------------------------------------------

def resolve_download_streams(req: DownloadRequest) -> DownloadStreamResponse:
    """
    Resolve direct streaming and download URLs for a given media request.

    Features:
    - Resolves optimal video and audio streams matching requested quality.
    - Handles clipping timestamps (start_time, end_time) and calculates clip metadata.
    - Matches requested subtitles (languages and format).
    - Extracts HTTP playback headers required for client streaming.
    - Returns structured DownloadStreamResponse.

    Args:
        req: Validated DownloadRequest model.

    Returns:
        DownloadStreamResponse instance.

    Raises:
        ValidationError: If clipping timestamps or parameters are invalid.
        MediaNotFoundError: If media cannot be found.
        ExtractionError: If stream URLs cannot be resolved.
    """
    # 1. Pre-validate clipping timestamps if provided
    clip_resp = None
    if req.start_time is not None or req.end_time is not None:
        clip_resp = validate_clip_range(req.start_time, req.end_time)
        if not clip_resp.is_valid:
            raise ValidationError(
                message=clip_resp.error_message or "Invalid clipping timestamps.",
                detail=clip_resp.error_message
            )

    # 2. Extract full metadata
    info = extract_info(req.url, extract_flat=False, process=True)

    title = str(info.get("title") or "Untitled Media")
    media_id = str(info.get("id") or "")
    uploader = info.get("uploader") or info.get("artist") or info.get("channel")
    thumbnail = info.get("thumbnail")
    duration = float(info["duration"]) if info.get("duration") is not None else None
    duration_fmt = format_seconds(duration) if duration else None

    # Re-validate clip against actual media duration if available
    if clip_resp and duration:
        clip_resp = validate_clip_range(req.start_time, req.end_time, media_duration=duration)
        if not clip_resp.is_valid:
            raise ValidationError(
                message=clip_resp.error_message or "Clipping range exceeds media duration.",
                detail=clip_resp.error_message
            )

    # Build ClipInfo model
    clip_info_model = None
    if clip_resp and (clip_resp.start_seconds is not None or clip_resp.end_seconds is not None):
        clip_info_model = ClipInfo(
            start_time=clip_resp.start_time,
            end_time=clip_resp.end_time,
            duration_seconds=clip_resp.clip_duration_seconds,
            start_seconds=clip_resp.start_seconds,
            end_seconds=clip_resp.end_seconds,
            clip_duration_seconds=clip_resp.clip_duration_seconds,
            clip_duration_formatted=clip_resp.clip_duration_formatted,
        )

    raw_formats = info.get("formats") or []
    if not raw_formats and "url" in info:
        # Single direct URL format fallback
        raw_formats = [{
            "format_id": "direct",
            "url": info["url"],
            "ext": info.get("ext", "mp4"),
            "vcodec": info.get("vcodec"),
            "acodec": info.get("acodec"),
        }]

    # Segregate formats
    video_formats: List[FormatInfo] = []
    audio_formats: List[FormatInfo] = []
    progressive_formats: List[FormatInfo] = []

    for rf in raw_formats:
        f_item = parse_format_item(rf)
        if not f_item.url:
            continue
        if f_item.has_video and f_item.has_audio:
            progressive_formats.append(f_item)
        elif f_item.has_video:
            video_formats.append(f_item)
        elif f_item.has_audio:
            audio_formats.append(f_item)

    # Sort formats
    video_formats.sort(key=lambda x: (x.height or 0, x.tbr or 0.0, x.fps or 0.0), reverse=True)
    audio_formats.sort(key=lambda x: (x.abr or 0.0, x.tbr or 0.0), reverse=True)
    progressive_formats.sort(key=lambda x: (x.height or 0, x.tbr or 0.0), reverse=True)

    # 3. Stream Selection based on media_type and quality
    media_type = str(req.media_type).lower().strip()
    selected_video_stream: Optional[FormatInfo] = None
    selected_audio_stream: Optional[FormatInfo] = None
    direct_download_url: Optional[str] = None
    audio_stream_url: Optional[str] = None
    resolved_quality_label: str = "best"
    out_format = validate_output_format(req.output_format, media_type=media_type)

    if media_type == "audio":
        resolved_quality_label = validate_audio_bitrate(req.quality)
        # Select best audio stream
        if audio_formats:
            selected_audio_stream = audio_formats[0]
        elif progressive_formats:
            selected_audio_stream = progressive_formats[0]
        elif video_formats:
            selected_audio_stream = video_formats[0]

        if not selected_audio_stream or not selected_audio_stream.url:
            raise ExtractionError("No playable audio stream could be resolved for this media.")

        direct_download_url = selected_audio_stream.url
        audio_stream_url = selected_audio_stream.url

    else:
        # Video stream selection
        target_height = validate_video_quality(req.quality)
        resolved_quality_label = f"{target_height}p" if target_height > 0 else "best"

        # Find best matching progressive format at or below target height
        best_prog: Optional[FormatInfo] = None
        if progressive_formats:
            if target_height > 0:
                matching_prog = [p for p in progressive_formats if (p.height or 0) <= target_height]
                best_prog = matching_prog[0] if matching_prog else progressive_formats[-1]
            else:
                best_prog = progressive_formats[0]

        # Find best matching video stream
        matching_vids = video_formats
        if target_height > 0:
            filtered = [v for v in video_formats if (v.height or 0) <= target_height]
            matching_vids = filtered if filtered else video_formats

        selected_video_stream = matching_vids[0] if matching_vids else best_prog

        # Find best audio stream to accompany video
        if audio_formats:
            selected_audio_stream = audio_formats[0]
        elif progressive_formats:
            selected_audio_stream = progressive_formats[0]

        # Determine direct URL: prefer progressive stream if it matches quality close enough,
        # otherwise use the direct video stream URL
        if best_prog and (target_height == 0 or (best_prog.height or 0) >= target_height):
            direct_download_url = best_prog.url
            selected_video_stream = best_prog
        elif selected_video_stream and selected_video_stream.url:
            direct_download_url = selected_video_stream.url
        elif best_prog:
            direct_download_url = best_prog.url
            selected_video_stream = best_prog
        else:
            raise ExtractionError("No playable video stream could be resolved for this media.")

        audio_stream_url = selected_audio_stream.url if selected_audio_stream else None

    # Extract headers needed for playback
    stream_headers = (
        (selected_video_stream.http_headers if selected_video_stream else None)
        or (selected_audio_stream.http_headers if selected_audio_stream else None)
        or info.get("http_headers")
        or DEFAULT_HTTP_HEADERS
    )

    # Subtitles filtering
    selected_subtitles: List[SubtitleTrack] = []
    if req.write_subtitles or req.write_auto_subs or req.sub_langs:
        all_subs = get_subtitles_info_from_dict(info)
        allowed_langs = None
        if req.sub_langs and req.sub_langs.lower() not in ("all", "*"):
            allowed_langs = {l.strip().lower() for l in req.sub_langs.split(",") if l.strip()}

        for sub in all_subs:
            # Language match
            if allowed_langs and sub.lang.lower() not in allowed_langs:
                continue
            # Auto vs manual match
            if sub.is_auto and not req.write_auto_subs and req.write_subtitles:
                continue
            if not sub.is_auto and not req.write_subtitles and req.write_auto_subs:
                continue
            selected_subtitles.append(sub)

    # Calculate filesize estimation
    est_filesize = None
    if selected_video_stream and selected_video_stream.filesize:
        est_filesize = selected_video_stream.filesize
        if selected_audio_stream and selected_audio_stream.filesize and selected_video_stream != selected_audio_stream:
            est_filesize += selected_audio_stream.filesize
    elif selected_audio_stream and selected_audio_stream.filesize:
        est_filesize = selected_audio_stream.filesize

    filesize_fmt = format_bytes(est_filesize) if est_filesize else None
    safe_filename = f"{sanitize_filename(title)}.{out_format}"

    return DownloadStreamResponse(
        success=True,
        message="Stream resolved successfully",
        title=title,
        id=media_id,
        filename=safe_filename,
        uploader=uploader,
        thumbnail=thumbnail,
        media_type=media_type,
        quality=resolved_quality_label,
        format=out_format,
        duration=duration,
        duration_formatted=duration_fmt,
        direct_url=direct_download_url,
        direct_download_url=direct_download_url,
        audio_url=audio_stream_url,
        filesize=est_filesize,
        filesize_formatted=filesize_fmt,
        clip_info=clip_info_model,
        subtitles=selected_subtitles,
        headers=stream_headers,
        http_headers=stream_headers,
        video_stream=selected_video_stream,
        audio_stream=selected_audio_stream,
    )


# ---------------------------------------------------------------------------
# Playlist Extraction
# ---------------------------------------------------------------------------

def get_playlist_details(url: str, limit: int = 50) -> PlaylistInfoResponse:
    """
    Extract playlist metadata and summarized video entries up to a specified limit.

    Args:
        url: Media playlist URL.
        limit: Maximum number of entries to extract (default: 50).

    Returns:
        PlaylistInfoResponse instance.

    Raises:
        InvalidUrlError: If URL is invalid.
        MediaNotFoundError: If playlist is unavailable.
        ExtractionError: If extraction fails.
    """
    info = extract_info(url, extract_flat="in_playlist", process=True)

    pl_id = str(info.get("id") or "playlist")
    title = str(info.get("title") or "Untitled Playlist")
    uploader = info.get("uploader") or info.get("channel") or info.get("artist")
    description = info.get("description")
    webpage_url = info.get("webpage_url") or url
    thumbnail = info.get("thumbnail")

    raw_entries = info.get("entries") or []
    if not isinstance(raw_entries, list):
        try:
            raw_entries = list(raw_entries)
        except Exception:
            raw_entries = []

    # Filter non-null entries and apply limit
    valid_entries = [e for e in raw_entries if e is not None][:max(1, limit)]
    entries_list: List[PlaylistEntry] = []

    for index, item in enumerate(valid_entries, start=1):
        if not isinstance(item, dict):
            continue
        v_id = str(item.get("id") or f"item_{index}")
        v_title = str(item.get("title") or f"Track {index}")
        v_dur = float(item["duration"]) if item.get("duration") is not None else None
        v_dur_fmt = format_seconds(v_dur) if v_dur else None
        v_thumb = item.get("thumbnail") or (item.get("thumbnails")[0].get("url") if item.get("thumbnails") else None)
        v_url = item.get("url") or item.get("webpage_url") or f"https://www.youtube.com/watch?v=#{v_id}"
        v_uploader = item.get("uploader") or item.get("channel")

        entries_list.append(
            PlaylistEntry(
                id=v_id,
                title=v_title,
                duration=v_dur,
                duration_formatted=v_dur_fmt,
                thumbnail=v_thumb,
                url=v_url,
                uploader=v_uploader,
                playlist_index=index,
            )
        )

    total_count = info.get("playlist_count") or len(raw_entries) or len(entries_list)

    return PlaylistInfoResponse(
        success=True,
        id=pl_id,
        title=title,
        uploader=uploader,
        count=total_count,
        entries=entries_list,
        description=description,
        webpage_url=webpage_url,
        thumbnail=thumbnail,
    )


def resolve_playlist_streams(
    url: str,
    media_type: str = "video",
    quality: Any = "best",
    output_format: Optional[str] = None,
    limit: int = 50
) -> PlaylistResolveResponse:
    """
    Resolve direct streaming and download URLs for entries in a playlist.
    Matches the CLI and Desktop downloader's indexed folder structure:
    '%(playlist_index&{:02d} - |)s%(title)s.%(ext)s'.

    Args:
        url: Media playlist URL.
        media_type: 'video' or 'audio'.
        quality: Video height or audio bitrate.
        output_format: Container format ('mp4', 'mp3', etc.).
        limit: Max playlist entries to resolve.

    Returns:
        PlaylistResolveResponse instance.
    """
    media_type = "audio" if str(media_type).lower().strip() in ("audio", "mp3") else "video"
    out_format = validate_output_format(output_format, media_type=media_type)
    pl_info = get_playlist_details(url, limit=limit)
    folder = sanitize_folder_name(pl_info.title)

    resolved_entries: List[PlaylistResolvedEntry] = []

    for entry in pl_info.entries:
        entry_url = entry.url
        idx = entry.playlist_index or (len(resolved_entries) + 1)
        safe_title = sanitize_filename(entry.title)
        filename = f"{idx:02d} - {safe_title}.{out_format}"

        # Resolve stream for each entry
        try:
            req = DownloadRequest(
                url=entry_url,
                media_type=media_type,
                quality=quality,
                output_format=out_format,
            )
            stream_res = resolve_download_streams(req)
            resolved_entries.append(
                PlaylistResolvedEntry(
                    id=entry.id,
                    playlist_index=idx,
                    title=entry.title,
                    filename=filename,
                    duration=entry.duration,
                    duration_formatted=entry.duration_formatted,
                    thumbnail=entry.thumbnail,
                    url=entry_url,
                    direct_url=stream_res.direct_url,
                    direct_download_url=stream_res.direct_url,
                    audio_url=stream_res.audio_url,
                    quality=stream_res.quality,
                    format=out_format,
                )
            )
        except Exception as e:
            logger.warning("Failed to resolve stream for playlist item %s (%s): %s", idx, entry_url, e)
            # Add fallback entry with standard web url if direct stream extraction fails
            resolved_entries.append(
                PlaylistResolvedEntry(
                    id=entry.id,
                    playlist_index=idx,
                    title=entry.title,
                    filename=filename,
                    duration=entry.duration,
                    duration_formatted=entry.duration_formatted,
                    thumbnail=entry.thumbnail,
                    url=entry_url,
                    direct_url=None,
                    direct_download_url=None,
                    audio_url=None,
                    quality=str(quality),
                    format=out_format,
                )
            )

    return PlaylistResolveResponse(
        success=True,
        id=pl_info.id,
        title=pl_info.title,
        uploader=pl_info.uploader,
        folder_name=folder,
        total_items=pl_info.count,
        resolved_items=len(resolved_entries),
        media_type=media_type,
        entries=resolved_entries,
    )


def resolve_subtitle_stream(
    url: str,
    lang: str = "en",
    sub_format: str = "srt",
    is_auto: bool = False
) -> Dict[str, Any]:
    """
    Resolve subtitle track URL and suggested safe filename for direct download.

    Args:
        url: Video URL.
        lang: Language code (e.g. 'en', 'ar').
        sub_format: Subtitle container format ('srt', 'vtt', 'ass', 'lrc').
        is_auto: Whether to match auto-generated caption or manual subtitle.

    Returns:
        Dictionary with title, filename, url, lang, format, and content-type.
    """
    info = extract_info(url, extract_flat=False, process=True)
    title = str(info.get("title") or "video")
    sub_fmt = validate_subtitle_format(sub_format)
    safe_title = sanitize_filename(title)
    target_lang = lang.lower().strip()

    manual_subs = info.get("subtitles") or {}
    auto_subs = info.get("automatic_captions") or {}

    subs_dict = auto_subs if is_auto else (manual_subs or auto_subs)
    matched_track_url = None

    if target_lang in subs_dict:
        tracks = subs_dict[target_lang]
        if isinstance(tracks, list):
            # Try to match format
            for t in tracks:
                if t.get("ext") == sub_fmt and t.get("url"):
                    matched_track_url = t["url"]
                    break
            if not matched_track_url and tracks and tracks[0].get("url"):
                matched_track_url = tracks[0]["url"]

    # Fallback to any language matching prefix
    if not matched_track_url:
        for l_key, tracks in subs_dict.items():
            if l_key.lower().startswith(target_lang) and isinstance(tracks, list) and tracks:
                matched_track_url = tracks[0].get("url")
                target_lang = l_key
                break

    if not matched_track_url:
        raise MediaNotFoundError(f"Subtitle track for language '{lang}' was not found for this media.")

    content_type = "text/vtt" if sub_fmt == "vtt" else ("application/x-subrip" if sub_fmt == "srt" else "text/plain")
    filename = f"{safe_title}.{target_lang}.{sub_fmt}"

    return {
        "title": title,
        "filename": filename,
        "url": matched_track_url,
        "lang": target_lang,
        "format": sub_fmt,
        "content_type": content_type,
    }


# ---------------------------------------------------------------------------
# Health Check & Service Metadata
# ---------------------------------------------------------------------------

def get_health_status(start_time: Optional[float] = None) -> HealthResponse:
    """
    Generate health check and runtime status report.

    Args:
        start_time: Optional process start timestamp.

    Returns:
        HealthResponse instance.
    """
    effective_start = start_time if start_time is not None else _SERVICE_START_TIME
    uptime = max(0.0, time.time() - effective_start)

    ytdlp_ver = getattr(yt_dlp.version, "__version__", "unknown")

    return HealthResponse(
        status="ok",
        version="2.0.0",
        ytdlp_version=ytdlp_ver,
        serverless=True,
        supported_platforms=SUPPORTED_PLATFORMS,
        uptime=uptime,
        uptime_seconds=uptime,
        timestamp=time.time(),
    )
