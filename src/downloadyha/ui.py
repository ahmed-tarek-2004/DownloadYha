"""
Modern Terminal User Interface module for Downloadyha.

Provides cross-platform ANSI color support, Unicode box art, styled banners,
media information cards, interactive menus, customizable progress bars,
status alerts, and user input helpers.
"""

from __future__ import annotations

import ctypes
import math
import os
import re
import shutil
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union


# ---------------------------------------------------------------------------
# Virtual Terminal & ANSI Support Detection
# ---------------------------------------------------------------------------

_COLOR_ENABLED: Optional[bool] = None


def enable_virtual_terminal() -> bool:
    """
    Enable ANSI virtual terminal processing on Windows and configure UTF-8 output.

    On Windows 10/11, activates ENABLE_VIRTUAL_TERMINAL_PROCESSING using ctypes
    and falls back to os.system('') initialization.

    Returns:
        True if terminal initialization succeeded, False otherwise.
    """
    # Reconfigure streams to UTF-8 if supported to prevent UnicodeEncodeError
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

        # Fallback 1: os.system('') initializes VT mode on Windows 10+
        try:
            os.system("")
        except Exception:
            pass

        # Primary: ctypes SetConsoleMode
        try:
            kernel32 = ctypes.windll.kernel32
            STD_OUTPUT_HANDLE = -11
            STD_ERROR_HANDLE = -12
            ENABLE_PROCESSED_OUTPUT = 0x0001
            ENABLE_WRAP_AT_EOL_OUTPUT = 0x0002
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

            for handle_id in (STD_OUTPUT_HANDLE, STD_ERROR_HANDLE):
                handle = kernel32.GetStdHandle(handle_id)
                if handle and handle != -1:
                    mode = ctypes.c_ulong()
                    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                        new_mode = (
                            mode.value
                            | ENABLE_PROCESSED_OUTPUT
                            | ENABLE_WRAP_AT_EOL_OUTPUT
                            | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                        )
                        kernel32.SetConsoleMode(handle, new_mode)
            return True
        except Exception:
            return False

    return True


# Backward compatibility alias
init_terminal = enable_virtual_terminal


def is_color_supported() -> bool:
    """
    Check if the current terminal environment supports ANSI colors.

    Respects NO_COLOR, FORCE_COLOR, and TTY status.

    Returns:
        True if colors are supported and enabled, False otherwise.
    """
    global _COLOR_ENABLED
    if _COLOR_ENABLED is not None:
        return _COLOR_ENABLED

    # Respect standard NO_COLOR (https://no-color.org)
    if os.environ.get("NO_COLOR", "").strip():
        return False

    # Force color if explicitly requested
    force_color = os.environ.get("FORCE_COLOR", "").strip()
    if force_color in ("1", "true", "yes", "on"):
        return True

    # Dumb terminal check
    if os.environ.get("TERM") == "dumb":
        return False

    # Check if standard output is a TTY
    try:
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    except Exception:
        return False


def set_color_enabled(enabled: bool) -> None:
    """
    Explicitly enable or disable ANSI color rendering.

    Args:
        enabled: Whether colors should be enabled.
    """
    global _COLOR_ENABLED
    _COLOR_ENABLED = bool(enabled)


def get_color_enabled() -> bool:
    """Get the current color enabled status."""
    return is_color_supported()


# ---------------------------------------------------------------------------
# Color Palette & Styles
# ---------------------------------------------------------------------------

class Colors:
    """ANSI color and style definitions with cyber/modern palette."""

    # Control
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    INVERT = "\033[7m"

    # Standard Foreground
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # High Intensity Foreground
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Standard Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Modern Cyber Theme Palette (24-bit TrueColor)
    PRIMARY = "\033[38;2;0;210;255m"       # Electric Cyan
    SECONDARY = "\033[38;2;220;80;255m"     # Neon Magenta
    ACCENT = "\033[38;2;155;81;224m"       # Cyber Purple
    SUCCESS = "\033[38;2;46;204;113m"      # Emerald Green
    WARNING = "\033[38;2;241;196;15m"      # Amber Yellow
    ERROR = "\033[38;2;231;76;60m"         # Crimson Red
    INFO = "\033[38;2;52;152;219m"         # Sky Blue
    MUTED = "\033[38;2;130;130;130m"       # Medium Gray
    DARK_GRAY = "\033[38;2;75;75;75m"      # Dark Gray (Bar background)
    HIGHLIGHT = "\033[38;2;250;250;250m"   # Bright White


class Symbols:
    """Unicode and fallback symbols for rich CLI rendering."""

    CHECK = "✔"
    INFO = "ℹ"
    WARN = "⚠"
    CROSS = "✖"
    WAIT = "⏳"
    DOWNLOAD = "⬇"
    AUDIO = "🎵"
    VIDEO = "🎬"
    FOLDER = "📁"
    PLAYLIST = "📑"
    ROCKET = "🚀"
    SPARKLE = "✨"
    GEAR = "⚙"
    ARROW_RIGHT = "➜"
    DIAMOND = "◆"
    BULLET = "•"
    PLAY = "▶"


# Box Drawing Glyphs
BOX_STYLES: Dict[str, Dict[str, str]] = {
    "rounded": {
        "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
        "h": "─", "v": "│",
        "tj": "┬", "bj": "┴", "lj": "├", "rj": "┤", "cross": "┼"
    },
    "double": {
        "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
        "h": "═", "v": "║",
        "tj": "╦", "bj": "╩", "lj": "╠", "rj": "╣", "cross": "╬"
    },
    "single": {
        "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
        "h": "─", "v": "│",
        "tj": "┬", "bj": "┴", "lj": "├", "rj": "┤", "cross": "┼"
    },
    "heavy": {
        "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
        "h": "━", "v": "┃",
        "tj": "┳", "bj": "┻", "lj": "┣", "rj": "┫", "cross": "╋"
    },
    "ascii": {
        "tl": "+", "tr": "+", "bl": "+", "br": "+",
        "h": "-", "v": "|",
        "tj": "+", "bj": "+", "lj": "+", "rj": "+", "cross": "+"
    },
}

ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


# ---------------------------------------------------------------------------
# String & Formatting Helpers
# ---------------------------------------------------------------------------

def strip_ansi(text: Any) -> str:
    """
    Remove all ANSI escape sequences from a string.

    Args:
        text: Input text containing potential ANSI escape codes.

    Returns:
        Clean plain text without escape sequences.
    """
    if text is None:
        return ""
    return ANSI_ESCAPE_RE.sub("", str(text))


def get_visible_length(text: Any) -> int:
    """
    Calculate the printable visual width of a string, ignoring ANSI codes.

    Args:
        text: Input text.

    Returns:
        Visible character length.
    """
    return len(strip_ansi(text))


def colorize(text: Any, *styles: str) -> str:
    """
    Wrap text in ANSI styles if color support is enabled.

    Args:
        text: The text to format.
        *styles: One or more ANSI code strings from Colors.

    Returns:
        Styled text ending with RESET if color is enabled, otherwise plain text.
    """
    str_text = str(text) if text is not None else ""
    if not is_color_supported() or not styles:
        return strip_ansi(str_text)
    return f"{''.join(styles)}{str_text}{Colors.RESET}"


def rgb_fg(r: int, g: int, b: int) -> str:
    """Generate 24-bit RGB foreground ANSI sequence."""
    return f"\033[38;2;{int(r)};{int(g)};{int(b)}m"


def rgb_bg(r: int, g: int, b: int) -> str:
    """Generate 24-bit RGB background ANSI sequence."""
    return f"\033[48;2;{int(r)};{int(g)};{int(b)}m"


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert a hex color string (e.g. '#00D2FF' or '00D2FF') to RGB tuple."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join(c * 2 for c in hex_code)
    return (
        int(hex_code[0:2], 16),
        int(hex_code[2:4], 16),
        int(hex_code[4:6], 16)
    )


def gradient_text(
    text: str,
    start_rgb: Tuple[int, int, int] = (0, 210, 255),
    end_rgb: Tuple[int, int, int] = (220, 80, 255)
) -> str:
    """
    Render text with a smooth color gradient from start_rgb to end_rgb.

    Args:
        text: The string to colorize.
        start_rgb: RGB tuple for the starting color.
        end_rgb: RGB tuple for the ending color.

    Returns:
        Gradient-styled ANSI string.
    """
    if not is_color_supported():
        return strip_ansi(text)

    clean = str(text)
    total = max(len(clean), 1)
    result: List[str] = []

    for i, char in enumerate(clean):
        t = i / max(total - 1, 1)
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
        result.append(f"{rgb_fg(r, g, b)}{char}")

    return "".join(result) + Colors.RESET


def get_terminal_width(
    default: int = 80,
    min_width: int = 40,
    max_width: int = 90
) -> int:
    """
    Get terminal column width clamped within safe readability limits.

    Args:
        default: Fallback width if detection fails.
        min_width: Minimum width bound.
        max_width: Maximum width bound.

    Returns:
        Clamped terminal width in columns.
    """
    try:
        cols = shutil.get_terminal_size(fallback=(default, 24)).columns
        return max(min_width, min(cols - 2, max_width))
    except Exception:
        return default


def wrap_text(text: str, max_width: int) -> List[str]:
    """
    Wrap text to fit within a given visual width, respecting words.

    Args:
        text: Input string.
        max_width: Maximum visible width per line.

    Returns:
        List of wrapped lines.
    """
    if not text:
        return [""]

    lines: List[str] = []
    paragraphs = text.split("\n")

    for paragraph in paragraphs:
        if not paragraph:
            lines.append("")
            continue

        words = paragraph.split(" ")
        current_line: List[str] = []
        current_len = 0

        for word in words:
            word_vis_len = get_visible_length(word)
            added_len = word_vis_len + (1 if current_line else 0)

            if current_len + added_len <= max_width:
                current_line.append(word)
                current_len += added_len
            else:
                if current_line:
                    lines.append(" ".join(current_line))

                # Handle exceptionally long single words
                while get_visible_length(word) > max_width:
                    chunk = word[:max_width]
                    lines.append(chunk)
                    word = word[max_width:]

                current_line = [word] if word else []
                current_len = get_visible_length(word) if word else 0

        if current_line:
            lines.append(" ".join(current_line))

    return lines if lines else [""]


def truncate_text(text: str, max_width: int, suffix: str = "...") -> str:
    """
    Truncate text to max_width appending suffix if needed.

    Args:
        text: Input text.
        max_width: Maximum allowed visible length.
        suffix: Suffix to append when truncated.

    Returns:
        Truncated string.
    """
    if get_visible_length(text) <= max_width:
        return text

    target_len = max_width - get_visible_length(suffix)
    if target_len <= 0:
        return suffix[:max_width]

    return text[:target_len] + suffix


def format_bytes(num_bytes: Union[int, float, None]) -> str:
    """
    Format a byte count into a human-readable string (KB, MB, GB).

    Args:
        num_bytes: Size in bytes.

    Returns:
        Formatted size string (e.g., '45.2 MB').
    """
    if num_bytes is None or num_bytes < 0:
        return "N/A"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    unit_index = 0

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def format_speed(bytes_per_sec: Union[int, float, None]) -> str:
    """
    Format bytes per second into human-readable download speed.

    Args:
        bytes_per_sec: Speed in bytes per second.

    Returns:
        Formatted speed string (e.g., '12.5 MB/s').
    """
    if bytes_per_sec is None or bytes_per_sec <= 0:
        return "--.- MB/s"
    return f"{format_bytes(bytes_per_sec)}/s"


def format_duration(seconds: Union[int, float, str, None]) -> str:
    """
    Format seconds into HH:MM:SS or MM:SS format.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted duration string (e.g. '01:05', '01:01:05', or 'Unknown').
    """
    if seconds is None:
        return "Unknown"

    if isinstance(seconds, str):
        if ":" in seconds:
            return seconds
        try:
            sec_val = float(seconds)
        except ValueError:
            return seconds
    else:
        sec_val = float(seconds)

    if sec_val <= 0:
        return "Unknown"

    total_secs = int(sec_val)
    hours = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    rem_secs = total_secs % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{rem_secs:02d}"
    else:
        return f"{minutes:02d}:{rem_secs:02d}"


def format_number(num: Union[int, float, str, None]) -> str:
    """
    Format a count into formatted number with thousands separators (e.g. 1,450,200).

    Args:
        num: Input number.

    Returns:
        Formatted number string.
    """
    if num is None:
        return "N/A"
    try:
        val = int(num)
        return f"{val:,}"
    except (ValueError, TypeError):
        return str(num)


# ---------------------------------------------------------------------------
# ASCII Banner & Visual Dividers
# ---------------------------------------------------------------------------

BANNER_ART = [
    r"    ____                      __                 ____  __          ",
    r"   / __ \____ _      ______  / /___  ____ _____ / / / / /_  ____ _ ",
    r"  / / / / __ \ \ /\ / / __ \/ / __ \/ __ `/ __  / /_/ / __ \/ __ `/",
    r" / /_/ / /_/ /\ V  V / / / / / /_/ / /_/ / /_/ / __  / / / / /_/ / ",
    r"/_____/\____/  \_/\_/_/ /_/_/\____/\__,_/\__,_/_/ /_/_/ /_/\__,_/  ",
]


def get_banner_text(
    version: str = "1.0.0",
    author: str = "Ahmed Tarek",
    subtitle: str = "Modern YouTube Downloader",
    width: Optional[int] = None
) -> str:
    """
    Build the styled ASCII banner with gradient coloring and box frame.

    Args:
        version: Application version string.
        author: Author credit name.
        subtitle: Application subtitle.
        width: Total width of the framed banner.

    Returns:
        Framed banner string.
    """
    box_width = max(width or get_terminal_width(default=74, max_width=76), 72)
    inner_width = box_width - 2
    b = BOX_STYLES["rounded"]
    border_color = Colors.PRIMARY

    lines: List[str] = []

    # Top border
    lines.append(f"{border_color}{b['tl']}{b['h'] * inner_width}{b['tr']}{Colors.RESET}")

    # ASCII Art Logo lines with gradient
    c_start = (0, 210, 255)    # Cyan
    c_end = (220, 80, 255)     # Magenta

    for art_line in BANNER_ART:
        pad_l = (inner_width - len(art_line)) // 2
        pad_r = inner_width - len(art_line) - pad_l
        colored_art = gradient_text(art_line, c_start, c_end)
        lines.append(
            f"{border_color}{b['v']}{Colors.RESET}"
            f"{' ' * pad_l}{colored_art}{' ' * pad_r}"
            f"{border_color}{b['v']}{Colors.RESET}"
        )

    # Empty separator row
    lines.append(
        f"{border_color}{b['v']}{' ' * inner_width}{b['v']}{Colors.RESET}"
    )

    # Subtitle with badge
    sub_text = f"⚡ {subtitle}  •  v{version} ⚡"
    sub_colored = gradient_text(sub_text, (0, 255, 200), (255, 120, 220))
    pad_l = (inner_width - get_visible_length(sub_text)) // 2
    pad_r = inner_width - get_visible_length(sub_text) - pad_l
    lines.append(
        f"{border_color}{b['v']}{Colors.RESET}"
        f"{' ' * pad_l}{sub_colored}{' ' * pad_r}"
        f"{border_color}{b['v']}{Colors.RESET}"
    )

    # Author credit
    author_text = f"Crafted by {author}"
    author_colored = colorize(author_text, Colors.DIM, Colors.MUTED)
    pad_l = (inner_width - get_visible_length(author_text)) // 2
    pad_r = inner_width - get_visible_length(author_text) - pad_l
    lines.append(
        f"{border_color}{b['v']}{Colors.RESET}"
        f"{' ' * pad_l}{author_colored}{' ' * pad_r}"
        f"{border_color}{b['v']}{Colors.RESET}"
    )

    # Bottom border
    lines.append(f"{border_color}{b['bl']}{b['h'] * inner_width}{b['br']}{Colors.RESET}")

    return "\n".join(lines)


def print_banner(
    version: str = "1.0.0",
    author: str = "Ahmed Tarek",
    subtitle: str = "Modern YouTube Downloader",
    width: Optional[int] = None
) -> None:
    """Print the styled banner to standard output."""
    print()
    print(get_banner_text(version=version, author=author, subtitle=subtitle, width=width))
    print()


def print_divider(
    title: Optional[str] = None,
    char: str = "─",
    width: Optional[int] = None,
    color: Optional[str] = None
) -> None:
    """
    Print a decorative horizontal divider with an optional title.

    Args:
        title: Optional section title.
        char: Divider character.
        width: Line width.
        color: ANSI color for the divider line.
    """
    w = width or get_terminal_width()
    div_color = color or Colors.PRIMARY

    if not title:
        line = char * w
        print(colorize(line, div_color))
        return

    title_clean = f" {title.strip()} "
    vis_len = get_visible_length(title_clean)
    remaining = max(0, w - vis_len - 4)

    left_dashes = char * 3
    right_dashes = char * remaining

    print(
        f"{colorize(left_dashes, div_color)}"
        f"{colorize(title_clean, Colors.BOLD, Colors.HIGHLIGHT)}"
        f"{colorize(right_dashes, div_color)}"
    )


def print_step(
    step_num: int,
    total_steps: int,
    title: str,
    description: Optional[str] = None,
    width: Optional[int] = None
) -> None:
    """
    Print a visual step indicator header.

    Args:
        step_num: Current step number (e.g. 1).
        total_steps: Total number of steps (e.g. 3).
        title: Step title.
        description: Optional step description.
        width: Output width.
    """
    w = width or get_terminal_width()
    b = BOX_STYLES["rounded"]
    border_color = Colors.PRIMARY

    step_tag = f" Step [{step_num}/{total_steps}] "
    step_colored = colorize(step_tag, Colors.BOLD, Colors.ACCENT)
    title_colored = colorize(f" {title} ", Colors.BOLD, Colors.HIGHLIGHT)

    header_vis_len = get_visible_length(step_tag) + get_visible_length(title) + 2
    right_dashes = max(0, w - header_vis_len - 3)

    print()
    print(
        f"{colorize(b['tl'] + b['h'], border_color)}"
        f"{step_colored}"
        f"{title_colored}"
        f"{colorize(b['h'] * right_dashes + b['tr'], border_color)}"
    )

    if description:
        inner_w = w - 4
        desc_lines = wrap_text(description, inner_w)
        for d_line in desc_lines:
            pad = inner_w - get_visible_length(d_line)
            print(
                f"{colorize(b['v'], border_color)} "
                f"{colorize(d_line, Colors.MUTED)}"
                f"{' ' * max(0, pad)} "
                f"{colorize(b['v'], border_color)}"
            )
        print(f"{colorize(b['bl'] + b['h'] * (w - 2) + b['br'], border_color)}")
    else:
        print(f"{colorize(b['bl'] + b['h'] * (w - 2) + b['br'], border_color)}")


# ---------------------------------------------------------------------------
# Cards & Info Panels
# ---------------------------------------------------------------------------

def render_card(
    title: Optional[str] = None,
    lines: Optional[List[str]] = None,
    items: Optional[Union[Dict[str, Any], Sequence[Tuple[str, Any]]]] = None,
    icon: Optional[str] = None,
    style: str = "rounded",
    width: Optional[int] = None,
    border_color: Optional[str] = None,
    title_color: Optional[str] = None
) -> str:
    """
    Render a generic boxed card with border styling, custom lines, or key-value items.

    Args:
        title: Optional title at top border.
        lines: Optional list of string lines inside the card.
        items: Optional list/dict of (key, value) pairs.
        icon: Optional icon prefix for title.
        style: Box style key from BOX_STYLES ('rounded', 'double', 'single', etc.).
        width: Card width.
        border_color: ANSI color for border.
        title_color: ANSI color for title.

    Returns:
        Formatted card string.
    """
    b = BOX_STYLES.get(style, BOX_STYLES["rounded"])
    b_color = border_color or Colors.PRIMARY
    t_color = title_color or Colors.HIGHLIGHT
    box_w = max(width or get_terminal_width(default=74, max_width=78), 44)
    inner_w = box_w - 4

    out: List[str] = []

    # Format header title with icon
    if title:
        header_title = f"{icon} {title.strip()}" if icon else title.strip()
        title_str = f" {header_title} "
        title_vis = get_visible_length(title_str)
        dashes = max(0, box_w - 3 - title_vis)
        top = (
            f"{colorize(b['tl'] + b['h'], b_color)}"
            f"{colorize(title_str, Colors.BOLD, t_color)}"
            f"{colorize(b['h'] * dashes + b['tr'], b_color)}"
        )
    else:
        top = colorize(b["tl"] + b["h"] * (box_w - 2) + b["tr"], b_color)
    out.append(top)

    def add_row(label: str, val_text: str, val_color: str = Colors.HIGHLIGHT) -> None:
        lbl_vis = get_visible_length(label)
        val_max_w = max(10, inner_w - lbl_vis - 1)
        wrapped_vals = wrap_text(val_text, val_max_w)

        for i, val_line in enumerate(wrapped_vals):
            if i == 0:
                line_content = f"{label} {colorize(val_line, val_color)}"
            else:
                line_content = f"{' ' * lbl_vis} {colorize(val_line, val_color)}"
            pad = inner_w - get_visible_length(line_content)
            out.append(
                f"{colorize(b['v'], b_color)} "
                f"{line_content}"
                f"{' ' * max(0, pad)} "
                f"{colorize(b['v'], b_color)}"
            )

    # Key-value items mode
    if items:
        item_list = list(items.items()) if isinstance(items, dict) else list(items)
        bullet = colorize(f"{Symbols.BULLET}", Colors.ACCENT)
        for k, v in item_list:
            lbl = f"{bullet} {colorize(f'{k}:', Colors.ACCENT, Colors.BOLD)}"
            add_row(lbl, str(v), Colors.HIGHLIGHT)

    # Lines mode
    if lines:
        for line in lines:
            wrapped = wrap_text(line, inner_w)
            for w_line in wrapped:
                pad = inner_w - get_visible_length(w_line)
                out.append(
                    f"{colorize(b['v'], b_color)} "
                    f"{w_line}"
                    f"{' ' * max(0, pad)} "
                    f"{colorize(b['v'], b_color)}"
                )

    # Bottom border
    bot = colorize(b["bl"] + b["h"] * (box_w - 2) + b["br"], b_color)
    out.append(bot)

    return "\n".join(out)


def print_card(
    title: Optional[str] = None,
    lines: Optional[List[str]] = None,
    items: Optional[Union[Dict[str, Any], Sequence[Tuple[str, Any]]]] = None,
    icon: Optional[str] = None,
    style: str = "rounded",
    width: Optional[int] = None,
    border_color: Optional[str] = None,
    title_color: Optional[str] = None
) -> None:
    """Print a generic boxed card."""
    print()
    print(render_card(
        title=title,
        lines=lines,
        items=items,
        icon=icon,
        style=style,
        width=width,
        border_color=border_color,
        title_color=title_color
    ))
    print()


def render_media_card(
    title: str,
    uploader: Optional[str] = None,
    duration: Optional[Union[int, float, str]] = None,
    views: Optional[Union[int, str]] = None,
    qualities: Optional[List[Union[int, str]]] = None,
    destination: Optional[str] = None,
    playlist_count: Optional[int] = None,
    is_playlist: bool = False,
    extra_info: Optional[Dict[str, Any]] = None,
    width: Optional[int] = None,
    style: str = "rounded"
) -> str:
    """
    Render a high-aesthetic boxed card for YouTube video/audio/playlist metadata.

    Args:
        title: Media title.
        uploader: Channel/artist name.
        duration: Video duration (seconds or string).
        views: View count.
        qualities: List of available video heights (e.g. [1080, 720, 480]).
        destination: Download target folder path.
        playlist_count: Total videos in playlist (if applicable).
        is_playlist: True if this item is a playlist.
        extra_info: Additional key-value metadata to display.
        width: Box width.
        style: Border style.

    Returns:
        Formatted card string.
    """
    b = BOX_STYLES.get(style, BOX_STYLES["rounded"])
    b_color = Colors.PRIMARY
    box_w = max(width or get_terminal_width(default=74, max_width=78), 50)
    inner_w = box_w - 4

    out: List[str] = []

    # Card header
    header_type = f"{Symbols.PLAYLIST} PLAYLIST INFORMATION" if is_playlist else f"{Symbols.VIDEO} MEDIA INFORMATION"
    header_title = f" {header_type} "
    hdr_vis = get_visible_length(header_title)
    dashes = max(0, box_w - 3 - hdr_vis)
    top_line = (
        f"{colorize(b['tl'] + b['h'], b_color)}"
        f"{colorize(header_title, Colors.BOLD, Colors.HIGHLIGHT)}"
        f"{colorize(b['h'] * dashes + b['tr'], b_color)}"
    )
    out.append(top_line)

    def add_row(label: str, val_text: str, val_color: str = Colors.HIGHLIGHT) -> None:
        lbl_vis = get_visible_length(label)
        val_max_w = max(10, inner_w - lbl_vis - 1)
        wrapped_vals = wrap_text(val_text, val_max_w)

        for i, val_line in enumerate(wrapped_vals):
            if i == 0:
                line_content = f"{label} {colorize(val_line, val_color)}"
            else:
                line_content = f"{' ' * lbl_vis} {colorize(val_line, val_color)}"
            pad = inner_w - get_visible_length(line_content)
            out.append(
                f"{colorize(b['v'], b_color)} "
                f"{line_content}"
                f"{' ' * max(0, pad)} "
                f"{colorize(b['v'], b_color)}"
            )

    # Add rows
    bullet = colorize(f"{Symbols.BULLET}", Colors.ACCENT)
    add_row(f"{bullet} {colorize('Title:', Colors.ACCENT, Colors.BOLD)}", title, Colors.BOLD + Colors.HIGHLIGHT)

    if uploader:
        add_row(f"{bullet} {colorize('Channel:', Colors.ACCENT, Colors.BOLD)}", uploader, Colors.PRIMARY)

    if is_playlist or playlist_count is not None:
        count_str = f"{playlist_count} items" if playlist_count else "Yes"
        add_row(f"{bullet} {colorize('Playlist:', Colors.ACCENT, Colors.BOLD)}", count_str, Colors.SECONDARY)

    if duration is not None and not is_playlist:
        dur_str = format_duration(duration)
        add_row(f"{bullet} {colorize('Duration:', Colors.ACCENT, Colors.BOLD)}", dur_str, Colors.WARNING)

    if views is not None and not is_playlist:
        v_str = f"{format_number(views)} views"
        add_row(f"{bullet} {colorize('Views:', Colors.ACCENT, Colors.BOLD)}", v_str, Colors.MUTED)

    if qualities:
        q_formatted = ", ".join(f"{q}p" if str(q).isdigit() else str(q) for q in qualities)
        add_row(f"{bullet} {colorize('Qualities:', Colors.ACCENT, Colors.BOLD)}", q_formatted, Colors.SUCCESS)

    if destination:
        add_row(f"{bullet} {colorize('Save to:', Colors.ACCENT, Colors.BOLD)}", destination, Colors.WARNING)

    if extra_info:
        for k, v in extra_info.items():
            add_row(f"{bullet} {colorize(f'{k}:', Colors.ACCENT, Colors.BOLD)}", str(v), Colors.MUTED)

    # Bottom border
    bot_line = colorize(b["bl"] + b["h"] * (box_w - 2) + b["br"], b_color)
    out.append(bot_line)

    return "\n".join(out)


def print_media_card(
    title: str,
    uploader: Optional[str] = None,
    duration: Optional[Union[int, float, str]] = None,
    views: Optional[Union[int, str]] = None,
    qualities: Optional[List[Union[int, str]]] = None,
    destination: Optional[str] = None,
    playlist_count: Optional[int] = None,
    is_playlist: bool = False,
    extra_info: Optional[Dict[str, Any]] = None,
    width: Optional[int] = None,
    style: str = "rounded"
) -> None:
    """Print the styled media metadata card."""
    print()
    print(render_media_card(
        title=title,
        uploader=uploader,
        duration=duration,
        views=views,
        qualities=qualities,
        destination=destination,
        playlist_count=playlist_count,
        is_playlist=is_playlist,
        extra_info=extra_info,
        width=width,
        style=style
    ))
    print()


def render_summary(
    title: str,
    items: Union[Dict[str, Any], Sequence[Tuple[str, Any]]],
    border_style: str = "rounded",
    width: Optional[int] = None
) -> str:
    """
    Render a key-value summary box.

    Args:
        title: Summary box title.
        items: Dictionary or sequence of (key, value) tuples.
        border_style: Box style.
        width: Box width.

    Returns:
        Formatted summary box string.
    """
    b = BOX_STYLES.get(border_style, BOX_STYLES["rounded"])
    b_color = Colors.PRIMARY
    box_w = max(width or get_terminal_width(default=70, max_width=74), 48)
    inner_w = box_w - 4

    out: List[str] = []

    # Title line
    title_text = f" 📋 {title.strip()} "
    hdr_vis = get_visible_length(title_text)
    dashes = max(0, box_w - 3 - hdr_vis)
    top_line = (
        f"{colorize(b['tl'] + b['h'], b_color)}"
        f"{colorize(title_text, Colors.BOLD, Colors.HIGHLIGHT)}"
        f"{colorize(b['h'] * dashes + b['tr'], b_color)}"
    )
    out.append(top_line)

    # Convert items to list of tuples
    item_list: List[Tuple[str, Any]] = (
        list(items.items()) if isinstance(items, dict) else list(items)
    )

    if item_list:
        max_key_len = max(get_visible_length(str(k)) for k, _ in item_list) + 2

        for k, v in item_list:
            k_str = str(k)
            v_str = str(v)
            key_col = f"{k_str}:".ljust(max_key_len)
            key_formatted = colorize(f"  {key_col}", Colors.ACCENT, Colors.BOLD)
            val_max_w = max(10, inner_w - get_visible_length(key_formatted) - 1)
            wrapped_vals = wrap_text(v_str, val_max_w)

            for idx, val_line in enumerate(wrapped_vals):
                if idx == 0:
                    content = f"{key_formatted} {colorize(val_line, Colors.HIGHLIGHT)}"
                else:
                    content = f"{' ' * get_visible_length(key_formatted)} {colorize(val_line, Colors.HIGHLIGHT)}"
                pad = inner_w - get_visible_length(content)
                out.append(
                    f"{colorize(b['v'], b_color)} "
                    f"{content}"
                    f"{' ' * max(0, pad)} "
                    f"{colorize(b['v'], b_color)}"
                )

    bot_line = colorize(b["bl"] + b["h"] * (box_w - 2) + b["br"], b_color)
    out.append(bot_line)
    return "\n".join(out)


def print_summary(
    title: str,
    items: Union[Dict[str, Any], Sequence[Tuple[str, Any]]],
    border_style: str = "rounded",
    width: Optional[int] = None
) -> None:
    """Print a key-value summary box."""
    print()
    print(render_summary(title=title, items=items, border_style=border_style, width=width))
    print()


# ---------------------------------------------------------------------------
# Interactive & Styled Menus
# ---------------------------------------------------------------------------

def render_menu(
    title: str,
    options: Union[
        Dict[str, str],
        Sequence[Tuple[str, str]],
        Sequence[Tuple[str, str, str]],
        Sequence[str]
    ],
    default: Optional[str] = None,
    width: Optional[int] = None,
    subtitle: Optional[str] = None
) -> str:
    """
    Render a styled boxed menu with badges and descriptions.

    Args:
        title: Menu title.
        options: Choices as dict, list of tuples (key, label) or (key, label, desc), or list of strings.
        default: Optional default key.
        width: Box width.
        subtitle: Optional subtitle under header.

    Returns:
        Formatted menu string.
    """
    b = BOX_STYLES["rounded"]
    b_color = Colors.PRIMARY
    box_w = max(width or get_terminal_width(default=68, max_width=72), 48)
    inner_w = box_w - 4

    out: List[str] = []

    # Title header
    header_str = f" {title.strip()} "
    hdr_vis = get_visible_length(header_str)
    dashes = max(0, box_w - 3 - hdr_vis)
    top_line = (
        f"{colorize(b['tl'] + b['h'], b_color)}"
        f"{colorize(header_str, Colors.BOLD, Colors.HIGHLIGHT)}"
        f"{colorize(b['h'] * dashes + b['tr'], b_color)}"
    )
    out.append(top_line)

    if subtitle:
        sub_lines = wrap_text(subtitle, inner_w - 2)
        for s_line in sub_lines:
            content = f" {colorize(s_line, Colors.MUTED)}"
            pad = inner_w - get_visible_length(content)
            out.append(
                f"{colorize(b['v'], b_color)} "
                f"{content}"
                f"{' ' * max(0, pad)} "
                f"{colorize(b['v'], b_color)}"
            )
        # Separator line
        out.append(
            f"{colorize(b['lj'] + b['h'] * (box_w - 2) + b['rj'], b_color)}"
        )

    # Normalize option entries to list of (key, label, desc)
    norm_options: List[Tuple[str, str, str]] = []
    if isinstance(options, dict):
        for k, v in options.items():
            norm_options.append((str(k), str(v), ""))
    elif isinstance(options, (list, tuple)):
        for idx, opt in enumerate(options, start=1):
            if isinstance(opt, tuple):
                if len(opt) == 2:
                    norm_options.append((str(opt[0]), str(opt[1]), ""))
                elif len(opt) >= 3:
                    norm_options.append((str(opt[0]), str(opt[1]), str(opt[2])))
            else:
                norm_options.append((str(idx), str(opt), ""))

    for key, label, desc in norm_options:
        badge_text = f"[{key}]"
        is_default = (default is not None and str(key) == str(default))
        if is_default:
            badge_colored = colorize(badge_text, Colors.BOLD, Colors.SUCCESS)
        else:
            badge_colored = colorize(badge_text, Colors.BOLD, Colors.SECONDARY)

        line_str = f"  {badge_colored} {colorize(label, Colors.BOLD, Colors.HIGHLIGHT)}"
        if desc:
            line_str += f" {colorize(f'({desc})', Colors.MUTED)}"
        if is_default:
            line_str += f" {colorize('(default)', Colors.SUCCESS, Colors.DIM)}"

        pad = inner_w - get_visible_length(line_str)
        out.append(
            f"{colorize(b['v'], b_color)} "
            f"{line_str}"
            f"{' ' * max(0, pad)} "
            f"{colorize(b['v'], b_color)}"
        )

    # Bottom border
    bot_line = colorize(b["bl"] + b["h"] * (box_w - 2) + b["br"], b_color)
    out.append(bot_line)

    return "\n".join(out)


def print_menu(
    title: str,
    options: Union[
        Dict[str, str],
        Sequence[Tuple[str, str]],
        Sequence[Tuple[str, str, str]],
        Sequence[str]
    ],
    default: Optional[str] = None,
    width: Optional[int] = None,
    subtitle: Optional[str] = None
) -> None:
    """Print the styled menu."""
    print()
    print(render_menu(title=title, options=options, default=default, width=width, subtitle=subtitle))


# ---------------------------------------------------------------------------
# Progress Bar & yt-dlp Integration
# ---------------------------------------------------------------------------

def render_progress_bar(
    percent: float,
    width: int = 24,
    speed: Optional[str] = None,
    eta: Optional[str] = None,
    downloaded: Optional[str] = None,
    total: Optional[str] = None,
    prefix: str = "",
    status: str = "downloading"
) -> str:
    """
    Render a modern aesthetic progress bar string with speed, ETA, and size metrics.

    Args:
        percent: Completion percentage (0.0 - 100.0).
        width: Width of the progress bar block in characters.
        speed: Download speed string (e.g. '12.5 MB/s').
        eta: Estimated time remaining string (e.g. '00:15').
        downloaded: Formatted downloaded bytes (e.g. '45.2 MB').
        total: Formatted total bytes (e.g. '90.4 MB').
        prefix: Optional prefix text (e.g. '[Video 1/5]').
        status: Download status ('downloading', 'finished', 'processing').

    Returns:
        Formatted ANSI progress bar string.
    """
    pct = max(0.0, min(100.0, float(percent)))
    bar_width = max(10, width)
    filled_len = int(bar_width * (pct / 100.0))
    empty_len = bar_width - filled_len

    # Custom smooth blocks
    fill_bar = colorize("█" * filled_len, Colors.PRIMARY)
    empty_bar = colorize("░" * empty_len, Colors.DARK_GRAY)
    bar_bracket = f"{colorize('[', Colors.PRIMARY)}{fill_bar}{empty_bar}{colorize(']', Colors.PRIMARY)}"

    pct_str = colorize(f"{pct:5.1f}%", Colors.BOLD, Colors.HIGHLIGHT)

    tokens: List[str] = [bar_bracket, pct_str]

    if speed:
        tokens.append(colorize(speed, Colors.WARNING))

    if eta:
        tokens.append(colorize(f"ETA {eta}", Colors.PRIMARY))

    if downloaded and total:
        tokens.append(colorize(f"{downloaded}/{total}", Colors.MUTED))
    elif downloaded:
        tokens.append(colorize(downloaded, Colors.MUTED))

    info_str = f" {colorize('|', Colors.MUTED)} ".join(tokens[1:])
    combined = f"{tokens[0]} {info_str}"

    if prefix:
        combined = f"{colorize(prefix, Colors.BOLD, Colors.SECONDARY)} {combined}"

    return combined


# Backward compatibility alias
format_progress_bar = render_progress_bar


def print_progress(
    percent: float,
    width: int = 24,
    speed: Optional[str] = None,
    eta: Optional[str] = None,
    downloaded: Optional[str] = None,
    total: Optional[str] = None,
    prefix: str = "",
    status: str = "downloading"
) -> None:
    """
    Print an in-place updating progress bar to standard output.
    """
    bar_str = render_progress_bar(
        percent=percent,
        width=width,
        speed=speed,
        eta=eta,
        downloaded=downloaded,
        total=total,
        prefix=prefix,
        status=status
    )
    # Carriage return without newline for smooth progress updates
    sys.stdout.write(f"\r{bar_str}\033[K")
    sys.stdout.flush()


def clear_progress_line() -> None:
    """Clear the current interactive progress line."""
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


class DownloadProgressBar:
    """
    Stateful progress handler compatible with yt-dlp progress hooks.

    Supports single downloads and multi-video playlist tracking with
    pretty visual headers and metrics.
    """

    def __init__(
        self,
        title: Optional[str] = None,
        is_playlist: bool = False,
        playlist_index: Optional[int] = None,
        playlist_count: Optional[int] = None,
        bar_width: int = 22
    ) -> None:
        self.title = title
        self.is_playlist = is_playlist
        self.playlist_index = playlist_index
        self.playlist_count = playlist_count
        self.bar_width = bar_width
        self.last_update_time = 0.0
        self._printed_header = False

    def get_prefix(self) -> str:
        """Construct the playlist / item prefix tag."""
        if self.is_playlist and self.playlist_index and self.playlist_count:
            return f"[{self.playlist_index}/{self.playlist_count}]"
        return f"{Symbols.DOWNLOAD}"

    def __call__(self, data: Dict[str, Any]) -> None:
        """yt-dlp hook callback."""
        status = data.get("status")

        if status == "downloading":
            # Print video title header once per item
            if not self._printed_header:
                vid_title = (
                    data.get("info_dict", {}).get("title")
                    or self.title
                    or data.get("filename", "")
                )
                if vid_title:
                    vid_title_clean = truncate_text(vid_title, 60)
                    if self.is_playlist and self.playlist_index and self.playlist_count:
                        print_download(
                            f"[Video {self.playlist_index}/{self.playlist_count}] "
                            f"{colorize(vid_title_clean, Colors.BOLD, Colors.HIGHLIGHT)}"
                        )
                    else:
                        print_download(
                            f"Downloading: {colorize(vid_title_clean, Colors.BOLD, Colors.HIGHLIGHT)}"
                        )
                self._printed_header = True

            # Calculate progress percentage
            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate", 0)

            if total and total > 0:
                percent = (downloaded / total) * 100.0
            else:
                raw_pct = data.get("_percent_str", "0.0%").strip().rstrip("%")
                try:
                    percent = float(strip_ansi(raw_pct))
                except ValueError:
                    percent = 0.0

            # Download speed
            speed_val = data.get("speed")
            if speed_val:
                speed_str = format_speed(speed_val)
            else:
                raw_speed = data.get("_speed_str", "").strip()
                speed_str = strip_ansi(raw_speed) if raw_speed else None

            # ETA
            eta_val = data.get("eta")
            if eta_val is not None:
                eta_str = f"{int(eta_val)//60:02d}:{int(eta_val)%60:02d}"
            else:
                raw_eta = data.get("_eta_str", "").strip()
                eta_str = strip_ansi(raw_eta) if raw_eta else None

            # Formatted sizes
            dl_str = format_bytes(downloaded) if downloaded else None
            tot_str = format_bytes(total) if total else None

            # Rate limit rendering to avoid flickering (max 20 fps)
            now = time.time()
            if now - self.last_update_time >= 0.05 or percent >= 100.0:
                self.last_update_time = now
                print_progress(
                    percent=percent,
                    width=self.bar_width,
                    speed=speed_str,
                    eta=eta_str,
                    downloaded=dl_str,
                    total=tot_str,
                    prefix=self.get_prefix()
                )

        elif status == "finished":
            clear_progress_line()
            print_wait("Processing media & merging streams...")


_global_progress_handler = DownloadProgressBar()


def render_progress(
    data: Dict[str, Any],
    prefix: str = "",
    playlist_index: Optional[int] = None,
    playlist_total: Optional[int] = None
) -> None:
    """
    Direct progress rendering function for yt-dlp hooks.

    Args:
        data: Progress dictionary from yt-dlp.
        prefix: Optional prefix string.
        playlist_index: Current item index in playlist.
        playlist_total: Total items in playlist.
    """
    global _global_progress_handler
    if playlist_index is not None or playlist_total is not None:
        handler = DownloadProgressBar(
            is_playlist=True,
            playlist_index=playlist_index,
            playlist_count=playlist_total
        )
        handler(data)
    else:
        _global_progress_handler(data)


def create_yt_dlp_progress_hook(
    title: Optional[str] = None,
    is_playlist: bool = False,
    playlist_index: Optional[int] = None,
    playlist_count: Optional[int] = None
) -> Callable[[Dict[str, Any]], None]:
    """
    Factory function for a yt-dlp compatible progress hook.

    Args:
        title: Optional video title.
        is_playlist: Whether the download belongs to a playlist.
        playlist_index: 1-based index in playlist.
        playlist_count: Total playlist items count.

    Returns:
        Callable hook for yt-dlp `progress_hooks`.
    """
    return DownloadProgressBar(
        title=title,
        is_playlist=is_playlist,
        playlist_index=playlist_index,
        playlist_count=playlist_count
    )


# ---------------------------------------------------------------------------
# Status Messages & Alerts
# ---------------------------------------------------------------------------

def _print_status_message(
    badge_text: str,
    badge_symbol: str,
    badge_color: str,
    message: str,
    details: Optional[str] = None
) -> None:
    """Internal helper to print standardized status alert messages."""
    badge = f"{badge_symbol} [{badge_text}]"
    formatted_badge = colorize(badge, Colors.BOLD, badge_color)
    msg_str = str(message)

    if details:
        print(f"{formatted_badge} {msg_str}")
        print(f"  {colorize(Symbols.ARROW_RIGHT, Colors.MUTED)} {colorize(details, Colors.MUTED)}")
    else:
        print(f"{formatted_badge} {msg_str}")


def print_success(message: str, title: str = "SUCCESS", details: Optional[str] = None) -> None:
    """Print a success message in emerald green."""
    _print_status_message(title, Symbols.CHECK, Colors.SUCCESS, message, details)


def print_info(message: str, title: str = "INFO", details: Optional[str] = None) -> None:
    """Print an informational message in sky blue."""
    _print_status_message(title, Symbols.INFO, Colors.INFO, message, details)


def print_warning(message: str, title: str = "WARNING", details: Optional[str] = None) -> None:
    """Print a warning message in amber yellow."""
    _print_status_message(title, Symbols.WARN, Colors.WARNING, message, details)


def print_error(message: str, title: str = "ERROR", details: Optional[str] = None) -> None:
    """Print an error message in crimson red."""
    _print_status_message(title, Symbols.CROSS, Colors.ERROR, message, details)


def print_wait(message: str, title: str = "WAIT", details: Optional[str] = None) -> None:
    """Print a waiting/processing indicator message."""
    _print_status_message(title, Symbols.WAIT, Colors.SECONDARY, message, details)


def print_download(message: str, details: Optional[str] = None) -> None:
    """Print a download operation status message."""
    _print_status_message("DOWNLOAD", Symbols.DOWNLOAD, Colors.PRIMARY, message, details)


def print_audio(message: str, details: Optional[str] = None) -> None:
    """Print an audio processing status message."""
    _print_status_message("AUDIO", Symbols.AUDIO, Colors.ACCENT, message, details)


def print_video(message: str, details: Optional[str] = None) -> None:
    """Print a video processing status message."""
    _print_status_message("VIDEO", Symbols.VIDEO, Colors.PRIMARY, message, details)


def print_folder(message: str, details: Optional[str] = None) -> None:
    """Print a folder/storage path status message."""
    _print_status_message("PATH", Symbols.FOLDER, Colors.WARNING, message, details)


# Backward compatibility aliases
success = print_success
info = print_info
warning = print_warning
error = print_error
wait = print_wait


def print_alert(
    message: str,
    alert_type: str = "info",
    title: Optional[str] = None,
    width: Optional[int] = None
) -> None:
    """
    Print a boxed alert callout panel.

    Args:
        message: Alert body text.
        alert_type: 'success', 'info', 'warning', or 'error'.
        title: Optional custom alert title.
        width: Box width.
    """
    type_map = {
        "success": (Symbols.CHECK, "SUCCESS", Colors.SUCCESS),
        "info": (Symbols.INFO, "INFORMATION", Colors.INFO),
        "warning": (Symbols.WARN, "WARNING", Colors.WARNING),
        "error": (Symbols.CROSS, "ERROR", Colors.ERROR),
    }

    sym, def_title, color = type_map.get(
        alert_type.lower(),
        (Symbols.INFO, "NOTICE", Colors.INFO)
    )

    box_title = f"{sym} {title or def_title}"
    b = BOX_STYLES["rounded"]
    box_w = max(width or get_terminal_width(default=68, max_width=72), 44)
    inner_w = box_w - 4

    hdr_str = f" {box_title} "
    hdr_vis = get_visible_length(hdr_str)
    dashes = max(0, box_w - 3 - hdr_vis)

    print()
    print(
        f"{colorize(b['tl'] + b['h'], color)}"
        f"{colorize(hdr_str, Colors.BOLD, color)}"
        f"{colorize(b['h'] * dashes + b['tr'], color)}"
    )

    for line in wrap_text(message, inner_w):
        pad = inner_w - get_visible_length(line)
        print(
            f"{colorize(b['v'], color)} "
            f"{colorize(line, Colors.HIGHLIGHT)}"
            f"{' ' * max(0, pad)} "
            f"{colorize(b['v'], color)}"
        )

    print(colorize(b["bl"] + b["h"] * (box_w - 2) + b["br"], color))
    print()


# ---------------------------------------------------------------------------
# User Input Helpers
# ---------------------------------------------------------------------------

def prompt_input(
    label: str,
    default: Optional[str] = None,
    validate_fn: Optional[Callable[[str], bool]] = None,
    error_msg: Optional[str] = None,
    allow_empty: bool = False
) -> str:
    """
    Display a styled two-line prompt with optional default value and validation.

    Example layout:
    ╭─ Enter download folder [default: C:\\Users\\...\\Downloads]
    ╰─>

    Args:
        label: Prompt description text.
        default: Optional fallback default value.
        validate_fn: Optional validation predicate returning True if valid.
        error_msg: Error message displayed on validation failure.
        allow_empty: Whether an empty string is acceptable when no default exists.

    Returns:
        User entered string or default.
    """
    b = BOX_STYLES["rounded"]
    p_color = Colors.PRIMARY

    while True:
        # Prompt Header Line
        if default is not None:
            default_badge = colorize(f"[default: {default}]", Colors.MUTED)
            prompt_header = f"{colorize(b['tl'] + b['h'], p_color)} {colorize(label, Colors.BOLD, Colors.HIGHLIGHT)} {default_badge}"
        else:
            prompt_header = f"{colorize(b['tl'] + b['h'], p_color)} {colorize(label, Colors.BOLD, Colors.HIGHLIGHT)}"

        print()
        print(prompt_header)
        prompt_arrow = f"{colorize(b['bl'] + b['h'] + Symbols.ARROW_RIGHT, p_color)} "

        try:
            val = input(prompt_arrow).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            raise

        # Strip surrounding quotes often pasted from file explorers
        val = val.strip('"\'')

        if not val and default is not None:
            return default

        if not val and not allow_empty:
            print_warning("Input cannot be empty. Please enter a value.")
            continue

        if validate_fn and not validate_fn(val):
            err = error_msg or "Invalid input. Please try again."
            print_error(err)
            continue

        return val


def prompt_choice(
    title: str,
    options: Union[
        Dict[str, str],
        Sequence[Tuple[str, str]],
        Sequence[Tuple[str, str, str]],
        Sequence[str]
    ],
    default: Optional[str] = None,
    default_index: Optional[int] = None,
    allow_quit: bool = False,
    width: Optional[int] = None
) -> Optional[str]:
    """
    Display a styled menu and prompt the user until a valid choice is made.

    Args:
        title: Menu title.
        options: Choices dictionary, list of tuples, or list of strings.
        default: Default choice key.
        default_index: Optional 0-based default option index.
        allow_quit: Whether to add a quit option [q].
        width: Menu width.

    Returns:
        The selected key string, or None if user quits.
    """
    # Normalize options to dict of {key: label} and preserve index mapping
    valid_keys: List[str] = []
    display_options: List[Tuple[str, str, str]] = []
    index_to_key: Dict[str, str] = {}

    if isinstance(options, dict):
        for idx, (k, v) in enumerate(options.items(), start=1):
            valid_keys.append(str(k))
            display_options.append((str(k), str(v), ""))
            index_to_key[str(idx)] = str(k)
    elif isinstance(options, (list, tuple)):
        for idx, opt in enumerate(options, start=1):
            if isinstance(opt, tuple):
                key = str(opt[0])
                label = str(opt[1])
                desc = str(opt[2]) if len(opt) > 2 else ""
                valid_keys.append(key)
                display_options.append((str(idx), f"{label}", desc))
                index_to_key[str(idx)] = key
            else:
                key = str(idx)
                label = str(opt)
                valid_keys.append(key)
                display_options.append((key, label, ""))
                index_to_key[key] = key

    # Determine default choice
    resolved_default = default
    if resolved_default is None and default_index is not None and 0 <= default_index < len(valid_keys):
        resolved_default = valid_keys[default_index]

    # Render menu
    print_menu(
        title=title,
        options=display_options,
        default=str(default_index + 1) if default_index is not None else (resolved_default if resolved_default in index_to_key else None),
        width=width
    )

    range_max = len(display_options)
    prompt_label = f"Select an option [1-{range_max}]" if range_max > 1 else "Select an option"
    default_input_val = str(default_index + 1) if default_index is not None else resolved_default

    while True:
        choice = prompt_input(
            label=prompt_label,
            default=default_input_val,
            allow_empty=False
        ).strip().lower()

        if choice == "q" and allow_quit:
            return None

        # Check numerical 1-based index match
        if choice in index_to_key:
            return index_to_key[choice]

        # Check direct key match
        for k in valid_keys:
            if choice == k.lower():
                return k

        valid_hints = f"1 to {range_max}" if range_max > 1 else "1"
        print_warning(f"Invalid selection '{choice}'. Please choose {valid_hints}.")


def prompt_confirm(message: str, default: bool = True) -> bool:
    """
    Prompt user for a yes/no confirmation with styled prompt.

    Args:
        message: Question string to prompt.
        default: Default answer if Enter is pressed (True for Yes, False for No).

    Returns:
        True if user confirmed, False otherwise.
    """
    b = BOX_STYLES["rounded"]
    p_color = Colors.PRIMARY
    suffix = "[Y/n]" if default else "[y/N]"

    header = f"{colorize(b['tl'] + b['h'], p_color)} {colorize(message, Colors.BOLD, Colors.HIGHLIGHT)} {colorize(suffix, Colors.MUTED)}"
    print()
    print(header)
    prompt_arrow = f"{colorize(b['bl'] + b['h'] + Symbols.ARROW_RIGHT, p_color)} "

    while True:
        try:
            val = input(prompt_arrow).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return False

        if not val:
            return default

        if val in ("y", "yes"):
            return True
        if val in ("n", "no"):
            return False

        print_warning("Please enter 'y' for yes or 'n' for no.")


# ---------------------------------------------------------------------------
# Module Auto-initialization
# ---------------------------------------------------------------------------

# Automatically initialize virtual terminal support on module import
enable_virtual_terminal()
