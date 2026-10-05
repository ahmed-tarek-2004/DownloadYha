"""
models.py - Complete, production-grade Pydantic v2 models and schemas for Downloadyha API.
Supports serverless deployment, type safety, flexible aliases, and validation.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MediaType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"


class VideoFormat(str, Enum):
    MP4 = "mp4"
    MKV = "mkv"
    WEBM = "webm"


class AudioFormat(str, Enum):
    MP3 = "mp3"
    M4A = "m4a"
    AAC = "aac"
    OPUS = "opus"
    WAV = "wav"
    FLAC = "flac"


class SubtitleFormat(str, Enum):
    SRT = "srt"
    VTT = "vtt"
    ASS = "ass"
    LRC = "lrc"


# ---------------------------------------------------------------------------
# Core Stream & Format Models
# ---------------------------------------------------------------------------

class FormatInfo(BaseModel):
    """
    Detailed information about a single audio or video stream format.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(..., alias="format_id", description="Unique format identifier (e.g., '137', '22', 'ba')")
    format_id: Optional[str] = Field(default=None, description="Alias matching yt-dlp format_id")
    ext: str = Field(default="mp4", description="File extension (e.g., 'mp4', 'webm', 'm4a')")
    resolution: Optional[str] = Field(default=None, description="Resolution string (e.g., '1920x1080', 'audio only')")
    height: Optional[int] = Field(default=None, description="Video height in pixels (e.g., 1080, 720)")
    width: Optional[int] = Field(default=None, description="Video width in pixels (e.g., 1920, 1280)")
    fps: Optional[float] = Field(default=None, description="Frames per second")
    filesize: Optional[int] = Field(default=None, description="File size in bytes")
    filesize_formatted: Optional[str] = Field(default=None, description="Human-readable file size (e.g., '45.2 MB')")
    vcodec: Optional[str] = Field(default=None, description="Video codec (e.g., 'avc1.640028', 'vp9', 'none')")
    acodec: Optional[str] = Field(default=None, description="Audio codec (e.g., 'mp4a.40.2', 'opus', 'none')")
    tbr: Optional[float] = Field(default=None, description="Total bitrate in kbps")
    abr: Optional[float] = Field(default=None, description="Audio bitrate in kbps")
    vbr: Optional[float] = Field(default=None, description="Video bitrate in kbps")
    url: Optional[str] = Field(default=None, description="Direct stream URL")
    note: Optional[str] = Field(default=None, description="Format note/description (e.g., '1080p', 'medium')")
    has_video: bool = Field(default=False, description="Whether format contains a video track")
    has_audio: bool = Field(default=False, description="Whether format contains an audio track")
    protocol: Optional[str] = Field(default=None, description="Protocol (e.g., 'https', 'm3u8_native')")
    http_headers: Optional[Dict[str, str]] = Field(default=None, description="HTTP headers required for playback")

    @model_validator(mode="before")
    @classmethod
    def sync_ids_and_flags(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Synchronize id and format_id
            fmt_id = data.get("id") or data.get("format_id") or ""
            data["id"] = str(fmt_id)
            data["format_id"] = str(fmt_id)

            # Auto-detect has_video and has_audio if not provided
            vcodec = data.get("vcodec")
            acodec = data.get("acodec")
            if "has_video" not in data:
                data["has_video"] = bool(vcodec and vcodec.lower() != "none")
            if "has_audio" not in data:
                data["has_audio"] = bool(acodec and acodec.lower() != "none")

            # Fallback for progressive streams (height present, neither codec explicitly none)
            if not data.get("has_video") and data.get("height"):
                data["has_video"] = True

            # Formatted filesize
            filesize = data.get("filesize") or data.get("filesize_approx")
            if filesize and not data.get("filesize_formatted"):
                val = float(filesize)
                units = ["B", "KB", "MB", "GB", "TB"]
                u_idx = 0
                while val >= 1024.0 and u_idx < len(units) - 1:
                    val /= 1024.0
                    u_idx += 1
                data["filesize_formatted"] = f"{val:.1f} {units[u_idx]}"
        return data


class SubtitleTrack(BaseModel):
    """
    Information about an individual subtitle track (manual or auto-generated).
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    lang: str = Field(..., description="Language code (e.g., 'en', 'ar', 'es')")
    name: Optional[str] = Field(default=None, description="Language descriptive name (e.g., 'English', 'Arabic')")
    is_auto: bool = Field(default=False, description="True if auto-generated caption, False if manual subtitle")
    ext: Optional[str] = Field(default=None, description="Primary subtitle format extension (e.g., 'srt', 'vtt')")
    url: Optional[str] = Field(default=None, description="Direct download URL for the subtitle track")
    formats: List[str] = Field(default_factory=list, description="Available container formats (e.g., ['srt', 'vtt', 'srv3'])")
    display: Optional[str] = Field(default=None, description="Display string (e.g., 'en (manual) [srt, vtt]')")

    @model_validator(mode="before")
    @classmethod
    def populate_display(cls, data: Any) -> Any:
        if isinstance(data, dict):
            lang = data.get("lang", "")
            is_auto = data.get("is_auto", False)
            formats = data.get("formats", [])
            ext = data.get("ext")
            if ext and ext not in formats:
                formats = [ext] + [f for f in formats if f != ext]
                data["formats"] = formats
            if not data.get("display"):
                fmts_str = ", ".join(formats) if formats else (ext or "srt")
                tag = "auto" if is_auto else "manual"
                data["display"] = f"{lang} ({tag}) [{fmts_str}]"
        return data


# ---------------------------------------------------------------------------
# Media Info Request & Response
# ---------------------------------------------------------------------------

class MediaInfoRequest(BaseModel):
    """
    Request model for extracting video or playlist metadata.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    url: str = Field(..., description="Media URL (YouTube, TikTok, Facebook, Instagram, Twitter/X, etc.)", min_length=3)
    extract_flat: bool = Field(default=False, description="Whether to extract playlist entries without resolving individual media")
    include_subtitles: bool = Field(default=True, description="Whether to include subtitle tracks in information")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("URL cannot be empty")
        if not (s.startswith("http://") or s.startswith("https://")):
            if "." in s and "/" in s:
                s = "https://" + s
            else:
                raise ValueError("Invalid media URL. Must start with http:// or https://")
        return s


class MediaInfoResponse(BaseModel):
    """
    Comprehensive media metadata response.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    success: bool = Field(default=True, description="Indicates successful metadata extraction")
    url: str = Field(..., description="Normalized media URL")
    id: str = Field(..., description="Unique media or video identifier")
    title: str = Field(..., description="Title of the media")
    uploader: Optional[str] = Field(default=None, description="Uploader or creator name")
    channel: Optional[str] = Field(default=None, description="Channel name")
    channel_url: Optional[str] = Field(default=None, description="Channel URL")
    duration: Optional[float] = Field(default=None, description="Duration in seconds")
    duration_formatted: Optional[str] = Field(default=None, description="Formatted duration (e.g., '03:45' or '01:15:00')")
    thumbnail: Optional[str] = Field(default=None, description="Primary thumbnail image URL")
    thumbnails: List[Dict[str, Any]] = Field(default_factory=list, description="List of all available thumbnail images")
    description: Optional[str] = Field(default=None, description="Media description text")
    view_count: Optional[int] = Field(default=None, description="Total view count")
    like_count: Optional[int] = Field(default=None, description="Total like count")
    upload_date: Optional[str] = Field(default=None, description="Upload date in YYYYMMDD format")
    is_playlist: bool = Field(default=False, description="True if URL is a playlist or collection")
    playlist_count: Optional[int] = Field(default=None, description="Number of items in playlist if applicable")
    formats: List[FormatInfo] = Field(default_factory=list, description="Available audio/video stream formats")
    available_resolutions: List[int] = Field(default_factory=list, description="Available video heights sorted descending (e.g., [1080, 720, 480, 360])")
    available_audio_qualities: List[str] = Field(
        default_factory=lambda: ["320 kbps", "192 kbps", "128 kbps", "Best (VBR)"],
        description="Available audio bitrate options"
    )
    subtitles: List[SubtitleTrack] = Field(default_factory=list, description="Available subtitle and caption tracks")
    tags: List[str] = Field(default_factory=list, description="Tags and keywords associated with the media")
    webpage_url: Optional[str] = Field(default=None, description="Original webpage URL")

    @model_validator(mode="before")
    @classmethod
    def format_duration_if_missing(cls, data: Any) -> Any:
        if isinstance(data, dict):
            dur = data.get("duration")
            if dur is not None and dur > 0 and not data.get("duration_formatted"):
                s = int(dur)
                hrs = s // 3600
                mins = (s % 3600) // 60
                secs = s % 60
                if hrs > 0:
                    data["duration_formatted"] = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                else:
                    data["duration_formatted"] = f"{mins:02d}:{secs:02d}"
        return data


# ---------------------------------------------------------------------------
# Download / Streaming Request & Response
# ---------------------------------------------------------------------------

class DownloadRequest(BaseModel):
    """
    Request model for resolving download streams or downloading media.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    url: str = Field(..., description="Media URL to download or stream", min_length=3)
    media_type: Union[MediaType, str] = Field(default=MediaType.VIDEO, description="Target media type: 'video' or 'audio'")
    quality: Optional[Union[str, int]] = Field(
        default="best",
        description="Target resolution height (e.g., '1080', '720', 1080, 0, 'best') or audio bitrate ('320', '192', '128', '0')"
    )
    output_format: Optional[str] = Field(default="mp4", description="Output container format ('mp4', 'mkv', 'webm', 'mp3', 'm4a')")
    start_time: Optional[Union[str, int, float]] = Field(
        default=None,
        description="Optional clip start timestamp (e.g., '01:30', '90', '01:15:00')"
    )
    end_time: Optional[Union[str, int, float]] = Field(
        default=None,
        description="Optional clip end timestamp (e.g., '03:45', '225', '01:20:00')"
    )
    write_subtitles: bool = Field(default=False, description="Include official/manual subtitles")
    write_auto_subs: bool = Field(default=False, description="Include auto-generated captions")
    sub_langs: Optional[str] = Field(default=None, description="Comma-separated language codes (e.g., 'en,ar') or 'all'")
    sub_format: Optional[Union[SubtitleFormat, str]] = Field(default="srt", description="Subtitle format ('srt', 'vtt', 'ass', 'lrc')")
    embed_subs: bool = Field(default=False, description="Embed subtitles into the media file")
    convert_subs: Optional[str] = Field(default=None, description="Target conversion format for subtitles (e.g., 'srt')")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("URL cannot be empty")
        if not (s.startswith("http://") or s.startswith("https://")):
            if "." in s and "/" in s:
                s = "https://" + s
            else:
                raise ValueError("Invalid media URL. Must start with http:// or https://")
        return s

    @field_validator("media_type")
    @classmethod
    def normalize_media_type(cls, v: Union[MediaType, str]) -> str:
        s = str(v).lower().strip()
        if s in ("audio", "mp3", "m4a", "aac", "opus", "wav"):
            return "audio"
        return "video"

    @field_validator("sub_format")
    @classmethod
    def normalize_sub_format(cls, v: Optional[Union[SubtitleFormat, str]]) -> str:
        if not v:
            return "srt"
        s = str(v).lower().strip().lstrip(".")
        if s in ("srt", "vtt", "ass", "lrc"):
            return s
        return "srt"


class ClipInfo(BaseModel):
    """
    Metadata about an extracted or requested media clip.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    start_time: Optional[str] = Field(default=None, description="Start timestamp string (e.g., '01:30')")
    end_time: Optional[str] = Field(default=None, description="End timestamp string (e.g., '03:45')")
    duration_seconds: Optional[float] = Field(default=None, description="Total clip duration in seconds")
    start_seconds: Optional[float] = Field(default=None, description="Start offset in seconds")
    end_seconds: Optional[float] = Field(default=None, description="End offset in seconds")
    clip_duration_seconds: Optional[float] = Field(default=None, description="Alias for duration_seconds")
    clip_duration_formatted: Optional[str] = Field(default=None, description="Formatted clip duration (e.g., '02:15')")

    @model_validator(mode="before")
    @classmethod
    def sync_durations(cls, data: Any) -> Any:
        if isinstance(data, dict):
            dur = data.get("duration_seconds") or data.get("clip_duration_seconds")
            if dur is not None:
                data["duration_seconds"] = float(dur)
                data["clip_duration_seconds"] = float(dur)
                if not data.get("clip_duration_formatted"):
                    s = int(dur)
                    hrs = s // 3600
                    mins = (s % 3600) // 60
                    secs = s % 60
                    if hrs > 0:
                        data["clip_duration_formatted"] = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                    else:
                        data["clip_duration_formatted"] = f"{mins:02d}:{secs:02d}"
        return data


class DownloadStreamResponse(BaseModel):
    """
    Complete response containing direct playback and download stream URLs.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    success: bool = Field(default=True, description="Indicates whether streams were resolved successfully")
    message: str = Field(default="Stream resolved successfully", description="Status message")
    title: str = Field(..., description="Media title")
    id: Optional[str] = Field(default=None, description="Media ID")
    filename: Optional[str] = Field(default=None, description="Suggested safe filename for downloading")
    uploader: Optional[str] = Field(default=None, description="Uploader / artist")
    media_type: str = Field(default="video", description="Media type: 'video' or 'audio'")
    quality: str = Field(default="best", description="Resolved quality identifier")
    format: str = Field(default="mp4", alias="selected_format", description="Target container format")
    duration: Optional[float] = Field(default=None, description="Media total duration in seconds")
    duration_formatted: Optional[str] = Field(default=None, description="Formatted duration string")
    direct_url: Optional[str] = Field(default=None, alias="direct_download_url", description="Primary direct stream / download URL")
    audio_url: Optional[str] = Field(default=None, description="Separate direct audio stream URL if applicable")
    filesize: Optional[int] = Field(default=None, description="Estimated file size in bytes")
    filesize_formatted: Optional[str] = Field(default=None, description="Formatted file size string (e.g., '14.2 MB')")
    thumbnail: Optional[str] = Field(default=None, description="Media thumbnail URL")
    clip_info: Optional[ClipInfo] = Field(default=None, description="Clip timestamp info if clipping was requested")
    subtitles: List[SubtitleTrack] = Field(default_factory=list, description="List of matched subtitle tracks")
    headers: Optional[Dict[str, str]] = Field(default=None, alias="http_headers", description="HTTP headers needed for stream playback")
    video_stream: Optional[FormatInfo] = Field(default=None, description="Selected video stream details")
    audio_stream: Optional[FormatInfo] = Field(default=None, description="Selected audio stream details")

    @model_validator(mode="before")
    @classmethod
    def sync_urls_and_formats(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync direct_url and direct_download_url
            d_url = data.get("direct_url") or data.get("direct_download_url")
            if d_url:
                data["direct_url"] = d_url
                data["direct_download_url"] = d_url

            # Sync headers and http_headers
            hdrs = data.get("headers") or data.get("http_headers")
            if hdrs:
                data["headers"] = hdrs
                data["http_headers"] = hdrs

            # Sync format and selected_format
            fmt = data.get("format") or data.get("selected_format") or "mp4"
            data["format"] = fmt
            data["selected_format"] = fmt
        return data


# ---------------------------------------------------------------------------
# Validation Request & Response Models
# ---------------------------------------------------------------------------

class ClipValidationRequest(BaseModel):
    """
    Request model for validating start and end timestamp ranges.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    start_time: Optional[Union[str, int, float]] = Field(default=None, description="Start timestamp (e.g., '01:30', '90')")
    end_time: Optional[Union[str, int, float]] = Field(default=None, description="End timestamp (e.g., '03:45', '225')")
    duration: Optional[Union[str, int, float]] = Field(default=None, alias="media_duration", description="Total media duration in seconds or timestamp")

    @property
    def media_duration(self) -> Optional[Union[str, int, float]]:
        return self.duration


class ClipValidationResponse(BaseModel):
    """
    Response model with parsed timestamp ranges and validation verdict.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    is_valid: bool = Field(..., description="Whether the clip range is valid")
    start_time: Optional[str] = Field(default=None, description="Formatted start timestamp (e.g., '01:30')")
    end_time: Optional[str] = Field(default=None, description="Formatted end timestamp (e.g., '03:45')")
    duration: Optional[float] = Field(default=None, description="Total media duration in seconds")
    start_seconds: Optional[float] = Field(default=None, description="Start timestamp in seconds")
    end_seconds: Optional[float] = Field(default=None, description="End timestamp in seconds")
    clip_duration_seconds: Optional[float] = Field(default=None, description="Total duration of the clip in seconds")
    clip_duration_formatted: Optional[str] = Field(default=None, description="Formatted clip duration (e.g., '02:15')")
    error_message: Optional[str] = Field(default=None, description="Validation error message if invalid")


class UrlValidationRequest(BaseModel):
    """
    Request model for URL verification and platform identification.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    url: str = Field(..., description="Media URL to validate")


class UrlValidationResponse(BaseModel):
    """
    Response model indicating platform and validity of a URL.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    url: str = Field(..., description="Submitted URL")
    is_valid: bool = Field(..., description="Whether the URL is valid and recognized")
    platform: str = Field(default="Unknown", description="Detected platform (YouTube, TikTok, Facebook, Instagram, Twitter/X, etc.)")
    is_playlist: bool = Field(default=False, description="Whether the URL is a playlist or album")
    normalized_url: Optional[str] = Field(default=None, description="Clean normalized URL")
    error_message: Optional[str] = Field(default=None, description="Error reason if URL is invalid")


# ---------------------------------------------------------------------------
# Playlist Models
# ---------------------------------------------------------------------------

class PlaylistEntry(BaseModel):
    """
    Summary entry for an individual video inside a playlist.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(..., description="Video ID")
    title: str = Field(..., description="Video title")
    duration: Optional[float] = Field(default=None, description="Video duration in seconds")
    duration_formatted: Optional[str] = Field(default=None, description="Formatted duration string (e.g., '04:12')")
    thumbnail: Optional[str] = Field(default=None, description="Thumbnail URL")
    url: str = Field(..., description="Direct video web URL")
    uploader: Optional[str] = Field(default=None, description="Video uploader or channel")
    playlist_index: Optional[int] = Field(default=None, description="1-based position inside playlist")


class PlaylistInfoResponse(BaseModel):
    """
    Response model containing playlist metadata and summarized entries.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    success: bool = Field(default=True, description="Indicates whether playlist info was retrieved")
    id: str = Field(..., description="Playlist ID")
    title: str = Field(..., description="Playlist title")
    uploader: Optional[str] = Field(default=None, description="Playlist owner or channel name")
    count: int = Field(default=0, description="Total number of entries in the playlist")
    entries: List[PlaylistEntry] = Field(default_factory=list, description="List of playlist entries")
    description: Optional[str] = Field(default=None, description="Playlist description")
    webpage_url: Optional[str] = Field(default=None, description="Original playlist webpage URL")
    thumbnail: Optional[str] = Field(default=None, description="Playlist cover thumbnail")


class PlaylistResolvedEntry(BaseModel):
    """
    Resolved download stream for a single entry inside a playlist.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(..., description="Video ID")
    playlist_index: int = Field(..., description="1-based position in playlist")
    title: str = Field(..., description="Video title")
    filename: str = Field(..., description="Indexed filename (e.g. '01 - Video Title.mp4')")
    duration: Optional[float] = Field(default=None, description="Duration in seconds")
    duration_formatted: Optional[str] = Field(default=None, description="Formatted duration")
    thumbnail: Optional[str] = Field(default=None, description="Thumbnail URL")
    url: str = Field(..., description="Web URL")
    direct_url: Optional[str] = Field(default=None, alias="direct_download_url", description="Direct stream CDN URL")
    audio_url: Optional[str] = Field(default=None, description="Direct audio stream URL")
    quality: str = Field(default="best", description="Resolved quality")
    format: str = Field(default="mp4", description="Resolved container format")


class PlaylistResolveResponse(BaseModel):
    """
    Response containing resolved download streams for playlist entries.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    success: bool = Field(default=True, description="Indicates whether playlist items were resolved")
    id: str = Field(..., description="Playlist ID")
    title: str = Field(..., description="Playlist title")
    uploader: Optional[str] = Field(default=None, description="Playlist owner / channel")
    folder_name: str = Field(..., description="Suggested folder name for saving playlist items")
    total_items: int = Field(default=0, description="Total entries in playlist")
    resolved_items: int = Field(default=0, description="Number of successfully resolved entries")
    media_type: str = Field(default="video", description="'video' or 'audio'")
    entries: List[PlaylistResolvedEntry] = Field(default_factory=list, description="Resolved playlist entries with stream URLs")


# ---------------------------------------------------------------------------
# System, Health & Error Models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """
    Health check response for monitoring and uptime tracking.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    status: str = Field(default="ok", description="Service status ('ok', 'degraded', 'error')")
    version: str = Field(default="2.0.0", description="Downloadyha API version")
    ytdlp_version: str = Field(..., description="yt-dlp core library version")
    serverless: bool = Field(default=True, description="Whether operating in serverless mode")
    supported_platforms: List[str] = Field(default_factory=list, description="List of supported media platforms")
    uptime: float = Field(default=0.0, alias="uptime_seconds", description="Service uptime in seconds")
    uptime_seconds: Optional[float] = Field(default=None, description="Service uptime in seconds")
    timestamp: float = Field(default_factory=time.time, description="Current UNIX timestamp")

    @model_validator(mode="before")
    @classmethod
    def sync_uptime(cls, data: Any) -> Any:
        if isinstance(data, dict):
            up = data.get("uptime") or data.get("uptime_seconds") or 0.0
            data["uptime"] = float(up)
            data["uptime_seconds"] = float(up)
        return data


class ErrorResponse(BaseModel):
    """
    Standardized error response returned when API operations fail.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    success: bool = Field(default=False, description="Always False for error responses")
    detail: Optional[str] = Field(default=None, description="Human-readable error description")
    error_code: str = Field(default="EXTRACTION_ERROR", description="Machine-readable error classification code")
    errors: List[str] = Field(default_factory=list, description="List of specific error messages")
    message: Optional[str] = Field(default=None, description="Summary error message")
    timestamp: float = Field(default_factory=time.time, description="Error timestamp")

    @model_validator(mode="before")
    @classmethod
    def sync_error_details(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync detail and message
            det = data.get("detail") or data.get("message") or data.get("error")
            if det:
                data["detail"] = str(det)
                data["message"] = str(det)
            # Ensure errors list has at least the main detail
            errors = data.get("errors") or []
            if not errors and det:
                errors = [str(det)]
            data["errors"] = errors
        return data
