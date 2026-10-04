"""
Subtitle utilities for Downloadyha.
Provides functions to extract and handle subtitle information using yt-dlp Python API.
"""

import yt_dlp
from typing import List, Dict, Any


def get_available_subtitles(url: str) -> List[Dict[str, Any]]:
    """
    Extract available subtitle information from a video URL using yt-dlp.

    Args:
        url (str): The video URL to check for subtitles.

    Returns:
        list: A list of dictionaries, each containing:
              - 'display': A string for display in the selection menu (e.g., "en (manual) [srt, vtt]")
              - 'lang': The language code (e.g., 'en')
              - 'is_auto': Boolean indicating if it's an automatic caption (True) or manual subtitle (False)
              - 'formats': List of available subtitle formats (e.g., ['srt', 'vtt'])
        Returns an empty list if no subtitles are found or an error occurs.
    """
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info without downloading the video
            info = ydl.extract_info(url, download=False)

            # Get manual subtitles and automatic captions
            manual_subs = info.get('subtitles', {})
            auto_subs = info.get('automatic_captions', {})

            # We'll collect all unique languages from both manual and auto
            all_langs = set(manual_subs.keys()) | set(auto_subs.keys())
            subtitle_options = []

            for lang in sorted(all_langs):
                # Get formats for manual subtitles (if available)
                manual_formats = []
                if lang in manual_subs:
                    manual_formats = list({sub.get('ext') for sub in manual_subs[lang] if sub.get('ext')})

                # Get formats for automatic captions (if available)
                auto_formats = []
                if lang in auto_subs:
                    auto_formats = list({sub.get('ext') for sub in auto_subs[lang] if sub.get('ext')})

                # Create option for manual subtitles if available
                if manual_formats:
                    formats_str = ', '.join(sorted(manual_formats))
                    display = f"{lang} (manual) [{formats_str}]"
                    subtitle_options.append({
                        'display': display,
                        'lang': lang,
                        'is_auto': False,
                        'formats': manual_formats
                    })

                # Create option for automatic captions if available
                if auto_formats:
                    formats_str = ', '.join(sorted(auto_formats))
                    display = f"{lang} (auto) [{formats_str}]"
                    subtitle_options.append({
                        'display': display,
                        'lang': lang,
                        'is_auto': True,
                        'formats': auto_formats
                    })

            return subtitle_options

    except Exception as e:
        # In a real application, you might want to log this error
        print(f"Error extracting subtitle information: {e}")
        return []


def get_subtitle_selection_prompt(subtitles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Prompt the user to select a subtitle from the available options (CLI version).
    This function is designed to be used in the CLI and returns the selected subtitle info.

    Args:
        subtitles (list): List of subtitle dictionaries from get_available_subtitles.

    Returns:
        dict: The selected subtitle dictionary, or None if no selection was made.
    """
    # This function is intended to be used in CLI contexts where we can use questionary or similar.
    # For now, we'll return a simple implementation that just returns the first subtitle.
    # In a real integration, we would use the CLI's prompting system.
    if not subtitles:
        return None
    # For demonstration, we return the first subtitle. In practice, this would be replaced
    # with an actual prompt using the application's CLI prompting utilities.
    return subtitles[0]