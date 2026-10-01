"""
gui.py - Desktop GUI for Downloadyha using tkinter.

Provides a cross-platform graphical interface for YouTube downloads with:
- URL input and validation
- Quality selection for video/audio
- Playlist detection and handling
- Real-time progress tracking
- Theme switching (Light/Dark)
- Settings persistence
"""

from __future__ import annotations

import queue
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import __version__
from .config import get_app_data_dir, get_download_dir, load, save
from .downloader import (
    DownloadResult,
    download_audio,
    download_video,
    get_media_info,
    is_playlist,
    is_playlist_url,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VIDEO_QUALITY_OPTIONS: List[Tuple[str, str, int]] = [
    ("1", "Best Available (Maximum Quality)", 0),
    ("2", "2160p (4K UHD)", 2160),
    ("3", "1440p (2K QHD)", 1440),
    ("4", "1080p (Full HD)", 1080),
    ("5", "720p (HD)", 720),
    ("6", "480p (SD)", 480),
    ("7", "360p (Low)", 360),
]

AUDIO_QUALITY_OPTIONS: List[Tuple[str, str, str]] = [
    ("1", "Best (Variable Bitrate ~256-320 kbps)", "0"),
    ("2", "320 kbps (High Quality)", "320"),
    ("3", "192 kbps (Standard Quality)", "192"),
    ("4", "128 kbps (Compact Size)", "128"),
]

# YouTube URL validation regex
YOUTUBE_URL_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$",
    re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Theme Configuration
# ---------------------------------------------------------------------------

class ThemeColors:
    """Color definitions for light and dark themes."""

    LIGHT = {
        "bg": "#F5F5F5",
        "fg": "#1A1A1A",
        "accent": "#00D2FF",
        "accent_dark": "#00A8D6",
        "success": "#2ECC71",
        "warning": "#F1C40F",
        "error": "#E74C3C",
        "card_bg": "#FFFFFF",
        "input_bg": "#FFFFFF",
        "border": "#E0E0E0",
        "muted": "#7F8C8D",
        "progress_bg": "#E0E0E0",
        "progress_fill": "#00D2FF",
    }

    DARK = {
        "bg": "#1E1E2E",
        "fg": "#EAEAEA",
        "accent": "#00D2FF",
        "accent_dark": "#00A8D6",
        "success": "#2ECC71",
        "warning": "#F1C40F",
        "error": "#E74C3C",
        "card_bg": "#2A2A3E",
        "input_bg": "#2A2A3E",
        "border": "#3D3D5C",
        "muted": "#95A5A6",
        "progress_bg": "#3D3D5C",
        "progress_fill": "#00D2FF",
    }


# ---------------------------------------------------------------------------
# URL Validation
# ---------------------------------------------------------------------------

def validate_youtube_url(url: str) -> Tuple[bool, str]:
    """
    Validate if a string is a valid YouTube URL.

    Args:
        url: The URL string to validate.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is empty string.
    """
    if not url or not url.strip():
        return False, "URL cannot be empty."

    url = url.strip()

    if not YOUTUBE_URL_PATTERN.match(url):
        return False, "Invalid YouTube URL format. Please enter a valid YouTube video or playlist URL."

    return True, ""


def is_valid_youtube_url(url: str) -> bool:
    """
    Quick check if URL is a valid YouTube URL.

    Args:
        url: URL string to check.

    Returns:
        True if valid YouTube URL, False otherwise.
    """
    valid, _ = validate_youtube_url(url)
    return valid


# ---------------------------------------------------------------------------
# Settings Management
# ---------------------------------------------------------------------------

def load_gui_settings() -> Dict[str, Any]:
    """
    Load GUI-specific settings from the config file.

    Returns:
        Dictionary with GUI settings including theme, window geometry,
        download directory, and quality preferences.
    """
    config = load()

    return {
        "download_directory": config.get("download_directory", str(get_download_dir())),
        "theme": config.get("theme", "light"),
        "check_updates": config.get("check_updates", True),
        "last_video_quality": config.get("last_video_quality", "1"),
        "last_audio_quality": config.get("last_audio_quality", "1"),
        "window_geometry": config.get("window_geometry", "700x600"),
    }


def save_gui_settings(settings: Dict[str, Any]) -> bool:
    """
    Save GUI settings to the config file.

    Args:
        settings: Dictionary of settings to save.

    Returns:
        True if save was successful, False otherwise.
    """
    config = load()
    config.update(settings)
    return save(config)


# ---------------------------------------------------------------------------
# Progress Callback Integration
# ---------------------------------------------------------------------------

class ProgressCallback:
    """
    Thread-safe progress callback for integrating with the downloader engine.

    Uses a queue to communicate progress updates from download threads
    to the GUI main thread.
    """

    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Initialize the progress callback.

        Args:
            callback: Optional callback function to invoke on progress updates.
        """
        self._queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._callback = callback
        self._cancelled = False

    def __call__(self, data: Dict[str, Any]) -> None:
        """
        Called by the downloader to report progress.

        Args:
            data: Progress data dictionary from yt-dlp.
        """
        if self._cancelled:
            return

        event = {
            "status": data.get("status", "unknown"),
            "percent": data.get("percent", 0.0),
            "speed": data.get("speed_str", "N/A"),
            "eta": data.get("eta_str", "N/A"),
            "downloaded": data.get("size_str", "N/A"),
            "filename": data.get("filename", ""),
            "item_title": data.get("item_title", ""),
            "playlist_index": data.get("playlist_index"),
            "playlist_count": data.get("playlist_count"),
        }

        self._queue.put(event)

        if self._callback:
            try:
                self._callback(event)
            except Exception:
                pass

    def get_pending_events(self) -> List[Dict[str, Any]]:
        """
        Retrieve all pending progress events from the queue.

        Returns:
            List of pending progress event dictionaries.
        """
        events = []
        try:
            while True:
                events.append(self._queue.get_nowait())
        except queue.Empty:
            pass
        return events

    def cancel(self) -> None:
        """Mark the download as cancelled."""
        self._cancelled = True

    def reset(self) -> None:
        """Reset the callback for a new download."""
        self._cancelled = False
        # Clear the queue
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass


# ---------------------------------------------------------------------------
# Main GUI Application
# ---------------------------------------------------------------------------

class DownloadyhaGUI:
    """
    Main GUI application class for Downloadyha.

    Provides a desktop interface for downloading YouTube videos and audio
    with real-time progress tracking and theme switching.
    """

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        """
        Initialize the GUI application.

        Args:
            root: Optional existing Tk root window. If None, creates a new one.
        """
        self.root = root or tk.Tk()
        self.root.title(f"Downloadyha v{__version__}")

        # Load settings
        self.settings = load_gui_settings()

        # State variables
        self._current_theme = self.settings.get("theme", "light")
        self._download_thread: Optional[threading.Thread] = None
        self._progress_callback = ProgressCallback()
        self._is_downloading = False
        self._media_info: Optional[Dict[str, Any]] = None

        # Apply saved window geometry
        geometry = self.settings.get("window_geometry", "700x600")
        self.root.geometry(geometry)

        # Build the UI
        self._setup_styles()
        self._build_ui()
        self._apply_theme()

        # Center window on screen
        self._center_window()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self) -> None:
        """Configure ttk styles for the application."""
        self.style = ttk.Style()

        # Configure button styles
        self.style.configure(
            "Primary.TButton",
            padding=(20, 10),
            font=("Segoe UI", 10, "bold"),
        )

        self.style.configure(
            "Secondary.TButton",
            padding=(15, 8),
            font=("Segoe UI", 9),
        )

        # Configure frame styles
        self.style.configure("Card.TFrame", padding=10)
        self.style.configure("Card.TLabelframe", padding=15)
        self.style.configure("Card.TLabelframe.Label", font=("Segoe UI", 11, "bold"))

    def _build_ui(self) -> None:
        """Build the main user interface."""
        # Main container with padding
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header section
        self._build_header()

        # URL input section
        self._build_url_section()

        # Download options section
        self._build_options_section()

        # Progress section
        self._build_progress_section()

        # Action buttons
        self._build_action_buttons()

        # Status bar
        self._build_status_bar()

    def _build_header(self) -> None:
        """Build the header section with title and theme toggle."""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        # Title label
        self.title_label = ttk.Label(
            header_frame,
            text=f"Downloadyha v{__version__}",
            font=("Segoe UI", 18, "bold"),
        )
        self.title_label.pack(side=tk.LEFT)

        # Theme toggle button
        self.theme_btn = ttk.Button(
            header_frame,
            text="🌙 Dark",
            command=self.toggle_theme,
            style="Secondary.TButton",
        )
        self.theme_btn.pack(side=tk.RIGHT)

    def _build_url_section(self) -> None:
        """Build the URL input section."""
        url_frame = ttk.LabelFrame(
            self.main_frame,
            text="YouTube URL",
            style="Card.TLabelframe",
        )
        url_frame.pack(fill=tk.X, pady=(0, 15))

        # URL entry
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(
            url_frame,
            textvariable=self.url_var,
            font=("Segoe UI", 11),
            width=60,
        )
        self.url_entry.pack(fill=tk.X, padx=10, pady=10)

        # URL validation label
        self.url_validation_label = ttk.Label(
            url_frame,
            text="",
            font=("Segoe UI", 9),
        )
        self.url_validation_label.pack(padx=10, pady=(0, 5))

        # Bind URL validation
        self.url_var.trace_add("write", self._validate_url_input)

        # Media info card (hidden initially)
        self.media_info_frame = ttk.Frame(url_frame)
        self.media_info_label = ttk.Label(
            self.media_info_frame,
            text="",
            font=("Segoe UI", 10),
            justify=tk.LEFT,
        )
        self.media_info_label.pack(anchor=tk.W, padx=10, pady=5)

    def _build_options_section(self) -> None:
        """Build the download options section."""
        options_frame = ttk.LabelFrame(
            self.main_frame,
            text="Download Options",
            style="Card.TLabelframe",
        )
        options_frame.pack(fill=tk.X, pady=(0, 15))

        # Download type selection
        type_frame = ttk.Frame(options_frame)
        type_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(type_frame, text="Download Type:", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self.download_type_var = tk.StringVar(value="video")

        ttk.Radiobutton(
            type_frame,
            text="Video",
            variable=self.download_type_var,
            value="video",
            command=self._on_type_change,
        ).pack(side=tk.LEFT, padx=(10, 5))

        ttk.Radiobutton(
            type_frame,
            text="Audio (MP3)",
            variable=self.download_type_var,
            value="audio",
            command=self._on_type_change,
        ).pack(side=tk.LEFT, padx=5)

        # Quality selection
        quality_frame = ttk.Frame(options_frame)
        quality_frame.pack(fill=tk.X, padx=10, pady=10)

        self.quality_label = ttk.Label(quality_frame, text="Video Quality:", font=("Segoe UI", 10))
        self.quality_label.pack(side=tk.LEFT)

        self.video_quality_var = tk.StringVar(value=self.settings.get("last_video_quality", "1"))
        self.audio_quality_var = tk.StringVar(value=self.settings.get("last_audio_quality", "1"))

        self.quality_combo = ttk.Combobox(
            quality_frame,
            values=[opt[1] for opt in VIDEO_QUALITY_OPTIONS],
            state="readonly",
            width=35,
            font=("Segoe UI", 9),
        )
        self.quality_combo.current(0)
        self.quality_combo.pack(side=tk.LEFT, padx=(10, 0))

        # Download directory
        dir_frame = ttk.Frame(options_frame)
        dir_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(dir_frame, text="Save to:", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self.dir_var = tk.StringVar(value=self.settings.get("download_directory", str(get_download_dir())))

        self.dir_entry = ttk.Entry(
            dir_frame,
            textvariable=self.dir_var,
            font=("Segoe UI", 9),
            width=45,
        )
        self.dir_entry.pack(side=tk.LEFT, padx=(10, 5))

        ttk.Button(
            dir_frame,
            text="Browse",
            command=self._browse_directory,
            style="Secondary.TButton",
        ).pack(side=tk.LEFT)

    def _build_progress_section(self) -> None:
        """Build the progress tracking section."""
        progress_frame = ttk.LabelFrame(
            self.main_frame,
            text="Progress",
            style="Card.TLabelframe",
        )
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            length=500,
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)

        # Progress label
        self.progress_label = ttk.Label(
            progress_frame,
            text="Ready to download",
            font=("Segoe UI", 10),
        )
        self.progress_label.pack(padx=10, pady=(0, 10))

        # Speed and ETA labels
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.speed_label = ttk.Label(stats_frame, text="Speed: --", font=("Segoe UI", 9))
        self.speed_label.pack(side=tk.LEFT)

        self.eta_label = ttk.Label(stats_frame, text="ETA: --", font=("Segoe UI", 9))
        self.eta_label.pack(side=tk.RIGHT)

    def _build_action_buttons(self) -> None:
        """Build the action buttons."""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Fetch info button
        self.fetch_btn = ttk.Button(
            button_frame,
            text="Fetch Info",
            command=self._fetch_media_info,
            style="Primary.TButton",
        )
        self.fetch_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Download button
        self.download_btn = ttk.Button(
            button_frame,
            text="Download",
            command=self._start_download,
            style="Primary.TButton",
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel_download,
            style="Secondary.TButton",
            state=tk.DISABLED,
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        # Open folder button
        self.open_folder_btn = ttk.Button(
            button_frame,
            text="Open Folder",
            command=self._open_download_folder,
            style="Secondary.TButton",
        )
        self.open_folder_btn.pack(side=tk.RIGHT)

    def _build_status_bar(self) -> None:
        """Build the status bar."""
        self.status_bar = ttk.Label(
            self.root,
            text="Ready",
            font=("Segoe UI", 9),
            relief=tk.SUNKEN,
            anchor=tk.W,
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _apply_theme(self) -> None:
        """Apply the current theme to the application."""
        colors = ThemeColors.DARK if self._current_theme == "dark" else ThemeColors.LIGHT

        # Configure root window
        self.root.configure(bg=colors["bg"])

        # Configure ttk styles with theme colors
        self.style.configure(
            ".",
            background=colors["bg"],
            foreground=colors["fg"],
        )

        self.style.configure(
            "TFrame",
            background=colors["bg"],
        )

        self.style.configure(
            "TLabelframe",
            background=colors["bg"],
        )

        self.style.configure(
            "TLabelframe.Label",
            background=colors["bg"],
            foreground=colors["fg"],
        )

        self.style.configure(
            "TLabel",
            background=colors["bg"],
            foreground=colors["fg"],
        )

        self.style.configure(
            "TEntry",
            fieldbackground=colors["input_bg"],
            foreground=colors["fg"],
        )

        self.style.configure(
            "TButton",
            background=colors["accent"],
        )

        self.style.configure(
            "TProgressbar",
            background=colors["progress_fill"],
            troughcolor=colors["progress_bg"],
        )

        self.style.configure(
            "TRadiobutton",
            background=colors["bg"],
            foreground=colors["fg"],
        )

        # Update status bar
        self.status_bar.configure(background=colors["card_bg"], foreground=colors["fg"])

        # Update theme button text
        if self._current_theme == "dark":
            self.theme_btn.configure(text="☀ Light")
        else:
            self.theme_btn.configure(text="🌙 Dark")

    def _center_window(self) -> None:
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _validate_url_input(self, *args) -> None:
        """Validate URL input in real-time."""
        url = self.url_var.get().strip()
        colors = ThemeColors.DARK if self._current_theme == "dark" else ThemeColors.LIGHT

        if not url:
            self.url_validation_label.configure(text="", foreground=colors["fg"])
            return

        is_valid, error_msg = validate_youtube_url(url)

        if is_valid:
            self.url_validation_label.configure(
                text="✓ Valid YouTube URL",
                foreground=colors["success"],
            )
        else:
            self.url_validation_label.configure(
                text=f"✗ {error_msg}",
                foreground=colors["error"],
            )

    def _on_type_change(self) -> None:
        """Handle download type change."""
        download_type = self.download_type_var.get()

        if download_type == "video":
            self.quality_label.configure(text="Video Quality:")
            self.quality_combo.configure(
                values=[opt[1] for opt in VIDEO_QUALITY_OPTIONS],
            )
            self.quality_combo.current(int(self.video_quality_var.get()) - 1)
        else:
            self.quality_label.configure(text="Audio Quality:")
            self.quality_combo.configure(
                values=[opt[1] for opt in AUDIO_QUALITY_OPTIONS],
            )
            self.quality_combo.current(int(self.audio_quality_var.get()) - 1)

    def _browse_directory(self) -> None:
        """Open a directory browser dialog."""
        current_dir = self.dir_var.get()
        new_dir = filedialog.askdirectory(initialdir=current_dir)

        if new_dir:
            self.dir_var.set(new_dir)
            self.settings["download_directory"] = new_dir
            save_gui_settings(self.settings)

    def _fetch_media_info(self) -> None:
        """Fetch and display media information from the URL."""
        url = self.url_var.get().strip()

        if not is_valid_youtube_url(url):
            messagebox.showerror("Error", "Please enter a valid YouTube URL.")
            return

        self._set_ui_state(downloading=True, message="Fetching media info...")
        self.status_bar.configure(text="Fetching media information...")

        def fetch_task() -> None:
            try:
                self._media_info = get_media_info(url)
                self.root.after(0, self._on_media_info_fetched)
            except Exception as e:
                self._media_info = None
                self.root.after(0, lambda: self._on_fetch_error(str(e)))

        thread = threading.Thread(target=fetch_task, daemon=True)
        thread.start()

    def _on_media_info_fetched(self) -> None:
        """Handle successful media info fetch."""
        self._set_ui_state(downloading=False)

        if not self._media_info:
            self.status_bar.configure(text="Failed to fetch media information.")
            messagebox.showwarning("Warning", "Could not fetch media information.")
            return

        # Build info string
        title = self._media_info.get("title", "Unknown")
        uploader = self._media_info.get("uploader", "Unknown")
        duration = self._media_info.get("duration", 0)
        is_pl = is_playlist(self._media_info)
        playlist_count = self._media_info.get("playlist_count", 0)

        if duration:
            mins, secs = divmod(int(duration), 60)
            duration_str = f"{mins}:{secs:02d}"
        else:
            duration_str = "Unknown"

        info_lines = [f"Title: {title}"]
        info_lines.append(f"Channel: {uploader}")

        if is_pl:
            info_lines.append(f"Type: Playlist ({playlist_count} items)")
        else:
            info_lines.append(f"Duration: {duration_str}")
            info_lines.append(f"Type: Single Video")

        self.media_info_label.configure(text="\n".join(info_lines))
        self.media_info_frame.pack(fill=tk.X, pady=5)

        self.status_bar.configure(text=f"Media info loaded: {title}")

    def _on_fetch_error(self, error: str) -> None:
        """Handle media info fetch error."""
        self._set_ui_state(downloading=False)
        self.status_bar.configure(text=f"Error: {error}")
        messagebox.showerror("Error", f"Failed to fetch media info:\n{error}")

    def _start_download(self) -> None:
        """Start the download process."""
        url = self.url_var.get().strip()

        if not is_valid_youtube_url(url):
            messagebox.showerror("Error", "Please enter a valid YouTube URL.")
            return

        download_dir = self.dir_var.get()
        download_type = self.download_type_var.get()

        # Get quality selection
        quality_idx = self.quality_combo.current()

        if download_type == "video":
            quality = VIDEO_QUALITY_OPTIONS[quality_idx][2]
            self.settings["last_video_quality"] = str(quality_idx + 1)
        else:
            quality = AUDIO_QUALITY_OPTIONS[quality_idx][2]
            self.settings["last_audio_quality"] = str(quality_idx + 1)

        save_gui_settings(self.settings)

        # Reset progress callback
        self._progress_callback.reset()

        # Update UI state
        self._is_downloading = True
        self._set_ui_state(downloading=True, message="Starting download...")

        # Start download in background thread
        def download_task() -> None:
            try:
                if download_type == "video":
                    result = download_video(
                        url=url,
                        download_path=download_dir,
                        height=quality,
                        progress_callback=self._progress_callback,
                    )
                else:
                    result = download_audio(
                        url=url,
                        download_path=download_dir,
                        quality=quality,
                        progress_callback=self._progress_callback,
                    )

                self.root.after(0, lambda: self._on_download_complete(result))

            except Exception as e:
                self.root.after(0, lambda: self._on_download_error(str(e)))

        self._download_thread = threading.Thread(target=download_task, daemon=True)
        self._download_thread.start()

        # Start progress update loop
        self._update_progress()

    def _update_progress(self) -> None:
        """Update progress UI from the callback queue."""
        if not self._is_downloading:
            return

        events = self._progress_callback.get_pending_events()

        for event in events:
            status = event.get("status")

            if status == "downloading":
                percent = event.get("percent", 0.0)
                self.progress_var.set(percent)
                self.progress_label.configure(
                    text=f"Downloading: {event.get('item_title', 'Unknown')}"
                )
                self.speed_label.configure(text=f"Speed: {event.get('speed', 'N/A')}")
                self.eta_label.configure(text=f"ETA: {event.get('eta', 'N/A')}")

                # Update status bar with playlist progress
                pl_idx = event.get("playlist_index")
                pl_count = event.get("playlist_count")
                if pl_idx and pl_count:
                    self.status_bar.configure(text=f"Downloading item {pl_idx} of {pl_count}")

            elif status == "finished":
                self.progress_var.set(100)
                self.progress_label.configure(text="Processing...")

        # Schedule next update
        if self._is_downloading:
            self.root.after(100, self._update_progress)

    def _on_download_complete(self, result: DownloadResult) -> None:
        """Handle download completion."""
        self._is_downloading = False
        self._set_ui_state(downloading=False)

        if result.success:
            self.progress_var.set(100)
            self.progress_label.configure(text="Download complete!")

            colors = ThemeColors.DARK if self._current_theme == "dark" else ThemeColors.LIGHT
            self.status_bar.configure(
                text=f"✓ Saved to: {result.download_directory}",
                foreground=colors["success"],
            )

            messagebox.showinfo(
                "Success",
                f"Download complete!\n\nSaved to:\n{result.download_directory}",
            )
        else:
            self.progress_label.configure(text="Download failed")
            self.status_bar.configure(text=f"Download failed: {result.message}")

            messagebox.showerror(
                "Error",
                f"Download failed:\n{result.message}",
            )

    def _on_download_error(self, error: str) -> None:
        """Handle download error."""
        self._is_downloading = False
        self._set_ui_state(downloading=False)
        self.progress_label.configure(text="Download failed")
        self.status_bar.configure(text=f"Error: {error}")

        messagebox.showerror("Error", f"Download failed:\n{error}")

    def _cancel_download(self) -> None:
        """Cancel the current download."""
        if self._is_downloading:
            self._progress_callback.cancel()
            self._is_downloading = False
            self._set_ui_state(downloading=False)
            self.progress_label.configure(text="Download cancelled")
            self.status_bar.configure(text="Download cancelled by user")

    def _set_ui_state(self, downloading: bool, message: str = "") -> None:
        """
        Set the UI state based on download status.

        Args:
            downloading: Whether a download is in progress.
            message: Optional status message.
        """
        if downloading:
            self.download_btn.configure(state=tk.DISABLED)
            self.fetch_btn.configure(state=tk.DISABLED)
            self.cancel_btn.configure(state=tk.NORMAL)
            self.url_entry.configure(state=tk.DISABLED)
        else:
            self.download_btn.configure(state=tk.NORMAL)
            self.fetch_btn.configure(state=tk.NORMAL)
            self.cancel_btn.configure(state=tk.DISABLED)
            self.url_entry.configure(state=tk.NORMAL)

    def _open_download_folder(self) -> None:
        """Open the download folder in the file explorer."""
        import subprocess
        import sys

        download_dir = self.dir_var.get()

        if sys.platform == "win32":
            subprocess.run(["explorer", download_dir], check=False)
        elif sys.platform == "darwin":
            subprocess.run(["open", download_dir], check=False)
        else:
            subprocess.run(["xdg-open", download_dir], check=False)

    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        self._current_theme = "dark" if self._current_theme == "light" else "light"
        self.settings["theme"] = self._current_theme
        save_gui_settings(self.settings)
        self._apply_theme()

    def _on_close(self) -> None:
        """Handle window close event."""
        if self._is_downloading:
            if not messagebox.askyesno(
                "Download in Progress",
                "A download is in progress. Are you sure you want to exit?",
            ):
                return

            self._progress_callback.cancel()

        # Save window geometry
        self.settings["window_geometry"] = self.root.geometry()
        save_gui_settings(self.settings)

        self.root.destroy()

    def run(self) -> None:
        """Run the GUI application main loop."""
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def launch_gui() -> None:
    """Launch the Downloadyha GUI application."""
    app = DownloadyhaGUI()
    app.run()


main = launch_gui


if __name__ == "__main__":
    launch_gui()
