"""
app.py - Main Desktop GUI Application for Downloadyha

Built with CustomTkinter for modern, cross-platform aesthetics with:
- Video info fetching with title, channel, duration, views & available resolution extraction
- Multi-platform support (YouTube, TikTok, Facebook, Instagram, Twitter/X, and more)
- Dynamic quality dropdown matching available video heights (e.g. 4K, 2K, 1080p, 720p, 480p, 360p)
- Audio MP3 bitrate options (Best VBR, 320k, 192k, 128k)
- Playlist detection and support (video & audio)
- Tab-based interface (Download, Queue / History, Settings)
- Real-time download progress with speed, ETA, and playlist item tracker
- Theme switching (Dark/Light/System)
- Modern glassmorphism cyber design
"""

from __future__ import annotations

import os
import re
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional, Tuple

import customtkinter as ctk

# Import downloadyha core engine
try:
    from downloadyha import __version__
    from downloadyha.config import get_download_dir, load as load_config, save as save_config
    from downloadyha.dependencies import check_dependencies, check_ffmpeg
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
    )
    from downloadyha.ui import format_duration, format_number
except ImportError:
    # Fallback for direct execution during development
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from downloadyha import __version__
    from downloadyha.config import get_download_dir, load as load_config, save as save_config
    from downloadyha.dependencies import check_dependencies, check_ffmpeg
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
    )
    from downloadyha.ui import format_duration, format_number


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
# Theme & Color Palette (Enhanced Modern Design)
# ---------------------------------------------------------------------------

class Theme:
    """Downloadyha brand color palette with modern cyber aesthetics."""
    # Primary Cyber Theme Colors (RGB tuples)
    ELECTRIC_CYAN = (0, 210, 255)
    CYBER_PURPLE = (155, 81, 224)
    EMERALD_GREEN = (46, 204, 113)
    AMBER_YELLOW = (241, 196, 15)
    CRIMSON_RED = (231, 76, 60)

    # Extended palette for gradients and accents
    DEEP_PURPLE = (102, 51, 153)
    LIGHT_CYAN = (128, 230, 255)
    DARK_BG = (18, 18, 24)
    CARD_BG = (30, 30, 42)
    CARD_BG_LIGHT = (45, 45, 65)

    # Status colors
    WARNING_ORANGE = (255, 165, 0)
    INFO_BLUE = (52, 152, 219)

    @staticmethod
    def rgb_to_hex(rgb: tuple) -> str:
        """Convert RGB tuple to hex color string."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    @classmethod
    def get_accent_color(cls) -> str:
        """Primary accent color for buttons and highlights."""
        return cls.rgb_to_hex(cls.ELECTRIC_CYAN)

    @classmethod
    def get_success_color(cls) -> str:
        """Success state color."""
        return cls.rgb_to_hex(cls.EMERALD_GREEN)

    @classmethod
    def get_error_color(cls) -> str:
        """Error state color."""
        return cls.rgb_to_hex(cls.CRIMSON_RED)

    @classmethod
    def get_warning_color(cls) -> str:
        """Warning state color."""
        return cls.rgb_to_hex(cls.WARNING_ORANGE)

    @classmethod
    def get_gradient_colors(cls) -> list:
        """Get gradient colors for animated effects."""
        return [cls.ELECTRIC_CYAN, cls.CYBER_PURPLE]

    @classmethod
    def get_card_bg(cls, dark_mode: bool = True) -> str:
        """Get card background color based on theme."""
        return cls.rgb_to_hex(cls.CARD_BG if dark_mode else (240, 240, 245))

    @classmethod
    def get_glassmorphism_bg(cls, dark_mode: bool = True) -> str:
        """Get glassmorphism-style semi-transparent background."""
        return cls.rgb_to_hex(cls.CARD_BG_LIGHT if dark_mode else (255, 255, 255))


# ---------------------------------------------------------------------------
# Modern Styled Components
# ---------------------------------------------------------------------------

class ModernButton(ctk.CTkButton):
    """Button with modern defaults and hover styling."""

    def __init__(self, master, gradient_hover: bool = True, **kwargs):
        # Set modern defaults
        if 'corner_radius' not in kwargs:
            kwargs['corner_radius'] = 12
        if 'border_width' not in kwargs:
            kwargs['border_width'] = 0
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = Theme.get_accent_color()
        if 'hover_color' not in kwargs:
            kwargs['hover_color'] = Theme.rgb_to_hex(Theme.CYBER_PURPLE)

        super().__init__(master, **kwargs)


class GlassCard(ctk.CTkFrame):
    """Frame with glassmorphism styling and subtle borders."""

    def __init__(self, master, **kwargs):
        # Modern card defaults
        if 'corner_radius' not in kwargs:
            kwargs['corner_radius'] = 14
        if 'border_width' not in kwargs:
            kwargs['border_width'] = 1
        if 'border_color' not in kwargs:
            kwargs['border_color'] = Theme.rgb_to_hex((60, 60, 80))

        # Get appropriate background
        dark_mode = ctk.get_appearance_mode().lower() == "dark"
        if 'fg_color' not in kwargs:
            kwargs['fg_color'] = Theme.get_card_bg(dark_mode)

        super().__init__(master, **kwargs)


class AnimatedProgressBar(ctk.CTkProgressBar):
    """Progress bar with animated gradient effect."""

    def __init__(self, master, **kwargs):
        if 'corner_radius' not in kwargs:
            kwargs['corner_radius'] = 10

        super().__init__(master, **kwargs)

        self._animation_running = False
        self._animation_id = None

        # Set gradient colors
        self.configure(
            progress_color=Theme.get_accent_color(),
            fg_color=Theme.rgb_to_hex((40, 40, 55))
        )

    def start_animation(self):
        """Start animated gradient effect during download."""
        self._animation_running = True
        self._animate_gradient()

    def stop_animation(self):
        """Stop the gradient animation."""
        self._animation_running = False
        if self._animation_id:
            try:
                self.after_cancel(self._animation_id)
            except Exception:
                pass

    def _animate_gradient(self):
        """Cycle through gradient colors."""
        if not self._animation_running:
            return

        colors = [Theme.ELECTRIC_CYAN, Theme.CYBER_PURPLE]
        current = self.cget('progress_color')

        if current == Theme.rgb_to_hex(colors[0]):
            next_color = Theme.rgb_to_hex(colors[1])
        else:
            next_color = Theme.rgb_to_hex(colors[0])

        self.configure(progress_color=next_color)
        self._animation_id = self.after(500, self._animate_gradient)


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
            'url': url,
            'title': title,
            'status': status,
            'file_path': file_path,
            'timestamp': self._get_timestamp()
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


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class DownloadyhaGUI(ctk.CTk):
    """Main GUI Application Window with Modern Cyber Design."""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title(f"Downloadyha v{__version__} - Video & Media Downloader")
        self.geometry("960x780")
        self.minsize(900, 720)
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

        # Download history
        self.download_history = DownloadHistory()

        # Apply theme from config or system default
        self._setup_theme()

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create main UI
        self._create_widgets()

        # Set icon if available
        self._set_window_icon()

        # Ensure dependencies (FFmpeg, Deno) are available in background
        self._prepare_dependencies_async()

    def _prepare_dependencies_async(self):
        """Ensure FFmpeg and Deno dependencies are available in background."""
        def worker():
            try:
                check_dependencies(auto_download=True)
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _setup_theme(self):
        """Configure application theme with modern styling."""
        theme_mode = self.config.get("theme", "system")
        ctk.set_appearance_mode(theme_mode)
        ctk.set_default_color_theme("blue")

        # Apply custom window background
        dark_mode = ctk.get_appearance_mode().lower() == "dark"
        bg_color = Theme.rgb_to_hex(Theme.DARK_BG if dark_mode else (245, 245, 250))
        self.configure(fg_color=bg_color)

    def _set_window_icon(self):
        """Set window icon if available."""
        try:
            potential_paths = [
                Path(__file__).parent / "resources" / "icon.ico",
                Path(__file__).resolve().parent.parent.parent / "assets" / "icons" / "downloadyha.ico",
                Path(__file__).resolve().parent.parent.parent / "assets" / "icons" / "app_icon_256.png",
            ]
            for icon_path in potential_paths:
                if icon_path.exists():
                    if icon_path.suffix == ".ico":
                        self.iconbitmap(str(icon_path))
                    else:
                        photo = tk.PhotoImage(file=str(icon_path))
                        self.wm_iconphoto(True, photo)
                    break
        except Exception:
            pass

    def _create_widgets(self):
        """Build main UI components with modern styling."""
        # Main container with responsive padding
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        # Create tabview for main sections
        self.tabview = ctk.CTkTabview(
            main_container,
            corner_radius=16,
            border_width=2,
            segmented_button_fg_color=Theme.get_card_bg(True),
            segmented_button_selected_color=Theme.get_accent_color(),
            segmented_button_selected_hover_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            segmented_button_unselected_color=Theme.rgb_to_hex(Theme.CARD_BG_LIGHT)
        )
        self.tabview.grid(row=0, column=0, sticky="nsew")

        # Add tabs
        self.tabview.add("⬇️ Download")
        self.tabview.add("📋 Queue")
        self.tabview.add("⚙️ Settings")

        # Configure tab content
        self._create_download_tab()
        self._create_queue_tab()
        self._create_settings_tab()

        # Set default tab
        self.tabview.set("⬇️ Download")

        # Copyright footer
        copyright_label = ctk.CTkLabel(
            main_container,
            text="© 2026 Ahmed Tarek Zaher. All rights reserved.",
            font=ctk.CTkFont(size=11),
            text_color=Theme.rgb_to_hex((100, 100, 120))
        )
        copyright_label.grid(row=1, column=0, pady=(4, 8), sticky="ew")

    def _create_compact_header(self, parent):
        """Create compact header with title and status."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent", height=32)
        header_frame.grid(row=0, column=0, padx=10, pady=(2, 2), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_propagate(False)

        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🎬 Downloadyha - Video & Media Downloader",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=Theme.get_accent_color()
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Status indicator
        self.status_indicator = ctk.CTkLabel(
            header_frame,
            text="● Ready",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.get_success_color()
        )
        self.status_indicator.grid(row=0, column=1, sticky="e")

    # -----------------------------------------------------------------------
    # Download Tab
    # -----------------------------------------------------------------------

    def _create_download_tab(self):
        """Create the main Download tab interface with metadata display and dynamic qualities."""
        tab = self.tabview.tab("⬇️ Download")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_propagate(True)

        # Main vertical container
        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.grid(row=0, column=0, padx=10, pady=4, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)

        # Header (row 0)
        self._create_compact_header(container)

        # URL Input Section (row 1 & 2)
        url_label_frame = ctk.CTkFrame(container, fg_color="transparent")
        url_label_frame.grid(row=1, column=0, padx=10, pady=(4, 2), sticky="ew")
        url_label_frame.grid_columnconfigure(0, weight=1)

        url_label = ctk.CTkLabel(
            url_label_frame,
            text="🔗 Video, Audio, or Playlist URL:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        url_label.grid(row=0, column=0, sticky="w")

        url_input_frame = ctk.CTkFrame(container, fg_color="transparent")
        url_input_frame.grid(row=2, column=0, padx=10, pady=(2, 6), sticky="ew")
        url_input_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            url_input_frame,
            placeholder_text="Paste YouTube, TikTok, Instagram, Facebook, or other video URL...",
            height=36,
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            border_width=2,
            border_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE)
        )
        self.url_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.url_entry.bind("<Return>", lambda event: self._fetch_media_info())

        paste_btn = ModernButton(
            url_input_frame,
            text="📋 Paste",
            width=80,
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            hover_color=Theme.rgb_to_hex(Theme.DEEP_PURPLE),
            command=self._paste_url
        )
        paste_btn.grid(row=0, column=1, padx=(0, 6))

        self.fetch_btn = ModernButton(
            url_input_frame,
            text="🔍 Fetch Info",
            width=105,
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=Theme.get_accent_color(),
            hover_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            text_color="black",
            command=self._fetch_media_info
        )
        self.fetch_btn.grid(row=0, column=2)

        # Media Information Card (row 3)
        self.media_info_card = GlassCard(container, height=95)
        self.media_info_card.grid(row=3, column=0, padx=10, pady=(2, 6), sticky="ew")
        self.media_info_card.grid_columnconfigure(0, weight=1)
        self.media_info_card.grid_propagate(False)

        # Header row inside card (Badge + Channel)
        card_header_frame = ctk.CTkFrame(self.media_info_card, fg_color="transparent")
        card_header_frame.grid(row=0, column=0, padx=12, pady=(6, 2), sticky="ew")
        card_header_frame.grid_columnconfigure(1, weight=1)

        self.media_badge = ctk.CTkLabel(
            card_header_frame,
            text="💡 Ready",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=Theme.rgb_to_hex((45, 45, 65)),
            text_color="white",
            corner_radius=6,
            width=85,
            height=20
        )
        self.media_badge.grid(row=0, column=0, padx=(0, 8), sticky="w")

        self.media_channel_label = ctk.CTkLabel(
            card_header_frame,
            text="Paste a video or playlist link above and click 'Fetch Info' (or press Enter)",
            font=ctk.CTkFont(size=11),
            text_color=Theme.rgb_to_hex((150, 150, 170)),
            anchor="w"
        )
        self.media_channel_label.grid(row=0, column=1, sticky="w")

        # Title row inside card
        self.media_title_label = ctk.CTkLabel(
            self.media_info_card,
            text="No video analyzed yet",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.get_accent_color(),
            anchor="w"
        )
        self.media_title_label.grid(row=1, column=0, padx=12, pady=(1, 2), sticky="ew")

        # Metadata row inside card (duration, views, detected qualities)
        self.media_meta_label = ctk.CTkLabel(
            self.media_info_card,
            text="Available resolutions will appear in the dropdown once analyzed",
            font=ctk.CTkFont(size=10),
            text_color=Theme.rgb_to_hex((130, 130, 150)),
            anchor="w"
        )
        self.media_meta_label.grid(row=2, column=0, padx=12, pady=(1, 6), sticky="ew")

        # Options Section (row 4 & 5) - Media Type + Quality
        options_label_frame = ctk.CTkFrame(container, fg_color="transparent")
        options_label_frame.grid(row=4, column=0, padx=10, pady=(4, 2), sticky="ew")
        options_label_frame.grid_columnconfigure(0, weight=1)
        options_label_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            options_label_frame,
            text="⚡ Media Type:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            options_label_frame,
            text="Quality / Resolution:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=1, padx=(15, 0), sticky="w")

        options_frame = ctk.CTkFrame(container, fg_color="transparent")
        options_frame.grid(row=5, column=0, padx=10, pady=(2, 6), sticky="ew")
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)

        # Media type selector (Video/Audio)
        self.media_type_var = tk.StringVar(value="video")
        self.media_type_selector = ctk.CTkSegmentedButton(
            options_frame,
            values=["🎥 Video", "🎵 Audio"],
            variable=self.media_type_var,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_media_type_changed,
            corner_radius=8,
            fg_color=Theme.rgb_to_hex(Theme.CARD_BG_LIGHT),
            selected_color=Theme.get_accent_color(),
            selected_hover_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            unselected_color=Theme.rgb_to_hex((50, 50, 65))
        )
        self.media_type_selector.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        # Quality dropdown (OptionMenu)
        self.quality_var = tk.StringVar(value=DEFAULT_VIDEO_QUALITIES[0])
        self.quality_menu = ctk.CTkOptionMenu(
            options_frame,
            variable=self.quality_var,
            values=DEFAULT_VIDEO_QUALITIES,
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=10),
            corner_radius=8,
            height=36,
            fg_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            button_color=Theme.rgb_to_hex(Theme.DEEP_PURPLE),
            button_hover_color=Theme.rgb_to_hex(Theme.ELECTRIC_CYAN),
            dropdown_fg_color=Theme.rgb_to_hex(Theme.CARD_BG_LIGHT)
        )
        self.quality_menu.grid(row=0, column=1, sticky="ew")

        # Destination Folder Section (row 6 & 7)
        dest_label_frame = ctk.CTkFrame(container, fg_color="transparent")
        dest_label_frame.grid(row=6, column=0, padx=10, pady=(4, 2), sticky="ew")

        ctk.CTkLabel(
            dest_label_frame,
            text="💾 Save Location:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        dest_entry_frame = ctk.CTkFrame(container, fg_color="transparent")
        dest_entry_frame.grid(row=7, column=0, padx=10, pady=(2, 6), sticky="ew")
        dest_entry_frame.grid_columnconfigure(0, weight=1)

        self.dest_entry = ctk.CTkEntry(
            dest_entry_frame,
            height=36,
            font=ctk.CTkFont(size=11),
            corner_radius=8,
            border_width=2,
            border_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE)
        )
        self.dest_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.dest_entry.insert(0, self.config.get("download_directory", str(get_download_dir())))

        browse_btn = ModernButton(
            dest_entry_frame,
            text="📁 Browse",
            width=90,
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            hover_color=Theme.rgb_to_hex(Theme.DEEP_PURPLE),
            command=self._browse_destination
        )
        browse_btn.grid(row=0, column=1)

        # Progress Section (row 8)
        progress_frame = GlassCard(container, height=120)
        progress_frame.grid(row=8, column=0, padx=10, pady=(6, 6), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        progress_frame.grid_propagate(False)

        progress_header = ctk.CTkLabel(
            progress_frame,
            text="📊 Download Progress",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        progress_header.grid(row=0, column=0, padx=15, pady=(8, 2), sticky="w")

        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to download",
            font=ctk.CTkFont(size=11),
            anchor="w",
            text_color=Theme.get_success_color()
        )
        self.status_label.grid(row=1, column=0, padx=15, pady=(0, 4), sticky="w")

        # Animated progress bar
        self.progress_bar = AnimatedProgressBar(progress_frame, height=16)
        self.progress_bar.grid(row=2, column=0, padx=15, pady=2, sticky="ew")
        self.progress_bar.set(0)

        # Progress details (percentage, speed, ETA)
        details_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        details_frame.grid(row=3, column=0, padx=15, pady=(2, 8), sticky="ew")
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_columnconfigure(1, weight=1)
        details_frame.grid_columnconfigure(2, weight=1)

        self.percent_label = ctk.CTkLabel(
            details_frame,
            text="0%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.get_accent_color()
        )
        self.percent_label.grid(row=0, column=0, sticky="w")

        self.speed_label = ctk.CTkLabel(
            details_frame,
            text="⚡ Speed: --",
            font=ctk.CTkFont(size=11)
        )
        self.speed_label.grid(row=0, column=1)

        self.eta_label = ctk.CTkLabel(
            details_frame,
            text="⏱ ETA: --",
            font=ctk.CTkFont(size=11)
        )
        self.eta_label.grid(row=0, column=2, sticky="e")

        # Buttons Section (row 9)
        buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        buttons_frame.grid(row=9, column=0, padx=10, pady=(4, 4), sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(2, weight=1)

        # Download Button
        self.download_btn = ModernButton(
            buttons_frame,
            text="⬇ START DOWNLOAD",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=Theme.get_accent_color(),
            hover_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            command=self._start_download,
            border_width=2,
            border_color=Theme.rgb_to_hex(Theme.LIGHT_CYAN),
            text_color="black"
        )
        self.download_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        # Cancel Button
        self.cancel_btn = ModernButton(
            buttons_frame,
            text="❌ Cancel",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=Theme.get_error_color(),
            hover_color=Theme.rgb_to_hex((200, 50, 50)),
            command=self._cancel_download
        )
        self.cancel_btn.grid(row=0, column=1, padx=5, sticky="ew")

        # Open Folder Button
        self.open_folder_btn = ModernButton(
            buttons_frame,
            text="📁 Open Folder",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=10,
            fg_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            hover_color=Theme.rgb_to_hex(Theme.DEEP_PURPLE),
            command=self._open_download_folder
        )
        self.open_folder_btn.grid(row=0, column=2, padx=(5, 0), sticky="ew")

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
                # Automatically fetch if it looks like a web URL
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
        self.fetch_btn.configure(text="⏳ Fetching...", state="disabled")
        self.status_indicator.configure(text="● Analyzing...", text_color=Theme.get_accent_color())
        self.status_label.configure(
            text="⏳ Fetching media metadata and available qualities...",
            text_color=Theme.get_accent_color()
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
        """Handle successfully fetched media metadata."""
        self.media_info = info
        self.last_fetched_url = url
        self.is_fetching_info = False

        self.status_indicator.configure(text="● Ready", text_color=Theme.get_success_color())
        self.fetch_btn.configure(text="🔍 Fetch Info", state="normal")

        is_pl = is_playlist(info) or is_playlist_url(url)
        title = info.get("title") or "Media"
        uploader = info.get("uploader") or info.get("channel") or "Unknown Creator"

        if is_pl:
            entries = get_playlist_entries(info)
            count = len(entries) if entries else info.get("playlist_count", "Multiple")
            self.available_video_qualities = []

            self.media_badge.configure(
                text="📑 Playlist",
                fg_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
                text_color="white"
            )
            self.media_channel_label.configure(text=f"Channel: {uploader}")
            self.media_title_label.configure(text=f"📑 {title}")
            self.media_meta_label.configure(
                text=f"Total Items: {count} videos    |    Type: Playlist"
            )
        else:
            duration_sec = info.get("duration")
            duration_str = format_duration(duration_sec) if duration_sec else "Unknown"
            views_raw = info.get("view_count")
            views_str = f"{format_number(views_raw)} views" if views_raw else "N/A"

            self.available_video_qualities = get_video_qualities(info)
            max_q = f"{self.available_video_qualities[0]}p" if self.available_video_qualities else "Best"

            self.media_badge.configure(
                text="🎬 Single Video",
                fg_color=Theme.get_accent_color(),
                text_color="black"
            )
            self.media_channel_label.configure(text=f"Channel: {uploader}")
            self.media_title_label.configure(text=f"🎬 {title}")
            self.media_meta_label.configure(
                text=f"⏱ Duration: {duration_str}    |    👁 {views_str}    |    ⚡ Max Quality: {max_q}"
            )

        # Update quality dropdown with the actual available formats
        self._update_quality_options()

        self.status_label.configure(
            text=f"✅ Video info loaded: {title[:55]}{'...' if len(title) > 55 else ''}",
            text_color=Theme.get_success_color()
        )

    def _on_media_info_error(self, error: str):
        """Handle error during media metadata fetch."""
        self.is_fetching_info = False
        self.fetch_btn.configure(text="🔍 Fetch Info", state="normal")
        self.status_indicator.configure(text="● Ready", text_color=Theme.get_success_color())
        self.status_label.configure(
            text=f"⚠️ {error}",
            text_color=Theme.get_warning_color()
        )
        self._show_toast(f"Failed to fetch info: {error}", "error")

    def _update_quality_options(self):
        """Update quality dropdown values based on media type and fetched video info."""
        media_type = self.media_type_var.get().lower().replace("🎥 ", "").replace("🎵 ", "")

        if media_type == "audio":
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

    def _browse_destination(self):
        """Open folder picker dialog."""
        folder = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=self.dest_entry.get()
        )
        if folder:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, folder)

    # -----------------------------------------------------------------------
    # Download Execution Workflow
    # -----------------------------------------------------------------------

    def _start_download(self):
        """Start download process in background thread."""
        if self.is_downloading:
            return

        # Validate inputs
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a video or playlist URL")
            return

        dest_path = self.dest_entry.get().strip()
        if not dest_path:
            messagebox.showerror("Error", "Please select a download location")
            return

        if not os.path.isdir(dest_path):
            try:
                os.makedirs(dest_path, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create destination folder: {e}")
                return

        # Start download in background thread
        self.is_downloading = True
        self.cancel_requested = False
        self._reset_progress()
        self.status_label.configure(text="Starting download...", text_color=Theme.get_accent_color())
        self.status_indicator.configure(text="● Downloading", text_color=Theme.get_accent_color())
        self.progress_bar.start_animation()

        self.current_download_thread = threading.Thread(
            target=self._download_worker,
            args=(url, dest_path),
            daemon=True
        )
        self.current_download_thread.start()

    def _download_worker(self, url: str, dest_path: str):
        """Background worker executing the download."""
        try:
            # Ensure FFmpeg is present for merging video/audio streams into a single file
            ffmpeg_ok, _ = check_ffmpeg()
            if not ffmpeg_ok:
                self.after(0, self._update_status, "Preparing FFmpeg components for audio/video merging...")
                check_dependencies(auto_download=True)

            # If metadata was not fetched yet or URL changed, fetch it first
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

            # Get media type and parse quality
            media_type = self.media_type_var.get().lower().replace("🎥 ", "").replace("🎵 ", "")
            quality_str = self.quality_var.get()

            if media_type == "video":
                quality = self._parse_video_quality(quality_str)
            else:
                quality = self._parse_audio_quality(quality_str)

            # Progress callback
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
            if is_pl:
                quality_arg = str(quality) if (media_type == "video" and quality > 0) else ("best" if media_type == "video" else quality)
                result = download_playlist(
                    url=url,
                    download_path=dest_path,
                    media_type=media_type,
                    quality=quality_arg,
                    progress_callback=progress_callback
                )
            else:
                if media_type == "video":
                    result = download_video(
                        url=url,
                        download_path=dest_path,
                        height=quality,
                        progress_callback=progress_callback
                    )
                else:
                    result = download_audio(
                        url=url,
                        download_path=dest_path,
                        quality=quality,
                        progress_callback=progress_callback
                    )

            # Handle result
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
        """Parse quality label (e.g. '1080p (Full HD)', 'Best Available') into height integer."""
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
        """Parse audio quality label into bitrate string ('0', '320', '192', '128')."""
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
        self.speed_label.configure(text=f"⚡ Speed: {speed}")
        self.eta_label.configure(text=f"⏱ ETA: {eta}")

        if pl_idx and pl_count:
            status_text = f"Downloading [{pl_idx}/{pl_count}]: {item_title}" if item_title else f"Downloading playlist item {pl_idx} of {pl_count}..."
        elif item_title:
            status_text = f"Downloading: {item_title}"
        else:
            status_text = "Downloading media..."

        self.status_label.configure(text=status_text, text_color=Theme.get_accent_color())

    def _update_status(self, message: str):
        """Update status label."""
        self.status_label.configure(text=message, text_color=Theme.rgb_to_hex((150, 150, 170)))

    def _reset_progress(self):
        """Reset progress indicators."""
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.speed_label.configure(text="⚡ Speed: --")
        self.eta_label.configure(text="⏱ ETA: --")

    def _download_complete(self, result: DownloadResult):
        """Handle successful download completion."""
        self.is_downloading = False
        self.progress_bar.stop_animation()
        self.progress_bar.set(1.0)
        self.percent_label.configure(text="100%")
        self.status_indicator.configure(text="● Ready", text_color=Theme.get_success_color())

        url = self.url_entry.get().strip()
        if result.is_playlist:
            title = result.playlist_title or f"Playlist ({result.completed_items}/{result.total_items} items)"
            msg = f"Playlist download complete!\n\n{result.completed_items}/{result.total_items} items saved to:\n{result.download_directory}"
        else:
            title = (self.media_info.get("title") if self.media_info else None) or "Video / Audio"
            msg = f"Download complete!\n\nSaved to:\n{result.download_directory}"

        self.download_history.add_item(url, title, "completed", result.download_directory)
        self._refresh_queue_tab()

        self.status_label.configure(text="✅ Download completed successfully!", text_color=Theme.get_success_color())
        messagebox.showinfo("Success", msg)
        self._reset_progress()
        self.status_label.configure(text="Ready to download", text_color=Theme.get_success_color())

    def _download_failed(self, error: str):
        """Handle download failure."""
        self.is_downloading = False
        self.progress_bar.stop_animation()
        self.status_label.configure(text="❌ Download failed", text_color=Theme.get_error_color())
        self.status_indicator.configure(text="● Error", text_color=Theme.get_error_color())

        url = self.url_entry.get().strip()
        title = (self.media_info.get("title") if self.media_info else None) or "Failed Download"
        self.download_history.add_item(url, title, "failed")
        self._refresh_queue_tab()

        messagebox.showerror("Download Failed", f"An error occurred:\n\n{error}")
        self._reset_progress()
        self.status_label.configure(text="Ready to download", text_color=Theme.get_success_color())
        self.status_indicator.configure(text="● Ready", text_color=Theme.get_success_color())

    def _download_cancelled(self):
        """Handle download cancellation."""
        self.is_downloading = False
        self.cancel_requested = False
        self.progress_bar.stop_animation()
        self.status_label.configure(text="Download cancelled", text_color=Theme.get_warning_color())
        self.status_indicator.configure(text="● Ready", text_color=Theme.get_success_color())

        url = self.url_entry.get().strip()
        title = (self.media_info.get("title") if self.media_info else None) or "Cancelled Download"
        self.download_history.add_item(url, title, "cancelled")
        self._refresh_queue_tab()

        messagebox.showinfo("Cancelled", "Download was cancelled.")
        self._reset_progress()
        self.status_label.configure(text="Ready to download", text_color=Theme.get_success_color())

    def _cancel_download(self):
        """Cancel the running download."""
        if self.is_downloading:
            self.cancel_requested = True
            self.status_indicator.configure(text="● Cancelling", text_color=Theme.get_warning_color())
            self.status_label.configure(text="Cancelling download...", text_color=Theme.get_warning_color())

    def _open_download_folder(self):
        """Open the download folder in file explorer."""
        folder = self.dest_entry.get().strip()
        if folder and os.path.isdir(folder):
            try:
                if sys.platform == 'win32':
                    os.startfile(folder)
                elif sys.platform == 'darwin':
                    os.system(f'open "{folder}"')
                else:
                    os.system(f'xdg-open "{folder}"')
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open folder: {e}")
        else:
            messagebox.showerror("Error", "Download folder does not exist")

    # -----------------------------------------------------------------------
    # Queue Tab
    # -----------------------------------------------------------------------

    def _create_queue_tab(self):
        """Create the Queue management tab with download history."""
        tab = self.tabview.tab("📋 Queue")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(tab, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=15, pady=(15, 8), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)

        header = ctk.CTkLabel(
            header_frame,
            text="📋 Download History",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.grid(row=0, column=0, sticky="w")

        # Clear history button
        self.clear_history_btn = ModernButton(
            header_frame,
            text="🗑️ Clear All",
            width=100,
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color=Theme.get_error_color(),
            hover_color=Theme.rgb_to_hex((200, 50, 50)),
            command=self._clear_history
        )
        self.clear_history_btn.grid(row=0, column=1, padx=(15, 0), sticky="e")

        # Queue list with history (scrollable)
        self.queue_frame = ctk.CTkScrollableFrame(tab, corner_radius=12)
        self.queue_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.queue_frame.grid_columnconfigure(0, weight=1)

        # History container frame
        self.history_items_frame = ctk.CTkFrame(self.queue_frame, fg_color="transparent")
        self.history_items_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.history_items_frame.grid_columnconfigure(0, weight=1)

        # Initial placeholder
        self._show_history_placeholder()

    def _show_history_placeholder(self):
        """Show placeholder when no history exists."""
        for widget in self.history_items_frame.winfo_children():
            widget.destroy()

        placeholder = ctk.CTkLabel(
            self.history_items_frame,
            text="📭 No downloads yet\n\nYour download history will appear here.",
            font=ctk.CTkFont(size=13),
            text_color=Theme.rgb_to_hex((100, 100, 120)),
            justify="center"
        )
        placeholder.grid(row=0, column=0, pady=60)

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
            'completed': {'icon': '✅', 'color': Theme.get_success_color(), 'text': 'Completed'},
            'failed': {'icon': '❌', 'color': Theme.get_error_color(), 'text': 'Failed'},
            'cancelled': {'icon': '⚠️', 'color': Theme.get_warning_color(), 'text': 'Cancelled'},
        }

        config = status_config.get(status, {'icon': '❓', 'color': 'gray', 'text': 'Unknown'})

        card = GlassCard(self.history_items_frame, height=60)
        card.grid(row=row, column=0, padx=5, pady=4, sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        card.grid_propagate(False)

        icon_label = ctk.CTkLabel(
            card,
            text=config['icon'],
            font=ctk.CTkFont(size=20),
            width=40
        )
        icon_label.grid(row=0, column=0, padx=(12, 8), pady=12)

        details_frame = ctk.CTkFrame(card, fg_color="transparent")
        details_frame.grid(row=0, column=1, padx=8, pady=12, sticky="w")

        title_label = ctk.CTkLabel(
            details_frame,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w")

        timestamp_label = ctk.CTkLabel(
            details_frame,
            text=f"🕒 {timestamp}",
            font=ctk.CTkFont(size=10),
            text_color=Theme.rgb_to_hex((150, 150, 170)),
            anchor="w"
        )
        timestamp_label.grid(row=1, column=0, sticky="w")

        status_badge = ctk.CTkLabel(
            card,
            text=config['text'],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=config['color'],
            fg_color=Theme.rgb_to_hex((40, 40, 55)),
            corner_radius=6,
            width=90,
            height=26
        )
        status_badge.grid(row=0, column=2, padx=12, pady=12)

    def _clear_history(self):
        """Clear download history."""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all download history?"):
            self.download_history.clear()
            self._refresh_queue_tab()

    # -----------------------------------------------------------------------
    # Settings Tab
    # -----------------------------------------------------------------------

    def _create_settings_tab(self):
        """Create the Settings configuration tab."""
        tab = self.tabview.tab("⚙️ Settings")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        settings_container = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        settings_container.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        settings_container.grid_columnconfigure(0, weight=1)

        # General Settings Section
        general_card = GlassCard(settings_container)
        general_card.grid(row=0, column=0, padx=5, pady=(0, 10), sticky="ew")
        general_card.grid_columnconfigure(1, weight=1)

        general_header = ctk.CTkLabel(
            general_card,
            text="📁 General Settings",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        general_header.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

        # Default Download Path
        ctk.CTkLabel(
            general_card,
            text="Default Download Path:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")

        path_frame = ctk.CTkFrame(general_card, fg_color="transparent")
        path_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        path_frame.grid_columnconfigure(0, weight=1)

        self.default_path_entry = ctk.CTkEntry(
            path_frame,
            height=36,
            font=ctk.CTkFont(size=11),
            corner_radius=8,
            border_width=2,
            border_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE)
        )
        self.default_path_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.default_path_entry.insert(0, self.config.get("download_directory", str(get_download_dir())))

        browse_btn = ModernButton(
            path_frame,
            text="📁 Browse",
            width=90,
            height=36,
            font=ctk.CTkFont(size=11),
            fg_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            hover_color=Theme.rgb_to_hex(Theme.DEEP_PURPLE),
            command=self._browse_default_path
        )
        browse_btn.grid(row=0, column=1)

        # Appearance Settings Section
        appearance_card = GlassCard(settings_container)
        appearance_card.grid(row=1, column=0, padx=5, pady=10, sticky="ew")
        appearance_card.grid_columnconfigure(1, weight=1)

        appearance_header = ctk.CTkLabel(
            appearance_card,
            text="🎨 Appearance",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        appearance_header.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

        # Theme Settings
        ctk.CTkLabel(
            appearance_card,
            text="Theme Mode:",
            font=ctk.CTkFont(size=11, weight="bold")
        ).grid(row=1, column=0, padx=15, pady=(0, 5), sticky="w")

        self.theme_var = tk.StringVar(value=self.config.get("theme", "system").title())

        theme_frame = ctk.CTkFrame(appearance_card, fg_color="transparent")
        theme_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")

        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            variable=self.theme_var,
            values=["System", "Dark", "Light"],
            font=ctk.CTkFont(size=11),
            corner_radius=8,
            width=180,
            height=36,
            fg_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            button_color=Theme.rgb_to_hex(Theme.DEEP_PURPLE),
            button_hover_color=Theme.rgb_to_hex(Theme.ELECTRIC_CYAN),
            command=self._on_theme_changed
        )
        theme_menu.grid(row=0, column=0, sticky="w")

        # Advanced Settings Section
        advanced_card = GlassCard(settings_container)
        advanced_card.grid(row=2, column=0, padx=5, pady=10, sticky="ew")

        advanced_header = ctk.CTkLabel(
            advanced_card,
            text="⚡ Advanced",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        advanced_header.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        # Auto Update Toggle
        self.auto_update_var = tk.BooleanVar(value=self.config.get("check_updates", True))
        auto_update_switch = ctk.CTkSwitch(
            advanced_card,
            text="Enable automatic update checking",
            variable=self.auto_update_var,
            font=ctk.CTkFont(size=11),
            command=self._save_settings,
            progress_color=Theme.get_accent_color(),
            button_color=Theme.rgb_to_hex(Theme.ELECTRIC_CYAN),
            button_hover_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE)
        )
        auto_update_switch.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")

        # Save Button
        save_btn = ModernButton(
            settings_container,
            text="💾 SAVE SETTINGS",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            corner_radius=10,
            fg_color=Theme.get_success_color(),
            hover_color=Theme.rgb_to_hex((36, 164, 93)),
            command=self._save_settings
        )
        save_btn.grid(row=3, column=0, padx=5, pady=(10, 10), sticky="ew")

        # About Section
        about_card = GlassCard(settings_container)
        about_card.grid(row=4, column=0, padx=5, pady=(0, 10), sticky="ew")

        about_header = ctk.CTkLabel(
            about_card,
            text="ℹ️ About",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        about_header.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        about_frame = ctk.CTkFrame(about_card, fg_color="transparent")
        about_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")

        version_label = ctk.CTkLabel(
            about_frame,
            text=f"Version: {__version__}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.get_accent_color(),
            anchor="w"
        )
        version_label.grid(row=0, column=0, sticky="w")

        author_label = ctk.CTkLabel(
            about_frame,
            text="Author: Ahmed Tarek Zaher",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        author_label.grid(row=1, column=0, pady=(3, 0), sticky="w")

        desc_label = ctk.CTkLabel(
            about_frame,
            text="A powerful video, audio, and playlist downloader with\ncustom resolutions up to 4K, and support for YouTube, TikTok,\nInstagram, Facebook, Twitter/X, and more.",
            font=ctk.CTkFont(size=10),
            text_color=Theme.rgb_to_hex((150, 150, 170)),
            justify="left",
            anchor="w"
        )
        desc_label.grid(row=2, column=0, pady=(8, 0), sticky="w")

        brand_label = ctk.CTkLabel(
            about_frame,
            text="Made with ❤️ using Python & CustomTkinter",
            font=ctk.CTkFont(size=10),
            text_color=Theme.rgb_to_hex((100, 100, 120)),
            anchor="w"
        )
        brand_label.grid(row=3, column=0, pady=(10, 0), sticky="w")

    def _browse_default_path(self):
        """Browse for default download path."""
        folder = filedialog.askdirectory(
            title="Select Default Download Folder",
            initialdir=self.default_path_entry.get()
        )
        if folder:
            self.default_path_entry.delete(0, tk.END)
            self.default_path_entry.insert(0, folder)

    def _on_theme_changed(self, choice: str):
        """Handle theme change."""
        theme_mode = choice.lower()
        ctk.set_appearance_mode(theme_mode)
        self._save_settings()

    def _save_settings(self):
        """Save all settings to config."""
        self.config["download_directory"] = self.default_path_entry.get()
        self.config["theme"] = self.theme_var.get().lower()
        self.config["check_updates"] = self.auto_update_var.get()

        if save_config(self.config):
            self._show_toast("Settings saved successfully!", "success")
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, self.config["download_directory"])
        else:
            messagebox.showerror("Error", "Failed to save settings")

    def _show_toast(self, message: str, toast_type: str = "info"):
        """Show a modern toast notification."""
        toast_colors = {
            'success': Theme.get_success_color(),
            'error': Theme.get_error_color(),
            'info': Theme.get_accent_color(),
            'warning': Theme.get_warning_color()
        }

        toast = ctk.CTkFrame(
            self,
            fg_color=toast_colors.get(toast_type, Theme.get_accent_color()),
            corner_radius=12
        )
        toast.place(relx=0.5, rely=0.9, anchor="center")

        label = ctk.CTkLabel(
            toast,
            text=message,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white"
        )
        label.grid(row=0, column=0, padx=20, pady=12)

        self.after(2000, lambda: toast.destroy())


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

def main():
    """Launch the Downloadyha GUI application."""
    app = DownloadyhaGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
