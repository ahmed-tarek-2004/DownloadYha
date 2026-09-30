import os
import shutil
import sys

import yt_dlp

from . import updater
from . import config


APP_NAME = "Downloadyha"


def get_common_options():
    return {
        "quiet": True,
        "no_warnings": True,

        "js_runtimes": {
            "deno": {}
        },

        "remote_components": [
            "ejs:github"
        ],
    }



def check_dependencies():
    missing = []

    if not shutil.which("ffmpeg"):
        missing.append("FFmpeg")

    if not shutil.which("deno"):
        missing.append("Deno")

    if not missing:
        return True

    print("\nMissing dependencies:")
    
    for dependency in missing:
        print(f"  - {dependency}")

    print(
        "\nPlease install the missing dependencies "
        "before using Downloadyha."
    )

    return False




def get_video_info(url):

    options = get_common_options()

    try:

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        return info

    except Exception as e:

        print(
            "\nFailed to get video information:"
        )

        print(e)

        return None



def get_video_qualities(info):

    formats = info.get(
        "formats",
        []
    )

    heights = set()

    for fmt in formats:

        height = fmt.get("height")

        if height and height >= 144:

            heights.add(height)

    return sorted(heights)


def choose_video_quality(info):

    heights = get_video_qualities(
        info
    )

    if not heights:

        print(
            "\nNo video qualities were found."
        )

        return None

    print(
        "\nAvailable video qualities:"
    )

    for index, height in enumerate(
        heights,
        start=1
    ):

        print(
            f"{index}. {height}p"
        )

    choice = input(
        "\nChoose quality: "
    ).strip()

    try:

        index = int(choice) - 1

        if (
            index < 0
            or index >= len(heights)
        ):

            print(
                "Invalid choice."
            )

            return None

        return heights[index]

    except ValueError:

        print(
            "Invalid choice."
        )

        return None




def choose_audio_quality():

    print(
        "\nAvailable audio qualities:"
    )

    print("1. Best")
    print("2. 128 kbps")
    print("3. 192 kbps")
    print("4. 320 kbps")

    choice = input(
        "\nChoose quality: "
    ).strip()

    quality_map = {
        "1": "0",
        "2": "128",
        "3": "192",
        "4": "320"
    }

    quality = quality_map.get(
        choice
    )

    if quality is None:

        print(
            "Invalid choice."
        )

        return None

    return quality




def download_audio(
    url,
    download_path,
    quality
):

    options = get_common_options()

    options.update({

        "format":
            "bestaudio/best",

        "outtmpl":
            os.path.join(
                download_path,
                "%(title)s.%(ext)s"
            ),

        "postprocessors": [
            {
                "key":
                    "FFmpegExtractAudio",

                "preferredcodec":
                    "mp3",

                "preferredquality":
                    quality
            }
        ],

        "progress_hooks": [
            progress_hook
        ]
    })

    try:

        print(
            "\nDownloading audio...\n"
        )

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download([url])

        print(
            "\nAudio download completed successfully."
        )

    except Exception as e:

        print(
            "\nDownload failed:"
        )

        print(e)




def download_video(
    url,
    download_path,
    height
):

    video_format = (
        f"bestvideo[height<={height}]"
        f"+bestaudio/"
        f"best[height<={height}]"
    )

    options = get_common_options()

    options.update({

        "format":
            video_format,

        "outtmpl":
            os.path.join(
                download_path,
                "%(title)s.%(ext)s"
            ),

        "merge_output_format":
            "mp4",

        "progress_hooks": [
            progress_hook
        ]
    })

    try:

        print(
            "\nDownloading video...\n"
        )

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download([url])

        print(
            "\nVideo download completed successfully."
        )

    except Exception as e:

        print(
            "\nDownload failed:"
        )

        print(e)




def progress_hook(data):

    status = data.get(
        "status"
    )

    if status == "downloading":

        percentage = data.get(
            "_percent_str",
            ""
        )

        speed = data.get(
            "_speed_str",
            ""
        )

        eta = data.get(
            "_eta_str",
            ""
        )

        print(
            f"\rDownloading "
            f"{percentage} "
            f"| Speed: {speed} "
            f"| ETA: {eta}",
            end="",
            flush=True
        )

    elif status == "finished":

        print(
            "\nProcessing file..."
        )



def choose_download_folder():

    download_path = input(
        "\nEnter download folder "
        "(leave empty for Downloads): "
    ).strip()

    if not download_path:

        download_path = os.path.join(
            os.path.expanduser("~"),
            "Downloads"
        )

    download_path = (
        download_path.strip('"')
    )

    try:

        os.makedirs(
            download_path,
            exist_ok=True
        )

    except Exception as e:

        print(
            "\nFailed to create download folder:"
        )

        print(e)

        return None

    return download_path



def main():
    # Handle 'downloadyha update' command
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()
        if arg == "update":
            updater.handle_update_command()
            return
        elif arg in ("--help", "-h", "help"):
            print()
            print("=" * 55)
            print("                 Downloadyha Help")
            print("=" * 55)
            print()
            print("Usage:")
            print("  downloadyha          Start the YouTube downloader")
            print("  downloadyha update   Check for and install updates")
            print("  downloadyha --help   Show this help message")
            print()
            print("=" * 55)
            print()
            return

    print()
    print("=" * 55)
    print("                  Downloadyha")
    print("=" * 55)
    print(
        "              YouTube Downloader"
    )
    print("=" * 55)

    # Non-intrusive update notification (respects 24-hour cache)
    updater.notify_update_available()

    if not check_dependencies():

        return


    url = input(
        "\nEnter YouTube URL: "
    ).strip()

    if not url:

        print(
            "\nURL cannot be empty."
        )

        return


    download_path = (
        choose_download_folder()
    )

    if download_path is None:

        return


    print(
        "\nGetting video information..."
    )

    info = get_video_info(
        url
    )

    if info is None:

        return

    title = info.get(
        "title",
        "Unknown"
    )

    print(
        f"\nTitle: {title}"
    )

   
    print(
        "\nChoose download type:"
    )

    print("1. Audio")
    print("2. Video")

    download_type = input(
        "\nEnter your choice: "
    ).strip()


    if download_type == "1":

        quality = (
            choose_audio_quality()
        )

        if quality is None:

            return

        download_audio(
            url,
            download_path,
            quality
        )

  
    elif download_type == "2":

        height = (
            choose_video_quality(
                info
            )
        )

        if height is None:

            return

        download_video(
            url,
            download_path,
            height
        )


    else:

        print(
            "\nInvalid choice."
        )

        return

    print(
        "\nThank you for using Downloadyha."
    )


if __name__ == "__main__":
    main()