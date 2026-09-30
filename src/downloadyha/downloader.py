"""
YouTube download logic using yt-dlp.

Handles video information retrieval, audio/video downloads,
and quality selection for YouTube content.
"""

import os
from typing import Dict, List, Optional, Any

import yt_dlp

from .dependencies import get_ffmpeg_path, get_deno_path
from .logging import get_logger


def get_yt_dlp_options() -> Dict[str, Any]:
    """
    Get common yt-dlp options.

    Configures yt-dlp with bundled Deno runtime and EJS remote components.

    Returns:
        Dictionary of yt-dlp options.
    """
    options: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
    }

    # Configure Deno runtime for yt-dlp
    deno_path = get_deno_path()
    if deno_path:
        options["js_runtimes"] = {
            "deno": {
                "path": str(deno_path)
            }
        }
    else:
        # Fall back to system deno if bundled not available
        options["js_runtimes"] = {
            "deno": {}
        }

    # Configure FFmpeg path
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path:
        options["ffmpeg_location"] = str(ffmpeg_path.parent)

    return options


def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract video information from a YouTube URL.

    Args:
        url: YouTube video URL.

    Returns:
        Video information dictionary, or None if extraction failed.
    """
    logger = get_logger("downloader")
    options = get_yt_dlp_options()

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        logger.error(f"Failed to get video information: {e}")
        print(f"\nFailed to get video information:")
        print(e)
        return None


def get_video_qualities(info: Dict[str, Any]) -> List[int]:
    """
    Extract available video qualities from video info.

    Args:
        info: Video information dictionary from yt-dlp.

    Returns:
        Sorted list of available video heights.
    """
    formats = info.get("formats", [])
    heights = set()

    for fmt in formats:
        height = fmt.get("height")
        if height and height >= 144:
            heights.add(height)

    return sorted(heights)


def choose_video_quality(info: Dict[str, Any]) -> Optional[int]:
    """
    Prompt user to select video quality.

    Args:
        info: Video information dictionary from yt-dlp.

    Returns:
        Selected video height, or None if selection failed.
    """
    heights = get_video_qualities(info)

    if not heights:
        print("\nNo video qualities were found.")
        return None

    print("\nAvailable video qualities:")
    for index, height in enumerate(heights, start=1):
        print(f"{index}. {height}p")

    choice = input("\nChoose quality: ").strip()

    try:
        index = int(choice) - 1
        if index < 0 or index >= len(heights):
            print("Invalid choice.")
            return None
        return heights[index]
    except ValueError:
        print("Invalid choice.")
        return None


def choose_audio_quality() -> Optional[str]:
    """
    Prompt user to select audio quality.

    Returns:
        Selected audio quality string for FFmpeg, or None if invalid.
    """
    print("\nAvailable audio qualities:")
    print("1. Best")
    print("2. 128 kbps")
    print("3. 192 kbps")
    print("4. 320 kbps")

    choice = input("\nChoose quality: ").strip()

    quality_map = {
        "1": "0",      # Best quality
        "2": "128",
        "3": "192",
        "4": "320"
    }

    quality = quality_map.get(choice)

    if quality is None:
        print("Invalid choice.")
        return None

    return quality


def progress_hook(data: Dict[str, Any]) -> None:
    """
    Progress hook for yt-dlp downloads.

    Args:
        data: Progress data from yt-dlp.
    """
    status = data.get("status")

    if status == "downloading":
        percentage = data.get("_percent_str", "")
        speed = data.get("_speed_str", "")
        eta = data.get("_eta_str", "")
        print(
            f"\rDownloading {percentage} | Speed: {speed} | ETA: {eta}",
            end="",
            flush=True
        )
    elif status == "finished":
        print("\nProcessing file...")


def download_audio(
    url: str,
    download_path: str,
    quality: str
) -> bool:
    """
    Download audio from a YouTube URL.

    Args:
        url: YouTube video URL.
        download_path: Directory to save the downloaded file.
        quality: Audio quality for MP3 conversion.

    Returns:
        True if download succeeded, False otherwise.
    """
    logger = get_logger("downloader")
    options = get_yt_dlp_options()

    options.update({
        "format": "bestaudio/best",
        "outtmpl": os.path.join(download_path, "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality
            }
        ],
        "progress_hooks": [progress_hook]
    })

    try:
        logger.info(f"Starting audio download: url={url}, quality={quality}")
        print("\nDownloading audio...\n")

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        logger.info("Audio download completed successfully")
        print("\nAudio download completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Audio download failed: {e}")
        print("\nDownload failed:")
        print(e)
        return False


def download_video(
    url: str,
    download_path: str,
    height: int
) -> bool:
    """
    Download video from a YouTube URL.

    Args:
        url: YouTube video URL.
        download_path: Directory to save the downloaded file.
        height: Maximum video height resolution.

    Returns:
        True if download succeeded, False otherwise.
    """
    logger = get_logger("downloader")

    video_format = (
        f"bestvideo[height<={height}]+bestaudio/"
        f"best[height<={height}]"
    )

    options = get_yt_dlp_options()

    options.update({
        "format": video_format,
        "outtmpl": os.path.join(download_path, "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "progress_hooks": [progress_hook]
    })

    try:
        logger.info(f"Starting video download: url={url}, height={height}p")
        print("\nDownloading video...\n")

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        logger.info("Video download completed successfully")
        print("\nVideo download completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Video download failed: {e}")
        print("\nDownload failed:")
        print(e)
        return False
