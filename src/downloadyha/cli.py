"""
cli.py - Main interactive CLI entry point for Downloadyha.

Provides a modern, colored terminal user interface for:
- Single video & audio downloads
- Playlist downloads (video & audio)
- Self-updater and uninstaller commands
- Dependency management and diagnostics
"""

import argparse
import os
import sys
from typing import Optional

from . import __app_name__, __version__
from . import config, uninstaller, updater
from .dependencies import check_dependencies, repair_dependencies, verify_dependencies
from .downloader import (
    download_audio,
    download_playlist,
    download_video,
    get_media_info,
    get_playlist_entries,
    get_video_qualities,
    is_playlist,
)
from .logging import get_logger, setup_logging
from .ui import (
    Colors,
    Symbols,
    error,
    format_duration,
    info,
    init_terminal,
    print_banner,
    print_card,
    print_step,
    print_summary,
    prompt_choice,
    prompt_confirm,
    prompt_input,
    success,
    wait,
    warning,
)


def choose_download_folder() -> Optional[str]:
    """
    Prompt user to select a destination directory.
    Defaults to the user's Downloads folder.
    """
    default_dir = str(config.get_download_dir())
    path_input = prompt_input("Enter destination folder", default=default_dir)

    # Clean quotes and strip whitespace
    clean_path = path_input.strip('"\'')

    try:
        os.makedirs(clean_path, exist_ok=True)
        return clean_path
    except Exception as e:
        error(f"Could not create download folder: {e}")
        return None


def run_download_interactive() -> int:
    """
    Execute the interactive download workflow with modern UI.
    """
    logger = get_logger("cli")

    init_terminal()
    print_banner()

    # Check for updates in the background
    updater.notify_update_available()

    # Verify dependencies
    if not check_dependencies():
        logger.error("Missing required dependencies, aborting")
        return 1

    # Step 1: Input URL
    print_step(1, 3, "Enter YouTube URL")
    url = prompt_input("Paste Video or Playlist URL")

    if not url:
        error("URL cannot be empty.")
        return 1

    # Step 2: Select destination
    print_step(2, 3, "Select Destination Folder")
    download_path = choose_download_folder()
    if download_path is None:
        return 1

    # Step 3: Fetch Metadata & Configure Download
    print_step(3, 3, "Analyzing Media & Selecting Quality")
    wait("Fetching media metadata from YouTube...")
    info_dict = get_media_info(url)

    if not info_dict:
        error("Failed to retrieve media information. Please check the URL or your internet connection.")
        return 1

    # -----------------------------------------------------------------------
    # Playlist Workflow
    # -----------------------------------------------------------------------
    if is_playlist(info_dict):
        entries = get_playlist_entries(info_dict)
        pl_title = info_dict.get("title", "YouTube Playlist")
        pl_author = info_dict.get("uploader") or info_dict.get("channel") or "Unknown"
        total_videos = len(entries) if entries else info_dict.get("playlist_count", "Multiple")

        print_card(
            title="Playlist Detected",
            items=[
                ("Title", pl_title),
                ("Channel", pl_author),
                ("Total Items", f"{total_videos} videos"),
                ("Type", "YouTube Playlist"),
                ("Destination", download_path),
            ],
            icon=Symbols.PLAYLIST
        )

        dl_type_choice = prompt_choice(
            title="Select Playlist Download Type",
            options=[
                ("video", "Video Playlist (MP4)", "Download all videos in playlist"),
                ("audio", "Audio Playlist (MP3)", "Extract all songs/audio to MP3"),
            ],
            default_index=0
        )

        if dl_type_choice == "video":
            quality_choice = prompt_choice(
                title="Select Maximum Video Quality for Playlist",
                options=[
                    ("best", "Best Available", "Maximum resolution per video"),
                    ("1080", "1080p (Full HD)", "1920x1080 maximum"),
                    ("720", "720p (HD)", "1280x720 standard HD"),
                    ("480", "480p (SD)", "Standard Definition"),
                    ("360", "360p", "Compact size"),
                ],
                default_index=0
            )
            print()
            info(f"Starting Video Playlist Download: {Colors.BOLD}{pl_title}{Colors.RESET}")
            res = download_playlist(
                url=url,
                download_path=download_path,
                media_type="video",
                quality=quality_choice
            )

        else:
            audio_quality = prompt_choice(
                title="Select MP3 Bitrate for Playlist",
                options=[
                    ("0", "Best Quality (VBR 0)", "~245 kbps Variable Bitrate"),
                    ("320", "320 kbps (High)", "Constant Bitrate - Maximum MP3 quality"),
                    ("192", "192 kbps (Standard)", "Balanced quality and file size"),
                    ("128", "128 kbps (Compact)", "Smaller files"),
                ],
                default_index=0
            )
            print()
            info(f"Starting Audio Playlist Download: {Colors.BOLD}{pl_title}{Colors.RESET}")
            res = download_playlist(
                url=url,
                download_path=download_path,
                media_type="audio",
                quality=audio_quality
            )

        if res.get("success"):
            print_summary(
                title="Playlist Download Complete",
                items=[
                    ("Playlist", pl_title),
                    ("Type", dl_type_choice.upper()),
                    ("Saved To", res.get("output_dir", download_path)),
                ]
            )
            return 0
        else:
            error(f"Playlist download finished with issues: {res.get('error', 'Some items may have failed')}")
            return 1

    # -----------------------------------------------------------------------
    # Single Video Workflow
    # -----------------------------------------------------------------------
    else:
        title = info_dict.get("title", "Unknown Title")
        author = info_dict.get("uploader") or info_dict.get("channel") or "Unknown"
        duration = format_duration(info_dict.get("duration"))

        print_card(
            title="Video Information",
            items=[
                ("Title", title),
                ("Channel", author),
                ("Duration", duration),
                ("Type", "Single Video"),
                ("Destination", download_path),
            ],
            icon=Symbols.VIDEO
        )

        dl_type = prompt_choice(
            title="Choose Download Format",
            options=[
                ("video", "Video (MP4)", "High quality video with audio merged"),
                ("audio", "Audio Only (MP3)", "Extract high quality MP3 audio"),
            ],
            default_index=0
        )

        if dl_type == "video":
            available_heights = get_video_qualities(info_dict)
            height_options = []
            for h in available_heights:
                label = f"{h}p"
                desc = "Full HD" if h >= 1080 else ("HD" if h >= 720 else "SD")
                height_options.append((str(h), label, desc))

            if not height_options:
                height_options = [("1080", "1080p", "Best"), ("720", "720p", "HD")]

            selected_height_str = prompt_choice(
                title="Select Video Resolution",
                options=height_options,
                default_index=0
            )
            selected_height = int(selected_height_str)

            print()
            info(f"Downloading Video: {Colors.BOLD}{title}{Colors.RESET} ({selected_height}p)...")
            success_status = download_video(url, download_path, selected_height)

        else:
            # Audio format selection
            selected_bitrate = prompt_choice(
                title="Select MP3 Audio Quality",
                options=[
                    ("0", "Best (VBR 0)", "~245 kbps Variable Bitrate"),
                    ("320", "320 kbps (High)", "Crisp high fidelity MP3"),
                    ("192", "192 kbps (Standard)", "Standard streaming quality"),
                    ("128", "128 kbps (Compact)", "Small file size"),
                ],
                default_index=0
            )

            print()
            info(f"Downloading Audio: {Colors.BOLD}{title}{Colors.RESET}...")
            success_status = download_audio(url, download_path, selected_bitrate)

        if success_status:
            print_summary(
                title="Download Successful",
                items=[
                    ("Title", title),
                    ("Format", dl_type.upper()),
                    ("Saved Folder", download_path),
                ]
            )
            return 0
        else:
            error("Download failed. Check your network connection and retry.")
            return 1


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.
    """
    parser = argparse.ArgumentParser(
        prog=__app_name__.lower(),
        description="A beautiful and fast YouTube Downloader CLI (Video, Audio & Playlists)."
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify dependencies and exit"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    return parser


def main() -> None:
    """Main CLI entry point."""
    setup_logging(log_to_file=True, log_to_console=False)
    logger = get_logger("cli")
    logger.info(f"Downloadyha v{__version__} started")

    # Command-line subcommands
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()

        if arg in ("gui", "--gui"):
            try:
                from .gui import launch_gui
                launch_gui()
                return
            except ImportError as e:
                error(f"Failed to start GUI: {e}")
                sys.exit(1)

        elif arg == "update":
            updater.handle_update_command()
            return

        elif arg == "repair":
            init_terminal()
            info("Attempting to repair Downloadyha dependencies...")
            if repair_dependencies():
                success("Repair completed successfully. All dependencies are installed.")
                sys.exit(0)
            else:
                error("Repair failed. Some dependencies could not be automatically downloaded.")
                sys.exit(1)

        elif arg == "uninstall":
            uninstaller.handle_uninstall_command()
            return

        elif arg in ("--help", "-h", "help"):
            init_terminal()
            print_banner()
            c = Colors
            print(f"{c.BOLD}{c.BRIGHT_WHITE}Usage:{c.RESET}")
            print(f"  {c.BRIGHT_CYAN}downloadyha{c.RESET}            Start interactive downloader (Video / Audio / Playlist)")
            print(f"  {c.BRIGHT_CYAN}downloadyha gui{c.RESET}        Launch Desktop GUI interface")
            print(f"  {c.BRIGHT_CYAN}downloadyha update{c.RESET}     Check for and install updates")
            print(f"  {c.BRIGHT_CYAN}downloadyha repair{c.RESET}     Re-download and repair dependencies (FFmpeg / Deno)")
            print(f"  {c.BRIGHT_CYAN}downloadyha uninstall{c.RESET}  Completely uninstall Downloadyha")
            print(f"  {c.BRIGHT_CYAN}downloadyha --verify{c.RESET}   Verify dependencies status")
            print(f"  {c.BRIGHT_CYAN}downloadyha --version{c.RESET}  Display version info")
            print()
            return

        elif arg == "--verify":
            init_terminal()
            info("Verifying system dependencies...")
            if verify_dependencies():
                success("All dependencies are ready and operational.")
                sys.exit(0)
            else:
                warning("Some dependencies are missing. Run 'downloadyha repair' to fix them.")
                sys.exit(1)

        elif arg in ("--version", "-v"):
            print(f"Downloadyha {__version__}")
            return

    # Interactive flow
    exit_code = run_download_interactive()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
