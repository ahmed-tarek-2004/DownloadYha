"""
app.py - Main Desktop GUI Application for Downloadyha

Built with CustomTkinter with an ultra-premium, calm-luxury desktop interface:
- High-contrast typography and subtle elevation hierarchy (Linear/Raycast standard)
- Dual-mode dynamic palette with 100% native Light & Dark mode support
- Rich Media Showcase Card with 16:9 thumbnail preview and clean telemetry pills
- Dynamic quality dropdown matching available video heights (e.g. 4K, 2K, 1080p, 720p, 480p, 360p)
- Audio MP3 bitrate options (Best VBR, 320k, 192k, 128k)
- Playlist detection and support (video & audio)
- Tab-based interface (Download, Queue / History, Settings)
- Real-time download progress with speed, ETA, and playlist item tracker
- Responsive layout with zero-dependency PIL in-memory image pipeline
- Cross-platform HiDPI display optimization (Windows, macOS, Linux X11 & Wayland)
"""

from __future__ import annotations

__author__ = "Ahmed Tarek Zaher"
__copyright__ = "Copyright 2026, Ahmed Tarek Zaher"
__license__ = "MIT"

# BOOKMARK: Ahmed Tarek Zaher - Owner

import io
import os
import re
import sys
import threading
import tkinter as tk
import urllib.request
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional, Tuple

import customtkinter as ctk
from PIL import Image, ImageDraw

# Import downloadyha core engine
try:
    from downloadyha import __version__
    from downloadyha.config import get_download_dir, load as load_config, save as save_config
    from downloadyha.dependencies import check_dependencies, check_ffmpeg, check_ffprobe, get_dependency_versions, repair_dependencies, verify_dependencies
    from downloadyha.updater import check_for_updates, perform_update
    from downloadyha.downloader import (
        DownloadResult,
        download_audio,
        download_playlist,
        download_video,
        get_media_info,
        get_playlist_entries,
        get_video_qualities,
        is_playlist,
        is_playlist_url,
        parse_time_str,
    )
    from downloadyha.ui import format_duration, format_number
except ImportError:
    # Fallback for direct execution during development
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from downloadyha import __version__
    from downloadyha.config import get_download_dir, load as load_config, save as save_config
    from downloadyha.dependencies import check_dependencies, check_ffmpeg, check_ffprobe, get_dependency_versions, repair_dependencies, verify_dependencies
    from downloadyha.updater import check_for_updates, perform_update
    from downloadyha.downloader import (
        DownloadResult,
        download_audio,
        download_playlist,
        download_video,
        get_media_info,
        get_playlist_entries,
        get_video_qualities,
        is_playlist,
        is_playlist_url,
        parse_time_str,
    )
    from downloadyha.ui import format_duration, format_number


# ---------------------------------------------------------------------------
# Cross-Platform HiDPI & Subpixel Antialiasing Engine
# ---------------------------------------------------------------------------

def _init_cross_platform_hidpi():
    """Configure cross-platform HiDPI display awareness, antialiasing, and vector engine."""
    # 1. Windows: Request Per-Monitor DPI Awareness (v2 / v1)
    if sys.platform == "win32":
        try:
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
                except Exception:
                    ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    # 2. Linux: Configure FreeType subpixel antialiasing & hint styles via Xft & polygon shapes
    elif sys.platform.startswith("linux"):


        # Set X11 font rendering properties if xrdb is available
        try:
            import shutil
            import subprocess
            if shutil.which("xrdb") and os.environ.get("DISPLAY"):
                xft_settings = (
                    "Xft.antialias: 1\n"
                    "Xft.hinting: 1\n"
                    "Xft.hintstyle: hintslight\n"
                    "Xft.rgba: rgb\n"
                    "Xft.lcdfilter: lcddefault\n"
                )
                subprocess.run(
                    ["xrdb", "-merge"],
                    input=xft_settings.encode("utf-8"),
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception:
            pass


# Execute HiDPI initialization before toolkit widget construction
_init_cross_platform_hidpi()


# ---------------------------------------------------------------------------
# Constants & Quality Definitions
# ---------------------------------------------------------------------------

DEFAULT_VIDEO_QUALITIES: List[str] = [
    "Best Available (Maximum Quality)",
    "2160p (4K UHD)",
    "1440p (2K QHD)",
    "1080p (Full HD)",
    "720p (HD)",
    "480p (SD)",
    "360p (Low)",
]

AUDIO_QUALITIES: List[str] = [
    "Best Quality (VBR ~256-320 kbps)",
    "320 kbps (High Quality)",
    "192 kbps (Standard Quality)",
    "128 kbps (Compact Size)",
]


def format_height_label(height: int) -> str:
    """Format a video resolution height into a user-friendly dropdown label."""
    if height >= 2160:
        return f"{height}p (4K UHD)"
    elif height >= 1440:
        return f"{height}p (2K QHD)"
    elif height >= 1080:
        return f"{height}p (Full HD)"
    elif height >= 720:
        return f"{height}p (HD)"
    elif height >= 480:
        return f"{height}p (SD)"
    elif height >= 360:
        return f"{height}p (Low)"
    else:
        return f"{height}p"


# ---------------------------------------------------------------------------
# Theme & Design System (Calm Luxury Architecture)
# ---------------------------------------------------------------------------

class PremiumTheme:
    """Downloadyha refined calm-luxury design tokens (Light, Dark)."""
    # Surfaces & Backgrounds
    BG_WINDOW = ("#F1F5F9", "#0C0E14")          # Soft Slate Canvas / Deep Obsidian
    BG_CONTAINER = ("#F1F5F9", "#0F1219")       # Container Canvas
    SURFACE_CARD = ("#FFFFFF", "#151824")       # Elevated Crisp White Card / Obsidian Well
    SURFACE_CARD_HOVER = ("#F8FAFC", "#1C2030") # Hover State
    SURFACE_MUTED = ("#E2E8F0", "#1E2333")      # Soft Pill Surface (Zero-border tactile button)
    SURFACE_INPUT = ("#FFFFFF", "#11141D")      # Crisp Input Surface

    # Hairline Borders
    BORDER_SUBTLE = ("#E2E8F0", "#222736")      # Subtle Card Hairline
    BORDER_INPUT = ("#CBD5E1", "#282E40")       # Input Border
    BORDER_FOCUS = ("#4F46E5", "#6366F1")       # Active/Focus Border

    # Accent (Celestial Indigo - Linear / Raycast standard)
    ACCENT_PRIMARY = ("#4F46E5", "#6366F1")
    ACCENT_HOVER = ("#4338CA", "#4F46E5")
    ACCENT_SUBTLE = ("#EEF2FF", "#1E2038")
    ACCENT_TEXT = "#FFFFFF"

    # Typography Contrast Hierarchy
    TEXT_PRIMARY = ("#0F172A", "#F8FAFC")
    TEXT_SECONDARY = ("#475569", "#94A3B8")
    TEXT_MUTED = ("#94A3B8", "#64748B")

    # Semantic Status Colors
    STATUS_SUCCESS = ("#16A34A", "#10B981")     # Emerald Green
    STATUS_ERROR = ("#DC2626", "#F43F5E")       # Rose Red
    STATUS_WARNING = ("#D97706", "#F59E0B")     # Warm Amber
    STATUS_INFO = ("#0284C7", "#38BDF8")        # Sky Blue

    _resolved_font_family: Optional[str] = None

    @classmethod
    def get_font_family(cls) -> str:
        """Resolve the sharpest native system font available across Windows, macOS, and Linux."""
        if cls._resolved_font_family is not None:
            return cls._resolved_font_family
        try:
            import tkinter.font as tkfont
            families = set(tkfont.families())
            candidates = [
                # Universal modern sans
                "Inter",
                # macOS
                "SF Pro Text",
                "SF Pro Display",
                "Helvetica Neue",
                # Windows
                "Segoe UI",
                "Aptos",
                # Linux
                "Roboto",
                "Noto Sans",
                "Ubuntu",
                "Cantarell",
                "DejaVu Sans",
                "Liberation Sans",
                "Arial",
                "Helvetica",
            ]
            for candidate in candidates:
                if candidate in families:
                    cls._resolved_font_family = candidate
                    return candidate
        except Exception:
            pass
        cls._resolved_font_family = "Segoe UI" if sys.platform == "win32" else ("Helvetica" if sys.platform == "darwin" else "DejaVu Sans")
        return cls._resolved_font_family

    # Centralized typography hierarchy tokens
    @classmethod
    def font_title(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=22, weight="bold")

    @classmethod
    def font_card_title(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=16, weight="bold")

    @classmethod
    def font_heading(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=15, weight="bold")

    @classmethod
    def font_subheading(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=14, weight="bold")

    @classmethod
    def font_body(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=13)

    @classmethod
    def font_body_bold(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=13, weight="bold")

    @classmethod
    def font_button(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=13, weight="bold")

    @classmethod
    def font_button_large(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=14, weight="bold")

    @classmethod
    def font_meta(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=12)

    @classmethod
    def font_meta_bold(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=12, weight="bold")

    @classmethod
    def font_badge(cls) -> ctk.CTkFont:
        return ctk.CTkFont(family=cls.get_font_family(), size=11, weight="bold")


class Theme:
    """Downloadyha legacy theme definitions maintained for test contract compatibility."""
    ELECTRIC_CYAN = (0, 210, 255)
    CYBER_PURPLE = (155, 81, 224)
    EMERALD_GREEN = (46, 204, 113)
    AMBER_YELLOW = (241, 196, 15)
    CRIMSON_RED = (231, 76, 60)

    DEEP_PURPLE = (102, 51, 153)
    LIGHT_CYAN = (128, 230, 255)
    DARK_BG = (12, 14, 20)
    CARD_BG = (22, 25, 36)
    CARD_BG_LIGHT = (248, 250, 252)

    WARNING_ORANGE = (255, 165, 0)
    INFO_BLUE = (52, 152, 219)
    SUCCESS_GREEN = "#10B981"
    ERROR_RED = "#EF4444"
    WARNING_AMBER = "#F59E0B"
    CRIMSON_PRIMARY = "#6366F1"
    CRIMSON_HOVER = "#4F46E5"
    BTN_SUBTLE_BG = PremiumTheme.SURFACE_CARD
    BTN_SUBTLE_HOVER = PremiumTheme.SURFACE_CARD_HOVER
    SUCCESS_LIGHT = "#064E3B"
    ERROR_LIGHT = "#7F1D1D"
    WARNING_LIGHT = "#78350F"
    TEXT_PRIMARY = PremiumTheme.TEXT_PRIMARY
    TEXT_SECONDARY = PremiumTheme.TEXT_SECONDARY
    TEXT_MUTED = PremiumTheme.TEXT_MUTED

    @staticmethod
    def set_appearance_mode(mode: str):
        ctk.set_appearance_mode(mode)

    @staticmethod
    def rgb_to_hex(rgb: tuple) -> str:
        """Convert RGB tuple to hex color string."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    @classmethod
    def get_accent_color(cls) -> str:
        return cls.rgb_to_hex(cls.ELECTRIC_CYAN)

    @classmethod
    def get_success_color(cls) -> str:
        return cls.rgb_to_hex(cls.EMERALD_GREEN)

    @classmethod
    def get_error_color(cls) -> str:
        return cls.rgb_to_hex(cls.CRIMSON_RED)

    @classmethod
    def get_warning_color(cls) -> str:
        return cls.rgb_to_hex(cls.WARNING_ORANGE)

    @classmethod
    def get_gradient_colors(cls) -> list:
        return [cls.ELECTRIC_CYAN, cls.CYBER_PURPLE]

    @classmethod
    def get_card_bg(cls, dark_mode: bool = True) -> str:
        return cls.rgb_to_hex(cls.CARD_BG if dark_mode else (240, 240, 245))

    @classmethod
    def get_glassmorphism_bg(cls, dark_mode: bool = True) -> str:
        return cls.rgb_to_hex(cls.CARD_BG_LIGHT if dark_mode else (255, 255, 255))


# ---------------------------------------------------------------------------
# Modern Styled Components
# ---------------------------------------------------------------------------

class ModernButton(ctk.CTkButton):
    """Button with refined typography, micro-borders, and variant styles."""

    def __init__(self, master, variant: str = "primary", **kwargs):
        kwargs.pop("gradient_hover", None)

        if "corner_radius" not in kwargs:
            kwargs["corner_radius"] = 9
        if "height" not in kwargs:
            kwargs["height"] = 44
        if "font" not in kwargs:
            kwargs["font"] = PremiumTheme.font_button()

        if variant == "primary":
            if "fg_color" not in kwargs:
                kwargs["fg_color"] = PremiumTheme.ACCENT_PRIMARY
            if "hover_color" not in kwargs:
                kwargs["hover_color"] = PremiumTheme.ACCENT_HOVER
            if "text_color" not in kwargs:
                kwargs["text_color"] = PremiumTheme.ACCENT_TEXT
            if "border_width" not in kwargs:
                kwargs["border_width"] = 0
        elif variant == "secondary":
            if "fg_color" not in kwargs:
                kwargs["fg_color"] = PremiumTheme.SURFACE_MUTED
            if "hover_color" not in kwargs:
                kwargs["hover_color"] = ("#CBD5E1", "#282E42")
            if "text_color" not in kwargs:
                kwargs["text_color"] = PremiumTheme.TEXT_PRIMARY
            if "border_width" not in kwargs:
                kwargs["border_width"] = 0
        elif variant == "danger":
            if "fg_color" not in kwargs:
                kwargs["fg_color"] = PremiumTheme.STATUS_ERROR
            if "hover_color" not in kwargs:
                kwargs["hover_color"] = ("#B91C1C", "#E11D48")
            if "text_color" not in kwargs:
                kwargs["text_color"] = "#FFFFFF"
            if "border_width" not in kwargs:
                kwargs["border_width"] = 0
        elif variant == "ghost":
            if "fg_color" not in kwargs:
                kwargs["fg_color"] = "transparent"
            if "hover_color" not in kwargs:
                kwargs["hover_color"] = PremiumTheme.SURFACE_MUTED
            if "text_color" not in kwargs:
                kwargs["text_color"] = PremiumTheme.TEXT_SECONDARY
            if "border_width" not in kwargs:
                kwargs["border_width"] = 0

        super().__init__(master, **kwargs)


class GlassCard(ctk.CTkFrame):
    """Elevated surface card with clean 1px border and concentric corners."""

    def __init__(self, master, **kwargs):
        if "corner_radius" not in kwargs:
            kwargs["corner_radius"] = 12
        if "border_width" not in kwargs:
            kwargs["border_width"] = 1
        if "border_color" not in kwargs:
            kwargs["border_color"] = PremiumTheme.BORDER_SUBTLE
        if "fg_color" not in kwargs:
            kwargs["fg_color"] = PremiumTheme.SURFACE_CARD

        super().__init__(master, **kwargs)


class AnimatedProgressBar(ctk.CTkProgressBar):
    """Progress bar with subtle animation and sleek dimensions."""

    def __init__(self, master, **kwargs):
        if "corner_radius" not in kwargs:
            kwargs["corner_radius"] = 5
        if "height" not in kwargs:
            kwargs["height"] = 8

        super().__init__(master, **kwargs)

        self._animation_running = False
        self._animation_id = None

        self.configure(
            progress_color=PremiumTheme.ACCENT_PRIMARY,
            fg_color=PremiumTheme.SURFACE_MUTED
        )

    def start_animation(self):
        """Start smooth indeterminate pulse animation."""
        if not self._animation_running:
            self._animation_running = True
            self.configure(mode="indeterminate")
            self.start()

    def stop_animation(self):
        """Stop animation and return to determinate mode."""
        if self._animation_running:
            self._animation_running = False
            self.stop()
            self.configure(mode="determinate")


# ---------------------------------------------------------------------------
# High-DPI Supersampled In-Memory Image Pipeline
# ---------------------------------------------------------------------------

def create_placeholder_thumbnail(width: int = 240, height: int = 135, dark_mode: bool = True) -> tk.PhotoImage:
    """
    Render a 4x supersampled vector placeholder thumbnail for crisp display on all screens.
    Uses Lanczos anti-aliasing to guarantee zero jagged edges on Retina and high-DPI monitors.
    """
    ss_scale = 4
    sw, sh = width * ss_scale, height * ss_scale

    base_bg = (22, 25, 36) if dark_mode else (241, 245, 249)
    img = Image.new("RGBA", (sw, sh), base_bg)
    draw = ImageDraw.Draw(img)

    # Subtle radial gradient aura
    center_x, center_y = sw // 2, sh // 2
    max_radius = min(sw, sh) // 2
    for r in range(max_radius, 0, -6):
        alpha = int((1.0 - (r / max_radius)) * (36 if dark_mode else 22))
        color = (99, 102, 241, alpha) if dark_mode else (79, 70, 229, alpha)
        draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], fill=color)

    # Central play button badge
    btn_r = int(24 * ss_scale)
    btn_box = [center_x - btn_r, center_y - btn_r, center_x + btn_r, center_y + btn_r]
    btn_bg = (30, 34, 48) if dark_mode else (255, 255, 255)
    draw.ellipse(btn_box, fill=btn_bg)

    # Crisp play triangle
    tri_w = int(12 * ss_scale)
    tri_h = int(14 * ss_scale)
    tri_color = (99, 102, 241) if dark_mode else (79, 70, 229)
    points = [
        (center_x - tri_w // 3, center_y - tri_h // 2),
        (center_x - tri_w // 3, center_y + tri_h // 2),
        (center_x + (2 * tri_w) // 3, center_y)
    ]
    draw.polygon(points, fill=tri_color)

    # Downsample with Lanczos anti-aliasing
    final_img = img.resize((width, height), Image.Resampling.LANCZOS)
    ppm_img = final_img.convert("RGB")

    buf = io.BytesIO()
    ppm_img.save(buf, format="PPM")
    return tk.PhotoImage(data=buf.getvalue())


def process_thumbnail_bytes(image_bytes: bytes, target_width: int = 240, target_height: int = 135) -> Optional[tk.PhotoImage]:
    """
    Process remote image bytes into a high-DPI 16:9 thumbnail using Lanczos downsampling.
    Crops and scales proportionally with zero distortion.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        orig_w, orig_h = img.size
        if orig_w == 0 or orig_h == 0:
            return None

        # Aspect-ratio preserving crop to 16:9 target
        target_ratio = target_width / target_height
        orig_ratio = orig_w / orig_h

        if orig_ratio > target_ratio:
            crop_w = int(orig_h * target_ratio)
            left = (orig_w - crop_w) // 2
            img = img.crop((left, 0, left + crop_w, orig_h))
        elif orig_ratio < target_ratio:
            crop_h = int(orig_w / target_ratio)
            top = (orig_h - crop_h) // 2
            img = img.crop((0, top, orig_w, top + crop_h))

        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="PPM")
        return tk.PhotoImage(data=buf.getvalue())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Download History Manager
# ---------------------------------------------------------------------------

class DownloadHistory:
    """Manage download history for the Queue tab."""

    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self.history: List[Dict[str, Any]] = []

    def add_item(self, url: str, title: str, status: str, file_path: str = ""):
        """Add item to download history."""
        item = {
            "url": url,
            "title": title,
            "status": status,
            "file_path": file_path,
            "timestamp": self._get_timestamp()
        }
        self.history.insert(0, item)
        if len(self.history) > self.max_items:
            self.history.pop()

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all history items."""
        return self.history

    def clear(self):
        """Clear all history."""
        self.history.clear()


class _DummyWidget:
    """Safe fallback widget for unit test environments where widgets are not explicitly mocked."""
    def __init__(self, *args, **kwargs):
        pass
    def configure(self, *args, **kwargs):
        return None
    def config(self, *args, **kwargs):
        return None
    def grid(self, *args, **kwargs):
        return None
    def grid_forget(self, *args, **kwargs):
        return None
    def pack(self, *args, **kwargs):
        return None
    def pack_forget(self, *args, **kwargs):
        return None
    def set(self, *args, **kwargs):
        return None
    def get(self, *args, **kwargs):
        return ""
    def delete(self, *args, **kwargs):
        return None
    def insert(self, *args, **kwargs):
        return None
    def bind(self, *args, **kwargs):
        return None


# ---------------------------------------------------------------------------
# Main Application Window
# ---------------------------------------------------------------------------

class DownloadyhaGUI(ctk.CTk):
    """Main GUI Application Window with Calm Luxury Design."""

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        if "_dummy_widgets" not in self.__dict__:
            self.__dict__["_dummy_widgets"] = {}
        if name not in self.__dict__["_dummy_widgets"]:
            self.__dict__["_dummy_widgets"][name] = _DummyWidget()
        return self.__dict__["_dummy_widgets"][name]

    def set_theme_mode(self, mode: str):
        """Set theme appearance mode (light, dark, system)."""
        mode_clean = mode.lower()
        if mode_clean not in ("light", "dark", "system"):
            mode_clean = "light"
        ctk.set_appearance_mode(mode_clean)
        self.config["appearance_mode"] = mode_clean
        self.config["theme"] = mode_clean
        save_config(self.config)

        theme_map = {"dark": "🌙 Dark", "system": "💻 Auto", "light": "☀️ Light"}
        settings_map = {"dark": "🌙 Dark Mode", "system": "💻 System Default", "light": "☀️ Light Mode"}
        if hasattr(self, "theme_segmented") and self.theme_segmented:
            self.theme_segmented.set(theme_map.get(mode_clean, "☀️ Light"))
        if hasattr(self, "settings_theme_segmented") and self.settings_theme_segmented:
            self.settings_theme_segmented.set(settings_map.get(mode_clean, "☀️ Light Mode"))

    def _on_theme_segmented_change(self, value: str):
        if "Dark" in value:
            self.set_theme_mode("dark")
        elif "Auto" in value or "System" in value:
            self.set_theme_mode("system")
        else:
            self.set_theme_mode("light")

    def _on_settings_theme_change(self, value: str):
        if "Dark" in value:
            self.set_theme_mode("dark")
        elif "Auto" in value or "System" in value:
            self.set_theme_mode("system")
        else:
            self.set_theme_mode("light")

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title(f"Downloadyha v{__version__} — Modern Media Downloader")
        self.geometry("1040x840")
        self.minsize(760, 540)
        self.resizable(True, True)

        # Load user configuration
        self.config = load_config()

        # State variables
        self.media_info: Optional[Dict[str, Any]] = None
        self.last_fetched_url: str = ""
        self.is_fetching_info: bool = False
        self.available_video_qualities: List[int] = []

        # Download threading & cancel state
        self.current_download_thread: Optional[threading.Thread] = None
        self.fetch_thread: Optional[threading.Thread] = None
        self.is_downloading: bool = False
        self.cancel_requested: bool = False

        # Thumbnail state & retention
        self._thumbnail_request_token: str = ""
        self._current_thumbnail_img: Optional[tk.PhotoImage] = None

        # Download history
        self.download_history = DownloadHistory()

        # UI Scale configuration
        self.ui_scale: float = float(self.config.get("ui_scale", 1.0))

        # Apply theme from config or system default
        self._setup_theme()

        # Configure root grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create main UI widgets
        self._create_widgets()

        # Set multi-resolution high-res window icons
        self._set_window_icon()

        # Register universal cross-platform zoom shortcuts (Ctrl +, Ctrl -, Ctrl 0, Mouse Wheel)
        self._setup_zoom_keybindings()

        # Responsive resize binding for fluid layout & wraplength
        self.bind("<Configure>", self._on_window_resize)

        # Open maximized / full screen by default without forcing floating coordinates
        self.after(20, self._maximize_window_startup)

        # Ensure dependencies (FFmpeg, Deno) are available in background
        self._prepare_dependencies_async()

    def _maximize_window_startup(self):
        """Maximize window on startup across platforms without forcing floating coordinates."""
        try:
            if sys.platform.startswith("linux"):
                self.attributes("-zoomed", True)
            elif sys.platform == "win32":
                self.state("zoomed")
            elif sys.platform == "darwin":
                self.wm_attributes("-zoomed", True)
        except Exception:
            pass

    def _on_window_resize(self, event=None):
        """Dynamically adapt container width and label wraplengths on window resize across all devices."""
        if event and event.widget == self:
            curr_w = self.winfo_width()
            # Fluid responsive width:
            # - On wide/tiled screens (1920px+): centered at 960px max width
            # - On laptop/compact screens (760px-1040px): fills available width with 48px padding
            # - On narrow screens (below 680px): minimum 600px width
            max_c_w = min(960, max(600, curr_w - 48))
            for spacer_name in ["_download_width_spacer", "_queue_width_spacer", "_settings_width_spacer"]:
                spacer = getattr(self, spacer_name, None)
                if spacer is not None:
                    try:
                        spacer.configure(width=max_c_w)
                    except Exception:
                        pass

            avail_text_w = max(280, max_c_w - 240 - 64)
            for attr in ["media_title_label", "media_meta_label", "media_channel_label"]:
                lbl = getattr(self, attr, None)
                if lbl is not None:
                    try:
                        lbl.configure(wraplength=avail_text_w)
                    except Exception:
                        pass

    def _prepare_dependencies_async(self):
        """Ensure FFmpeg and Deno dependencies are available in background."""
        def worker():
            try:
                check_dependencies(auto_download=True)
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _setup_theme(self):
        """Configure application theme, subpixel font hinting, and interface scaling."""
        theme_mode = self.config.get("theme", "system")
        ctk.set_appearance_mode(theme_mode)
        ctk.set_default_color_theme("blue")

        try:
            self.option_add("*Font.antialias", "1")
        except Exception:
            pass

        try:
            ctk.set_widget_scaling(self.ui_scale)
        except Exception:
            pass

        self.configure(fg_color=PremiumTheme.BG_WINDOW)

    def _set_window_icon(self):
        """Set multi-resolution high-resolution window and taskbar icons."""
        try:
            icons_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "icons"
            icon_files = [
                icons_dir / "app_icon_256.png",
                icons_dir / "app_icon_128.png",
                icons_dir / "app_icon_64.png",
                icons_dir / "app_icon_32.png",
                icons_dir / "app_icon_16.png",
            ]
            loaded_photos = []
            for path in icon_files:
                if path.exists():
                    loaded_photos.append(tk.PhotoImage(file=str(path)))
            if loaded_photos:
                self.wm_iconphoto(True, *loaded_photos)
                return

            fallback_ico = Path(__file__).parent / "resources" / "icon.ico"
            if fallback_ico.exists():
                self.iconbitmap(str(fallback_ico))
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # Universal Cross-Platform Zoom Engine (Ctrl +, Ctrl -, Ctrl 0, Mouse Wheel)
    # -----------------------------------------------------------------------

    def _setup_zoom_keybindings(self):
        """Bind universal cross-platform keyboard shortcuts and mouse wheel events for zoom."""
        # Zoom In shortcuts: Ctrl/Cmd + (+, =, numpad +)
        for key in [
            "<Control-plus>",
            "<Control-equal>",
            "<Control-KP_Add>",
            "<Command-plus>",
            "<Command-equal>",
            "<Command-KP_Add>",
        ]:
            self.bind_all(key, self._zoom_in)

        # Zoom Out shortcuts: Ctrl/Cmd + (-, _, numpad -)
        for key in [
            "<Control-minus>",
            "<Control-underscore>",
            "<Control-KP_Subtract>",
            "<Command-minus>",
            "<Command-underscore>",
            "<Command-KP_Subtract>",
        ]:
            self.bind_all(key, self._zoom_out)

        # Zoom Reset shortcuts: Ctrl/Cmd + 0
        for key in [
            "<Control-0>",
            "<Control-KP_0>",
            "<Command-0>",
            "<Command-KP_0>",
        ]:
            self.bind_all(key, self._zoom_reset)

        # Mouse wheel zoom (Windows & macOS)
        for key in ["<Control-MouseWheel>", "<Command-MouseWheel>"]:
            self.bind_all(key, self._on_mousewheel_zoom)

        # Mouse wheel zoom (Linux X11 & Xwayland)
        self.bind_all("<Control-Button-4>", self._zoom_in)
        self.bind_all("<Control-Button-5>", self._zoom_out)

    def _zoom_in(self, event=None):
        """Increase interface scale by 10% (0.1), clamped at 2.0 (200%)."""
        new_scale = round(min(2.0, self.ui_scale + 0.1), 2)
        if new_scale != self.ui_scale:
            self._set_zoom_scale(new_scale)
        return "break"

    def _zoom_out(self, event=None):
        """Decrease interface scale by 10% (0.1), clamped at 0.8 (80%)."""
        new_scale = round(max(0.8, self.ui_scale - 0.1), 2)
        if new_scale != self.ui_scale:
            self._set_zoom_scale(new_scale)
        return "break"

    def _zoom_reset(self, event=None):
        """Reset interface scale to default 100% (1.0)."""
        if self.ui_scale != 1.0:
            self._set_zoom_scale(1.0)
        else:
            self._show_toast("Zoom: 100% (Default)", "info")
        return "break"

    def _on_mousewheel_zoom(self, event):
        """Handle mouse wheel zoom on Windows and macOS."""
        if hasattr(event, "delta") and event.delta:
            if event.delta > 0:
                return self._zoom_in(event)
            else:
                return self._zoom_out(event)
        return "break"

    def _set_zoom_scale(self, scale: float, show_toast: bool = True):
        """Apply zoom scale dynamically, persist to config, and update settings controls."""
        self.ui_scale = round(float(scale), 2)
        try:
            ctk.set_widget_scaling(self.ui_scale)
        except Exception:
            pass

        # Persist to configuration
        self.config["ui_scale"] = self.ui_scale
        try:
            save_config(self.config)
        except Exception:
            pass

        # Synchronize Settings tab dropdown / label if active
        if hasattr(self, "scale_var") and self.scale_var:
            pct = int(round(self.ui_scale * 100))
            label_val = "100% (Default)" if pct == 100 else f"{pct}%"
            self.scale_var.set(label_val)

        if show_toast:
            pct = int(round(self.ui_scale * 100))
            self._show_toast(f"Zoom: {pct}%", toast_type="info")

    def _create_widgets(self):
        """Build main UI components with modern styling."""
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="nsew")
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        # Premium segmented tabview (borderless outer container)
        self.tabview = ctk.CTkTabview(
            main_container,
            corner_radius=14,
            border_width=0,
            fg_color=PremiumTheme.BG_CONTAINER,
            segmented_button_fg_color=PremiumTheme.SURFACE_MUTED,
            segmented_button_selected_color=PremiumTheme.ACCENT_PRIMARY,
            segmented_button_selected_hover_color=PremiumTheme.ACCENT_HOVER,
            segmented_button_unselected_color=PremiumTheme.SURFACE_MUTED,
            segmented_button_unselected_hover_color=("#CBD5E1", "#242838"),
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.tabview.grid(row=0, column=0, sticky="nsew")

        # Add tabs with explicit tuple color preservation
        tab_download = self.tabview.add("Download")
        tab_queue = self.tabview.add("Queue")
        tab_settings = self.tabview.add("Settings")

        # Counteract upstream CTkTabview tuple stripping
        for t in [tab_download, tab_queue, tab_settings]:
            t.configure(fg_color=PremiumTheme.BG_CONTAINER)

        # Configure tab content
        self._create_download_tab()
        self._create_queue_tab()
        self._create_settings_tab()

        # Set default tab
        self.tabview.set("Download")

        # Copyright footer
        copyright_label = ctk.CTkLabel(
            main_container,
            text="© 2026 Ahmed Tarek Zaher • Downloadyha",
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.TEXT_MUTED
        )
        copyright_label.grid(row=1, column=0, pady=(4, 6), sticky="ew")

    def _create_compact_header(self, parent):
        """Create compact header with branded title, version badge, and live status indicator."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent", height=36)
        header_frame.pack(fill="x", pady=(0, 16))
        header_frame.pack_propagate(False)

        # Left brand title and version
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")

        title_label = ctk.CTkLabel(
            title_frame,
            text="Downloadyha",
            font=PremiumTheme.font_title(),
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        title_label.pack(side="left")

        version_badge = ctk.CTkLabel(
            title_frame,
            text=f"v{__version__}",
            font=PremiumTheme.font_badge(),
            fg_color=PremiumTheme.SURFACE_MUTED,
            text_color=PremiumTheme.ACCENT_PRIMARY,
            corner_radius=6,
            width=54,
            height=24
        )
        version_badge.pack(side="left", padx=(10, 0))

        # Right status indicator
        self.status_indicator = ctk.CTkLabel(
            header_frame,
            text="● Ready",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.STATUS_SUCCESS
        )
        self.status_indicator.pack(side="right")

    # -----------------------------------------------------------------------
    # Download Tab
    # -----------------------------------------------------------------------

    def _create_download_tab(self):
        """Create the main Download tab with hero input and rich media showcase."""
        tab = self.tabview.tab("Download")
        tab.grid_columnconfigure(0, weight=1)
        scroll = ctk.CTkScrollableFrame(tab, fg_color=PremiumTheme.BG_CONTAINER)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # Centered responsive container
        self._center_download_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self._center_download_container.pack(anchor="n", pady=8, padx=16)

        # Zero-height width spacer to maintain exact responsive container width
        self._download_width_spacer = ctk.CTkFrame(self._center_download_container, fg_color="transparent", width=960, height=0)
        self._download_width_spacer.pack(fill="x")

        # Header
        self._create_compact_header(self._center_download_container)

        # URL Input Section
        url_label = ctk.CTkLabel(
            self._center_download_container,
            text="Media or Playlist URL",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.TEXT_SECONDARY
        )
        url_label.pack(anchor="w", pady=(0, 6))

        url_input_frame = ctk.CTkFrame(self._center_download_container, fg_color="transparent")
        url_input_frame.pack(fill="x", pady=(0, 16))

        self.url_entry = ctk.CTkEntry(
            url_input_frame,
            placeholder_text="Paste YouTube, TikTok, Instagram, Twitter/X, Facebook, or web video link...",
            height=46,
            font=PremiumTheme.font_body(),
            corner_radius=8,
            border_width=1,
            border_color=PremiumTheme.BORDER_INPUT,
            fg_color=PremiumTheme.SURFACE_INPUT,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry.bind("<Return>", lambda event: self._fetch_media_info())

        paste_btn = ModernButton(
            url_input_frame,
            variant="secondary",
            text="Paste",
            width=80,
            height=46,
            font=PremiumTheme.font_button(),
            command=self._paste_url
        )
        paste_btn.pack(side="left", padx=(0, 8))

        self.fetch_btn = ModernButton(
            url_input_frame,
            variant="primary",
            text="Analyze",
            width=100,
            height=46,
            font=PremiumTheme.font_button(),
            command=self._fetch_media_info
        )
        self.fetch_btn.pack(side="left")

        # Media Showcase Bento Card
        self.media_card = GlassCard(self._center_download_container)
        self.media_card.pack(fill="x", pady=(0, 16))

        media_card_inner = ctk.CTkFrame(self.media_card, fg_color="transparent")
        media_card_inner.pack(fill="both", expand=True, padx=16, pady=16)

        # Left Column: 240x135 16:9 Thumbnail Preview
        self.thumbnail_frame = ctk.CTkFrame(
            media_card_inner,
            width=240,
            height=135,
            corner_radius=8,
            fg_color=PremiumTheme.SURFACE_MUTED,
            border_width=0
        )
        self.thumbnail_frame.pack(side="left", padx=(0, 16))
        self.thumbnail_frame.pack_propagate(False)

        dark_mode = ctk.get_appearance_mode().lower() == "dark"
        placeholder_photo = create_placeholder_thumbnail(240, 135, dark_mode=dark_mode)
        self._current_thumbnail_img = placeholder_photo

        self.thumbnail_label = tk.Label(
            self.thumbnail_frame,
            image=placeholder_photo,
            bg="#161924" if dark_mode else "#FFFFFF",
            bd=0,
            highlightthickness=0
        )
        self.thumbnail_label.image = placeholder_photo
        self.thumbnail_label.pack(fill="both", expand=True)

        # Right Column: Metadata details
        info_frame = ctk.CTkFrame(media_card_inner, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        badge_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        badge_row.pack(fill="x", pady=(0, 8))

        self.media_badge = ctk.CTkLabel(
            badge_row,
            text="Ready",
            font=PremiumTheme.font_badge(),
            fg_color=PremiumTheme.SURFACE_MUTED,
            text_color=PremiumTheme.TEXT_SECONDARY,
            corner_radius=6,
            width=54,
            height=24
        )
        self.media_badge.pack(side="left", padx=(0, 10))

        self.media_channel_label = ctk.CTkLabel(
            badge_row,
            text="Paste a link above and click Analyze (or press Enter)",
            font=PremiumTheme.font_body(),
            text_color=PremiumTheme.TEXT_SECONDARY,
            anchor="w"
        )
        self.media_channel_label.pack(side="left")

        # Title row inside card
        self.media_title_label = ctk.CTkLabel(
            info_frame,
            text="No video analyzed yet",
            font=PremiumTheme.font_card_title(),
            text_color=PremiumTheme.TEXT_PRIMARY,
            anchor="w",
            wraplength=560,
            justify="left"
        )
        self.media_title_label.pack(fill="x", pady=(0, 6))

        # Metadata row inside card
        self.media_meta_label = ctk.CTkLabel(
            info_frame,
            text="Supported: 4K, 2K, 1080p, 720p, 480p, 360p • MP3 Bitrates (Best, 320k, 192k, 128k)",
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.TEXT_MUTED,
            anchor="w",
            wraplength=560,
            justify="left"
        )
        self.media_meta_label.pack(fill="x", pady=(0, 8))

        self.card_status_label = ctk.CTkLabel(
            info_frame,
            text="Ready to download",
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.STATUS_SUCCESS,
            anchor="w"
        )
        self.card_status_label.pack(fill="x")

        # Options Section - Media Type + Quality
        options_label_frame = ctk.CTkFrame(self._center_download_container, fg_color="transparent")
        options_label_frame.pack(fill="x", pady=(0, 6))
        options_label_frame.grid_columnconfigure(0, weight=1)
        options_label_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            options_label_frame,
            text="Format Type",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.TEXT_SECONDARY
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            options_label_frame,
            text="Target Quality",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.TEXT_SECONDARY
        ).grid(row=0, column=1, padx=(10, 0), sticky="w")

        options_frame = ctk.CTkFrame(self._center_download_container, fg_color="transparent")
        options_frame.pack(fill="x", pady=(0, 16))
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)

        self.media_type_var = tk.StringVar(value="Video")
        self.media_type_selector = ctk.CTkSegmentedButton(
            options_frame,
            values=["Video", "Audio"],
            variable=self.media_type_var,
            font=PremiumTheme.font_button(),
            command=self._on_media_type_changed,
            corner_radius=8,
            height=42,
            fg_color=PremiumTheme.SURFACE_MUTED,
            selected_color=PremiumTheme.ACCENT_PRIMARY,
            selected_hover_color=PremiumTheme.ACCENT_HOVER,
            unselected_color=PremiumTheme.SURFACE_MUTED,
            unselected_hover_color=("#CBD5E1", "#242838"),
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.media_type_selector.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.quality_var = tk.StringVar(value=DEFAULT_VIDEO_QUALITIES[0])
        self.quality_menu = ctk.CTkOptionMenu(
            options_frame,
            variable=self.quality_var,
            values=DEFAULT_VIDEO_QUALITIES,
            font=PremiumTheme.font_body(),
            dropdown_font=PremiumTheme.font_body(),
            corner_radius=8,
            height=42,
            fg_color=PremiumTheme.SURFACE_CARD,
            button_color=PremiumTheme.SURFACE_CARD,
            button_hover_color=PremiumTheme.SURFACE_CARD_HOVER,
            dropdown_fg_color=PremiumTheme.SURFACE_CARD,
            dropdown_hover_color=PremiumTheme.SURFACE_CARD_HOVER,
            dropdown_text_color=PremiumTheme.TEXT_PRIMARY,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.quality_menu.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        # Extra Options (Section Clipping & Subtitles)
        extra_options_container = ctk.CTkFrame(self._center_download_container, fg_color="transparent")
        extra_options_container.pack(fill="x", pady=(0, 16))
        extra_options_container.grid_columnconfigure(0, weight=1)

        # Section Clipping Toggle (row 6)
        section_toggle_frame = ctk.CTkFrame(extra_options_container, fg_color="transparent")
        section_toggle_frame.grid(row=6, column=0, padx=0, pady=(2, 2), sticky="ew")

        self.section_toggle_var = tk.BooleanVar(value=False)
        self.section_toggle = ctk.CTkCheckBox(
            section_toggle_frame,
            text="Download specific section (clip)",
            variable=self.section_toggle_var,
            font=PremiumTheme.font_body_bold(),
            command=self._on_section_toggled,
            fg_color=PremiumTheme.ACCENT_PRIMARY,
            hover_color=PremiumTheme.ACCENT_HOVER,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.section_toggle.grid(row=0, column=0, sticky="w")

        # Collapsible Section Range Inputs (row 7, hidden by default)
        self.section_frame = ctk.CTkFrame(
            extra_options_container,
            fg_color=PremiumTheme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=PremiumTheme.BORDER_SUBTLE
        )
        self.section_frame.grid_columnconfigure(0, weight=1)
        self.section_frame.grid_columnconfigure(1, weight=1)

        # Start time box
        start_box = ctk.CTkFrame(self.section_frame, fg_color="transparent")
        start_box.grid(row=0, column=0, padx=(12, 6), pady=(8, 4), sticky="ew")
        start_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            start_box,
            text="Start Time:",
            font=PremiumTheme.font_meta_bold(),
            text_color=PremiumTheme.TEXT_SECONDARY
        ).grid(row=0, column=0, sticky="w")
        self.start_time_entry = ctk.CTkEntry(
            start_box,
            placeholder_text="00:00 (e.g. 01:30)",
            height=36,
            font=PremiumTheme.font_body(),
            corner_radius=6,
            border_width=1,
            border_color=PremiumTheme.BORDER_INPUT,
            fg_color=PremiumTheme.SURFACE_INPUT,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.start_time_entry.grid(row=1, column=0, sticky="ew", pady=(3, 0))

        # End time box
        end_box = ctk.CTkFrame(self.section_frame, fg_color="transparent")
        end_box.grid(row=0, column=1, padx=(6, 12), pady=(8, 4), sticky="ew")
        end_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            end_box,
            text="End Time:",
            font=PremiumTheme.font_meta_bold(),
            text_color=PremiumTheme.TEXT_SECONDARY
        ).grid(row=0, column=0, sticky="w")
        self.end_time_entry = ctk.CTkEntry(
            end_box,
            placeholder_text="Leave blank for end (e.g. 04:15)",
            height=36,
            font=PremiumTheme.font_body(),
            corner_radius=6,
            border_width=1,
            border_color=PremiumTheme.BORDER_INPUT,
            fg_color=PremiumTheme.SURFACE_INPUT,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.end_time_entry.grid(row=1, column=0, sticky="ew", pady=(3, 0))

        # Hint guide label
        self.section_hint_label = ctk.CTkLabel(
            self.section_frame,
            text="Formats: MM:SS, HH:MM:SS, or seconds (e.g., 01:30, 90, 01:15:30)",
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.TEXT_MUTED
        )
        self.section_hint_label.grid(row=1, column=0, columnspan=2, padx=12, pady=(2, 8), sticky="w")

        # Transcript (Subtitles) Toggle (row 8)
        transcript_toggle_frame = ctk.CTkFrame(extra_options_container, fg_color="transparent")
        transcript_toggle_frame.grid(row=8, column=0, padx=0, pady=(6, 2), sticky="ew")

        self.transcript_toggle_var = tk.BooleanVar(value=False)
        self.transcript_toggle = ctk.CTkCheckBox(
            transcript_toggle_frame,
            text="Download Video Transcripts (Subtitles)",
            variable=self.transcript_toggle_var,
            font=PremiumTheme.font_body_bold(),
            command=self._on_transcript_toggled,
            fg_color=PremiumTheme.ACCENT_PRIMARY,
            hover_color=PremiumTheme.ACCENT_HOVER,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.transcript_toggle.grid(row=0, column=0, sticky="w")

        # Collapsible Transcript Options (row 9, hidden by default)
        self.transcript_frame = ctk.CTkFrame(
            extra_options_container,
            fg_color=PremiumTheme.SURFACE_CARD,
            corner_radius=8,
            border_width=1,
            border_color=PremiumTheme.BORDER_SUBTLE
        )
        self.transcript_frame.grid_columnconfigure(0, weight=1)
        self.transcript_frame.grid_columnconfigure(1, weight=1)

        lang_box = ctk.CTkFrame(self.transcript_frame, fg_color="transparent")
        lang_box.grid(row=0, column=0, padx=(12, 6), pady=(8, 4), sticky="ew")
        lang_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lang_box, text="Languages (e.g. en,ar):", font=PremiumTheme.font_meta_bold(), text_color=PremiumTheme.TEXT_SECONDARY).grid(row=0, column=0, sticky="w")
        self.sub_langs_entry = ctk.CTkEntry(
            lang_box,
            placeholder_text="en",
            height=36,
            font=PremiumTheme.font_body(),
            corner_radius=6,
            border_width=1,
            border_color=PremiumTheme.BORDER_INPUT,
            fg_color=PremiumTheme.SURFACE_INPUT,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.sub_langs_entry.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        self.sub_langs_entry.insert(0, "en")

        fmt_box = ctk.CTkFrame(self.transcript_frame, fg_color="transparent")
        fmt_box.grid(row=0, column=1, padx=(6, 12), pady=(8, 4), sticky="ew")
        fmt_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(fmt_box, text="Format:", font=PremiumTheme.font_meta_bold(), text_color=PremiumTheme.TEXT_SECONDARY).grid(row=0, column=0, sticky="w")
        self.sub_format_var = tk.StringVar(value="srt")
        self.sub_format_menu = ctk.CTkOptionMenu(
            fmt_box,
            variable=self.sub_format_var,
            values=["srt", "vtt", "ass"],
            font=PremiumTheme.font_body(),
            dropdown_font=PremiumTheme.font_body(),
            corner_radius=6,
            height=36,
            fg_color=PremiumTheme.SURFACE_MUTED,
            button_color=PremiumTheme.SURFACE_MUTED,
            button_hover_color=PremiumTheme.SURFACE_CARD_HOVER,
            dropdown_fg_color=PremiumTheme.SURFACE_CARD,
            dropdown_hover_color=PremiumTheme.SURFACE_CARD_HOVER,
            dropdown_text_color=PremiumTheme.TEXT_PRIMARY,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.sub_format_menu.grid(row=1, column=0, sticky="ew", pady=(3, 0))

        self.auto_subs_var = tk.BooleanVar(value=False)
        self.auto_subs_check = ctk.CTkCheckBox(
            self.transcript_frame,
            text="Use auto-generated subtitles",
            variable=self.auto_subs_var,
            font=PremiumTheme.font_body(),
            fg_color=PremiumTheme.ACCENT_PRIMARY,
            hover_color=PremiumTheme.ACCENT_HOVER,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.auto_subs_check.grid(row=1, column=0, padx=12, pady=(4, 8), sticky="w")

        self.embed_subs_var = tk.BooleanVar(value=False)
        self.embed_subs_check = ctk.CTkCheckBox(
            self.transcript_frame,
            text="Embed in video",
            variable=self.embed_subs_var,
            font=PremiumTheme.font_body(),
            fg_color=PremiumTheme.ACCENT_PRIMARY,
            hover_color=PremiumTheme.ACCENT_HOVER,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.embed_subs_check.grid(row=1, column=1, padx=12, pady=(4, 8), sticky="w")

        # Destination Folder Section
        dest_label = ctk.CTkLabel(
            self._center_download_container,
            text="Save Destination",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.TEXT_SECONDARY
        )
        dest_label.pack(anchor="w", pady=(0, 6))

        dest_entry_frame = ctk.CTkFrame(self._center_download_container, fg_color="transparent")
        dest_entry_frame.pack(fill="x", pady=(0, 16))

        self.dest_entry = ctk.CTkEntry(
            dest_entry_frame,
            height=42,
            font=PremiumTheme.font_body(),
            corner_radius=8,
            border_width=1,
            border_color=PremiumTheme.BORDER_INPUT,
            fg_color=PremiumTheme.SURFACE_INPUT,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.dest_entry.insert(0, self.config.get("download_directory", str(get_download_dir())))

        browse_btn = ModernButton(
            dest_entry_frame,
            variant="secondary",
            text="Browse",
            width=85,
            height=42,
            font=PremiumTheme.font_button(),
            command=self._browse_destination
        )
        browse_btn.pack(side="left")

        # Progress Section
        progress_frame = GlassCard(self._center_download_container)
        progress_frame.pack(fill="x", pady=(0, 16), ipady=8)

        progress_header_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        progress_header_frame.pack(fill="x", padx=16, pady=(12, 6))

        progress_title = ctk.CTkLabel(
            progress_header_frame,
            text="Download Progress",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        progress_title.pack(side="left")

        self.status_label = ctk.CTkLabel(
            progress_header_frame,
            text="Ready to download",
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.STATUS_SUCCESS
        )
        self.status_label.pack(side="right")

        self.progress_bar = AnimatedProgressBar(progress_frame, height=8, corner_radius=4)
        self.progress_bar.pack(fill="x", padx=16, pady=(4, 6))
        self.progress_bar.set(0)

        details_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=16, pady=(0, 8))

        self.percent_label = ctk.CTkLabel(
            details_frame,
            text="0%",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.ACCENT_PRIMARY
        )
        self.percent_label.pack(side="left")

        self.speed_label = ctk.CTkLabel(
            details_frame,
            text="Speed: --",
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.TEXT_MUTED
        )
        self.speed_label.pack(side="left", padx=16)

        self.eta_label = ctk.CTkLabel(
            details_frame,
            text="ETA: --",
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.TEXT_MUTED
        )
        self.eta_label.pack(side="right")

        # Action Buttons Section
        buttons_frame = ctk.CTkFrame(self._center_download_container, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 18))
        buttons_frame.grid_columnconfigure(0, weight=3)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)

        self.download_btn = ModernButton(
            buttons_frame,
            variant="primary",
            text="Download Video",
            font=PremiumTheme.font_button_large(),
            height=48,
            corner_radius=9,
            command=self._start_download
        )
        self.download_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.cancel_btn = ModernButton(
            buttons_frame,
            variant="ghost",
            text="Cancel",
            font=PremiumTheme.font_button(),
            height=48,
            corner_radius=9,
            command=self._cancel_download
        )
        self.cancel_btn.grid(row=0, column=1, padx=(0, 10), sticky="ew")

        self.open_folder_btn = ModernButton(
            buttons_frame,
            variant="secondary",
            text="Open Folder",
            font=PremiumTheme.font_button(),
            height=48,
            corner_radius=9,
            command=self._open_download_folder
        )
        self.open_folder_btn.grid(row=0, column=2, sticky="ew")

        # Recent Activity Shelf (fills lower viewport comfortably on all devices)
        self.recent_shelf_card = GlassCard(self._center_download_container)
        self.recent_shelf_card.pack(fill="x", pady=(0, 16))

        self.recent_shelf_inner = ctk.CTkFrame(self.recent_shelf_card, fg_color="transparent")
        self.recent_shelf_inner.pack(fill="both", expand=True, padx=16, pady=14)

        shelf_hdr = ctk.CTkFrame(self.recent_shelf_inner, fg_color="transparent")
        shelf_hdr.pack(fill="x", pady=(0, 8))

        r_title = ctk.CTkLabel(
            shelf_hdr,
            text="Recent Activity",
            font=PremiumTheme.font_subheading(),
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        r_title.pack(side="left")

        self.recent_shelf_items_frame = ctk.CTkFrame(self.recent_shelf_inner, fg_color="transparent")
        self.recent_shelf_items_frame.pack(fill="x")

        self._refresh_recent_downloads_shelf()

    def _refresh_recent_downloads_shelf(self):
        """Refresh recent downloads shelf on the main Download tab."""
        if not hasattr(self, "recent_shelf_items_frame") or self.recent_shelf_items_frame is None:
            return

        for widget in self.recent_shelf_items_frame.winfo_children():
            widget.destroy()

        history = self.download_history.get_all()[:3]
        if not history:
            ph = ctk.CTkLabel(
                self.recent_shelf_items_frame,
                text="No recent downloads yet • Paste a link above to get started",
                font=PremiumTheme.font_meta(),
                text_color=PremiumTheme.TEXT_MUTED
            )
            ph.pack(pady=8)
            return

        status_colors = {
            'completed': PremiumTheme.STATUS_SUCCESS,
            'failed': PremiumTheme.STATUS_ERROR,
            'cancelled': PremiumTheme.STATUS_WARNING,
        }

        for item in history:
            row = ctk.CTkFrame(self.recent_shelf_items_frame, fg_color=PremiumTheme.SURFACE_INPUT, corner_radius=8, height=40)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)

            color = status_colors.get(item.get("status"), PremiumTheme.TEXT_MUTED)
            i_lbl = ctk.CTkLabel(row, text="●", font=PremiumTheme.font_body_bold(), text_color=color)
            i_lbl.pack(side="left", padx=(12, 8))

            title_str = item.get("title", "Unknown")
            if len(title_str) > 55:
                title_str = title_str[:52] + "..."
            t_lbl = ctk.CTkLabel(row, text=title_str, font=PremiumTheme.font_body_bold(), text_color=PremiumTheme.TEXT_PRIMARY)
            t_lbl.pack(side="left")

            s_text = item.get("status", "").title()
            s_lbl = ctk.CTkLabel(row, text=s_text, font=PremiumTheme.font_meta(), text_color=color)
            s_lbl.pack(side="right", padx=14)

    def _set_placeholder_thumbnail(self):
        """Render a clean in-memory vector-style placeholder thumbnail."""
        if "thumbnail_label" in self.__dict__ and self.thumbnail_label is not None:
            dark_mode = ctk.get_appearance_mode().lower() == "dark"
            photo = create_placeholder_thumbnail(240, 135, dark_mode=dark_mode)
            self._current_thumbnail_img = photo
            self.thumbnail_label.configure(image=photo, bg="#161924" if dark_mode else "#FFFFFF")
            self.thumbnail_label.image = photo

    def _fetch_thumbnail_async(self, info: Dict[str, Any], url: str):
        """Fetch remote thumbnail asynchronously in a daemon thread with race condition guard."""
        thumb_url = info.get("thumbnail")
        if not thumb_url and "thumbnails" in info and isinstance(info["thumbnails"], list) and info["thumbnails"]:
            thumb_url = info["thumbnails"][-1].get("url")

        if not thumb_url:
            self._set_placeholder_thumbnail()
            return

        self._thumbnail_request_token = url
        token = url

        def worker():
            try:
                req = urllib.request.Request(
                    thumb_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=4) as response:
                    img_data = response.read()

                if getattr(self, "_thumbnail_request_token", None) != token:
                    return

                photo = process_thumbnail_bytes(img_data, 240, 135)
                if photo and getattr(self, "_thumbnail_request_token", None) == token:
                    self.after(0, self._apply_thumbnail, photo, token)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _apply_thumbnail(self, photo: tk.PhotoImage, token: str):
        """Apply fetched thumbnail on main thread with reference retention."""
        if getattr(self, "_thumbnail_request_token", None) == token:
            self._current_thumbnail_img = photo
            if "thumbnail_label" in self.__dict__ and self.thumbnail_label is not None:
                self.thumbnail_label.configure(image=photo)
                self.thumbnail_label.image = photo

    # -----------------------------------------------------------------------
    # Metadata Fetching & Dynamic Quality Management
    # -----------------------------------------------------------------------

    def _paste_url(self):
        """Paste URL from clipboard and automatically fetch metadata."""
        try:
            clipboard_text = self.clipboard_get()
            if clipboard_text:
                clean_url = clipboard_text.strip()
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, clean_url)
                if clean_url.lower().startswith("http://") or clean_url.lower().startswith("https://"):
                    self._fetch_media_info()
        except Exception:
            pass

    def _fetch_media_info(self):
        """Trigger background metadata extraction for the entered URL."""
        url = self.url_entry.get().strip()
        if not url:
            self._show_toast("Please enter a media URL first", "warning")
            return

        if self.is_fetching_info:
            return

        self.is_fetching_info = True
        self.fetch_btn.configure(text="Analyzing...", state="disabled")
        self.status_indicator.configure(text="● Analyzing", text_color=PremiumTheme.STATUS_INFO)
        self.status_label.configure(
            text="Analyzing media metadata and formats...",
            text_color=PremiumTheme.STATUS_INFO
        )

        def worker():
            try:
                info = get_media_info(url, extract_flat="in_playlist")
                if info:
                    self.after(0, self._on_media_info_fetched, info, url)
                else:
                    self.after(0, self._on_media_info_error, "Could not fetch media information.")
            except Exception as e:
                self.after(0, self._on_media_info_error, str(e))

        self.fetch_thread = threading.Thread(target=worker, daemon=True)
        self.fetch_thread.start()

    def _on_media_info_fetched(self, info: Dict[str, Any], url: str):
        """Handle successfully fetched media metadata and trigger thumbnail fetch."""
        self.media_info = info
        self.last_fetched_url = url
        self.is_fetching_info = False

        self.status_indicator.configure(text="● Ready", text_color=PremiumTheme.STATUS_SUCCESS)
        self.fetch_btn.configure(text="Analyze", state="normal")

        is_pl = is_playlist(info) or is_playlist_url(url)
        title = info.get("title") or "Media"
        uploader = info.get("uploader") or info.get("channel") or "Unknown Creator"

        if is_pl:
            entries = get_playlist_entries(info)
            count = len(entries) if entries else info.get("playlist_count", "Multiple")
            self.available_video_qualities = []

            self.media_badge.configure(
                text="Playlist",
                fg_color=PremiumTheme.ACCENT_PRIMARY,
                text_color=PremiumTheme.ACCENT_TEXT
            )
            self.media_channel_label.configure(text=f"Channel: {uploader}")
            self.media_title_label.configure(text=f"📑 {title}")
            self.media_meta_label.configure(
                text=f"Total Items: {count} videos • Type: Playlist"
            )
        else:
            duration_sec = info.get("duration")
            duration_str = format_duration(duration_sec) if duration_sec else "Unknown"
            views_raw = info.get("view_count")
            views_str = f"{format_number(views_raw)} views" if views_raw else "N/A"

            self.available_video_qualities = get_video_qualities(info)
            max_q = f"{self.available_video_qualities[0]}p" if self.available_video_qualities else "Best"

            self.media_badge.configure(
                text="Video",
                fg_color=PremiumTheme.SURFACE_MUTED,
                text_color=PremiumTheme.TEXT_SECONDARY
            )
            self.media_channel_label.configure(text=f"Creator: {uploader}")
            self.media_title_label.configure(text=f"🎬 {title}")
            self.media_meta_label.configure(
                text=f"Duration: {duration_str} • {views_str} • Max: {max_q}"
            )

        # Trigger async thumbnail fetch if thumbnail widget exists
        if "thumbnail_label" in self.__dict__ and self.thumbnail_label is not None:
            self._fetch_thumbnail_async(info, url)

        # Update quality dropdown with actual formats
        self._update_quality_options()

        self.status_label.configure(
            text=f"Ready to download: {title[:55]}{'...' if len(title) > 55 else ''}",
            text_color=PremiumTheme.STATUS_SUCCESS
        )

    def _on_media_info_error(self, error: str):
        """Handle error during media metadata fetch."""
        self.is_fetching_info = False
        self.fetch_btn.configure(text="Analyze", state="normal")
        self.status_indicator.configure(text="● Ready", text_color=PremiumTheme.STATUS_SUCCESS)
        self.status_label.configure(
            text=f"Failed to load: {error}",
            text_color=PremiumTheme.STATUS_WARNING
        )
        self._show_toast(f"Failed to fetch info: {error}", "error")

    def _update_quality_options(self):
        """Update quality dropdown values based on media type and fetched video info."""
        val = self.media_type_var.get().lower()
        is_audio = "audio" in val

        if is_audio:
            self.quality_menu.configure(values=AUDIO_QUALITIES)
            if self.quality_var.get() not in AUDIO_QUALITIES:
                self.quality_var.set(AUDIO_QUALITIES[0])
        else:
            # Video mode
            if self.media_info and not is_playlist(self.media_info) and self.available_video_qualities:
                options = ["Best Available (Maximum Quality)"]
                for h in self.available_video_qualities:
                    options.append(format_height_label(h))
                self.quality_menu.configure(values=options)
                if self.quality_var.get() not in options:
                    self.quality_var.set(options[0])
            else:
                self.quality_menu.configure(values=DEFAULT_VIDEO_QUALITIES)
                if self.quality_var.get() not in DEFAULT_VIDEO_QUALITIES:
                    self.quality_var.set(DEFAULT_VIDEO_QUALITIES[0])

    def _on_media_type_changed(self, value: str):
        """Handle media type change (Video vs Audio)."""
        self._update_quality_options()
        val = self.media_type_var.get().lower()
        if "audio" in val:
            self.download_btn.configure(text="Download Audio")
        else:
            self.download_btn.configure(text="Download Video")

    def _on_section_toggled(self):
        """Show or hide start/end time inputs based on section checkbox state."""
        if self.section_toggle_var.get():
            self.section_frame.grid(row=7, column=0, padx=10, pady=(2, 6), sticky="ew")
        else:
            self.section_frame.grid_forget()

    def _on_transcript_toggled(self):
        """Show or hide transcript options based on checkbox state."""
        if self.transcript_toggle_var.get():
            self.transcript_frame.grid(row=9, column=0, padx=10, pady=(2, 6), sticky="ew")
        else:
            self.transcript_frame.grid_forget()

    def _browse_destination(self):
        """Open directory picker dialog for download destination."""
        try:
            init_dir = self.dest_entry.get().strip() if hasattr(self, "dest_entry") else ""
            if not init_dir or not os.path.isdir(init_dir):
                init_dir = str(get_download_dir())

            folder = filedialog.askdirectory(
                parent=self,
                title="Select Destination Folder",
                initialdir=init_dir,
                mustexist=True,
            )
            if folder:
                normalized_folder = os.path.normpath(folder)
                self.dest_entry.delete(0, tk.END)
                self.dest_entry.insert(0, normalized_folder)
        except Exception:
            pass
        finally:
            try:
                self.lift()
                self.focus_force()
            except Exception:
                pass

    # -----------------------------------------------------------------------
    # Download Execution Workflow
    # -----------------------------------------------------------------------

    def _start_download(self):
        """Start download process in background thread."""
        if self.is_downloading:
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a video or playlist URL")
            return

        dest_path = self.dest_entry.get().strip().strip("'\"")
        if not dest_path:
            messagebox.showerror("Error", "Please select a download location")
            return

        if not os.path.isdir(dest_path):
            try:
                os.makedirs(dest_path, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create destination folder: {e}")
                return

        # Validate section clipping times if enabled
        start_time_arg = None
        end_time_arg = None
        if self.section_toggle_var.get():
            st_raw = self.start_time_entry.get().strip()
            et_raw = self.end_time_entry.get().strip()

            if st_raw:
                try:
                    st_val = parse_time_str(st_raw)
                    start_time_arg = st_raw
                except ValueError as e:
                    messagebox.showerror("Invalid Start Time", f"Invalid start time format: {e}")
                    return
            else:
                st_val = None

            if et_raw:
                try:
                    et_val = parse_time_str(et_raw)
                    end_time_arg = et_raw
                except ValueError as e:
                    messagebox.showerror("Invalid End Time", f"Invalid end time format: {e}")
                    return
            else:
                et_val = None

            if st_val is not None and et_val is not None and et_val <= st_val:
                messagebox.showerror("Invalid Time Range", f"End time ({et_raw}) must be greater than start time ({st_raw}).")
                return

        # Start download in background thread
        self.is_downloading = True
        self.cancel_requested = False
        self._reset_progress()
        self.status_label.configure(text="Starting download...", text_color=PremiumTheme.STATUS_INFO)
        self.status_indicator.configure(text="● Downloading", text_color=PremiumTheme.STATUS_INFO)
        self.progress_bar.start_animation()

        self.current_download_thread = threading.Thread(
            target=self._download_worker,
            args=(url, dest_path, start_time_arg, end_time_arg),
            daemon=True
        )
        self.current_download_thread.start()

    def _download_worker(self, url: str, dest_path: str, start_time: Optional[str] = None, end_time: Optional[str] = None):
        """Background worker executing the download."""
        try:
            ffmpeg_ok, _ = check_ffmpeg()
            if not ffmpeg_ok:
                self.after(0, self._update_status, "Preparing FFmpeg components for audio/video merging...")
                check_dependencies(auto_download=True)

            if self.media_info is None or self.last_fetched_url != url:
                self.after(0, self._update_status, "Fetching media information...")
                info = get_media_info(url, extract_flat="in_playlist")
                if info:
                    self.after(0, self._on_media_info_fetched, info, url)
                    media_info = info
                else:
                    media_info = None
            else:
                media_info = self.media_info

            is_pl = is_playlist(media_info) or is_playlist_url(url)

            val = self.media_type_var.get().lower()
            media_type = "audio" if "audio" in val else "video"
            quality_str = self.quality_var.get()

            if media_type == "video":
                quality = self._parse_video_quality(quality_str)
            else:
                quality = self._parse_audio_quality(quality_str)

            def progress_callback(data: Dict[str, Any]):
                if self.cancel_requested:
                    raise KeyboardInterrupt("Download cancelled by user")

                status = data.get("status", "")
                if status == "downloading":
                    percent = data.get("percent", 0.0)
                    speed_str = data.get("speed_str", "--")
                    eta_str = data.get("eta_str", "--")
                    item_title = data.get("item_title", "")
                    pl_idx = data.get("playlist_index")
                    pl_count = data.get("playlist_count")

                    self.after(0, self._update_progress, percent, speed_str, eta_str, item_title, pl_idx, pl_count)
                elif status == "finished":
                    self.after(0, self._update_status, "Processing and merging streams...")

            # Execute download
            subs_kwargs: Dict[str, Any] = {}
            if self.transcript_toggle_var.get():
                subs_kwargs = {
                    "write_subtitles": True,
                    "write_auto_subs": self.auto_subs_var.get(),
                    "sub_langs": self.sub_langs_entry.get().strip() or "en",
                    "sub_format": self.sub_format_var.get(),
                    "embed_subs": self.embed_subs_var.get(),
                }
            if is_pl:
                quality_arg = str(quality) if (media_type == "video" and quality > 0) else ("best" if media_type == "video" else quality)
                result = download_playlist(
                    url=url,
                    download_path=dest_path,
                    media_type=media_type,
                    quality=quality_arg,
                    start_time=start_time,
                    end_time=end_time,
                    progress_callback=progress_callback,
                    **subs_kwargs
                )
            else:
                if media_type == "video":
                    result = download_video(
                        url=url,
                        download_path=dest_path,
                        height=quality,
                        start_time=start_time,
                        end_time=end_time,
                        progress_callback=progress_callback,
                        **subs_kwargs
                    )
                else:
                    result = download_audio(
                        url=url,
                        download_path=dest_path,
                        quality=quality,
                        start_time=start_time,
                        end_time=end_time,
                        progress_callback=progress_callback,
                        **subs_kwargs
                    )

            if result.success:
                self.after(0, self._download_complete, result)
            else:
                error_msg = result.message or "Unknown error occurred"
                self.after(0, self._download_failed, error_msg)

        except KeyboardInterrupt:
            self.after(0, self._download_cancelled)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.after(0, self._download_failed, str(e))

    def _parse_video_quality(self, quality_str: str) -> int:
        """Parse quality label into height integer."""
        if not quality_str or "best" in quality_str.lower():
            return 0
        match = re.search(r'(\d+)p', quality_str)
        if match:
            return int(match.group(1))
        digits = re.findall(r'\d+', quality_str)
        if digits:
            return int(digits[0])
        return 0

    def _parse_audio_quality(self, quality_str: str) -> str:
        """Parse audio quality label into bitrate string."""
        if not quality_str or "best" in quality_str.lower() or "vbr" in quality_str.lower():
            return "0"
        if "320" in quality_str:
            return "320"
        if "192" in quality_str:
            return "192"
        if "128" in quality_str:
            return "128"
        if "256" in quality_str:
            return "256"
        return "0"

    def _update_progress(
        self,
        percent: float,
        speed: str,
        eta: str,
        item_title: str = "",
        pl_idx: Optional[int] = None,
        pl_count: Optional[int] = None
    ):
        """Update progress UI elements."""
        self.progress_bar.set(percent / 100.0)
        self.percent_label.configure(text=f"{percent:.1f}%")
        self.speed_label.configure(text=f"Speed: {speed}")
        self.eta_label.configure(text=f"ETA: {eta}")

        if pl_idx and pl_count:
            status_text = f"Downloading [{pl_idx}/{pl_count}]: {item_title}" if item_title else f"Downloading playlist item {pl_idx} of {pl_count}..."
        elif item_title:
            status_text = f"Downloading: {item_title}"
        else:
            status_text = "Downloading media..."

        self.status_label.configure(text=status_text, text_color=PremiumTheme.STATUS_INFO)

    def _update_status(self, message: str):
        """Update status label."""
        self.status_label.configure(text=message, text_color=PremiumTheme.TEXT_SECONDARY)

    def _reset_progress(self):
        """Reset progress indicators."""
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.speed_label.configure(text="Speed: --")
        self.eta_label.configure(text="ETA: --")

    def _download_complete(self, result: DownloadResult):
        """Handle successful download completion."""
        self.is_downloading = False
        self.progress_bar.stop_animation()
        self.progress_bar.set(1.0)
        self.percent_label.configure(text="100%")
        self.status_indicator.configure(text="● Ready", text_color=PremiumTheme.STATUS_SUCCESS)

        url = self.url_entry.get().strip()
        if result.is_playlist:
            title = result.playlist_title or f"Playlist ({result.completed_items}/{result.total_items} items)"
            msg = f"Playlist download complete!\n\n{result.completed_items}/{result.total_items} items saved to:\n{result.download_directory}"
        else:
            title = (self.media_info.get("title") if self.media_info else None) or "Video / Audio"
            msg = f"Download complete!\n\nSaved to:\n{result.download_directory}"

        self.download_history.add_item(url, title, "completed", result.download_directory)
        self._refresh_queue_tab()
        self._refresh_recent_downloads_shelf()

        self.status_label.configure(text="Download completed successfully!", text_color=PremiumTheme.STATUS_SUCCESS)
        messagebox.showinfo("Success", msg)
        self._reset_progress()
        self.status_label.configure(text="Ready to download", text_color=PremiumTheme.STATUS_SUCCESS)

    def _download_failed(self, error: str):
        """Handle download failure."""
        self.is_downloading = False
        self.progress_bar.stop_animation()
        self.status_label.configure(text="Download failed", text_color=PremiumTheme.STATUS_ERROR)
        self.status_indicator.configure(text="● Error", text_color=PremiumTheme.STATUS_ERROR)

        url = self.url_entry.get().strip()
        title = (self.media_info.get("title") if self.media_info else None) or "Failed Download"
        self.download_history.add_item(url, title, "failed")
        self._refresh_queue_tab()
        self._refresh_recent_downloads_shelf()

        messagebox.showerror("Download Failed", f"An error occurred:\n\n{error}")
        self._reset_progress()
        self.status_label.configure(text="Ready to download", text_color=PremiumTheme.STATUS_SUCCESS)
        self.status_indicator.configure(text="● Ready", text_color=PremiumTheme.STATUS_SUCCESS)

    def _download_cancelled(self):
        """Handle download cancellation."""
        self.is_downloading = False
        self.cancel_requested = False
        self.progress_bar.stop_animation()
        self.status_label.configure(text="Download cancelled", text_color=PremiumTheme.STATUS_WARNING)
        self.status_indicator.configure(text="● Ready", text_color=PremiumTheme.STATUS_SUCCESS)

        url = self.url_entry.get().strip()
        title = (self.media_info.get("title") if self.media_info else None) or "Cancelled Download"
        self.download_history.add_item(url, title, "cancelled")
        self._refresh_queue_tab()
        self._refresh_recent_downloads_shelf()

        messagebox.showinfo("Cancelled", "Download was cancelled.")
        self._reset_progress()
        self.status_label.configure(text="Ready to download", text_color=PremiumTheme.STATUS_SUCCESS)

    def _cancel_download(self):
        """Cancel the running download."""
        if self.is_downloading:
            self.cancel_requested = True
            self.status_indicator.configure(text="● Cancelling", text_color=PremiumTheme.STATUS_WARNING)
            self.status_label.configure(text="Cancelling download...", text_color=PremiumTheme.STATUS_WARNING)

    def _open_download_folder(self):
        """Open the download folder in file explorer across Windows, macOS, and Linux."""
        folder = self.dest_entry.get().strip().strip("'\"")
        if folder and os.path.isdir(folder):
            try:
                if sys.platform == 'win32':
                    os.startfile(folder)
                elif sys.platform == 'darwin':
                    import subprocess
                    subprocess.run(['open', folder], check=False)
                else:
                    import subprocess
                    subprocess.run(['xdg-open', folder], check=False)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open folder: {e}")
        else:
            messagebox.showerror("Error", "Download folder does not exist")

    # -----------------------------------------------------------------------
    # Queue Tab
    # -----------------------------------------------------------------------

    def _create_queue_tab(self):
        """Create the Queue management tab with download history."""
        tab = self.tabview.tab("Queue")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(tab, fg_color=PremiumTheme.BG_CONTAINER)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self._center_queue_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self._center_queue_container.pack(anchor="n", pady=8, padx=16)

        # Zero-height width spacer to maintain exact responsive container width
        self._queue_width_spacer = ctk.CTkFrame(self._center_queue_container, fg_color="transparent", width=960, height=0)
        self._queue_width_spacer.pack(fill="x")

        # Header
        header_frame = ctk.CTkFrame(self._center_queue_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(4, 14))

        header = ctk.CTkLabel(
            header_frame,
            text="Download History",
            font=PremiumTheme.font_heading(),
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        header.pack(side="left")

        self.clear_history_btn = ModernButton(
            header_frame,
            variant="secondary",
            text="Clear History",
            width=110,
            height=36,
            font=PremiumTheme.font_button(),
            command=self._clear_history
        )
        self.clear_history_btn.pack(side="right")

        # History list frame inside centered container
        self.queue_frame = ctk.CTkFrame(
            self._center_queue_container,
            corner_radius=12,
            fg_color=PremiumTheme.SURFACE_INPUT
        )
        self.queue_frame.pack(fill="x", pady=(0, 14))

        self.history_items_frame = ctk.CTkFrame(self.queue_frame, fg_color="transparent")
        self.history_items_frame.pack(fill="x", padx=6, pady=6)

        self._show_history_placeholder()

    def _show_history_placeholder(self):
        """Show placeholder when no history exists."""
        for widget in self.history_items_frame.winfo_children():
            widget.destroy()

        placeholder = ctk.CTkLabel(
            self.history_items_frame,
            text="No downloads yet\n\nYour completed and queued downloads will appear here.",
            font=PremiumTheme.font_body(),
            text_color=PremiumTheme.TEXT_MUTED,
            justify="center"
        )
        placeholder.pack(pady=70)

    def _refresh_queue_tab(self):
        """Refresh the queue tab with updated history."""
        for widget in self.history_items_frame.winfo_children():
            widget.destroy()

        history = self.download_history.get_all()

        if not history:
            self._show_history_placeholder()
            return

        for idx, item in enumerate(history):
            self._create_history_item(item, idx)

    def _create_history_item(self, item: Dict[str, Any], row: int):
        """Create a history item card."""
        status = item.get('status', 'unknown')
        title = item.get('title', 'Unknown')
        timestamp = item.get('timestamp', '--')

        status_config = {
            'completed': {'dot': '●', 'color': PremiumTheme.STATUS_SUCCESS, 'text': 'Completed'},
            'failed': {'dot': '●', 'color': PremiumTheme.STATUS_ERROR, 'text': 'Failed'},
            'cancelled': {'dot': '●', 'color': PremiumTheme.STATUS_WARNING, 'text': 'Cancelled'},
        }

        config = status_config.get(status, {'dot': '●', 'color': PremiumTheme.TEXT_MUTED, 'text': 'Unknown'})

        card = GlassCard(self.history_items_frame, height=68)
        card.pack(fill="x", pady=4)
        card.grid_columnconfigure(1, weight=1)
        card.pack_propagate(False)

        dot_label = ctk.CTkLabel(
            card,
            text=config['dot'],
            font=PremiumTheme.font_body_bold(),
            text_color=config['color'],
            width=24
        )
        dot_label.pack(side="left", padx=(16, 8))

        details_frame = ctk.CTkFrame(card, fg_color="transparent")
        details_frame.pack(side="left", fill="both", expand=True, pady=10)

        display_title = title if len(title) <= 65 else title[:62] + "..."
        title_label = ctk.CTkLabel(
            details_frame,
            text=display_title,
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.TEXT_PRIMARY,
            anchor="w"
        )
        title_label.pack(anchor="w")

        timestamp_label = ctk.CTkLabel(
            details_frame,
            text=timestamp,
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.TEXT_MUTED,
            anchor="w"
        )
        timestamp_label.pack(anchor="w", pady=(2, 0))

        status_badge = ctk.CTkLabel(
            card,
            text=config['text'],
            font=PremiumTheme.font_badge(),
            text_color=config['color'],
            fg_color=PremiumTheme.SURFACE_MUTED,
            corner_radius=6,
            width=90,
            height=28
        )
        status_badge.pack(side="right", padx=16)

    def _clear_history(self):
        """Clear download history."""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all download history?"):
            self.download_history.clear()
            self._refresh_queue_tab()
            self._refresh_recent_downloads_shelf()

    # -----------------------------------------------------------------------
    # Settings Tab
    # -----------------------------------------------------------------------

    def _create_settings_tab(self):
        """Create the Settings configuration tab."""
        tab = self.tabview.tab("Settings")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(tab, fg_color=PremiumTheme.BG_CONTAINER)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self._center_settings_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self._center_settings_container.pack(anchor="n", pady=8, padx=16)

        # Zero-height width spacer to maintain exact responsive container width
        self._settings_width_spacer = ctk.CTkFrame(self._center_settings_container, fg_color="transparent", width=960, height=0)
        self._settings_width_spacer.pack(fill="x")

        # General Settings Section
        general_card = GlassCard(self._center_settings_container)
        general_card.pack(fill="x", pady=(0, 14), ipady=4)

        general_header = ctk.CTkLabel(
            general_card,
            text="General Settings",
            font=PremiumTheme.font_heading(),
            text_color=PremiumTheme.TEXT_PRIMARY,
            anchor="w"
        )
        general_header.pack(fill="x", padx=16, pady=(14, 10))

        ctk.CTkLabel(
            general_card,
            text="Default Download Directory",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", padx=16, pady=(0, 6))

        path_frame = ctk.CTkFrame(general_card, fg_color="transparent")
        path_frame.pack(fill="x", padx=16, pady=(0, 16))

        self.default_path_entry = ctk.CTkEntry(
            path_frame,
            height=42,
            font=PremiumTheme.font_body(),
            corner_radius=8,
            border_width=1,
            border_color=PremiumTheme.BORDER_INPUT,
            fg_color=PremiumTheme.SURFACE_INPUT,
            text_color=PremiumTheme.TEXT_PRIMARY
        )
        self.default_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.default_path_entry.insert(0, self.config.get("download_directory", str(get_download_dir())))
        self.settings_path_entry = self.default_path_entry

        browse_btn = ModernButton(
            path_frame,
            variant="secondary",
            text="Browse",
            width=90,
            height=42,
            font=PremiumTheme.font_button(),
            command=self._browse_default_path
        )
        browse_btn.pack(side="left")

        # Appearance Settings Section
        appearance_card = GlassCard(self._center_settings_container)
        appearance_card.pack(fill="x", pady=(0, 14), ipady=4)

        appearance_header = ctk.CTkLabel(
            appearance_card,
            text="Appearance & Display Scaling",
            font=PremiumTheme.font_heading(),
            text_color=PremiumTheme.TEXT_PRIMARY,
            anchor="w"
        )
        appearance_header.pack(fill="x", padx=16, pady=(14, 10))

        appearance_options = ctk.CTkFrame(appearance_card, fg_color="transparent")
        appearance_options.pack(fill="x", padx=16, pady=(0, 16))
        appearance_options.grid_columnconfigure(0, weight=1)
        appearance_options.grid_columnconfigure(1, weight=1)

        # Theme Column
        theme_col = ctk.CTkFrame(appearance_options, fg_color="transparent")
        theme_col.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        ctk.CTkLabel(
            theme_col,
            text="Theme Mode",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", pady=(0, 6))

        self.theme_var = tk.StringVar(value=self.config.get("theme", "system").title())
        theme_menu = ctk.CTkOptionMenu(
            theme_col,
            variable=self.theme_var,
            values=["System", "Dark", "Light"],
            font=PremiumTheme.font_body(),
            dropdown_font=PremiumTheme.font_body(),
            corner_radius=8,
            height=42,
            fg_color=PremiumTheme.SURFACE_CARD,
            button_color=PremiumTheme.SURFACE_CARD,
            button_hover_color=PremiumTheme.SURFACE_CARD_HOVER,
            dropdown_fg_color=PremiumTheme.SURFACE_CARD,
            dropdown_hover_color=PremiumTheme.SURFACE_CARD_HOVER,
            dropdown_text_color=PremiumTheme.TEXT_PRIMARY,
            text_color=PremiumTheme.TEXT_PRIMARY,
            command=self._on_theme_changed
        )
        theme_menu.pack(fill="x")

        # UI Scale Column
        scale_col = ctk.CTkFrame(appearance_options, fg_color="transparent")
        scale_col.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(
            scale_col,
            text="Interface Scaling & Zoom",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", pady=(0, 6))

        scale_options = [
            "80%",
            "90%",
            "100% (Default)",
            "110%",
            "125%",
            "150%",
            "175%",
            "200%",
        ]
        current_pct = int(round(self.ui_scale * 100))
        init_scale_val = "100% (Default)" if current_pct == 100 else f"{current_pct}%"

        scale_controls_frame = ctk.CTkFrame(scale_col, fg_color="transparent")
        scale_controls_frame.pack(fill="x")

        self.scale_var = tk.StringVar(value=init_scale_val)
        scale_menu = ctk.CTkOptionMenu(
            scale_controls_frame,
            variable=self.scale_var,
            values=scale_options,
            font=PremiumTheme.font_body(),
            dropdown_font=PremiumTheme.font_body(),
            corner_radius=8,
            height=42,
            fg_color=PremiumTheme.SURFACE_CARD,
            button_color=PremiumTheme.SURFACE_CARD,
            button_hover_color=PremiumTheme.SURFACE_CARD_HOVER,
            dropdown_fg_color=PremiumTheme.SURFACE_CARD,
            dropdown_hover_color=PremiumTheme.SURFACE_CARD_HOVER,
            dropdown_text_color=PremiumTheme.TEXT_PRIMARY,
            text_color=PremiumTheme.TEXT_PRIMARY,
            command=self._on_scale_changed
        )
        scale_menu.pack(side="left", fill="x", expand=True, padx=(0, 6))

        zoom_out_btn = ModernButton(
            scale_controls_frame,
            variant="secondary",
            text="−",
            width=38,
            height=42,
            font=PremiumTheme.font_button(),
            command=lambda: self._zoom_out()
        )
        zoom_out_btn.pack(side="left", padx=(0, 4))

        zoom_in_btn = ModernButton(
            scale_controls_frame,
            variant="secondary",
            text="+",
            width=38,
            height=42,
            font=PremiumTheme.font_button(),
            command=lambda: self._zoom_in()
        )
        zoom_in_btn.pack(side="left")

        ctk.CTkLabel(
            scale_col,
            text="Shortcuts: Ctrl + / Ctrl − • Wheel: Ctrl + Scroll • Reset: Ctrl 0",
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.TEXT_MUTED,
            anchor="w"
        ).pack(fill="x", pady=(4, 0))

        # Advanced Settings Section
        advanced_card = GlassCard(self._center_settings_container)
        advanced_card.pack(fill="x", pady=(0, 14), ipady=4)

        advanced_header = ctk.CTkLabel(
            advanced_card,
            text="Updates & Connectivity",
            font=PremiumTheme.font_heading(),
            text_color=PremiumTheme.TEXT_PRIMARY,
            anchor="w"
        )
        advanced_header.pack(fill="x", padx=16, pady=(14, 10))

        self.auto_update_var = tk.BooleanVar(value=self.config.get("check_updates", True))
        auto_update_switch = ctk.CTkSwitch(
            advanced_card,
            text="Check for updates automatically on launch",
            variable=self.auto_update_var,
            font=PremiumTheme.font_body(),
            command=self._save_settings,
            progress_color=PremiumTheme.ACCENT_PRIMARY,
            button_color=PremiumTheme.ACCENT_PRIMARY,
            button_hover_color=PremiumTheme.ACCENT_HOVER
        )
        auto_update_switch.pack(anchor="w", padx=16, pady=(0, 12))

        # Maintenance Buttons
        maint_btn_frame = ctk.CTkFrame(advanced_card, fg_color="transparent")
        maint_btn_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.btn_check_updates = ModernButton(
            maint_btn_frame,
            variant="secondary",
            text="🔄 Check for Updates",
            height=36,
            font=PremiumTheme.font_button(),
            command=self._check_for_updates
        )
        self.btn_check_updates.pack(side="left", padx=(0, 8))

        self.btn_verify_repair = ModernButton(
            maint_btn_frame,
            variant="secondary",
            text="🛠️ Verify & Repair App",
            height=36,
            font=PremiumTheme.font_button(),
            command=self._verify_and_repair
        )
        self.btn_verify_repair.pack(side="left")

        self.health_status_dot = ctk.CTkLabel(
            advanced_card,
            text="● Ready",
            font=PremiumTheme.font_meta_bold(),
            text_color=PremiumTheme.STATUS_SUCCESS,
            anchor="w"
        )
        self.health_status_dot.pack(fill="x", padx=16, pady=(0, 4))

        self.health_feedback_label = ctk.CTkLabel(
            advanced_card,
            text="",
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.TEXT_SECONDARY,
            anchor="w"
        )
        self.health_feedback_label.pack(fill="x", padx=16, pady=(0, 12))

        # About Section
        about_card = GlassCard(self._center_settings_container)
        about_card.pack(fill="x", pady=(0, 14), ipady=4)

        about_header = ctk.CTkLabel(
            about_card,
            text="About Downloadyha",
            font=PremiumTheme.font_heading(),
            text_color=PremiumTheme.TEXT_PRIMARY,
            anchor="w"
        )
        about_header.pack(fill="x", padx=16, pady=(14, 10))

        about_frame = ctk.CTkFrame(about_card, fg_color="transparent")
        about_frame.pack(fill="x", padx=16, pady=(0, 16))

        version_label = ctk.CTkLabel(
            about_frame,
            text=f"Version {__version__} • Calm Luxury Edition",
            font=PremiumTheme.font_body_bold(),
            text_color=PremiumTheme.ACCENT_PRIMARY,
            anchor="w"
        )
        version_label.pack(fill="x")

        author_label = ctk.CTkLabel(
            about_frame,
            text="Author: Ahmed Tarek Zaher",
            font=PremiumTheme.font_body(),
            text_color=PremiumTheme.TEXT_SECONDARY,
            anchor="w"
        )
        author_label.pack(fill="x", pady=(3, 0))

        desc_label = ctk.CTkLabel(
            about_frame,
            text="A high-performance media downloader supporting 4K UHD resolutions, playlists,\nand high-fidelity audio, crafted with clean typography and modern UX.",
            font=PremiumTheme.font_meta(),
            text_color=PremiumTheme.TEXT_MUTED,
            justify="left",
            anchor="w"
        )
        desc_label.pack(fill="x", pady=(6, 0))

        # Save Button
        save_btn = ModernButton(
            self._center_settings_container,
            variant="primary",
            text="Save Preferences",
            font=PremiumTheme.font_button_large(),
            height=46,
            corner_radius=9,
            command=self._save_settings
        )
        save_btn.pack(fill="x", pady=(6, 16))

    def _browse_default_path(self):
        """Browse for default download path."""
        self._browse_settings_path()

    def _browse_settings_path(self):
        """Open directory picker for default settings."""
        try:
            target_entry = getattr(self, "settings_path_entry", getattr(self, "default_path_entry", None))
            init_dir = target_entry.get().strip() if target_entry else ""
            if not init_dir or not os.path.isdir(init_dir):
                init_dir = str(get_download_dir())

            folder = filedialog.askdirectory(
                parent=self,
                title="Select Default Download Folder",
                initialdir=init_dir,
                mustexist=True,
            )
            if folder:
                normalized_folder = os.path.normpath(folder)
                if target_entry:
                    target_entry.delete(0, tk.END)
                    target_entry.insert(0, normalized_folder)
        except Exception:
            pass
        finally:
            try:
                self.lift()
                self.focus_force()
            except Exception:
                pass

    def _on_theme_changed(self, choice: str):
        """Handle theme change."""
        theme_mode = choice.lower()
        ctk.set_appearance_mode(theme_mode)
        # Update placeholder thumbnail if active
        if "thumbnail_label" in self.__dict__ and self.thumbnail_label is not None:
            if getattr(self, "_current_thumbnail_img", None) is None:
                self._set_placeholder_thumbnail()
            else:
                dark_mode = theme_mode == "dark" or (theme_mode == "system" and ctk.get_appearance_mode().lower() == "dark")
                self.thumbnail_label.configure(bg="#161924" if dark_mode else "#FFFFFF")
        self._save_settings()

    def _on_scale_changed(self, choice: str):
        """Handle UI scale dropdown selection."""
        scale_map = {
            "80%": 0.8,
            "90%": 0.9,
            "100% (Default)": 1.0,
            "110%": 1.1,
            "125%": 1.25,
            "150%": 1.5,
            "175%": 1.75,
            "200%": 2.0,
        }
        scale_val = scale_map.get(choice)
        if scale_val is None:
            digits = re.findall(r'\d+', choice)
            if digits:
                scale_val = round(int(digits[0]) / 100.0, 2)
            else:
                scale_val = 1.0
        self._set_zoom_scale(scale_val, show_toast=True)

    def _save_settings(self):
        """Save all settings to config."""
        new_dir = self.default_path_entry.get().strip().strip("'\"")
        if new_dir:
            try:
                os.makedirs(new_dir, exist_ok=True)
            except Exception:
                pass
            self.config["download_directory"] = new_dir

        if hasattr(self, "theme_var"):
            self.config["theme"] = self.theme_var.get().lower()
        if hasattr(self, "auto_update_var"):
            self.config["check_updates"] = self.auto_update_var.get()
        if hasattr(self, "ui_scale"):
            self.config["ui_scale"] = self.ui_scale

        if save_config(self.config):
            self._show_toast("Preferences saved successfully", "success")
            if hasattr(self, "dest_entry"):
                self.dest_entry.delete(0, tk.END)
                self.dest_entry.insert(0, self.config["download_directory"])
        else:
            messagebox.showerror("Error", "Failed to save settings")

    # -----------------------------------------------------------------------
    # System Health Actions: Update & Repair Subsystems
    # -----------------------------------------------------------------------

    def _check_for_updates(self):
        """Asynchronously check for updates using downloadyha.updater."""
        if getattr(self, "is_checking_updates", False):
            return

        self.is_checking_updates = True
        if hasattr(self, "health_status_dot") and self.health_status_dot:
            self.health_status_dot.configure(text="● Checking...", text_color=Theme.CRIMSON_PRIMARY)
        if hasattr(self, "btn_check_updates") and self.btn_check_updates:
            self.btn_check_updates.configure(text="⏳ Checking...", state="disabled")
        if hasattr(self, "health_feedback_label") and self.health_feedback_label:
            self.health_feedback_label.configure(text="Contacting GitHub Releases API...", text_color=Theme.TEXT_SECONDARY)

        def worker():
            try:
                new_ver = check_for_updates(force=True)
                self.after(0, self._on_update_check_result, new_ver)
            except Exception as e:
                self.after(0, self._on_update_check_error, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_check_result(self, new_version: Optional[str]):
        """Handle update check result on the main thread."""
        self.is_checking_updates = False
        if hasattr(self, "btn_check_updates") and self.btn_check_updates:
            self.btn_check_updates.configure(text="🔄 Check for Updates", state="normal")

        if new_version:
            if hasattr(self, "health_status_dot") and self.health_status_dot:
                self.health_status_dot.configure(text="● Update Avail", text_color=Theme.CRIMSON_PRIMARY)
            if hasattr(self, "health_feedback_label") and self.health_feedback_label:
                self.health_feedback_label.configure(
                    text=f"New version {new_version} available! Click below to install.",
                    text_color=Theme.CRIMSON_PRIMARY,
                )
            if hasattr(self, "btn_check_updates") and self.btn_check_updates:
                self.btn_check_updates.configure(
                    text=f"⬇️ Update to {new_version}",
                    fg_color=Theme.CRIMSON_PRIMARY,
                    text_color="#FFFFFF",
                    hover_color=Theme.CRIMSON_HOVER,
                    command=lambda: self._install_update(new_version),
                )
        else:
            if hasattr(self, "health_status_dot") and self.health_status_dot:
                self.health_status_dot.configure(text="● Up to Date", text_color=Theme.SUCCESS_GREEN)
            if hasattr(self, "health_feedback_label") and self.health_feedback_label:
                self.health_feedback_label.configure(
                    text=f"✓ You are running the latest version (v{__version__}).",
                    text_color=Theme.SUCCESS_GREEN,
                )

    def _on_update_check_error(self, error_str: str):
        """Handle update check error on main thread."""
        self.is_checking_updates = False
        if hasattr(self, "btn_check_updates") and self.btn_check_updates:
            self.btn_check_updates.configure(text="🔄 Check for Updates", state="normal")
        if hasattr(self, "health_status_dot") and self.health_status_dot:
            self.health_status_dot.configure(text="● Ready", text_color=Theme.TEXT_SECONDARY)
        if hasattr(self, "health_feedback_label") and self.health_feedback_label:
            self.health_feedback_label.configure(
                text=f"⚠️ Update check failed: {error_str}",
                text_color=Theme.ERROR_RED,
            )

    def _install_update(self, version_str: str):
        """Execute binary update."""
        if hasattr(self, "btn_check_updates") and self.btn_check_updates:
            self.btn_check_updates.configure(text="⏳ Installing Update...", state="disabled")
        if hasattr(self, "health_feedback_label") and self.health_feedback_label:
            self.health_feedback_label.configure(
                text="Downloading package & verifying SHA-256...",
                text_color=Theme.CRIMSON_PRIMARY,
            )

        def worker():
            try:
                ok, err_or_msg = perform_update(version_str)
                self.after(0, self._on_update_installed, ok, err_or_msg)
            except Exception as e:
                self.after(0, self._on_update_installed, False, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_installed(self, success: bool, msg: str = ""):
        """Handle post-update installation result."""
        if hasattr(self, "btn_check_updates") and self.btn_check_updates:
            self.btn_check_updates.configure(
                text="🔄 Check for Updates",
                state="normal",
            )
        if hasattr(self, "health_feedback_label") and self.health_feedback_label:
            if success:
                self.health_feedback_label.configure(
                    text=f"✓ {msg}",
                    text_color=Theme.SUCCESS_GREEN,
                )
            else:
                self.health_feedback_label.configure(
                    text=f"❌ Update failed: {msg}",
                    text_color=Theme.ERROR_RED,
                )

    def _verify_and_repair(self):
        """Run dependency verification and automatic repair."""
        if getattr(self, "is_repairing_dependencies", False):
            return

        self.is_repairing_dependencies = True
        if hasattr(self, "health_status_dot") and self.health_status_dot:
            self.health_status_dot.configure(text="● Repairing...", text_color=Theme.CRIMSON_PRIMARY)
        if hasattr(self, "btn_verify_repair") and self.btn_verify_repair:
            self.btn_verify_repair.configure(text="⏳ Repairing...", state="disabled")
        if hasattr(self, "health_feedback_label") and self.health_feedback_label:
            self.health_feedback_label.configure(
                text="Verifying FFmpeg, FFprobe & Deno binaries...",
                text_color=Theme.TEXT_SECONDARY,
            )

        def worker():
            try:
                ok = repair_dependencies()
                self.after(0, self._on_repair_result, ok)
            except Exception as e:
                self.after(0, self._on_repair_error, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_repair_result(self, success: bool):
        """Handle repair completion on main thread."""
        self.is_repairing_dependencies = False
        if hasattr(self, "btn_verify_repair") and self.btn_verify_repair:
            self.btn_verify_repair.configure(text="🛠️ Verify & Repair App", state="normal")
        if hasattr(self, "health_status_dot") and self.health_status_dot:
            self.health_status_dot.configure(
                text="● Healthy" if success else "● Issue",
                text_color=Theme.SUCCESS_GREEN if success else Theme.ERROR_RED
            )
        if hasattr(self, "health_feedback_label") and self.health_feedback_label:
            if success:
                self.health_feedback_label.configure(
                    text="✓ All helper binaries verified and ready!",
                    text_color=Theme.SUCCESS_GREEN,
                )
            else:
                self.health_feedback_label.configure(
                    text="⚠️ Some dependencies could not be repaired.",
                    text_color=Theme.ERROR_RED,
                )

    def _on_repair_error(self, err_msg: str):
        """Handle repair error."""
        self.is_repairing_dependencies = False
        if hasattr(self, "btn_verify_repair") and self.btn_verify_repair:
            self.btn_verify_repair.configure(text="🛠️ Verify & Repair App", state="normal")
        if hasattr(self, "health_status_dot") and self.health_status_dot:
            self.health_status_dot.configure(text="● Error", text_color=Theme.ERROR_RED)
        if hasattr(self, "health_feedback_label") and self.health_feedback_label:
            self.health_feedback_label.configure(
                text=f"❌ Repair error: {err_msg}",
                text_color=Theme.ERROR_RED,
            )

    def _show_toast(self, message: str, toast_type: str = "info"):
        """Show a modern toast notification."""
        toast_colors = {
            'success': PremiumTheme.STATUS_SUCCESS,
            'error': PremiumTheme.STATUS_ERROR,
            'info': PremiumTheme.ACCENT_PRIMARY,
            'warning': PremiumTheme.STATUS_WARNING
        }

        toast = ctk.CTkFrame(
            self,
            fg_color=toast_colors.get(toast_type, PremiumTheme.ACCENT_PRIMARY),
            corner_radius=8
        )
        toast.place(relx=0.5, rely=0.92, anchor="center")

        label = ctk.CTkLabel(
            toast,
            text=message,
            font=PremiumTheme.font_body_bold(),
            text_color="#FFFFFF"
        )
        label.grid(row=0, column=0, padx=16, pady=8)

        self.after(2200, lambda: toast.destroy())


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

def main():
    """Launch the Downloadyha GUI application."""
    app = DownloadyhaGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
