"""
api.services package - Core business logic and yt-dlp extraction services for Downloadyha.
"""

from .ytdlp_service import (
    # Exceptions
    DownloadyhaException,
    ExtractionError,
    InvalidUrlError,
    MediaNotFoundError,
    ValidationError,
    AgeRestrictedError,
    GeoBlockedError,
    PrivateMediaError,
    RateLimitError,
    # Core Functions
    extract_info,
    get_structured_media_info,
    get_formats_breakdown,
    get_subtitles_info,
    resolve_download_streams,
    resolve_playlist_streams,
    resolve_subtitle_stream,
    get_playlist_details,
    get_health_status,
    build_serverless_ytdlp_options,
)

__all__ = [
    "DownloadyhaException",
    "ExtractionError",
    "InvalidUrlError",
    "MediaNotFoundError",
    "ValidationError",
    "AgeRestrictedError",
    "GeoBlockedError",
    "PrivateMediaError",
    "RateLimitError",
    "extract_info",
    "get_structured_media_info",
    "get_formats_breakdown",
    "get_subtitles_info",
    "resolve_download_streams",
    "resolve_playlist_streams",
    "resolve_subtitle_stream",
    "get_playlist_details",
    "get_health_status",
    "build_serverless_ytdlp_options",
]
