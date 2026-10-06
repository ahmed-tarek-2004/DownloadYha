"""
app.py - Main Desktop GUI Application for Downloadyha

A modern, production-grade desktop GUI built with CustomTkinter featuring:
- Light Grey & Crimson aesthetic with clean cards and typography
- Persistent sidebar navigation with dedicated System Health controls
- Real-time video/playlist metadata fetching and dynamic resolution detection (up to 4K)
- Audio MP3 conversion with customizable bitrates (320k, 192k, 128k, Best VBR)
- Partial segment clipping (start/end timestamps)
- Comprehensive subtitle downloading, format conversion, and embedding
- Multi-threaded asynchronous execution with strict thread safety
- Stable download queue with 100% INLINE error handling (zero intrusive pop-ups)
- Direct integration with updater and dependency self-repair subsystems
"""

from __future__ import annotations

__author__ = "Ahmed Tarek Zaher"
__copyright__ = "Copyright 2026, Ahmed Tarek Zaher"
__license__ = "MIT"

# BOOKMARK: Ahmed Tarek Zaher - Owner

import os
import re
import sys
import threading
import time
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional, Tuple

import customtkinter as ctk

# Import downloadyha core engine
try:
    from downloadyha import __version__
    from downloadyha.config import get_download_dir, load as load_config, save as save_config
    from downloadyha.dependencies import (
        check_dependencies,
        check_ffmpeg,
        check_ffprobe,
        get_dependency_versions,
        repair_dependencies,
        verify_dependencies,
    )
    from downloadyha.downloader import (
        DownloadResult,
        download_audio,
        download_playlist,
        download_video,
        get_media_info,
        get_playlist_entries,
        get_video_qualities,
        has_video_id,
        is_playlist,
        is_playlist_url,
        is_pure_playlist_url,
        is_video_in_playlist_url,
        parse_time_str,
        strip_playlist_params,
    )
    from downloadyha.subtitle_utils import get_available_subtitles
    from downloadyha.ui import format_duration, format_number
    from downloadyha.updater import check_for_updates, perform_update
except ImportError:
    # Fallback for direct execution during development
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from downloadyha import __version__
    from downloadyha.config import get_download_dir, load as load_config, save as save_config
    from downloadyha.dependencies import (
        check_dependencies,
        check_ffmpeg,
        check_ffprobe,
        get_dependency_versions,
        repair_dependencies,
        verify_dependencies,
    )
    from downloadyha.downloader import (
        DownloadResult,
        download_audio,
        download_playlist,
        download_video,
        get_media_info,
        get_playlist_entries,
        get_video_qualities,
        has_video_id,
        is_playlist,
        is_playlist_url,
        is_pure_playlist_url,
        is_video_in_playlist_url,
        parse_time_str,
        strip_playlist_params,
    )
    from downloadyha.subtitle_utils import get_available_subtitles
    from downloadyha.ui import format_duration, format_number
    from downloadyha.updater import check_for_updates, perform_update


# ---------------------------------------------------------------------------
# Theme & Color Palette (Light Grey & Crimson with Dark & Light Mode Support)
# ---------------------------------------------------------------------------

class Theme:
    """Light Grey & Crimson brand color palette with full Light & Dark mode support."""
    # Primary Backgrounds (Light, Dark)
    BG_LIGHT = ("#F4F6F8", "#0F172A")          # Main application background
    BG_SECONDARY = ("#EAEFF5", "#1E293B")      # Persistent sidebar background
    BG_TERTIARY = ("#DFE6EE", "#334155")       # Subtle inset / borders

    # Cards / Surfaces (Light, Dark)
    CARD_BG = ("#FFFFFF", "#1E293B")           # Pure white / dark slate card surface
    CARD_BORDER = ("#E2E8F0", "#334155")       # Card border
    CARD_BORDER_HOVER = ("#CBD5E1", "#475569")

    # Accents & Crimson Branding (Light, Dark)
    CRIMSON_PRIMARY = ("#DC2626", "#EF4444")   # Main action crimson
    CRIMSON_HOVER = ("#B91C1C", "#DC2626")     # Darker crimson on hover
    CRIMSON_LIGHT = ("#FEE2E2", "#450A0A")     # Soft crimson tint for badges
    CRIMSON_DARK = "#991B1B"                    # Deep crimson

    # Typography (Light, Dark)
    TEXT_PRIMARY = ("#0F172A", "#F8FAFC")      # Primary headings & main text
    TEXT_SECONDARY = ("#475569", "#94A3B8")    # Muted secondary / metadata labels
    TEXT_MUTED = ("#94A3B8", "#64748B")        # Subtle helper / timestamp text

    # Status Accents (Light, Dark)
    SUCCESS_GREEN = ("#059669", "#10B981")     # Emerald Green for success
    SUCCESS_LIGHT = ("#ECFDF5", "#064E3B")     # Soft green tint
    ERROR_RED = ("#EF4444", "#F87171")         # Crimson Red for errors & failed cards
    ERROR_LIGHT = ("#FEF2F2", "#450A0A")       # Error card background tint
    WARNING_AMBER = ("#D97706", "#F59E0B")     # Amber Yellow for warnings
    WARNING_LIGHT = ("#FFFBEB", "#451A03")     # Soft amber tint
    INFO_BLUE = ("#2563EB", "#3B82F6")         # Information blue
    INFO_LIGHT = ("#EFF6FF", "#1E3A8A")

    # Buttons & Form Elements (Light, Dark)
    BTN_SECONDARY_BG = ("#E2E8F0", "#334155")
    BTN_SECONDARY_HOVER = ("#CBD5E1", "#475569")
    BTN_SECONDARY_TEXT = ("#0F172A", "#F8FAFC")
    BTN_SUBTLE_BG = ("#F1F5F9", "#243044")
    BTN_SUBTLE_HOVER = ("#E2E8F0", "#334155")
    ENTRY_BG = ("#FFFFFF", "#0F172A")
    ENTRY_BORDER = ("#E2E8F0", "#334155")
    ENTRY_TEXT = ("#0F172A", "#F8FAFC")
    PROGRESS_BG = ("#E2E8F0", "#334155")

    # Backward Compatibility Constants & Methods
    ELECTRIC_CYAN = (0, 210, 255)
    ACCENT_HEX = "#00D2FF"

    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to Hex string."""
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    @classmethod
    def get_accent_color(cls) -> str:
        """Get primary accent color."""
        return cls.ACCENT_HEX

    @classmethod
    def get_success_color(cls) -> str:
        """Get success status color."""
        return "#2ECC71"

    @classmethod
    def get_error_color(cls) -> str:
        """Get error status color."""
        return "#E74C3C"

    @classmethod
    def get_warning_color(cls) -> str:
        """Get warning status color."""
        return "#FFA500"


# ---------------------------------------------------------------------------
# Quality Definitions & Helpers
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
# Download History Tracker
# ---------------------------------------------------------------------------

class DownloadHistory:
    """Manages history records for completed and downloaded items."""

    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self._items: List[Dict[str, Any]] = []

    def add_item(self, url: str, title: str, status: str, file_path: str = "") -> Dict[str, Any]:
        """Record an item into the history."""
        item = {
            "url": url,
            "title": title,
            "status": status,
            "file_path": file_path,
            "timestamp": time.time(),
        }
        self._items.insert(0, item)
        if len(self._items) > self.max_items:
            self._items = self._items[:self.max_items]
        return item

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all history items."""
        return list(self._items)

    def clear(self) -> None:
        """Clear the history."""
        self._items.clear()


# ---------------------------------------------------------------------------
# Reusable Styled Components
# ---------------------------------------------------------------------------

class CrimsonButton(ctk.CTkButton):
    """Primary Action Button with Deep Crimson styling."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("height", 38)
        kwargs.setdefault("font", ctk.CTkFont(size=12, weight="bold"))
        kwargs.setdefault("fg_color", Theme.CRIMSON_PRIMARY)
        kwargs.setdefault("hover_color", Theme.CRIMSON_HOVER)
        kwargs.setdefault("text_color", "#FFFFFF")
        super().__init__(master, **kwargs)

    def _on_leave(self, event=None):
        """Handle mouse leave safely."""
        try:
            super()._on_leave(event)
        except TypeError:
            super()._on_leave()

    def _on_enter(self, event=None):
        """Handle mouse enter safely."""
        try:
            super()._on_enter(event)
        except TypeError:
            super()._on_enter()


class ModernButton(CrimsonButton):
    """Alias for backwards compatibility with test suites."""
    pass


class SecondaryButton(ctk.CTkButton):
    """Secondary Action Button with adaptive Light/Dark styling."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("height", 36)
        kwargs.setdefault("font", ctk.CTkFont(size=12, weight="normal"))
        kwargs.setdefault("fg_color", Theme.BTN_SECONDARY_BG)
        kwargs.setdefault("hover_color", Theme.BTN_SECONDARY_HOVER)
        kwargs.setdefault("text_color", Theme.BTN_SECONDARY_TEXT)
        super().__init__(master, **kwargs)


class GlassCard(ctk.CTkFrame):
    """Adaptive Card frame with subtle border and rounded corners."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Theme.CARD_BORDER)
        kwargs.setdefault("fg_color", Theme.CARD_BG)
        super().__init__(master, **kwargs)


class StyledProgressBar(ctk.CTkProgressBar):
    """Progress bar configured with Crimson accents."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", 6)
        kwargs.setdefault("height", 10)
        kwargs.setdefault("progress_color", Theme.CRIMSON_PRIMARY)
        kwargs.setdefault("fg_color", Theme.PROGRESS_BG)
        super().__init__(master, **kwargs)


# ---------------------------------------------------------------------------
# Download Task Data Structure
# ---------------------------------------------------------------------------

class DownloadTask:
    """Represents a download job with state, parameters, and results."""

    def __init__(
        self,
        url: str,
        dest_path: str,
        media_type: str,
        quality: Any,
        quality_label: str,
        title: str = "Analyzing media...",
        uploader: str = "Unknown",
        duration_str: str = "",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        subs_kwargs: Optional[Dict[str, Any]] = None,
        is_playlist: Optional[bool] = None,
    ):
        self.id = str(uuid.uuid4())[:8]
        self.url = url
        self.dest_path = dest_path
        self.media_type = media_type
        self.quality = quality
        self.quality_label = quality_label
        self.title = title
        self.uploader = uploader
        self.duration_str = duration_str
        self.start_time = start_time
        self.end_time = end_time
        self.subs_kwargs = subs_kwargs or {}
        self.is_playlist = is_playlist

        self.status = "queued"  # queued, downloading, completed, failed, cancelled
        self.progress = 0.0
        self.speed = "--"
        self.eta = "--"
        self.downloaded_size = "--"
        self.error_message = ""
        self.saved_directory = ""
        self.completed_files: List[str] = []


# ---------------------------------------------------------------------------
# Dynamic Download Card Component for Queue & History (Inline Error Handling)
# ---------------------------------------------------------------------------

class DownloadQueueCard(ctk.CTkFrame):
    """
    Card representing a download item in the Queue.
    Handles dynamic state transitions (active, completed, failed, cancelled)
    with strict INLINE error messages, crimson borders, and retry buttons.
    """

    def __init__(
        self,
        master,
        task: DownloadTask,
        on_retry: Callable[[DownloadTask], None],
        on_remove: Callable[[DownloadTask], None],
        **kwargs
    ):
        self.task = task
        self.on_retry = on_retry
        self.on_remove = on_remove

        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
            border_color=Theme.CARD_BORDER,
            fg_color=Theme.CARD_BG,
            **kwargs
        )

        self.grid_columnconfigure(1, weight=1)
        self._build_ui()
        self.update_state()

    def _build_ui(self):
        """Construct the card layout."""
        # Left icon badge
        self.icon_badge = ctk.CTkLabel(
            self,
            text="🎬" if self.task.media_type == "video" else "🎵",
            font=ctk.CTkFont(size=20),
            width=40,
            height=40,
            fg_color=Theme.BG_LIGHT,
            corner_radius=8,
        )
        self.icon_badge.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=12, sticky="n")

        # Center content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, padx=(0, 10), pady=(10, 8), sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Title label
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text=self.task.title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="ew")

        # Metadata line
        type_str = "Video" if self.task.media_type == "video" else "Audio"
        meta_info = f"{type_str} • {self.task.quality_label}"
        if self.task.uploader and self.task.uploader != "Unknown":
            meta_info += f" • {self.task.uploader}"
        if self.task.start_time or self.task.end_time:
            st = self.task.start_time or "00:00"
            et = self.task.end_time or "End"
            meta_info += f" • ✂️ Clip ({st} - {et})"

        self.meta_label = ctk.CTkLabel(
            self.content_frame,
            text=meta_info,
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        )
        self.meta_label.grid(row=1, column=0, sticky="ew", pady=(2, 4))

        # Progress bar
        self.progress_bar = StyledProgressBar(self.content_frame)
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=(2, 2))
        self.progress_bar.set(self.task.progress)

        # Metrics line (Speed, ETA, Percentage)
        self.metrics_label = ctk.CTkLabel(
            self.content_frame,
            text="Queued...",
            font=ctk.CTkFont(size=10),
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        )
        self.metrics_label.grid(row=3, column=0, sticky="ew", pady=(1, 0))

        # INLINE ERROR CONTAINER (hidden unless failed)
        self.error_container = ctk.CTkFrame(
            self.content_frame,
            fg_color=Theme.ERROR_LIGHT,
            border_width=1,
            border_color=Theme.ERROR_RED,
            corner_radius=6,
        )
        self.error_label = ctk.CTkLabel(
            self.error_container,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.ERROR_RED,
            wraplength=520,
            justify="left",
            anchor="w",
        )
        self.error_label.pack(fill="x", padx=8, pady=6)

        # Right Action & Status Frame
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=0, column=2, rowspan=2, padx=12, pady=10, sticky="ne")

        # Status badge
        self.status_badge = ctk.CTkLabel(
            self.action_frame,
            text="Queued",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.TEXT_SECONDARY,
            fg_color=Theme.BG_SECONDARY,
            corner_radius=6,
            width=95,
            height=26,
        )
        self.status_badge.pack(side="top", pady=(0, 6))

        # Action button container
        self.btn_container = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        self.btn_container.pack(side="top", fill="x")

        # Retry button (shown on failure)
        self.retry_btn = CrimsonButton(
            self.btn_container,
            text="↺ Retry",
            width=70,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: self.on_retry(self.task),
        )

        # Remove button
        self.remove_btn = ctk.CTkButton(
            self.btn_container,
            text="✕",
            width=28,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=Theme.BTN_SUBTLE_BG,
            hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            command=lambda: self.on_remove(self.task),
        )
        self.remove_btn.pack(side="right", padx=(4, 0))

        # Open folder button (shown on success)
        self.open_btn = SecondaryButton(
            self.btn_container,
            text="📁 Open",
            width=65,
            height=28,
            font=ctk.CTkFont(size=11),
            command=self._open_item_folder,
        )

    def update_progress(self, percent: float, speed: str, eta: str, title: str = ""):
        """Update live progress metrics."""
        self.task.progress = percent / 100.0
        self.task.speed = speed
        self.task.eta = eta
        if title:
            self.task.title = title
            self.title_label.configure(text=title)

        self.progress_bar.set(self.task.progress)
        self.metrics_label.configure(
            text=f"{percent:.1f}% • Speed: {speed} • ETA: {eta}",
            text_color=Theme.CRIMSON_PRIMARY,
        )
        self.status_badge.configure(
            text="Downloading",
            text_color=Theme.CRIMSON_PRIMARY,
            fg_color=Theme.CRIMSON_LIGHT,
        )

    def update_state(self):
        """Update visual styling based on current task status."""
        status = self.task.status
        self.title_label.configure(text=self.task.title)

        if status == "downloading":
            self.configure(border_color=Theme.CRIMSON_PRIMARY, border_width=1, fg_color=Theme.CARD_BG)
            self.status_badge.configure(text="Downloading", text_color=Theme.CRIMSON_PRIMARY, fg_color=Theme.CRIMSON_LIGHT)
            self.progress_bar.grid()
            self.metrics_label.grid()
            self.error_container.grid_forget()
            self.retry_btn.pack_forget()
            self.open_btn.pack_forget()

        elif status == "completed":
            self.configure(border_color=Theme.SUCCESS_GREEN, border_width=1, fg_color=Theme.CARD_BG)
            self.status_badge.configure(text="✓ Completed", text_color=Theme.SUCCESS_GREEN, fg_color=Theme.SUCCESS_LIGHT)
            self.progress_bar.set(1.0)
            self.metrics_label.configure(text="Download complete • 100%", text_color=Theme.SUCCESS_GREEN)
            self.error_container.grid_forget()
            self.retry_btn.pack_forget()
            self.open_btn.pack(side="left", padx=(0, 4))

        elif status == "failed":
            # CRITICAL: Inline error styling, Crimson 2px border, Error box, Retry button
            self.configure(border_color=Theme.ERROR_RED, border_width=2, fg_color=Theme.CARD_BG)
            self.status_badge.configure(text="✕ Failed", text_color=Theme.ERROR_RED, fg_color=Theme.ERROR_LIGHT)
            self.progress_bar.grid_forget()
            self.metrics_label.grid_forget()
            self.open_btn.pack_forget()

            # Display exact error inside the card
            err_text = f"⚠️ Error: {self.task.error_message or 'Download was interrupted or encountered a network issue.'}"
            self.error_label.configure(text=err_text)
            self.error_container.grid(row=2, column=0, sticky="ew", pady=(4, 2))

            # Show inline Retry button
            self.retry_btn.pack(side="left", padx=(0, 4))

        elif status == "cancelled":
            self.configure(border_color=Theme.WARNING_AMBER, border_width=1, fg_color=Theme.CARD_BG)
            self.status_badge.configure(text="Cancelled", text_color=Theme.WARNING_AMBER, fg_color=Theme.WARNING_LIGHT)
            self.metrics_label.configure(text="Download was cancelled", text_color=Theme.WARNING_AMBER)
            self.error_container.grid_forget()
            self.open_btn.pack_forget()
            self.retry_btn.pack(side="left", padx=(0, 4))

        else:  # queued
            self.configure(border_color=Theme.CARD_BORDER, border_width=1, fg_color=Theme.CARD_BG)
            self.status_badge.configure(text="Queued", text_color=Theme.TEXT_SECONDARY, fg_color=Theme.BG_SECONDARY)
            self.progress_bar.set(0)
            self.metrics_label.configure(text="Waiting in queue...", text_color=Theme.TEXT_MUTED)
            self.error_container.grid_forget()
            self.retry_btn.pack_forget()
            self.open_btn.pack_forget()

    def _open_item_folder(self):
        """Open the target directory in file manager."""
        target_dir = self.task.saved_directory or self.task.dest_path
        if target_dir and os.path.exists(target_dir):
            try:
                if sys.platform == "win32":
                    os.startfile(target_dir)
                elif sys.platform == "darwin":
                    os.system(f'open "{target_dir}"')
                else:
                    os.system(f'xdg-open "{target_dir}"')
            except Exception:
                pass


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
# Main Application Class (CustomTkinter GUI)
# BOOKMARK: Ahmed Tarek Zaher - Owner
# ---------------------------------------------------------------------------

class DownloadyhaGUI(ctk.CTk):
    """
    Main Desktop GUI application window for Downloadyha with
    Light Grey & Crimson design, persistent sidebar navigation,
    System Health actions, and robust inline error handling.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Window configuration
        self.title(f"Downloadyha v{__version__} - Video & Media Downloader")
        self.geometry("1080x760")
        self.minsize(980, 680)

        # Load persisted settings
        self.config = load_config()

        # Appearance mode (Light, Dark, or System Default)
        saved_mode = self.config.get("appearance_mode", self.config.get("theme", "light"))
        if saved_mode not in ("light", "dark", "system"):
            saved_mode = "light"
        ctk.set_appearance_mode(saved_mode)
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=Theme.BG_LIGHT)

        # State tracking
        self.media_info: Optional[Dict[str, Any]] = None
        self.last_fetched_url: str = ""
        self.is_fetching_info: bool = False
        self.available_video_qualities: List[int] = []

        # Download & Queue Management
        self.download_queue: List[DownloadTask] = []
        self.active_task: Optional[DownloadTask] = None
        self.active_card: Optional[DownloadQueueCard] = None
        self.is_downloading: bool = False
        self.cancel_requested: bool = False
        self.download_thread: Optional[threading.Thread] = None

        # System Health state
        self.is_checking_updates: bool = False
        self.is_repairing_dependencies: bool = False

        # Build Layout (Persistent Sidebar + Content Views)
        self._build_main_layout()

        # Aliases for backwards compatibility with tests and helpers
        self.download_btn = self.start_download_btn
        self.status_label = self.active_item_label
        self.status_indicator = self.active_status_badge

        # Set window icon
        self._set_window_icon()

        # Background dependency self-check
        self._async_background_dependency_check()

    def _set_window_icon(self):
        """Locate and set the application icon."""
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

    def _async_background_dependency_check(self):
        """Silently verify dependencies in background."""
        def worker():
            try:
                check_dependencies(auto_download=True)
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _set_ui_state(self, state: str):
        """Helper to set UI button states for backwards compatibility."""
        pass

    # -----------------------------------------------------------------------
    # Layout Structure: Sidebar + Main Workspace
    # -----------------------------------------------------------------------

    def _build_main_layout(self):
        """Create the two-column layout: Persistent Sidebar & Dynamic Views."""
        self.grid_columnconfigure(0, weight=0, minsize=230)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Persistent Sidebar
        self._build_sidebar()

        # 2. Right Content Area (View Switcher)
        self.content_area = ctk.CTkFrame(self, fg_color=Theme.BG_LIGHT, corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        # Views Dictionary
        self.views: Dict[str, ctk.CTkFrame] = {}
        self._build_views()

        # Switch to default view
        self.show_view("downloader")

    # -----------------------------------------------------------------------
    # Sidebar: Brand, Navigation, & System Health Section
    # -----------------------------------------------------------------------

    def _build_sidebar(self):
        """Construct the persistent left sidebar with navigation, Appearance switcher, and System Health."""
        self.sidebar = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0,
            fg_color=Theme.BG_SECONDARY,
            border_width=1,
            border_color=Theme.BG_TERTIARY,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(2, weight=1)  # Spacer row

        # Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=16, pady=(20, 16), sticky="ew")

        brand_title = ctk.CTkLabel(
            brand_frame,
            text="🎬 Downloadyha",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        )
        brand_title.pack(anchor="w")

        brand_subtitle = ctk.CTkLabel(
            brand_frame,
            text=f"Zero-Config Downloader • v{__version__}",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        )
        brand_subtitle.pack(anchor="w", pady=(2, 0))

        brand_author = ctk.CTkLabel(
            brand_frame,
            text="Crafted by Ahmed Tarek Zaher",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.CRIMSON_PRIMARY,
            anchor="w",
        )
        brand_author.pack(anchor="w", pady=(2, 0))

        # Navigation Buttons Container
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.grid(row=1, column=0, padx=12, pady=0, sticky="ew")
        self.nav_frame.grid_columnconfigure(0, weight=1)

        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

        self.btn_nav_down = self._create_nav_button(
            self.nav_frame, "downloader", "⬇️  Downloader", 0
        )
        self.btn_nav_queue = self._create_nav_button(
            self.nav_frame, "queue", "📋  Download Queue", 1, badge_text="0"
        )
        self.btn_nav_settings = self._create_nav_button(
            self.nav_frame, "settings", "⚙️  Settings", 2
        )

        # Spacer in row 2 (absorbs vertical space)

        # THEME SWITCHER (Docked above System Health in sidebar)
        self.theme_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.theme_frame.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="ew")
        self.theme_frame.grid_columnconfigure(0, weight=1)

        theme_sidebar_title = ctk.CTkLabel(
            self.theme_frame,
            text="THEME MODE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        )
        theme_sidebar_title.pack(anchor="w", padx=2, pady=(0, 4))

        saved_mode = self.config.get("appearance_mode", self.config.get("theme", "light"))
        sidebar_mode_val_map = {"light": "☀️ Light", "dark": "🌙 Dark", "system": "💻 Auto"}
        sidebar_initial_val = sidebar_mode_val_map.get(saved_mode, "☀️ Light")

        self.theme_segmented = ctk.CTkSegmentedButton(
            self.theme_frame,
            values=["☀️ Light", "🌙 Dark", "💻 Auto"],
            font=ctk.CTkFont(size=11, weight="bold"),
            height=30,
            selected_color=Theme.CRIMSON_PRIMARY,
            selected_hover_color=Theme.CRIMSON_HOVER,
            unselected_color=Theme.BTN_SUBTLE_BG,
            unselected_hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            command=self._on_theme_segmented_change,
        )
        self.theme_segmented.pack(fill="x")
        self.theme_segmented.set(sidebar_initial_val)

        # SYSTEM HEALTH SECTION (Docked at the bottom of the sidebar)
        self.health_frame = ctk.CTkFrame(
            self.sidebar,
            corner_radius=10,
            fg_color=Theme.CARD_BG,
            border_width=1,
            border_color=Theme.CARD_BORDER,
        )
        self.health_frame.grid(row=4, column=0, padx=12, pady=(0, 16), sticky="ew")
        self.health_frame.grid_columnconfigure(0, weight=1)

        # Health Header
        health_header_frame = ctk.CTkFrame(self.health_frame, fg_color="transparent")
        health_header_frame.pack(fill="x", padx=12, pady=(10, 6))

        health_title = ctk.CTkLabel(
            health_header_frame,
            text="SYSTEM HEALTH",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.TEXT_MUTED,
        )
        health_title.pack(side="left")

        self.health_status_dot = ctk.CTkLabel(
            health_header_frame,
            text="● Ready",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.SUCCESS_GREEN,
        )
        self.health_status_dot.pack(side="right")

        # 1. Check for Updates Button
        self.btn_check_updates = ctk.CTkButton(
            self.health_frame,
            text="🔄 Check for Updates",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=6,
            fg_color=Theme.BTN_SUBTLE_BG,
            hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            command=self._check_for_updates,
        )
        self.btn_check_updates.pack(fill="x", padx=10, pady=(0, 6))

        # 2. Verify & Repair App Button
        self.btn_verify_repair = ctk.CTkButton(
            self.health_frame,
            text="🛠️🛡️ Verify & Repair App",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            corner_radius=6,
            fg_color=Theme.BTN_SUBTLE_BG,
            hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            command=self._verify_and_repair,
        )
        self.btn_verify_repair.pack(fill="x", padx=10, pady=(0, 10))

        # Health Feedback Label (inline inside sidebar)
        self.health_feedback_label = ctk.CTkLabel(
            self.health_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=Theme.TEXT_SECONDARY,
            wraplength=180,
            justify="center",
        )

        # Footer Copyright Label
        sidebar_footer = ctk.CTkLabel(
            self.sidebar,
            text="© 2026 Ahmed Tarek Zaher",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="center",
        )
        sidebar_footer.grid(row=5, column=0, padx=12, pady=(0, 10), sticky="ew")

    def _create_nav_button(
        self,
        parent,
        view_key: str,
        label: str,
        row: int,
        badge_text: Optional[str] = None
    ) -> ctk.CTkButton:
        """Create a styled navigation button with active indicator support."""
        btn = ctk.CTkButton(
            parent,
            text=label,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            corner_radius=8,
            fg_color="transparent",
            hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            command=lambda: self.show_view(view_key),
        )
        btn.grid(row=row, column=0, pady=2, sticky="ew")
        self.nav_buttons[view_key] = btn
        return btn

    def show_view(self, view_key: str):
        """Switch active workspace view and highlight the corresponding sidebar tab."""
        self.current_view = view_key
        for key, frame in self.views.items():
            if key == view_key:
                frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            else:
                frame.grid_forget()

        # Update sidebar button highlighting
        for key, btn in self.nav_buttons.items():
            if key == view_key:
                btn.configure(
                    fg_color=Theme.CRIMSON_PRIMARY,
                    text_color="#FFFFFF",
                    hover_color=Theme.CRIMSON_HOVER,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Theme.TEXT_PRIMARY,
                    hover_color=Theme.BTN_SUBTLE_HOVER,
                )

        if view_key == "queue":
            self._refresh_queue_view()

    # -----------------------------------------------------------------------
    # Theme & Appearance Mode Management (Light, Dark, & System Auto)
    # -----------------------------------------------------------------------

    def set_theme_mode(self, mode: str):
        """
        Switch application appearance mode dynamically and persist to configuration.

        Args:
            mode: 'light', 'dark', or 'system'
        """
        if mode not in ("light", "dark", "system"):
            mode = "light"

        ctk.set_appearance_mode(mode)
        self.config["appearance_mode"] = mode
        self.config["theme"] = mode
        save_config(self.config)

        # Sync sidebar segmented control
        sidebar_val_map = {"light": "☀️ Light", "dark": "🌙 Dark", "system": "💻 Auto"}
        if hasattr(self, "theme_segmented") and self.theme_segmented:
            expected_sidebar = sidebar_val_map.get(mode, "☀️ Light")
            if self.theme_segmented.get() != expected_sidebar:
                self.theme_segmented.set(expected_sidebar)

        # Sync settings view segmented control
        settings_val_map = {"light": "☀️ Light Mode", "dark": "🌙 Dark Mode", "system": "💻 System Default"}
        if hasattr(self, "settings_theme_segmented") and self.settings_theme_segmented:
            expected_settings = settings_val_map.get(mode, "☀️ Light Mode")
            if self.settings_theme_segmented.get() != expected_settings:
                self.settings_theme_segmented.set(expected_settings)

    def _on_theme_segmented_change(self, value: str):
        """Handle sidebar theme switch event."""
        mode_map = {
            "☀️ Light": "light",
            "🌙 Dark": "dark",
            "💻 Auto": "system",
        }
        mode = mode_map.get(value, "light")
        self.set_theme_mode(mode)

    def _on_settings_theme_change(self, value: str):
        """Handle settings panel theme switch event."""
        mode_map = {
            "☀️ Light Mode": "light",
            "🌙 Dark Mode": "dark",
            "💻 System Default": "system",
        }
        mode = mode_map.get(value, "light")
        self.set_theme_mode(mode)

    # -----------------------------------------------------------------------
    # Views Initializer
    # -----------------------------------------------------------------------

    def _build_views(self):
        """Build the three primary views in the right workspace."""
        self.views["downloader"] = self._create_downloader_view()
        self.views["queue"] = self._create_queue_view()
        self.views["settings"] = self._create_settings_view()

    # -----------------------------------------------------------------------
    # VIEW 1: Downloader Workspace
    # -----------------------------------------------------------------------

    def _create_downloader_view(self) -> ctk.CTkFrame:
        """Construct the main Downloader view."""
        view = ctk.CTkFrame(self.content_area, fg_color=Theme.BG_LIGHT)
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(0, weight=1)
        view.grid_rowconfigure(1, weight=0)

        # Scrollable form container
        scroll = ctk.CTkScrollableFrame(view, fg_color="transparent")
        scroll.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # 1. URL Input Card
        url_card = GlassCard(scroll)
        url_card.grid(row=0, column=0, padx=4, pady=(0, 10), sticky="ew")
        url_card.grid_columnconfigure(0, weight=1)

        url_header = ctk.CTkLabel(
            url_card,
            text="🔗 Media or Playlist Link",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        )
        url_header.grid(row=0, column=0, padx=16, pady=(12, 6), sticky="w")

        url_input_frame = ctk.CTkFrame(url_card, fg_color="transparent")
        url_input_frame.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="ew")
        url_input_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            url_input_frame,
            placeholder_text="Paste YouTube, TikTok, Facebook, Instagram, or video URL...",
            height=40,
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            border_width=1,
            border_color=Theme.CARD_BORDER,
        )
        self.url_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.url_entry.bind("<Return>", lambda event: self._fetch_media_info())

        paste_btn = SecondaryButton(
            url_input_frame,
            text="📋 Paste",
            width=80,
            height=40,
            command=self._paste_url,
        )
        paste_btn.grid(row=0, column=1, padx=(0, 6))

        self.fetch_btn = CrimsonButton(
            url_input_frame,
            text="🔍 Fetch Info",
            width=105,
            height=40,
            command=self._fetch_media_info,
        )
        self.fetch_btn.grid(row=0, column=2)

        # Inline URL Feedback / Error label
        self.url_feedback_label = ctk.CTkLabel(
            url_card,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_SECONDARY,
        )
        self.url_feedback_label.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")

        # 2. Media Inspection Details Card
        self.media_card = GlassCard(scroll)
        self.media_card.grid(row=1, column=0, padx=4, pady=(0, 10), sticky="ew")
        self.media_card.grid_columnconfigure(0, weight=1)

        media_card_header = ctk.CTkFrame(self.media_card, fg_color="transparent")
        media_card_header.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="ew")
        media_card_header.grid_columnconfigure(1, weight=1)

        self.media_badge = ctk.CTkLabel(
            media_card_header,
            text="💡 Ready",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=Theme.BG_SECONDARY,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=6,
            width=90,
            height=22,
        )
        self.media_badge.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.media_channel_label = ctk.CTkLabel(
            media_card_header,
            text="Paste a link above to inspect title, channel, duration, and resolutions",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        )
        self.media_channel_label.grid(row=0, column=1, sticky="w")

        self.media_title_label = ctk.CTkLabel(
            self.media_card,
            text="No media analyzed yet",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.media_title_label.grid(row=1, column=0, padx=16, pady=(0, 2), sticky="ew")

        self.media_meta_label = ctk.CTkLabel(
            self.media_card,
            text="Available resolutions will appear in the dropdown once analyzed",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        )
        self.media_meta_label.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="ew")

        # 3. Format, Quality & Options Card
        options_card = GlassCard(scroll)
        options_card.grid(row=2, column=0, padx=4, pady=(0, 10), sticky="ew")
        options_card.grid_columnconfigure(0, weight=1)
        options_card.grid_columnconfigure(1, weight=1)

        # Media Type Selection
        ctk.CTkLabel(
            options_card,
            text="⚡ Format:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        ctk.CTkLabel(
            options_card,
            text="🎯 Quality / Bitrate:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=1, padx=(10, 16), pady=(12, 4), sticky="w")

        self.media_type_var = tk.StringVar(value="video")
        self.media_type_selector = ctk.CTkSegmentedButton(
            options_card,
            values=["🎥 Video", "🎵 Audio"],
            variable=self.media_type_var,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_media_type_changed,
            corner_radius=8,
            height=36,
            selected_color=Theme.CRIMSON_PRIMARY,
            selected_hover_color=Theme.CRIMSON_HOVER,
            unselected_color=Theme.BTN_SUBTLE_BG,
            unselected_hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
        )
        self.media_type_selector.grid(row=1, column=0, padx=(16, 10), pady=(0, 12), sticky="ew")

        self.quality_var = tk.StringVar(value=DEFAULT_VIDEO_QUALITIES[0])
        self.quality_menu = ctk.CTkOptionMenu(
            options_card,
            variable=self.quality_var,
            values=DEFAULT_VIDEO_QUALITIES,
            font=ctk.CTkFont(size=11),
            dropdown_font=ctk.CTkFont(size=11),
            corner_radius=8,
            height=36,
            fg_color=Theme.BTN_SUBTLE_BG,
            button_color=Theme.BTN_SECONDARY_BG,
            button_hover_color=Theme.BTN_SECONDARY_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_fg_color=Theme.CARD_BG,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            dropdown_hover_color=Theme.BTN_SUBTLE_HOVER,
        )
        self.quality_menu.grid(row=1, column=1, padx=(10, 16), pady=(0, 12), sticky="ew")

        # 4. Partial Section Clipping & Subtitles (Collapsible inside options card)
        # Checkbox Row
        toggles_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        toggles_frame.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="ew")

        self.section_toggle_var = tk.BooleanVar(value=False)
        self.section_toggle = ctk.CTkCheckBox(
            toggles_frame,
            text="✂️ Download specific section (clip)",
            variable=self.section_toggle_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
            command=self._on_section_toggled,
            fg_color=Theme.CRIMSON_PRIMARY,
            hover_color=Theme.CRIMSON_HOVER,
            checkmark_color="#FFFFFF",
        )
        self.section_toggle.pack(side="left", padx=(0, 20))

        self.transcript_toggle_var = tk.BooleanVar(value=False)
        self.transcript_toggle = ctk.CTkCheckBox(
            toggles_frame,
            text="📝 Subtitles & Transcripts",
            variable=self.transcript_toggle_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
            command=self._on_transcript_toggled,
            fg_color=Theme.CRIMSON_PRIMARY,
            hover_color=Theme.CRIMSON_HOVER,
            checkmark_color="#FFFFFF",
        )
        self.transcript_toggle.pack(side="left")

        # Collapsible Section Inputs (Clipping)
        self.section_frame = ctk.CTkFrame(options_card, fg_color=Theme.BG_LIGHT, corner_radius=8)
        self.section_frame.grid_columnconfigure(0, weight=1)
        self.section_frame.grid_columnconfigure(1, weight=1)

        start_box = ctk.CTkFrame(self.section_frame, fg_color="transparent")
        start_box.grid(row=0, column=0, padx=(12, 6), pady=(8, 2), sticky="ew")
        start_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(start_box, text="Start Time:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self.start_time_entry = ctk.CTkEntry(start_box, placeholder_text="00:00 (e.g. 01:30)", height=32, font=ctk.CTkFont(size=11))
        self.start_time_entry.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        end_box = ctk.CTkFrame(self.section_frame, fg_color="transparent")
        end_box.grid(row=0, column=1, padx=(6, 12), pady=(8, 2), sticky="ew")
        end_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(end_box, text="End Time:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self.end_time_entry = ctk.CTkEntry(end_box, placeholder_text="Leave blank for end (e.g. 03:45)", height=32, font=ctk.CTkFont(size=11))
        self.end_time_entry.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        self.section_hint_label = ctk.CTkLabel(
            self.section_frame,
            text="💡 Formats: MM:SS, HH:MM:SS, or seconds (e.g. 01:30, 90, 01:15:30)",
            font=ctk.CTkFont(size=10),
            text_color=Theme.TEXT_SECONDARY,
        )
        self.section_hint_label.grid(row=1, column=0, columnspan=2, padx=12, pady=(2, 8), sticky="w")

        # Collapsible Subtitles Frame
        self.transcript_frame = ctk.CTkFrame(options_card, fg_color=Theme.BG_LIGHT, corner_radius=8)
        self.transcript_frame.grid_columnconfigure(0, weight=1)
        self.transcript_frame.grid_columnconfigure(1, weight=1)

        lang_box = ctk.CTkFrame(self.transcript_frame, fg_color="transparent")
        lang_box.grid(row=0, column=0, padx=(12, 6), pady=(8, 2), sticky="ew")
        lang_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lang_box, text="Subtitle Language:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self.sub_langs_var = tk.StringVar(value="en (English)")
        self.sub_langs_menu = ctk.CTkOptionMenu(
            lang_box,
            variable=self.sub_langs_var,
            values=["en (English)", "ar (Arabic)", "es (Spanish)", "all (All Available)"],
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color=Theme.BTN_SUBTLE_BG,
            button_color=Theme.BTN_SECONDARY_BG,
            button_hover_color=Theme.BTN_SECONDARY_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_fg_color=Theme.CARD_BG,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            dropdown_hover_color=Theme.BTN_SUBTLE_HOVER,
        )
        self.sub_langs_menu.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        fmt_box = ctk.CTkFrame(self.transcript_frame, fg_color="transparent")
        fmt_box.grid(row=0, column=1, padx=(6, 12), pady=(8, 2), sticky="ew")
        fmt_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(fmt_box, text="Subtitle Format:", font=ctk.CTkFont(size=11, weight="bold"), text_color=Theme.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self.sub_format_var = tk.StringVar(value="srt")
        self.sub_format_menu = ctk.CTkOptionMenu(
            fmt_box,
            variable=self.sub_format_var,
            values=["srt", "vtt", "ass", "lrc"],
            font=ctk.CTkFont(size=11),
            height=32,
            fg_color=Theme.BTN_SUBTLE_BG,
            button_color=Theme.BTN_SECONDARY_BG,
            button_hover_color=Theme.BTN_SECONDARY_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_fg_color=Theme.CARD_BG,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            dropdown_hover_color=Theme.BTN_SUBTLE_HOVER,
        )
        self.sub_format_menu.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        sub_checks_frame = ctk.CTkFrame(self.transcript_frame, fg_color="transparent")
        sub_checks_frame.grid(row=1, column=0, columnspan=2, padx=12, pady=(4, 8), sticky="ew")

        self.auto_subs_var = tk.BooleanVar(value=True)
        self.auto_subs_check = ctk.CTkCheckBox(
            sub_checks_frame,
            text="Include auto-generated captions",
            variable=self.auto_subs_var,
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_PRIMARY,
            fg_color=Theme.CRIMSON_PRIMARY,
            hover_color=Theme.CRIMSON_HOVER,
            checkmark_color="#FFFFFF",
        )
        self.auto_subs_check.pack(side="left", padx=(0, 16))

        self.embed_subs_var = tk.BooleanVar(value=False)
        self.embed_subs_check = ctk.CTkCheckBox(
            sub_checks_frame,
            text="Embed in video container",
            variable=self.embed_subs_var,
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_PRIMARY,
            fg_color=Theme.CRIMSON_PRIMARY,
            hover_color=Theme.CRIMSON_HOVER,
            checkmark_color="#FFFFFF",
        )
        self.embed_subs_check.pack(side="left")

        # Collapsible Playlist Scope Frame (Visible when video-in-playlist / mix is detected)
        self.playlist_scope_frame = ctk.CTkFrame(options_card, fg_color=Theme.BG_LIGHT, corner_radius=8)
        self.playlist_scope_frame.grid_columnconfigure(0, weight=1)

        scope_header_box = ctk.CTkFrame(self.playlist_scope_frame, fg_color="transparent")
        scope_header_box.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            scope_header_box,
            text="📋 Video in Playlist/Mix Detected — Choose Download Scope:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left")

        self.playlist_scope_var = tk.StringVar(value="single")
        self.playlist_scope_segmented = ctk.CTkSegmentedButton(
            self.playlist_scope_frame,
            values=["🎬 Single Video (Recommended)", "📑 Entire Playlist Batch"],
            font=ctk.CTkFont(size=11, weight="bold"),
            height=32,
            selected_color=Theme.CRIMSON_PRIMARY,
            selected_hover_color=Theme.CRIMSON_HOVER,
            unselected_color=Theme.BTN_SUBTLE_BG,
            unselected_hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            command=self._on_playlist_scope_changed,
        )
        self.playlist_scope_segmented.pack(fill="x", padx=12, pady=(0, 8))
        self.playlist_scope_segmented.set("🎬 Single Video (Recommended)")

        # 5. Destination Directory Card
        dest_card = GlassCard(scroll)
        dest_card.grid(row=3, column=0, padx=4, pady=(0, 10), sticky="ew")
        dest_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dest_card,
            text="💾 Save Location:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        dest_input_frame = ctk.CTkFrame(dest_card, fg_color="transparent")
        dest_input_frame.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
        dest_input_frame.grid_columnconfigure(0, weight=1)

        self.dest_entry = ctk.CTkEntry(
            dest_input_frame,
            height=38,
            font=ctk.CTkFont(size=11),
            corner_radius=8,
            border_width=1,
            border_color=Theme.CARD_BORDER,
        )
        self.dest_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.dest_entry.insert(0, self.config.get("download_directory", str(get_download_dir())))

        browse_btn = SecondaryButton(
            dest_input_frame,
            text="📁 Browse",
            width=90,
            height=38,
            command=self._browse_destination,
        )
        browse_btn.grid(row=0, column=1)

        # 6. Active Download & Status Card
        self.active_status_card = GlassCard(scroll)
        self.active_status_card.grid(row=4, column=0, padx=4, pady=(0, 10), sticky="ew")
        self.active_status_card.grid_columnconfigure(0, weight=1)

        status_header = ctk.CTkFrame(self.active_status_card, fg_color="transparent")
        status_header.grid(row=0, column=0, padx=16, pady=(10, 2), sticky="ew")
        status_header.grid_columnconfigure(0, weight=1)

        self.status_title_label = ctk.CTkLabel(
            status_header,
            text="📊 Download Progress & Status",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.status_title_label.grid(row=0, column=0, sticky="w")

        self.active_status_badge = ctk.CTkLabel(
            status_header,
            text="Idle",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=Theme.TEXT_MUTED,
            fg_color=Theme.BG_LIGHT,
            corner_radius=6,
            width=70,
            height=20,
        )
        self.active_status_badge.grid(row=0, column=1, sticky="e")

        self.active_item_label = ctk.CTkLabel(
            self.active_status_card,
            text="Ready to download",
            font=ctk.CTkFont(size=12),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        )
        self.active_item_label.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="ew")

        self.main_progress_bar = StyledProgressBar(self.active_status_card)
        self.main_progress_bar.grid(row=2, column=0, padx=16, pady=(2, 4), sticky="ew")
        self.main_progress_bar.set(0)

        # Metrics bar
        metrics_bar = ctk.CTkFrame(self.active_status_card, fg_color="transparent")
        metrics_bar.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="ew")
        metrics_bar.grid_columnconfigure(0, weight=1)
        metrics_bar.grid_columnconfigure(1, weight=1)
        metrics_bar.grid_columnconfigure(2, weight=1)

        self.main_percent_label = ctk.CTkLabel(
            metrics_bar,
            text="0%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.CRIMSON_PRIMARY,
            anchor="w",
        )
        self.main_percent_label.grid(row=0, column=0, sticky="w")

        self.main_speed_label = ctk.CTkLabel(
            metrics_bar,
            text="Speed: --",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="center",
        )
        self.main_speed_label.grid(row=0, column=1, sticky="ew")

        self.main_eta_label = ctk.CTkLabel(
            metrics_bar,
            text="ETA: --",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="e",
        )
        self.main_eta_label.grid(row=0, column=2, sticky="e")

        # INLINE ERROR CONTAINER FOR ACTIVE CARD (CRITICAL - NO POP-UPS)
        self.main_error_banner = ctk.CTkFrame(
            self.active_status_card,
            fg_color=Theme.ERROR_LIGHT,
            border_width=1,
            border_color=Theme.ERROR_RED,
            corner_radius=6,
        )
        self.main_error_banner.grid_columnconfigure(0, weight=1)

        self.main_error_label = ctk.CTkLabel(
            self.main_error_banner,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.ERROR_RED,
            wraplength=600,
            justify="left",
            anchor="w",
        )
        self.main_error_label.grid(row=0, column=0, padx=12, pady=8, sticky="ew")

        self.main_retry_btn = CrimsonButton(
            self.main_error_banner,
            text="↺ Retry Download",
            width=120,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._retry_active_download,
        )
        self.main_retry_btn.grid(row=0, column=1, padx=(0, 10), pady=8)

        # -------------------------------------------------------------------
        # DOCKED ACTION BAR (Fixed at the bottom of the View)
        # -------------------------------------------------------------------
        action_bar = ctk.CTkFrame(view, fg_color=Theme.CARD_BG, corner_radius=0, border_width=1, border_color=Theme.CARD_BORDER)
        action_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        action_bar.grid_columnconfigure(0, weight=2)
        action_bar.grid_columnconfigure(1, weight=1)
        action_bar.grid_columnconfigure(2, weight=1)

        self.start_download_btn = CrimsonButton(
            action_bar,
            text="⬇ START DOWNLOAD",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44,
            command=self._start_download,
        )
        self.start_download_btn.grid(row=0, column=0, padx=(16, 8), pady=12, sticky="ew")

        self.cancel_download_btn = ctk.CTkButton(
            action_bar,
            text="❌ Cancel",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=44,
            corner_radius=8,
            fg_color=Theme.ERROR_LIGHT,
            hover_color=("#FECACA", "#5C1111"),
            text_color=Theme.ERROR_RED,
            command=self._cancel_download,
            state="disabled",
        )
        self.cancel_download_btn.grid(row=0, column=1, padx=4, pady=12, sticky="ew")

        self.open_folder_btn = SecondaryButton(
            action_bar,
            text="📁 Open Folder",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=44,
            command=self._open_download_folder,
        )
        self.open_folder_btn.grid(row=0, column=2, padx=(8, 16), pady=12, sticky="ew")

        return view

    # -----------------------------------------------------------------------
    # VIEW 2: Download Queue & History
    # -----------------------------------------------------------------------

    def _create_queue_view(self) -> ctk.CTkFrame:
        """Construct the Download Queue & History view with inline error cards."""
        view = ctk.CTkFrame(self.content_area, fg_color=Theme.BG_LIGHT)
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(1, weight=1)

        # Header Bar
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="📋 Download Queue & History",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        )
        title.grid(row=0, column=0, sticky="w")

        clear_btn = SecondaryButton(
            header,
            text="🗑️ Clear Finished",
            width=120,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._clear_completed_queue,
        )
        clear_btn.grid(row=0, column=1, sticky="e")

        # Scrollable list of cards
        self.queue_scroll = ctk.CTkScrollableFrame(view, fg_color="transparent")
        self.queue_scroll.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="nsew")
        self.queue_scroll.grid_columnconfigure(0, weight=1)

        # Placeholder label
        self.queue_placeholder = ctk.CTkLabel(
            self.queue_scroll,
            text="📭 No items in queue\n\nDownloads will appear here with live progress and inline status.",
            font=ctk.CTkFont(size=13),
            text_color=Theme.TEXT_MUTED,
            justify="center",
        )
        self.queue_placeholder.grid(row=0, column=0, pady=80)

        return view

    # -----------------------------------------------------------------------
    # VIEW 3: Settings Panel
    # -----------------------------------------------------------------------

    def _create_settings_view(self) -> ctk.CTkFrame:
        """Construct the Settings configuration view."""
        view = ctk.CTkFrame(self.content_area, fg_color=Theme.BG_LIGHT)
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(view, fg_color="transparent")
        scroll.grid(row=0, column=0, padx=20, pady=16, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # 1. Appearance & Theme Configuration Card
        theme_card = GlassCard(scroll)
        theme_card.grid(row=0, column=0, padx=4, pady=(0, 12), sticky="ew")
        theme_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            theme_card,
            text="🎨 Appearance & Theme",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(14, 4), sticky="w")

        ctk.CTkLabel(
            theme_card,
            text="Switch between Light Mode (Light Grey & Crimson), Dark Mode (Dark Slate & Crimson), or System Auto.",
            font=ctk.CTkFont(size=11),
            text_color=Theme.TEXT_SECONDARY,
        ).grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        theme_select_frame = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_select_frame.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")
        theme_select_frame.grid_columnconfigure(0, weight=1)

        saved_mode = self.config.get("appearance_mode", self.config.get("theme", "light"))
        settings_mode_val_map = {"light": "☀️ Light Mode", "dark": "🌙 Dark Mode", "system": "💻 System Default"}
        settings_initial_val = settings_mode_val_map.get(saved_mode, "☀️ Light Mode")

        self.settings_theme_var = tk.StringVar(value=settings_initial_val)
        self.settings_theme_segmented = ctk.CTkSegmentedButton(
            theme_select_frame,
            values=["☀️ Light Mode", "🌙 Dark Mode", "💻 System Default"],
            variable=self.settings_theme_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            selected_color=Theme.CRIMSON_PRIMARY,
            selected_hover_color=Theme.CRIMSON_HOVER,
            unselected_color=Theme.BTN_SUBTLE_BG,
            unselected_hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            command=self._on_settings_theme_change,
        )
        self.settings_theme_segmented.pack(fill="x")

        # 2. General Preferences Card
        general_card = GlassCard(scroll)
        general_card.grid(row=1, column=0, padx=4, pady=(0, 12), sticky="ew")
        general_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            general_card,
            text="📁 Download Preferences",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        ctk.CTkLabel(
            general_card,
            text="Default Download Directory:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.TEXT_SECONDARY,
        ).grid(row=1, column=0, padx=16, pady=(0, 4), sticky="w")

        path_frame = ctk.CTkFrame(general_card, fg_color="transparent")
        path_frame.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")
        path_frame.grid_columnconfigure(0, weight=1)

        self.settings_path_entry = ctk.CTkEntry(
            path_frame,
            height=38,
            font=ctk.CTkFont(size=11),
            corner_radius=8,
            border_width=1,
            border_color=Theme.CARD_BORDER,
        )
        self.settings_path_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.settings_path_entry.insert(0, self.config.get("download_directory", str(get_download_dir())))

        browse_btn = SecondaryButton(
            path_frame,
            text="📁 Browse",
            width=90,
            height=38,
            command=self._browse_settings_path,
        )
        browse_btn.grid(row=0, column=1)

        # 3. System Diagnostics & Installed Versions Card
        diag_card = GlassCard(scroll)
        diag_card.grid(row=2, column=0, padx=4, pady=(0, 12), sticky="ew")
        diag_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            diag_card,
            text="🛠️ System & Dependency Diagnostics",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        dep_versions = get_dependency_versions()
        ffmpeg_v = dep_versions.get("ffmpeg", "Bundled / Auto-Managed")
        deno_v = dep_versions.get("deno", "Bundled / Auto-Managed")
        ytdlp_v = dep_versions.get("yt-dlp", "Bundled Engine")

        diag_text = (
            f"• Downloadyha Version: v{__version__}\n"
            f"• FFmpeg Audio/Video Engine: {ffmpeg_v}\n"
            f"• Deno JavaScript Runtime: {deno_v}\n"
            f"• Core Downloader Backend: {ytdlp_v}\n"
            f"• Platform: {sys.platform.capitalize()} ({sys.version.split()[0]})"
        )

        diag_label = ctk.CTkLabel(
            diag_card,
            text=diag_text,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=Theme.TEXT_SECONDARY,
            justify="left",
            anchor="w",
        )
        diag_label.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="w")

        # 4. About & Code Ownership Card
        about_card = GlassCard(scroll)
        about_card.grid(row=3, column=0, padx=4, pady=(0, 12), sticky="ew")
        about_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            about_card,
            text="ℹ️ About & Ownership",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        about_text = (
            f"• Application: Downloadyha Desktop GUI\n"
            f"• Version: v{__version__}\n"
            f"• Author & Developer: Ahmed Tarek Zaher\n"
            f"• Copyright: © 2026 Ahmed Tarek Zaher. All rights reserved.\n"
            f"• License: MIT License\n"
            f"• Repository: https://github.com/ahmed-tarek-2004/DownloadYha"
        )

        about_label = ctk.CTkLabel(
            about_card,
            text=about_text,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=Theme.TEXT_SECONDARY,
            justify="left",
            anchor="w",
        )
        about_label.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="w")

        # 5. Save Settings Button
        self.save_settings_btn = CrimsonButton(
            scroll,
            text="💾 Save Preferences",
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save_settings,
        )
        self.save_settings_btn.grid(row=4, column=0, padx=4, pady=(4, 16), sticky="ew")

        # Inline confirmation label
        self.settings_feedback_label = ctk.CTkLabel(
            scroll,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=Theme.SUCCESS_GREEN,
        )
        self.settings_feedback_label.grid(row=5, column=0, pady=(0, 8))

        return view

    # -----------------------------------------------------------------------
    # System Health Actions: Update & Repair Subsystems
    # -----------------------------------------------------------------------

    def _check_for_updates(self):
        """Asynchronously check for updates using downloadyha.updater."""
        if self.is_checking_updates:
            return

        self.is_checking_updates = True
        self.health_status_dot.configure(text="● Checking...", text_color=Theme.CRIMSON_PRIMARY)
        self.btn_check_updates.configure(text="⏳ Checking...", state="disabled")
        self.health_feedback_label.configure(text="Contacting GitHub Releases API...", text_color=Theme.TEXT_SECONDARY)
        self.health_feedback_label.pack(fill="x", padx=10, pady=(0, 6))

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
        self.btn_check_updates.configure(text="🔄 Check for Updates", state="normal")

        if new_version:
            self.health_status_dot.configure(text="● Update Avail", text_color=Theme.CRIMSON_PRIMARY)
            self.health_feedback_label.configure(
                text=f"New version {new_version} available! Click below to install.",
                text_color=Theme.CRIMSON_PRIMARY,
            )
            # Switch update button to install action
            self.btn_check_updates.configure(
                text=f"⬇️ Update to {new_version}",
                fg_color=Theme.CRIMSON_PRIMARY,
                text_color="#FFFFFF",
                hover_color=Theme.CRIMSON_HOVER,
                command=lambda: self._install_update(new_version),
            )
        else:
            self.health_status_dot.configure(text="● Up to Date", text_color=Theme.SUCCESS_GREEN)
            self.health_feedback_label.configure(
                text=f"✓ You are running the latest version (v{__version__}).",
                text_color=Theme.SUCCESS_GREEN,
            )

    def _on_update_check_error(self, error_str: str):
        """Handle update check error on main thread."""
        self.is_checking_updates = False
        self.btn_check_updates.configure(text="🔄 Check for Updates", state="normal")
        self.health_status_dot.configure(text="● Ready", text_color=Theme.TEXT_SECONDARY)
        self.health_feedback_label.configure(
            text=f"⚠️ Update check failed: {error_str}",
            text_color=Theme.ERROR_RED,
        )

    def _install_update(self, version_str: str):
        """Execute binary update."""
        self.btn_check_updates.configure(text="⏳ Installing Update...", state="disabled")
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

    def _on_update_installed(self, success: bool, msg: str):
        """Handle post-update installation result."""
        self.btn_check_updates.configure(
            text="🔄 Check for Updates",
            state="normal",
            fg_color=Theme.BTN_SUBTLE_BG,
            hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
        )
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
        if self.is_repairing_dependencies:
            return

        self.is_repairing_dependencies = True
        self.health_status_dot.configure(text="● Repairing...", text_color=Theme.CRIMSON_PRIMARY)
        self.btn_verify_repair.configure(text="⏳ Repairing...", state="disabled")
        self.health_feedback_label.configure(
            text="Verifying FFmpeg, FFprobe & Deno binaries...",
            text_color=Theme.TEXT_SECONDARY,
        )
        self.health_feedback_label.pack(fill="x", padx=10, pady=(0, 6))

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
        self.btn_verify_repair.configure(text="🛠️🛡️ Verify & Repair App", state="normal")
        if success:
            self.health_status_dot.configure(text="● Healthy", text_color=Theme.SUCCESS_GREEN)
            self.health_feedback_label.configure(
                text="✓ All helper binaries verified and ready!",
                text_color=Theme.SUCCESS_GREEN,
            )
        else:
            self.health_status_dot.configure(text="● Issue", text_color=Theme.ERROR_RED)
            self.health_feedback_label.configure(
                text="⚠️ Some dependencies could not be repaired.",
                text_color=Theme.ERROR_RED,
            )

    def _on_repair_error(self, err_msg: str):
        """Handle repair error."""
        self.is_repairing_dependencies = False
        self.btn_verify_repair.configure(text="🛠️🛡️ Verify & Repair App", state="normal")
        self.health_status_dot.configure(text="● Error", text_color=Theme.ERROR_RED)
        self.health_feedback_label.configure(
            text=f"❌ Repair error: {err_msg}",
            text_color=Theme.ERROR_RED,
        )

    # -----------------------------------------------------------------------
    # Metadata Fetching & Dynamic Quality Management
    # -----------------------------------------------------------------------

    def _paste_url(self):
        """Paste clipboard URL and fetch info automatically."""
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
            self.url_feedback_label.configure(
                text="⚠️ Please enter or paste a valid URL first.",
                text_color=Theme.WARNING_AMBER,
            )
            return

        if self.is_fetching_info:
            return

        self.is_fetching_info = True
        self.url_feedback_label.configure(text="", text_color=Theme.TEXT_SECONDARY)
        self.fetch_btn.configure(text="⏳ Fetching...", state="disabled")
        self.media_badge.configure(text="⏳ Analyzing...", fg_color=Theme.BG_SECONDARY, text_color=Theme.CRIMSON_PRIMARY)
        self.media_title_label.configure(text="Analyzing video title, creator, and quality streams...")

        def worker():
            try:
                info = get_media_info(url, extract_flat="in_playlist")
                if info:
                    self.after(0, self._on_media_info_fetched, info, url)
                else:
                    self.after(0, self._on_media_info_error, "Could not extract metadata from this URL.")
            except Exception as e:
                self.after(0, self._on_media_info_error, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_media_info_fetched(self, info: Dict[str, Any], url: str):
        """Handle successfully fetched media metadata."""
        self.media_info = info
        self.last_fetched_url = url
        self.is_fetching_info = False

        self.fetch_btn.configure(text="🔍 Fetch Info", state="normal")

        is_video_in_pl = is_video_in_playlist_url(url)
        is_pure_pl = is_pure_playlist_url(url) or (is_playlist(info) and not has_video_id(url))
        title = info.get("title") or "Media"
        uploader = info.get("uploader") or info.get("channel") or "Unknown Creator"

        if is_video_in_pl:
            duration_sec = info.get("duration")
            duration_str = format_duration(duration_sec) if duration_sec else "Unknown"
            views_raw = info.get("view_count")
            views_str = f"{format_number(views_raw)} views" if views_raw else "N/A"

            self.available_video_qualities = get_video_qualities(info)
            max_q = f"{self.available_video_qualities[0]}p" if self.available_video_qualities else "Best"

            self.media_badge.configure(
                text="🎬 Video in Playlist",
                fg_color=Theme.CRIMSON_LIGHT,
                text_color=Theme.CRIMSON_PRIMARY,
            )
            self.media_channel_label.configure(text=f"Channel: {uploader}")
            self.media_title_label.configure(text=f"🎬 {title}")
            self.media_meta_label.configure(
                text=f"⏱ Duration: {duration_str} • 👁 {views_str} • ⚡ Max Quality: {max_q} • 📋 Playlist context detected"
            )
            if hasattr(self, "playlist_scope_frame") and self.playlist_scope_frame:
                self.playlist_scope_frame.grid(row=5, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="ew")
                self.playlist_scope_segmented.set("🎬 Single Video (Recommended)")
                self.playlist_scope_var.set("single")

        elif is_pure_pl:
            if hasattr(self, "playlist_scope_frame") and self.playlist_scope_frame:
                self.playlist_scope_frame.grid_forget()
            entries = get_playlist_entries(info)
            count = len(entries) if entries else info.get("playlist_count", "Multiple")
            self.available_video_qualities = []

            self.media_badge.configure(
                text="📑 Playlist",
                fg_color=Theme.CRIMSON_LIGHT,
                text_color=Theme.CRIMSON_PRIMARY,
            )
            self.media_channel_label.configure(text=f"Channel: {uploader}")
            self.media_title_label.configure(text=f"📑 {title}")
            self.media_meta_label.configure(text=f"Total Items: {count} videos • Type: Full Playlist Batch")

        else:
            if hasattr(self, "playlist_scope_frame") and self.playlist_scope_frame:
                self.playlist_scope_frame.grid_forget()
            duration_sec = info.get("duration")
            duration_str = format_duration(duration_sec) if duration_sec else "Unknown"
            views_raw = info.get("view_count")
            views_str = f"{format_number(views_raw)} views" if views_raw else "N/A"

            self.available_video_qualities = get_video_qualities(info)
            max_q = f"{self.available_video_qualities[0]}p" if self.available_video_qualities else "Best"

            self.media_badge.configure(
                text="🎬 Single Video",
                fg_color=Theme.BG_SECONDARY,
                text_color=Theme.TEXT_PRIMARY,
            )
            self.media_channel_label.configure(text=f"Channel: {uploader}")
            self.media_title_label.configure(text=f"🎬 {title}")
            self.media_meta_label.configure(
                text=f"⏱ Duration: {duration_str} • 👁 {views_str} • ⚡ Max Quality: {max_q}"
            )

        self._update_quality_options()
        self.url_feedback_label.configure(text="✓ Metadata successfully fetched.", text_color=Theme.SUCCESS_GREEN)

    def _on_media_info_error(self, error: str):
        """Handle error during media metadata fetch."""
        self.is_fetching_info = False
        self.fetch_btn.configure(text="🔍 Fetch Info", state="normal")
        self.media_badge.configure(text="⚠️ Error", fg_color=Theme.ERROR_LIGHT, text_color=Theme.ERROR_RED)
        self.media_title_label.configure(text="Could not inspect media")
        self.url_feedback_label.configure(text=f"⚠️ {error}", text_color=Theme.ERROR_RED)

    def _on_playlist_scope_changed(self, value: str):
        """Handle playlist scope switch (Single Video vs Entire Playlist)."""
        if "Entire Playlist" in value:
            self.playlist_scope_var.set("playlist")
        else:
            self.playlist_scope_var.set("single")
        self._update_quality_options()

    def _update_quality_options(self):
        """Update quality dropdown values dynamically based on format and media."""
        media_type = self.media_type_var.get().lower().replace("🎥 ", "").replace("🎵 ", "")

        if media_type == "audio":
            self.quality_menu.configure(values=AUDIO_QUALITIES)
            if self.quality_var.get() not in AUDIO_QUALITIES:
                self.quality_var.set(AUDIO_QUALITIES[0])
        else:
            is_single = (
                self.media_info
                and not is_pure_playlist_url(self.last_fetched_url)
                and (not is_playlist(self.media_info) or (hasattr(self, "playlist_scope_var") and self.playlist_scope_var.get() == "single"))
                and self.available_video_qualities
            )
            if is_single:
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
        """Handle media format switch (Video vs Audio)."""
        self._update_quality_options()

    def _on_section_toggled(self):
        """Toggle section clipping inputs."""
        if self.section_toggle_var.get():
            self.section_frame.grid(row=7, column=0, padx=10, pady=(2, 6), sticky="ew")
        else:
            self.section_frame.grid_forget()

    def _on_transcript_toggled(self):
        """Toggle subtitle & transcript inputs."""
        if self.transcript_toggle_var.get():
            self._fetch_subtitles_for_url()
            self.transcript_frame.grid(row=4, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="ew")
        else:
            self.transcript_frame.grid_forget()

    def _fetch_subtitles_for_url(self):
        """Query available subtitles for the entered URL."""
        url = self.url_entry.get().strip()
        if not url:
            return

        def worker():
            try:
                subtitles = get_available_subtitles(url)
                self.after(0, self._populate_subtitles, subtitles)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _populate_subtitles(self, subtitles: List[Dict[str, Any]]):
        """Populate language dropdown with fetched languages."""
        if not subtitles:
            return

        lang_codes = sorted(list(set([sub.get("lang", "") for sub in subtitles if sub.get("lang")])))
        if lang_codes:
            opts = [f"{c} ({c.upper()})" for c in lang_codes]
            opts.insert(0, "all (All Available)")
            self.sub_langs_menu.configure(values=opts)
            self.sub_langs_var.set(opts[1] if len(opts) > 1 else opts[0])

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

    def _browse_settings_path(self):
        """Open directory picker for default settings."""
        try:
            init_dir = self.settings_path_entry.get().strip() if hasattr(self, "settings_path_entry") else ""
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
                self.settings_path_entry.delete(0, tk.END)
                self.settings_path_entry.insert(0, normalized_folder)
        except Exception:
            pass
        finally:
            try:
                self.lift()
                self.focus_force()
            except Exception:
                pass

    def _save_settings(self):
        """Save preferences to configuration file."""
        new_dir = self.settings_path_entry.get().strip().strip("\"'")
        if new_dir:
            try:
                os.makedirs(new_dir, exist_ok=True)
            except Exception:
                pass
            self.config["download_directory"] = new_dir

        if hasattr(self, "settings_theme_segmented") and self.settings_theme_segmented:
            val = self.settings_theme_segmented.get()
            mode_map = {
                "☀️ Light Mode": "light",
                "🌙 Dark Mode": "dark",
                "💻 System Default": "system",
            }
            mode = mode_map.get(val, "light")
            self.set_theme_mode(mode)

        if save_config(self.config):
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, self.config["download_directory"])
            self.settings_feedback_label.configure(
                text="✓ Preferences saved successfully!",
                text_color=Theme.SUCCESS_GREEN,
            )
            self.after(3000, lambda: self.settings_feedback_label.configure(text=""))
        else:
            self.settings_feedback_label.configure(
                text="⚠️ Failed to save settings to disk.",
                text_color=Theme.ERROR_RED,
            )

    # -----------------------------------------------------------------------
    # Download Execution Engine & Thread Safety (Bug-Free Success/Fail Handling)
    # -----------------------------------------------------------------------

    def _start_download(self):
        """Validate inputs and launch the download task."""
        if self.is_downloading:
            return

        # Hide main error banner on fresh attempt
        self.main_error_banner.grid_forget()

        url = self.url_entry.get().strip()
        if not url:
            self.url_feedback_label.configure(text="⚠️ Please enter a video or playlist URL.", text_color=Theme.WARNING_AMBER)
            return

        dest_path = self.dest_entry.get().strip().strip("\"'")
        if not dest_path:
            self.url_feedback_label.configure(text="⚠️ Please specify a destination folder.", text_color=Theme.WARNING_AMBER)
            return

        try:
            os.makedirs(dest_path, exist_ok=True)
        except Exception as e:
            self.url_feedback_label.configure(text=f"⚠️ Cannot create destination directory: {e}", text_color=Theme.ERROR_RED)
            return

        # Validate section clipping
        start_time = None
        end_time = None
        if self.section_toggle_var.get():
            st_raw = self.start_time_entry.get().strip()
            et_raw = self.end_time_entry.get().strip()

            st_val = None
            et_val = None

            if st_raw:
                try:
                    st_val = parse_time_str(st_raw)
                    start_time = st_raw
                except ValueError as e:
                    self.url_feedback_label.configure(text=f"⚠️ Invalid start time format: {e}", text_color=Theme.ERROR_RED)
                    return

            if et_raw:
                try:
                    et_val = parse_time_str(et_raw)
                    end_time = et_raw
                except ValueError as e:
                    self.url_feedback_label.configure(text=f"⚠️ Invalid end time format: {e}", text_color=Theme.ERROR_RED)
                    return

            if st_val is not None and et_val is not None and et_val <= st_val:
                err_msg = f"End time ({et_raw}) must be greater than start time ({st_raw})."
                self.url_feedback_label.configure(text=f"⚠️ {err_msg}", text_color=Theme.ERROR_RED)
                try:
                    messagebox.showerror("Invalid Time Range", err_msg)
                except Exception:
                    pass
                return

        # Parse media type and quality
        media_type = self.media_type_var.get().lower().replace("🎥 ", "").replace("🎵 ", "")
        quality_str = self.quality_var.get()
        if media_type == "video":
            quality = self._parse_video_quality(quality_str)
        else:
            quality = self._parse_audio_quality(quality_str)

        # Prepare subtitles config
        subs_kwargs: Dict[str, Any] = {}
        if self.transcript_toggle_var.get():
            lang_choice = self.sub_langs_var.get().strip()
            lang_code = lang_choice.split()[0] if lang_choice else "en"
            subs_kwargs = {
                "write_subtitles": True,
                "write_auto_subs": self.auto_subs_var.get(),
                "sub_langs": lang_code,
                "sub_format": self.sub_format_var.get(),
                "embed_subs": self.embed_subs_var.get(),
            }

        title = (self.media_info.get("title") if self.media_info else None) or "Media Download"
        uploader = (self.media_info.get("uploader") if self.media_info else None) or "Unknown"

        # Determine playlist vs single video mode
        if is_pure_playlist_url(url):
            is_pl_task = True
        elif is_video_in_playlist_url(url):
            is_pl_task = (hasattr(self, "playlist_scope_var") and self.playlist_scope_var and self.playlist_scope_var.get() == "playlist")
        else:
            is_pl_task = False

        # Create Task
        task = DownloadTask(
            url=url,
            dest_path=dest_path,
            media_type=media_type,
            quality=quality,
            quality_label=quality_str,
            title=title,
            uploader=uploader,
            start_time=start_time,
            end_time=end_time,
            subs_kwargs=subs_kwargs,
            is_playlist=is_pl_task,
        )

        self._enqueue_and_run_task(task)

    def _enqueue_and_run_task(self, task: DownloadTask):
        """Enqueue task and start execution."""
        self.download_queue.append(task)
        self.active_task = task

        # Update Queue Badge in Sidebar
        self.btn_nav_queue.configure(text=f"📋  Download Queue ({len(self.download_queue)})")

        # Set UI to downloading state
        self.is_downloading = True
        self.cancel_requested = False

        self.start_download_btn.configure(state="disabled")
        self.cancel_download_btn.configure(state="normal")
        self.active_status_badge.configure(text="Active", text_color=Theme.CRIMSON_PRIMARY, fg_color=Theme.CRIMSON_LIGHT)
        self.active_item_label.configure(text=f"Downloading: {task.title}", text_color=Theme.TEXT_PRIMARY)
        self.main_progress_bar.set(0)
        self.main_percent_label.configure(text="0%")
        self.main_speed_label.configure(text="Speed: Starting...")
        self.main_eta_label.configure(text="ETA: Calculating...")

        task.status = "downloading"
        self._refresh_queue_view()

        # Spawn download thread
        self.download_thread = threading.Thread(target=self._download_worker, args=(task,), daemon=True)
        self.download_thread.start()

    def _download_worker(self, task: DownloadTask):
        """
        Background worker executing the download.
        Guarantees STRICT success/failure separation so that failed downloads
        NEVER invoke the completion callback.
        """
        try:
            # 1. Dependency check
            ffmpeg_ok, _ = check_ffmpeg()
            if not ffmpeg_ok:
                self.after(0, self._set_active_status_text, "Setting up FFmpeg stream merging components...")
                check_dependencies(auto_download=True)

            # 2. Extract metadata if needed
            if not self.media_info or self.last_fetched_url != task.url:
                noplaylist = False if (task.is_playlist is True) or (is_pure_playlist_url(task.url) and task.is_playlist is not False) else True
                info = get_media_info(task.url, extract_flat="in_playlist", noplaylist=noplaylist)
                if info:
                    task.title = info.get("title", task.title)
                    task.uploader = info.get("uploader", task.uploader)
                    self.after(0, self._on_media_info_fetched, info, task.url)
            else:
                info = self.media_info

            if task.is_playlist is not None:
                is_pl = task.is_playlist
            elif is_pure_playlist_url(task.url):
                is_pl = True
            elif has_video_id(task.url):
                is_pl = False
            else:
                is_pl = is_playlist(info) or is_pure_playlist_url(task.url)

            # Progress Hook
            def progress_callback(data: Dict[str, Any]):
                if self.cancel_requested:
                    raise KeyboardInterrupt("Download cancelled by user.")

                status = data.get("status", "")
                if status == "downloading":
                    percent = data.get("percent", 0.0)
                    speed_str = data.get("speed_str", "--")
                    eta_str = data.get("eta_str", "--")
                    item_title = data.get("item_title", task.title)
                    self.after(0, self._update_download_progress, percent, speed_str, eta_str, item_title, task)
                elif status == "finished":
                    self.after(0, self._set_active_status_text, "Processing and merging streams into final file...")

            # 3. Perform yt-dlp Download Execution
            if is_pl:
                quality_arg = str(task.quality) if (task.media_type == "video" and task.quality > 0) else ("best" if task.media_type == "video" else task.quality)
                result: DownloadResult = download_playlist(
                    url=task.url,
                    download_path=task.dest_path,
                    media_type=task.media_type,
                    quality=quality_arg,
                    start_time=task.start_time,
                    end_time=task.end_time,
                    progress_callback=progress_callback,
                    **task.subs_kwargs,
                )
            else:
                if task.media_type == "video":
                    result = download_video(
                        url=task.url,
                        download_path=task.dest_path,
                        height=task.quality,
                        start_time=task.start_time,
                        end_time=task.end_time,
                        progress_callback=progress_callback,
                        **task.subs_kwargs,
                    )
                else:
                    result = download_audio(
                        url=task.url,
                        download_path=task.dest_path,
                        quality=task.quality,
                        start_time=task.start_time,
                        end_time=task.end_time,
                        progress_callback=progress_callback,
                        **task.subs_kwargs,
                    )

            # 4. Strict Result Dispatch (No false successes!)
            if result is not None and getattr(result, "success", False):
                task.saved_directory = result.download_directory
                task.completed_files = result.files
                self.after(0, self._on_download_complete, task, result)
            else:
                err_msg = ""
                if result:
                    err_msg = result.message or ("; ".join(result.errors) if result.errors else "Download failed.")
                if not err_msg:
                    err_msg = "Download failed due to an unknown network or format error."
                task.error_message = err_msg
                self.after(0, self._on_download_failed, task, err_msg)

        except KeyboardInterrupt:
            self.after(0, self._on_download_cancelled, task)
        except Exception as e:
            err_msg = str(e) or "An unexpected exception occurred during download."
            task.error_message = err_msg
            self.after(0, self._on_download_failed, task, err_msg)

    # -----------------------------------------------------------------------
    # Thread-Safe UI Update Handlers (Dispatched strictly via self.after)
    # -----------------------------------------------------------------------

    def _update_download_progress(
        self,
        percent: float,
        speed: str,
        eta: str,
        title: str,
        task: DownloadTask
    ):
        """Update live download progress indicators."""
        if not self.is_downloading or task != self.active_task:
            return

        self.main_progress_bar.set(percent / 100.0)
        self.main_percent_label.configure(text=f"{percent:.1f}%")
        self.main_speed_label.configure(text=f"Speed: {speed}")
        self.main_eta_label.configure(text=f"ETA: {eta}")
        self.active_item_label.configure(text=f"Downloading: {title}")

        # Update card in queue view if created
        if self.active_card:
            self.active_card.update_progress(percent, speed, eta, title)

    def _set_active_status_text(self, text: str):
        """Set active item text label."""
        self.active_item_label.configure(text=text)

    def _on_download_complete(self, task: DownloadTask, result: DownloadResult):
        """Handle successful download completion."""
        self.is_downloading = False
        task.status = "completed"

        self.start_download_btn.configure(state="normal")
        self.cancel_download_btn.configure(state="disabled")

        self.main_progress_bar.set(1.0)
        self.main_percent_label.configure(text="100%")
        self.active_status_badge.configure(text="✓ Saved", text_color=Theme.SUCCESS_GREEN, fg_color=Theme.SUCCESS_LIGHT)
        self.active_item_label.configure(
            text=f"✓ Download complete! Saved to {task.saved_directory or task.dest_path}",
            text_color=Theme.SUCCESS_GREEN,
        )

        self._refresh_queue_view()

    def _on_download_failed(self, task: DownloadTask, error_msg: str):
        """
        Handle download failure with 100% INLINE ERROR HANDLING (ZERO POP-UPS).
        """
        self.is_downloading = False
        task.status = "failed"
        task.error_message = error_msg

        self.start_download_btn.configure(state="normal")
        self.cancel_download_btn.configure(state="disabled")

        # Update active card
        self.active_status_badge.configure(text="✕ Failed", text_color=Theme.ERROR_RED, fg_color=Theme.ERROR_LIGHT)
        self.active_item_label.configure(
            text="Download was interrupted or encountered an error.",
            text_color=Theme.ERROR_RED,
        )

        # Show inline error banner with Retry button in the active panel
        self.main_error_label.configure(text=f"⚠️ Error: {error_msg}")
        self.main_error_banner.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="ew")

        # Refresh queue so the failed card gets the Crimson border and Retry button
        self._refresh_queue_view()

    def _on_download_cancelled(self, task: DownloadTask):
        """Handle user-initiated download cancellation."""
        self.is_downloading = False
        self.cancel_requested = False
        task.status = "cancelled"

        self.start_download_btn.configure(state="normal")
        self.cancel_download_btn.configure(state="disabled")

        self.active_status_badge.configure(text="Cancelled", text_color=Theme.WARNING_AMBER, fg_color=Theme.WARNING_LIGHT)
        self.active_item_label.configure(text="Download was cancelled by user.", text_color=Theme.WARNING_AMBER)

        self._refresh_queue_view()

    def _cancel_download(self):
        """Request immediate download cancellation."""
        if self.is_downloading:
            self.cancel_requested = True
            self.active_status_badge.configure(text="Cancelling...", text_color=Theme.WARNING_AMBER)
            self.active_item_label.configure(text="Cancelling current operation...")

    def _retry_active_download(self):
        """Retry from the main download view error banner."""
        if self.active_task:
            self.main_error_banner.grid_forget()
            self._retry_task(self.active_task)

    def _retry_task(self, task: DownloadTask):
        """Retry a failed or cancelled task directly from its card."""
        if self.is_downloading:
            return

        task.status = "queued"
        task.error_message = ""
        task.progress = 0.0
        self._enqueue_and_run_task(task)

    def _remove_task(self, task: DownloadTask):
        """Remove a task from the download queue."""
        if task in self.download_queue:
            self.download_queue.remove(task)
            self.btn_nav_queue.configure(text=f"📋  Download Queue ({len(self.download_queue)})")
            self._refresh_queue_view()

    def _clear_completed_queue(self):
        """Remove finished, failed, or cancelled tasks from queue."""
        self.download_queue = [t for t in self.download_queue if t.status == "downloading"]
        self.btn_nav_queue.configure(text=f"📋  Download Queue ({len(self.download_queue)})")
        self._refresh_queue_view()

    def _refresh_queue_view(self):
        """Re-render all download cards in the Queue view."""
        for widget in self.queue_scroll.winfo_children():
            widget.destroy()

        if not self.download_queue:
            self.queue_placeholder = ctk.CTkLabel(
                self.queue_scroll,
                text="📭 No items in queue\n\nDownloads will appear here with live progress and inline status.",
                font=ctk.CTkFont(size=13),
                text_color=Theme.TEXT_MUTED,
                justify="center",
            )
            self.queue_placeholder.grid(row=0, column=0, pady=80)
            self.active_card = None
            return

        self.active_card = None
        for idx, task in enumerate(self.download_queue):
            card = DownloadQueueCard(
                self.queue_scroll,
                task=task,
                on_retry=self._retry_task,
                on_remove=self._remove_task,
            )
            card.grid(row=idx, column=0, padx=4, pady=4, sticky="ew")
            if task.status == "downloading":
                self.active_card = card

    def _open_download_folder(self):
        """Open the target folder in file manager."""
        folder = self.dest_entry.get().strip().strip("\"'")
        if folder and os.path.exists(folder):
            try:
                if sys.platform == "win32":
                    os.startfile(folder)
                elif sys.platform == "darwin":
                    os.system(f'open "{folder}"')
                else:
                    os.system(f'xdg-open "{folder}"')
            except Exception:
                pass

    def _parse_video_quality(self, quality_str: str) -> int:
        """Parse video quality label into height integer."""
        if not quality_str or "best" in quality_str.lower():
            return 0
        match = re.search(r"(\d+)p", quality_str)
        if match:
            return int(match.group(1))
        digits = re.findall(r"\d+", quality_str)
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
        return "0"


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main():
    """Launch the Downloadyha GUI application."""
    app = DownloadyhaGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
