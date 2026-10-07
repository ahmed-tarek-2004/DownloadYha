"""
Subtitle utilities for Downloadyha.
Provides functions to extract and handle subtitle information using yt-dlp Python API.
"""

import yt_dlp
from typing import List, Dict, Any

# Language code to name mapping
LANGUAGE_NAMES: Dict[str, str] = {
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
    'aa': 'Afar', 'ab': 'Abkhazian', 'ak': 'Akan', 'sq': 'Albanian',
    'am': 'Amharic', 'an': 'Aragonese', 'hy': 'Armenian', 'as': 'Assamese',
    'av': 'Avaric', 'ae': 'Avestan', 'ay': 'Aymara', 'az': 'Azerbaijani',
    'bm': 'Bambara', 'ba': 'Bashkir', 'eu': 'Basque', 'be': 'Belarusian',
    'bh': 'Bihari', 'bi': 'Bislama', 'bs': 'Bosnian', 'br': 'Breton',
    'my': 'Burmese', 'ca': 'Catalan', 'ch': 'Chamorro', 'ce': 'Chechen',
    'ny': 'Chichewa', 'cv': 'Chuvash', 'kw': 'Cornish', 'co': 'Corsican',
    'cr': 'Cree', 'dv': 'Divehi', 'dz': 'Dzongkha', 'eo': 'Esperanto',
    'ee': 'Ewe', 'fo': 'Faroese', 'fj': 'Fijian', 'ff': 'Fulah',
    'gd': 'Gaelic', 'gl': 'Galician', 'lg': 'Ganda', 'ka': 'Georgian',
    'ki': 'Gikuyu', 'kl': 'Greenlandic', 'gn': 'Guarani', 'ht': 'Haitian',
    'ha': 'Hausa', 'hz': 'Herero', 'ho': 'Hiri Motu', 'is': 'Icelandic',
    'io': 'Ido', 'ig': 'Igbo', 'ia': 'Interlingua', 'ie': 'Interlingue',
    'iu': 'Inuktitut', 'ik': 'Inupiaq', 'ga': 'Irish', 'jv': 'Javanese',
    'kr': 'Kanuri', 'ks': 'Kashmiri', 'kk': 'Kazakh', 'km': 'Khmer',
    'rw': 'Kinyarwanda', 'ky': 'Kyrgyz', 'kv': 'Komi', 'kg': 'Kongo',
    'ku': 'Kurdish', 'kj': 'Kwanyama', 'lo': 'Lao', 'la': 'Latin',
    'li': 'Limburgan', 'ln': 'Lingala', 'lu': 'Luba-Katanga', 'lb': 'Luxembourgish',
    'mk': 'Macedonian', 'mg': 'Malagasy', 'mt': 'Maltese', 'gv': 'Manx',
    'mi': 'Maori', 'mh': 'Marshallese', 'mn': 'Mongolian', 'na': 'Nauru',
    'nv': 'Navajo', 'nd': 'North Ndebele', 'ng': 'Ndonga', 'ne': 'Nepali',
    'nb': 'Norwegian Bokmål', 'nn': 'Norwegian Nynorsk', 'ii': 'Nuosu',
    'nr': 'South Ndebele', 'oc': 'Occitan', 'oj': 'Ojibwa',
    'cu': 'Old Church Slavonic', 'om': 'Oromo', 'or': 'Oriya', 'os': 'Ossetian',
    'pi': 'Pali', 'ps': 'Pashto', 'qu': 'Quechua', 'rm': 'Romansh',
    'rn': 'Rundi', 'sm': 'Samoan', 'sg': 'Sango', 'sa': 'Sanskrit',
    'sc': 'Sardinian', 'sn': 'Shona', 'sd': 'Sindhi', 'si': 'Sinhala',
    'so': 'Somali', 'st': 'Southern Sotho', 'su': 'Sundanese', 'ss': 'Swati',
    'ty': 'Tahitian', 'tg': 'Tajik', 'tt': 'Tatar', 'bo': 'Tibetan',
    'ti': 'Tigrinya', 'to': 'Tonga', 'ts': 'Tsonga', 'tn': 'Tswana',
    'tk': 'Turkmen', 'tw': 'Twi', 'ug': 'Uighur', 'uk': 'Ukrainian',
    'uz': 'Uzbek', 've': 'Venda', 'vi': 'Vietnamese', 'vo': 'Volapük',
    'wa': 'Walloon', 'cy': 'Welsh', 'wo': 'Wolof', 'fy': 'Western Frisian',
    'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba', 'za': 'Zhuang', 'zu': 'Zulu'
}


def get_language_name(code: str) -> str:
    """
    Get the full English language name for a given language code.

    Args:
        code: Language code (e.g. 'en', 'ar', 'zh-Hans', 'en-US', 'all').

    Returns:
        The language name, or uppercase code if unknown.
    """
    if not code:
        return ""
    if code.lower() == "all":
        return "All Available"
    if code in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[code]
    # Check lowercased code
    if code.lower() in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[code.lower()]
    # Check base code if code has region/variant (e.g., en-US, pt-BR)
    base_code = code.replace("_", "-").split("-")[0].lower()
    if base_code in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[base_code]
    return code.upper()


def format_language_option(code: str) -> str:
    """
    Format a language code with its full name/description (e.g., 'en (English)').

    Args:
        code: Language code (e.g., 'en', 'ar', 'all').

    Returns:
        Formatted string like 'en (English)' or 'all (All Available)'.
    """
    name = get_language_name(code)
    if not name or name == code.upper():
        return f"{code} ({code.upper()})"
    return f"{code} ({name})"


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
                lang_name = get_language_name(lang)
                if manual_formats:
                    formats_str = ', '.join(sorted(manual_formats))
                    display = f"{lang} ({lang_name}) (manual) [{formats_str}]"
                    subtitle_options.append({
                        'display': display,
                        'lang': lang,
                        'lang_name': lang_name,
                        'is_auto': False,
                        'formats': manual_formats
                    })

                # Create option for automatic captions if available
                if auto_formats:
                    formats_str = ', '.join(sorted(auto_formats))
                    display = f"{lang} ({lang_name}) (auto) [{formats_str}]"
                    subtitle_options.append({
                        'display': display,
                        'lang': lang,
                        'lang_name': lang_name,
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