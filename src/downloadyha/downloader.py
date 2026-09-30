"""
downloader.py - Core YouTube downloading engine using yt-dlp.

Supports:
- Single video downloads (custom resolution up to 4K, audio/video stream merging).
- Single audio downloads (MP3 extraction with customizable bitrate: 320k, 192k, 128k, best).
- Full Playlist downloads (video or audio, indexed filenames, organized folder hierarchy).
- Real-time progress reporting hooks.
- Cross-platform dependency integration (bundled FFmpeg and Deno runtimes).
"""

import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import yt_dlp

from .dependencies import get_deno_path, get_ffmpeg_path
from .logging import get_logger
from .ui import render_progress


# ---------------------------------------------------------------------------
# Options Builder
# ---------------------------------------------------------------------------

def get_yt_dlp_options(extra_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get baseline yt-dlp options with bundled runtime and ffmpeg paths.
    """
    options: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": False,
        "ignoreerrors": False,
        "logtostderr": False,
    }

    # Configure Deno runtime for YouTube JS challenges if available
    deno_path = get_deno_path()
    if deno_path:
        options["js_runtimes"] = {
            "deno": {
                "path": str(deno_path)
            }
        }
    else:
        options["js_runtimes"] = {
            "deno": {}
        }

    # Configure FFmpeg path
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path:
        options["ffmpeg_location"] = str(ffmpeg_path.parent)

    if extra_opts:
        options.update(extra_opts)

    return options


def sanitize_folder_name(name: str) -> str:
    """
    Sanitize folder/file names to be safe on Windows and Linux.
    """
    # Replace invalid characters: < > : " / \ | ? * with an underscore
    clean = re.sub(r'[<>:"/\\|?*]+', "_", name).strip(". _")
    return clean if clean else "YouTube_Download"


# ---------------------------------------------------------------------------
# Metadata Extraction
# ---------------------------------------------------------------------------

def get_media_info(url: str, extract_flat: bool = False) -> Optional[Dict[str, Any]]:
    """
    Extract metadata for a YouTube URL (video or playlist).

    Args:
        url: YouTube URL.
        extract_flat: If True, quickly extract playlist metadata without fetching all video details.

    Returns:
        Information dictionary or None on failure.
    """
    logger = get_logger("downloader")
    options = get_yt_dlp_options({
        "extract_flat": "in_playlist" if extract_flat else False,
    })

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        logger.error(f"Failed to get media info for {url}: {e}")
        return None


def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """Backward-compatible alias for get_media_info."""
    return get_media_info(url)


def is_playlist(info: Dict[str, Any]) -> bool:
    """
    Check if the extracted metadata represents a playlist.
    """
    if not info:
        return False
    if info.get("_type") == "playlist":
        return True
    if "entries" in info and isinstance(info["entries"], list):
        return True
    return False


def get_playlist_entries(info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract list of non-null entries from playlist info.
    """
    if not is_playlist(info):
        return [info]
    entries = info.get("entries", [])
    return [e for e in entries if e is not None]


def get_video_qualities(info: Dict[str, Any]) -> List[int]:
    """
    Extract available video resolutions (height in pixels) sorted descending.

    Args:
        info: Single video or playlist metadata dictionary.

    Returns:
        List of unique heights (e.g. [1080, 720, 480, 360, 240, 144]).
    """
    heights: Set[int] = set()

    # If this is a playlist, check the first few entries to find representative qualities
    if is_playlist(info):
        entries = get_playlist_entries(info)
        # Default standard qualities for playlists
        return [1080, 720, 480, 360]

    formats = info.get("formats", [])
    for fmt in formats:
        h = fmt.get("height")
        if h and isinstance(h, int) and h >= 144:
            heights.add(h)

    # Standard fallback list if no heights found
    if not heights:
        return [1080, 720, 480, 360]

    return sorted(heights, reverse=True)


# ---------------------------------------------------------------------------
# Single Downloads
# ---------------------------------------------------------------------------

def download_video(
    url: str,
    download_path: str,
    height: Optional[int] = None,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> bool:
    """
    Download a single YouTube video with audio merged.

    Args:
        url: YouTube video URL.
        download_path: Destination folder.
        height: Maximum video height (e.g., 1080, 720). If None, best quality.
        progress_callback: Optional callback for progress hook.

    Returns:
        True on success, False on error.
    """
    logger = get_logger("downloader")
    os.makedirs(download_path, exist_ok=True)

    if height:
        video_format = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
    else:
        video_format = "bestvideo+bestaudio/best"

    def _hook(data: Dict[str, Any]) -> None:
        if progress_callback:
            progress_callback(data)
        else:
            render_progress(data)

    options = get_yt_dlp_options({
        "format": video_format,
        "outtmpl": os.path.join(download_path, "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "progress_hooks": [_hook],
    })

    try:
        logger.info(f"Starting video download: url={url}, height={height}p")
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        logger.info("Video download completed successfully")
        return True
    except Exception as e:
        logger.error(f"Video download failed: {e}")
        return False


def download_audio(
    url: str,
    download_path: str,
    quality: str = "0",
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> bool:
    """
    Download single YouTube video as MP3 audio.

    Args:
        url: YouTube video URL.
        download_path: Destination folder.
        quality: MP3 bitrate or quality ("0" for best, "320", "192", "128").
        progress_callback: Optional callback for progress hook.

    Returns:
        True on success, False on error.
    """
    logger = get_logger("downloader")
    os.makedirs(download_path, exist_ok=True)

    def _hook(data: Dict[str, Any]) -> None:
        if progress_callback:
            progress_callback(data)
        else:
            render_progress(data)

    options = get_yt_dlp_options({
        "format": "bestaudio/best",
        "outtmpl": os.path.join(download_path, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ],
        "progress_hooks": [_hook],
    })

    try:
        logger.info(f"Starting audio download: url={url}, quality={quality}kbps")
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        logger.info("Audio download completed successfully")
        return True
    except Exception as e:
        logger.error(f"Audio download failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Playlist Downloads
# ---------------------------------------------------------------------------

def download_playlist(
    url: str,
    download_path: str,
    download_type: str,
    quality: str,
    playlist_title: str = "Playlist"
) -> Dict[str, Any]:
    """
    Download a full YouTube playlist with organized subfolder and indexed files.

    Args:
        url: Playlist URL.
        download_path: Root download directory.
        download_type: "video" or "audio".
        quality: Video height (e.g. "1080", "720") or Audio bitrate (e.g. "320", "0").
        playlist_title: Title of the playlist for folder naming.

    Returns:
        Summary dict with results { "success": bool, "output_dir": str, "error": str }.
    """
    logger = get_logger("downloader")

    # Create safe playlist folder
    folder_name = sanitize_folder_name(playlist_title)
    target_dir = os.path.join(download_path, folder_name)
    os.makedirs(target_dir, exist_ok=True)

    # Filename template with playlist index for proper order
    out_template = os.path.join(target_dir, "%(playlist_index)02d - %(title)s.%(ext)s")

    def _hook(data: Dict[str, Any]) -> None:
        # Pass index info to progress renderer if available
        pl_idx = data.get("info_dict", {}).get("playlist_index")
        pl_total = data.get("info_dict", {}).get("n_entries")
        render_progress(data, playlist_index=pl_idx, playlist_total=pl_total)

    extra_opts: Dict[str, Any] = {
        "outtmpl": out_template,
        "ignoreerrors": True,  # Don't fail entire playlist if one video is blocked/deleted
        "progress_hooks": [_hook],
    }

    if download_type == "video":
        if quality and quality != "best":
            try:
                h = int(quality)
                extra_opts["format"] = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
            except ValueError:
                extra_opts["format"] = "bestvideo+bestaudio/best"
        else:
            extra_opts["format"] = "bestvideo+bestaudio/best"
        extra_opts["merge_output_format"] = "mp4"

    else:
        # Audio download
        extra_opts["format"] = "bestaudio/best"
        extra_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality if quality else "0",
            }
        ]

    options = get_yt_dlp_options(extra_opts)

    try:
        logger.info(f"Starting playlist download ({download_type}): title={playlist_title}")
        with yt_dlp.YoutubeDL(options) as ydl:
            exit_code = ydl.download([url])

        success = (exit_code == 0)
        return {
            "success": success,
            "output_dir": target_dir,
            "folder_name": folder_name,
        }
    except Exception as e:
        logger.error(f"Playlist download error: {e}")
        return {
            "success": False,
            "output_dir": target_dir,
            "error": str(e),
        }
