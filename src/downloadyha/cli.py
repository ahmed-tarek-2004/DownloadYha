import argparse
import os
import sys
from typing import Optional

from . import __version__, __app_name__
from . import updater
from . import config
from .dependencies import check_dependencies, verify_dependencies, repair_dependencies
from .downloader import (
    get_video_info,
    choose_video_quality,
    choose_audio_quality,
    download_audio,
    download_video
)
from .logging import setup_logging, get_logger



def choose_download_folder() -> Optional[str]:
    """
    Prompt user to enter a download folder.

    Returns:
        Selected download path, or None if failed.
    """
    download_path = input(
        "\nEnter download folder (leave empty for Downloads): "
    ).strip()

    if not download_path:
        download_path = os.path.join(
            os.path.expanduser("~"),
            "Downloads"
        )

    # Remove quotes if present
    download_path = download_path.strip('"')

    try:
        os.makedirs(download_path, exist_ok=True)
    except Exception as e:
        print(f"\nFailed to create download folder:")
        print(e)
        return None

    return download_path


def print_banner() -> None:
    """Print the application banner."""
    print()
    print("=" * 55)
    print("                  Downloadyha")
    print("=" * 55)
    print("              YouTube Downloader")
    print("=" * 55)


def run_download_interactive() -> int:
    """
    Run the interactive download workflow.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger = get_logger("cli")

    print_banner()

    # Non-intrusive update notification (respects 24-hour cache)
    updater.notify_update_available()

    # Check dependencies
    if not check_dependencies():
        logger.error("Missing dependencies, aborting")
        return 1

    # Get URL
    url = input("\nEnter YouTube URL: ").strip()

    if not url:
        print("\nURL cannot be empty.")
        return 1

    # Get download folder
    download_path = choose_download_folder()
    if download_path is None:
        return 1

    # Get video info
    print("\nGetting video information...")
    info = get_video_info(url)

    if info is None:
        return 1

    title = info.get("title", "Unknown")
    print(f"\nTitle: {title}")
    logger.info(f"Video title: {title}")

    # Choose download type
    print("\nChoose download type:")
    print("1. Audio")
    print("2. Video")

    download_type = input("\nEnter your choice: ").strip()
    logger.info(f"Download type selected: {download_type}")

    if download_type == "1":
        # Audio download
        quality = choose_audio_quality()
        if quality is None:
            return 1

        success = download_audio(url, download_path, quality)

    elif download_type == "2":
        # Video download
        height = choose_video_quality(info)
        if height is None:
            return 1

        success = download_video(url, download_path, height)

    else:
        print("\nInvalid choice.")
        return 1

    print("\nThank you for using Downloadyha.")
    logger.info("Downloadyha finished")

    return 0 if success else 1


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog=__app_name__.lower(),
        description="A YouTube downloader CLI with audio and video support."
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
        help="Enable verbose output"
    )

    return parser


def main() -> None:
    """Main entry point for the CLI."""
    # Setup logging
    setup_logging(log_to_file=True, log_to_console=False)
    logger = get_logger("cli")
    logger.info(f"Downloadyha v{__version__} started")

    # Handle 'downloadyha update' command
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()

        if arg == "update":
            updater.handle_update_command()
            return

        elif arg == "repair":
            print("\nAttempting to repair Downloadyha dependencies...")
            if repair_dependencies():
                print("\nRepair completed successfully.")
                sys.exit(0)
            else:
                print("\nRepair failed. Some dependencies could not be installed.")
                sys.exit(1)

        elif arg in ("--help", "-h", "help"):
            print()
            print("=" * 55)
            print("                 Downloadyha Help")
            print("=" * 55)
            print()
            print("Usage:")
            print("  downloadyha          Start the YouTube downloader")
            print("  downloadyha update   Check for and install updates")
            print("  downloadyha repair   Repair/reinstall dependencies")
            print("  downloadyha --verify Verify dependencies")
            print("  downloadyha --help   Show this help message")
            print()
            print("=" * 55)
            print()
            return

        elif arg == "--verify":
            print("Verifying dependencies...")
            if verify_dependencies():
                print("All dependencies are available.")
                sys.exit(0)
            else:
                print("Some dependencies are missing.")
                sys.exit(1)

        elif arg == "--version" or arg == "-v":
            print(f"Downloadyha {__version__}")
            return

    # Run interactive mode
    exit_code = run_download_interactive()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()