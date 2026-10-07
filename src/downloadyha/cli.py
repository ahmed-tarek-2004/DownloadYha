"""
cli.py - Main interactive CLI entry point for Downloadyha.

Provides a modern, colored terminal user interface for:
- Single video & audio downloads
- Playlist downloads (video & audio)
- Self-updater and uninstaller commands
- Dependency management and diagnostics
"""

from __future__ import annotations

__author__ = "Ahmed Tarek Zaher"
__copyright__ = "Copyright 2026, Ahmed Tarek Zaher"
__license__ = "MIT"

# BOOKMARK: Ahmed Tarek Zaher - Owner

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
    has_video_id,
    is_playlist,
    is_pure_playlist_url,
    is_video_in_playlist_url,
    parse_time_str,
    strip_playlist_params,
)
from .logging import get_logger, setup_logging
from .subtitle_utils import get_available_subtitles
from .ui import (
    Colors,
    Symbols,
    error,
    format_duration,
    info,
    init_terminal,
    print_banner,
    print_card,
    print_interrupted,
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


def prompt_transcript_options(url: str) -> dict:
    """
    Interactively ask the user whether they want video transcripts
    (subtitles) downloaded, and with which settings.
    Returns a dict of subtitle options understood by the downloader.

    Args:
        url (str): The video URL to check for available subtitles.
    """
    # Language code to name mapping
    LANGUAGE_NAMES = {
        'en': 'English', 'ar': 'Arabic', 'es': 'Spanish', 'fr': 'French',
        'de': 'German', 'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian',
        'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese', 'zh-Hans': 'Chinese (Simplified)',
        'zh-Hant': 'Chinese (Traditional)', 'hi': 'Hindi', 'bn': 'Bengali',
        'pa': 'Punjabi', 'ta': 'Tamil', 'te': 'Telugu', 'mr': 'Marathi',
        'gu': 'Gujarati', 'kn': 'Kannada', 'ml': 'Malayalam', 'ur': 'Urdu',
        'fa': 'Persian', 'tr': 'Turkish', 'pl': 'Polish', 'nl': 'Dutch',
        'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian', 'fi': 'Finnish',
        'cs': 'Czech', 'sk': 'Slovak', 'hu': 'Hungarian', 'ro': 'Romanian',
        'bg': 'Bulgarian', 'hr': 'Croatian', 'sr': 'Serbian', 'sl': 'Slovenian',
        'et': 'Estonian', 'lv': 'Latvian', 'lt': 'Lithuanian', 'el': 'Greek',
        'he': 'Hebrew', 'vi': 'Vietnamese', 'th': 'Thai', 'id': 'Indonesian',
        'ms': 'Malay', 'tl': 'Filipino', 'sw': 'Swahili', 'af': 'Afrikaans',
        'aa': 'Afar', 'ab': 'Abkhazian', 'af': 'Afrikaans', 'ak': 'Akan',
        'sq': 'Albanian', 'am': 'Amharic', 'an': 'Aragonese', 'hy': 'Armenian',
        'as': 'Assamese', 'av': 'Avaric', 'ae': 'Avestan', 'ay': 'Aymara',
        'az': 'Azerbaijani', 'bm': 'Bambara', 'ba': 'Bashkir', 'eu': 'Basque',
        'be': 'Belarusian', 'bh': 'Bihari', 'bi': 'Bislama', 'bs': 'Bosnian',
        'br': 'Breton', 'my': 'Burmese', 'ca': 'Catalan', 'ch': 'Chamorro',
        'ce': 'Chechen', 'ny': 'Chichewa', 'zh': 'Chinese', 'cv': 'Chuvash',
        'kw': 'Cornish', 'co': 'Corsican', 'cr': 'Cree', 'hr': 'Croatian',
        'cs': 'Czech', 'da': 'Danish', 'dv': 'Divehi', 'nl': 'Dutch',
        'dz': 'Dzongkha', 'en': 'English', 'eo': 'Esperanto', 'et': 'Estonian',
        'ee': 'Ewe', 'fo': 'Faroese', 'fj': 'Fijian', 'fi': 'Finnish',
        'fr': 'French', 'ff': 'Fulah', 'gd': 'Gaelic', 'gl': 'Galician',
        'lg': 'Ganda', 'ka': 'Georgian', 'de': 'German', 'ki': 'Gikuyu',
        'el': 'Greek', 'kl': 'Greenlandic', 'gn': 'Guarani', 'gu': 'Gujarati',
        'ht': 'Haitian', 'ha': 'Hausa', 'he': 'Hebrew', 'hz': 'Herero',
        'hi': 'Hindi', 'ho': 'Hiri Motu', 'hu': 'Hungarian', 'is': 'Icelandic',
        'io': 'Ido', 'ig': 'Igbo', 'id': 'Indonesian', 'ia': 'Interlingua',
        'ie': 'Interlingue', 'iu': 'Inuktitut', 'ik': 'Inupiaq', 'ga': 'Irish',
        'it': 'Italian', 'ja': 'Japanese', 'jv': 'Javanese', 'kn': 'Kannada',
        'kr': 'Kanuri', 'ks': 'Kashmiri', 'kk': 'Kazakh', 'km': 'Khmer',
        'ki': 'Kikuyu', 'rw': 'Kinyarwanda', 'ky': 'Kyrgyz', 'kv': 'Komi',
        'kg': 'Kongo', 'ko': 'Korean', 'ku': 'Kurdish', 'kj': 'Kwanyama',
        'lo': 'Lao', 'la': 'Latin', 'lv': 'Latvian', 'li': 'Limburgan',
        'ln': 'Lingala', 'lt': 'Lithuanian', 'lu': 'Luba-Katanga',
        'lb': 'Luxembourgish', 'mk': 'Macedonian', 'mg': 'Malagasy',
        'ms': 'Malay', 'ml': 'Malayalam', 'mt': 'Maltese', 'gv': 'Manx',
        'mi': 'Maori', 'mr': 'Marathi', 'mh': 'Marshallese', 'mn': 'Mongolian',
        'na': 'Nauru', 'nv': 'Navajo', 'nd': 'North Ndebele', 'ng': 'Ndonga',
        'ne': 'Nepali', 'no': 'Norwegian', 'nb': 'Norwegian Bokmål',
        'nn': 'Norwegian Nynorsk', 'ii': 'Nuosu', 'nr': 'South Ndebele',
        'oc': 'Occitan', 'oj': 'Ojibwa', 'cu': 'Old Church Slavonic',
        'om': 'Oromo', 'or': 'Oriya', 'os': 'Ossetian', 'pa': 'Panjabi',
        'pi': 'Pali', 'fa': 'Persian', 'pl': 'Polish', 'ps': 'Pashto',
        'pt': 'Portuguese', 'qu': 'Quechua', 'rm': 'Romansh', 'rn': 'Rundi',
        'ro': 'Romanian', 'ru': 'Russian', 'sm': 'Samoan', 'sg': 'Sango',
        'sa': 'Sanskrit', 'sc': 'Sardinian', 'sr': 'Serbian', 'sn': 'Shona',
        'sd': 'Sindhi', 'si': 'Sinhala', 'sk': 'Slovak', 'sl': 'Slovenian',
        'so': 'Somali', 'st': 'Southern Sotho', 'es': 'Spanish', 'su': 'Sundanese',
        'sw': 'Swahili', 'ss': 'Swati', 'sv': 'Swedish', 'tl': 'Tagalog',
        'ty': 'Tahitian', 'tg': 'Tajik', 'ta': 'Tamil', 'tt': 'Tatar',
        'te': 'Telugu', 'th': 'Thai', 'bo': 'Tibetan', 'ti': 'Tigrinya',
        'to': 'Tonga', 'ts': 'Tsonga', 'tn': 'Tswana', 'tr': 'Turkish',
        'tk': 'Turkmen', 'tw': 'Twi', 'ug': 'Uighur', 'uk': 'Ukrainian',
        'ur': 'Urdu', 'uz': 'Uzbek', 've': 'Venda', 'vi': 'Vietnamese',
        'vo': 'Volapük', 'wa': 'Walloon', 'cy': 'Welsh', 'wo': 'Wolof',
        'fy': 'Western Frisian', 'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba',
        'za': 'Zhuang', 'zu': 'Zulu'
    }

    # First ask if user wants subtitles at all
    want_subtitles = prompt_choice(
        title="Download Video Transcripts (Subtitles)?",
        options=[
            ("no", "No Subtitles", "Download media only (faster)"),
            ("yes", "Yes, I want subtitles", "Fetch and select available subtitle tracks"),
        ],
        default_index=0
    )

    if not want_subtitles or want_subtitles == "no":
        return {
            "write_subtitles": False,
            "write_auto_subs": False,
            "sub_langs": None,
            "sub_format": "srt",
            "embed_subs": False,
            "convert_subs": None,
        }

    # User wants subtitles - now fetch them
    print("Fetching available subtitles...")
    available_subtitles = get_available_subtitles(url)

    # If no subtitles available
    if not available_subtitles:
        warning("No subtitles found for this video. Continuing without subtitle options.")
        return {
            "write_subtitles": False,
            "write_auto_subs": False,
            "sub_langs": None,
            "sub_format": "srt",
            "embed_subs": False,
            "convert_subs": None,
        }

    # Prepare subtitle choices for display with language names
    subtitle_choices = [
        ("none", "No subtitles", "Continue without subtitles")
    ]

    subtitle_map = {}

    for index, sub in enumerate(available_subtitles):
        key = f"subtitle_{index}"
        lang_code = sub['lang']
        lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
        type_label = "auto" if sub['is_auto'] else "manual"
        formats_str = ', '.join(sorted(sub['formats']))
        display = f"{lang_code} ({lang_name}) [{type_label}] [{formats_str}]"

        subtitle_choices.append(
            (key, display, "")
        )

        subtitle_map[key] = sub

    # Let user select a subtitle
    selected_key = prompt_choice(
        title="Select Subtitle Track",
        options=subtitle_choices,
        default_index=1 if len(subtitle_choices) > 1 else 0
    )

    # Handle no subtitles or invalid choice
    if not selected_key or selected_key == "none" or selected_key not in subtitle_map:
        return {
            "write_subtitles": False,
            "write_auto_subs": False,
            "sub_langs": None,
            "sub_format": "srt",
            "embed_subs": False,
            "convert_subs": None,
        }

    # Get selected subtitle info
    selected_sub = subtitle_map[selected_key]

    # Ask user what they want to do with the selected subtitle
    action_choice = prompt_choice(
        title="What would you like to do with this subtitle?",
        options=[
            ("download", "Download Subtitle File", "Save subtitle as a separate file"),
            ("embed", "Embed Subtitles", "Embed subtitles into the video file"),
            ("both", "Download and Embed", "Both download as file and embed in video"),
        ],
        default_index=0
    )

    # Determine subtitle options based on selection
    write_subtitles = action_choice in ("download", "both")
    write_auto_subs = selected_sub['is_auto'] and action_choice in ("download", "both")
    embed_subs = action_choice in ("embed", "both")

    # For format selection, let user choose from available formats
    if selected_sub['formats']:
        # Define recommended players map for helper text
        players_map = {
            "srt": "VLC, MPC-HC, or almost any media player",
            "vtt": "Browser, VLC, or modern media players",
            "ass": "VLC, MPC-HC, or Aegisub (advanced styling support)",
            "lrc": "Music players (lyrics support)",
        }

        format_options = []
        for fmt in selected_sub['formats']:
            rec_player = players_map.get(fmt, "Standard media players")
            format_options.append((fmt, fmt.upper(), f"{fmt} format ({rec_player})"))

        sub_format = prompt_choice(
            title="Select Subtitle Format",
            options=format_options,
            default_index=0
        )
    else:
        sub_format = "srt"  # fallback

    # Language is determined by the selected subtitle
    sub_langs = selected_sub['lang']

    return {
        "write_subtitles": write_subtitles,
        "write_auto_subs": write_auto_subs,
        "sub_langs": sub_langs,
        "sub_format": sub_format or "srt",
        "embed_subs": embed_subs,
        "convert_subs": None,
    }


def run_download_interactive(
    url: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    download_path: Optional[str] = None,
    dl_type: Optional[str] = None,
    quality: Optional[str] = None,
    write_subtitles: bool = False,
    write_auto_subs: bool = False,
    sub_langs: Optional[str] = None,
    sub_format: str = "srt",
    embed_subs: bool = False,
    convert_subs: Optional[str] = None,
    is_playlist_mode: Optional[bool] = None,
) -> int:
    """
    Execute the interactive download workflow with modern UI.

    Supports optional pre-populated parameters from CLI arguments
    (e.g., start_time, end_time, url, download_path, dl_type, quality, is_playlist_mode).
    """
    logger = get_logger("cli")

    init_terminal()
    print_banner(__version__)

    # Check for updates in the background
    updater.notify_update_available()

    # Verify dependencies
    if not check_dependencies():
        logger.error("Missing required dependencies, aborting")
        return 1

    # Step 1: Input URL
    if not url:
        print_step(1, 3, "Enter Media URL")
        url = prompt_input("Paste Video or Playlist URL")

    if not url:
        error("URL cannot be empty.")
        return 1

    # Step 2: Select destination
    if not download_path:
        print_step(2, 3, "Select Destination Folder")
        download_path = choose_download_folder()
        if download_path is None:
            return 1
    else:
        try:
            os.makedirs(download_path, exist_ok=True)
        except Exception as e:
            error(f"Could not create download folder: {e}")
            return 1

    # Step 3: Fetch Metadata & Configure Download
    print_step(3, 3, "Analyzing Media & Selecting Quality")
    wait("Fetching media metadata...")

    noplaylist = False if (is_playlist_mode is True) or (is_pure_playlist_url(url) and is_playlist_mode is not False) else True
    info_dict = get_media_info(url, noplaylist=noplaylist)

    if not info_dict:
        error("Failed to retrieve media information. Please check the URL or your internet connection.")
        return 1

    # Determine whether to run the playlist workflow or single video workflow
    is_pl_workflow = False
    if is_playlist_mode is True:
        is_pl_workflow = True
    elif is_playlist_mode is False:
        is_pl_workflow = False
    elif is_pure_playlist_url(url) or (is_playlist(info_dict) and not has_video_id(url)):
        is_pl_workflow = True
    elif is_video_in_playlist_url(url):
        # Video is part of a playlist / mix
        if not (dl_type and quality):
            scope_choice = prompt_choice(
                title="Video in Playlist/Mix Detected",
                options=[
                    ("single", "Download Single Video (Recommended)", "Download only this selected video"),
                    ("playlist", "Download Entire Playlist Batch", "Download all videos in the playlist/mix"),
                ],
                default_index=0
            )
            if scope_choice == "playlist":
                is_pl_workflow = True
                pl_info = get_media_info(url, noplaylist=False)
                if pl_info:
                    info_dict = pl_info
            else:
                is_pl_workflow = False
        else:
            # When format and quality are pre-supplied via CLI without --playlist, default to single video
            is_pl_workflow = False
    else:
        is_pl_workflow = is_playlist(info_dict)

    # -----------------------------------------------------------------------
    # Playlist Workflow
    # -----------------------------------------------------------------------
    if is_pl_workflow:
        entries = get_playlist_entries(info_dict)
        pl_title = info_dict.get("title", "Playlist")
        pl_author = info_dict.get("uploader") or info_dict.get("channel") or "Unknown"
        total_videos = len(entries) if entries else info_dict.get("playlist_count", "Multiple")

        print_card(
            title="Playlist Detected",
            items=[
                ("Title", pl_title),
                ("Channel", pl_author),
                ("Total Items", f"{total_videos} videos"),
                ("Type", "Playlist"),
                ("Destination", download_path),
            ],
            icon=Symbols.PLAYLIST
        )

        dl_type_choice = dl_type or prompt_choice(
            title="Select Playlist Download Type",
            options=[
                ("video", "Video Playlist (MP4)", "Download all videos in playlist"),
                ("audio", "Audio Playlist (MP3)", "Extract all songs/audio to MP3"),
            ],
            default_index=0
        )

        # Default transcript (subtitle) options
        transcripts = {
            "write_subtitles": write_subtitles,
            "write_auto_subs": write_auto_subs,
            "sub_langs": sub_langs,
            "sub_format": sub_format,
            "embed_subs": embed_subs,
            "convert_subs": convert_subs,
        }

        if dl_type_choice == "video":
            quality_choice = quality or prompt_choice(
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

            # Transcript (subtitle) options - prompt for video playlist unless provided via CLI args
            if not (write_subtitles or write_auto_subs or embed_subs or sub_langs) and not (dl_type and quality):
                transcripts = prompt_transcript_options(url)

            print()
            info(f"Starting Video Playlist Download: {Colors.BOLD}{pl_title}{Colors.RESET}")
            res = download_playlist(
                url=url,
                download_path=download_path,
                media_type="video",
                quality=quality_choice,
                start_time=start_time,
                end_time=end_time,
                **transcripts
            )

        else:
            audio_quality = quality or prompt_choice(
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
                quality=audio_quality,
                start_time=start_time,
                end_time=end_time,
                **transcripts
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

        chosen_format = dl_type or prompt_choice(
            title="Choose Download Format",
            options=[
                ("video", "Video (MP4)", "High quality video with audio merged"),
                ("audio", "Audio Only (MP3)", "Extract high quality MP3 audio"),
            ],
            default_index=0
        )

        # Section clipping (start_time / end_time)
        clip_start = start_time
        clip_end = end_time

        # If not supplied on command line, prompt interactively if user wants a clip
        if clip_start is None and clip_end is None:
            want_clip = prompt_confirm("Download a specific section only (clip)?", default=False)
            if want_clip:
                clip_start_raw = prompt_input("Start time [e.g. 01:30, 90, or 00:00]", default="00:00")
                clip_end_raw = prompt_input("End time [e.g. 03:45, 225, or leave empty for end]", default="")
                clip_start = clip_start_raw.strip() if clip_start_raw.strip() else None
                clip_end = clip_end_raw.strip() if clip_end_raw.strip() else None

                # Validate timestamps
                try:
                    s_sec = parse_time_str(clip_start)
                    e_sec = parse_time_str(clip_end)
                    if s_sec is not None and e_sec is not None and e_sec <= s_sec:
                        warning("End time must be greater than start time. Defaulting to full download.")
                        clip_start = None
                        clip_end = None
                except ValueError as e:
                    warning(f"{e} Defaulting to full download.")
                    clip_start = None
                    clip_end = None

        # Default transcript (subtitle) options
        transcripts = {
            "write_subtitles": write_subtitles,
            "write_auto_subs": write_auto_subs,
            "sub_langs": sub_langs,
            "sub_format": sub_format,
            "embed_subs": embed_subs,
            "convert_subs": convert_subs,
        }

        if chosen_format == "video":
            if quality:
                selected_height = int(quality) if quality.isdigit() else 0
            else:
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

            # Transcript (subtitle) options - prompt for video downloads unless provided via CLI args
            if not (write_subtitles or write_auto_subs or embed_subs or sub_langs) and not (dl_type and quality):
                transcripts = prompt_transcript_options(url)

            section_note = f" [section: {clip_start or '00:00'} - {clip_end or 'end'}]" if (clip_start or clip_end) else ""
            print()
            info(f"Downloading Video: {Colors.BOLD}{title}{Colors.RESET} ({selected_height}p){section_note}...")
            success_status = download_video(
                url=url,
                download_path=download_path,
                height=selected_height,
                start_time=clip_start,
                end_time=clip_end,
                **transcripts
            )

        else:
            # Audio format selection
            if quality:
                selected_bitrate = quality
            else:
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

            section_note = f" [section: {clip_start or '00:00'} - {clip_end or 'end'}]" if (clip_start or clip_end) else ""
            print()
            info(f"Downloading Audio: {Colors.BOLD}{title}{Colors.RESET}{section_note}...")
            success_status = download_audio(
                url=url,
                download_path=download_path,
                quality=selected_bitrate,
                start_time=clip_start,
                end_time=clip_end,
                **transcripts
            )

        if success_status:
            summary_items = [
                ("Title", title),
                ("Format", chosen_format.upper()),
                ("Saved Folder", download_path),
            ]
            if clip_start or clip_end:
                summary_items.append(("Section", f"{clip_start or '00:00'} to {clip_end or 'end'}"))

            print_summary(
                title="Download Successful",
                items=summary_items
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
        description="A beautiful and fast Video, Audio & Playlist Downloader CLI for YouTube, TikTok & Social Media."
    )

    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="Optional URL of the video, audio, or playlist to download"
    )

    parser.add_argument(
        "-s", "--start-time",
        dest="start_time",
        type=str,
        default=None,
        help="Start time for partial video/audio download (e.g. '01:30', '90', '00:01:30')"
    )

    parser.add_argument(
        "-e", "--end-time",
        dest="end_time",
        type=str,
        default=None,
        help="End time for partial video/audio download (e.g. '04:15', '255', '00:04:15')"
    )

    parser.add_argument(
        "-o", "-d", "--output-dir", "--dir",
        dest="output_dir",
        type=str,
        default=None,
        help="Destination directory for downloads"
    )

    parser.add_argument(
        "-f", "--format",
        dest="format",
        choices=["video", "audio"],
        default=None,
        help="Download format ('video' or 'audio')"
    )

    parser.add_argument(
        "-q", "--quality",
        dest="quality",
        type=str,
        default=None,
        help="Video resolution (e.g., 1080, 720, best) or Audio bitrate (e.g., 320, 192, 0)"
    )

    # Subtitle options
    parser.add_argument(
        "--write-subs",
        action="store_true",
        help="Write subtitle files alongside the media (also enables auto-generated subs for compatibility)"
    )
    parser.add_argument(
        "--write-auto-subs",
        action="store_true",
        help="Write automatically generated subtitle files (also enables regular subs for compatibility)"
    )
    parser.add_argument(
        "--sub-langs",
        type=str,
        default=None,
        help="Languages of subtitles to download (comma-separated, e.g. 'en,ar')"
    )
    parser.add_argument(
        "--sub-format",
        type=str,
        default="srt",
        help="Subtitle format (e.g., srt, vtt, ass)"
    )
    parser.add_argument(
        "--embed-subs",
        action="store_true",
        help="Embed subtitles in the video (only for mp4, webm, mkv)"
    )
    parser.add_argument(
        "--convert-subs",
        type=str,
        default=None,
        help="Convert subtitles to another format after extraction (e.g., srt)"
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the Desktop GUI interface"
    )

    parser.add_argument(
        "--update",
        action="store_true",
        help="Check for and install updates from GitHub Releases"
    )

    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall Downloadyha and remove all application data"
    )

    parser.add_argument(
        "--repair",
        action="store_true",
        help="Repair and reinstall bundled dependencies (FFmpeg, Deno)"
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


def handle_gui_command() -> None:
    """
    Launch the Downloadyha Desktop GUI.

    1. Checks for a standalone GUI executable (downloadyha-gui) in PATH or app directory.
    2. Falls back to importing the Python GUI module if tkinter is available.
    3. Displays helpful instructions if GUI dependencies are missing in the current environment.
    """
    import shutil
    import subprocess
    from pathlib import Path

    init_terminal()
    logger = get_logger("cli")

    gui_binary_name = "downloadyha-gui.exe" if sys.platform == "win32" else "downloadyha-gui"

    # 1. Look for standalone GUI binary alongside current executable or in PATH
    exe_dir = Path(sys.executable).parent
    sibling_gui = exe_dir / gui_binary_name

    gui_exec_path = None
    if sibling_gui.exists() and os.access(str(sibling_gui), os.X_OK):
        gui_exec_path = str(sibling_gui)
    else:
        found_in_path = shutil.which("downloadyha-gui") or shutil.which("downloadyha-gui.exe")
        if found_in_path:
            gui_exec_path = found_in_path

    if gui_exec_path:
        info(f"Launching Downloadyha Desktop GUI ({gui_exec_path})...")
        try:
            if sys.platform == "win32":
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                subprocess.Popen(
                    [gui_exec_path],
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                    close_fds=True
                )
            else:
                subprocess.Popen(
                    [gui_exec_path],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            return
        except Exception as e:
            logger.warning(f"Failed to launch standalone GUI executable: {e}")

    # 2. Try in-process Python GUI (Modern CustomTkinter GUI first, then Tkinter fallback)
    try:
        from downloadyha_gui.app import main as launch_modern_gui
        launch_modern_gui()
        return
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from .gui import launch_gui
        launch_gui()
        return
    except (ImportError, ModuleNotFoundError) as e:
        logger.warning(f"Failed to launch in-process GUI: {e}")
        c = Colors
        print()
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}╭─ 🖥️  Downloadyha Desktop GUI ──────────────────────────────╮{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}  The standalone CLI binary is lightweight and does not     {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}  bundle Desktop GUI graphical components.                  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}├────────────────────────────────────────────────────────────┤{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}Option 1: Download Standalone GUI App (Recommended){c.RESET}       {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}  Download {c.CYBER_PURPLE}downloadyha-gui-windows.zip{c.RESET} or {c.CYBER_PURPLE}downloadyha-gui-linux.tar.gz{c.RESET} {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}  from GitHub Releases:                                     {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}  {c.UNDERLINE}https://github.com/ahmed-tarek-2004/DownloadYha/releases{c.RESET}   {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}                                                            {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}  {c.BOLD}{c.BRIGHT_CYAN}Option 2: Run via Python / Pip{c.RESET}                            {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}  {c.BRIGHT_GREEN}pip install downloadyha[gui]{c.RESET}                              {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}  {c.BRIGHT_GREEN}downloadyha-gui{c.RESET}                                           {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        if sys.platform != "win32":
            print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}                                                            {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
            print(f"  {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}  {c.MUTED}On Linux: sudo apt install python3-tk{c.RESET}                      {c.BOLD}{c.BRIGHT_WHITE}│{c.RESET}")
        print(f"  {c.BOLD}{c.BRIGHT_WHITE}╰────────────────────────────────────────────────────────────╯{c.RESET}")
        print()
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    setup_logging(log_to_file=True, log_to_console=False)
    logger = get_logger("cli")
    logger.info(f"Downloadyha v{__version__} started")

    try:
        # Command-line subcommands without flags
        if len(sys.argv) > 1:
            arg = sys.argv[1].strip().lower()

            if arg == "gui":
                handle_gui_command()
                return

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
                print_banner(__version__)
                parser = create_parser()
                parser.print_help()
                return

            elif arg in ("--version", "-v"):
                print(f"Downloadyha {__version__}")
                return

        # Parse standard command-line flags and arguments
        parser = create_parser()
        args = parser.parse_args()

        if args.gui:
            handle_gui_command()
            return

        if args.update:
            updater.handle_update_command()
            return

        if args.repair:
            init_terminal()
            info("Attempting to repair Downloadyha dependencies...")
            if repair_dependencies():
                success("Repair completed successfully. All dependencies are installed.")
                sys.exit(0)
            else:
                error("Repair failed. Some dependencies could not be automatically downloaded.")
                sys.exit(1)

        if args.uninstall:
            uninstaller.handle_uninstall_command()
            return

        if args.verify:
            init_terminal()
            info("Verifying system dependencies...")
            if verify_dependencies():
                success("All dependencies are ready and operational.")
                sys.exit(0)
            else:
                warning("Some dependencies are missing. Run 'downloadyha repair' to fix them.")
                sys.exit(1)

        # Interactive flow with optional CLI arguments
        exit_code = run_download_interactive(
            url=args.url,
            start_time=args.start_time,
            end_time=args.end_time,
            download_path=args.output_dir,
            dl_type=args.format,
            quality=args.quality,
            write_subtitles=args.write_subs,
            write_auto_subs=args.write_auto_subs,
            sub_langs=args.sub_langs,
            sub_format=args.sub_format,
            embed_subs=args.embed_subs,
            convert_subs=args.convert_subs,
        )
        sys.exit(exit_code)

    except (KeyboardInterrupt, EOFError):
        logger.info("Session canceled by user (Ctrl+C / EOF)")
        print_interrupted()
        sys.exit(130)


if __name__ == "__main__":
    main()
