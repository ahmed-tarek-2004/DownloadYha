"""
app.py - Main Desktop GUI Application for Downloadyha

Built with CustomTkinter for modern, cross-platform aesthetics with:
- Tab-based interface (Download, Queue, Settings)
- Real-time download progress with speed and ETA
- Theme switching (Dark/Light/System)
- Integrated folder picker and quality selection
- Background download threading to prevent UI freezing
"""

import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Dict, Optional

import customtkinter as ctk

# Import downloadyha core engine
try:
    from downloadyha.config import get_download_dir, load as load_config, save as save_config
    from downloadyha.downloader import download_audio, download_video, get_media_info
except ImportError:
    # Fallback for direct execution during development
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from downloadyha.config import get_download_dir, load as load_config, save as save_config
    from downloadyha.downloader import download_audio, download_video, get_media_info


# ---------------------------------------------------------------------------
# Theme & Color Palette (from ui.py)
# ---------------------------------------------------------------------------

class Theme:
    """Downloadyha brand color palette matching terminal UI."""
    # Cyber Theme Colors (RGB tuples)
    ELECTRIC_CYAN = (0, 210, 255)
    CYBER_PURPLE = (155, 81, 224)
    EMERALD_GREEN = (46, 204, 113)
    AMBER_YELLOW = (241, 196, 15)
    CRIMSON_RED = (231, 76, 60)

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


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class DownloadyhaGUI(ctk.CTk):
    """Main GUI Application Window."""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Downloadyha - YouTube Downloader")
        self.geometry("900x650")
        self.minsize(800, 600)

        # Load user configuration
        self.config = load_config()

        # Download state
        self.current_download_thread: Optional[threading.Thread] = None
        self.is_downloading = False
        self.cancel_requested = False

        # Apply theme from config or system default
        self._setup_theme()

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create main UI
        self._create_widgets()

        # Set icon if available
        self._set_window_icon()

    def _setup_theme(self):
        """Configure application theme."""
        theme_mode = self.config.get("theme", "system")
        ctk.set_appearance_mode(theme_mode)
        ctk.set_default_color_theme("blue")

    def _set_window_icon(self):
        """Set window icon if available."""
        try:
            # Try to set icon from resources
            icon_path = Path(__file__).parent / "resources" / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass

    def _create_widgets(self):
        """Build main UI components."""
        # Create tabview for main sections
        self.tabview = ctk.CTkTabview(self, width=880, height=620)
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Add tabs
        self.tabview.add("Download")
        self.tabview.add("Queue")
        self.tabview.add("Settings")

        # Configure tab content
        self._create_download_tab()
        self._create_queue_tab()
        self._create_settings_tab()

        # Set default tab
        self.tabview.set("Download")

    # -----------------------------------------------------------------------
    # Download Tab
    # -----------------------------------------------------------------------

    def _create_download_tab(self):
        """Create the main Download tab interface."""
        tab = self.tabview.tab("Download")
        tab.grid_columnconfigure(0, weight=1)

        # Title/Header
        header = ctk.CTkLabel(
            tab,
            text="⬇ Download YouTube Media",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # URL Input Section
        url_frame = ctk.CTkFrame(tab)
        url_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        url_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            url_frame,
            text="YouTube URL:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        self.url_entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        paste_btn = ctk.CTkButton(
            url_frame,
            text="📋 Paste",
            width=100,
            height=40,
            command=self._paste_url
        )
        paste_btn.grid(row=1, column=1, padx=(0, 10), pady=(0, 10))

        # Quality Selection Section
        quality_frame = ctk.CTkFrame(tab)
        quality_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        quality_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            quality_frame,
            text="Mode & Quality:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        # Media type selector (Video/Audio)
        self.media_type_var = tk.StringVar(value="video")
        self.media_type_selector = ctk.CTkSegmentedButton(
            quality_frame,
            values=["Video", "Audio"],
            variable=self.media_type_var,
            command=self._on_media_type_changed
        )
        self.media_type_selector.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        # Quality dropdown
        self.quality_var = tk.StringVar(value="Best Available")
        self.quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            variable=self.quality_var,
            values=["Best Available", "2160p (4K)", "1440p (2K)", "1080p (Full HD)", "720p (HD)", "480p (SD)", "360p (Low)"],
            width=200,
            height=35
        )
        self.quality_menu.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="w")

        # Destination Folder Section
        dest_frame = ctk.CTkFrame(tab)
        dest_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        dest_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dest_frame,
            text="Save Location:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        dest_entry_frame = ctk.CTkFrame(dest_frame)
        dest_entry_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        dest_entry_frame.grid_columnconfigure(0, weight=1)

        self.dest_entry = ctk.CTkEntry(
            dest_entry_frame,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.dest_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.dest_entry.insert(0, self.config.get("download_directory", str(get_download_dir())))

        browse_btn = ctk.CTkButton(
            dest_entry_frame,
            text="📁 Browse",
            width=100,
            height=35,
            command=self._browse_destination
        )
        browse_btn.grid(row=0, column=1)

        # Download Button
        self.download_btn = ctk.CTkButton(
            tab,
            text="⬇ Download",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color=Theme.get_accent_color(),
            hover_color=Theme.rgb_to_hex(Theme.CYBER_PURPLE),
            command=self._start_download
        )
        self.download_btn.grid(row=4, column=0, padx=20, pady=20, sticky="ew")

        # Progress Section
        progress_frame = ctk.CTkFrame(tab)
        progress_frame.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to download",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=20)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.set(0)

        # Progress details (percentage, speed, ETA)
        details_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        details_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_columnconfigure(1, weight=1)
        details_frame.grid_columnconfigure(2, weight=1)

        self.percent_label = ctk.CTkLabel(details_frame, text="0%", font=ctk.CTkFont(size=11))
        self.percent_label.grid(row=0, column=0, sticky="w")

        self.speed_label = ctk.CTkLabel(details_frame, text="Speed: --", font=ctk.CTkFont(size=11))
        self.speed_label.grid(row=0, column=1)

        self.eta_label = ctk.CTkLabel(details_frame, text="ETA: --", font=ctk.CTkFont(size=11))
        self.eta_label.grid(row=0, column=2, sticky="e")

    def _on_media_type_changed(self, value: str):
        """Update quality options when media type changes."""
        media_type = value.lower()

        if media_type == "video":
            self.quality_menu.configure(
                values=["Best Available", "2160p (4K)", "1440p (2K)", "1080p (Full HD)", "720p (HD)", "480p (SD)", "360p (Low)"]
            )
            self.quality_var.set("Best Available")
        else:  # audio
            self.quality_menu.configure(
                values=["Best Quality", "320 kbps", "192 kbps", "128 kbps"]
            )
            self.quality_var.set("Best Quality")

    def _paste_url(self):
        """Paste URL from clipboard."""
        try:
            clipboard_text = self.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_text.strip())
        except Exception:
            pass

    def _browse_destination(self):
        """Open folder picker dialog."""
        folder = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=self.dest_entry.get()
        )
        if folder:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, folder)

    def _start_download(self):
        """Start download process in background thread."""
        if self.is_downloading:
            # Cancel current download
            self.cancel_requested = True
            self.download_btn.configure(text="⏳ Cancelling...")
            return

        # Validate inputs
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
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
        self.download_btn.configure(text="❌ Cancel", fg_color=Theme.get_error_color())
        self._reset_progress()
        self.status_label.configure(text="Fetching media information...")

        self.current_download_thread = threading.Thread(
            target=self._download_worker,
            args=(url, dest_path),
            daemon=True
        )
        self.current_download_thread.start()

    def _download_worker(self, url: str, dest_path: str):
        """Background worker for download execution."""
        try:
            # Get media type and quality
            media_type = self.media_type_var.get().lower()
            quality_str = self.quality_var.get()

            # Parse quality
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

                    self.after(0, self._update_progress, percent, speed_str, eta_str)
                elif status == "finished":
                    self.after(0, self._update_status, "Processing and merging streams...")

            # Execute download
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
            self.after(0, self._download_failed, str(e))

    def _parse_video_quality(self, quality_str: str) -> int:
        """Parse quality string to height value."""
        quality_map = {
            "Best Available": 0,
            "2160p (4K)": 2160,
            "1440p (2K)": 1440,
            "1080p (Full HD)": 1080,
            "720p (HD)": 720,
            "480p (SD)": 480,
            "360p (Low)": 360,
        }
        return quality_map.get(quality_str, 0)

    def _parse_audio_quality(self, quality_str: str) -> str:
        """Parse audio quality string to bitrate."""
        quality_map = {
            "Best Quality": "0",
            "320 kbps": "320",
            "192 kbps": "192",
            "128 kbps": "128",
        }
        return quality_map.get(quality_str, "0")

    def _update_progress(self, percent: float, speed: str, eta: str):
        """Update progress UI elements."""
        self.progress_bar.set(percent / 100.0)
        self.percent_label.configure(text=f"{percent:.1f}%")
        self.speed_label.configure(text=f"Speed: {speed}")
        self.eta_label.configure(text=f"ETA: {eta}")
        self.status_label.configure(text="Downloading...")

    def _update_status(self, message: str):
        """Update status label."""
        self.status_label.configure(text=message)

    def _reset_progress(self):
        """Reset progress indicators."""
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.speed_label.configure(text="Speed: --")
        self.eta_label.configure(text="ETA: --")

    def _download_complete(self, result):
        """Handle successful download completion."""
        self.is_downloading = False
        self.download_btn.configure(
            text="⬇ Download",
            fg_color=Theme.get_accent_color()
        )
        self.progress_bar.set(1.0)
        self.percent_label.configure(text="100%")

        if result.is_playlist:
            msg = f"Playlist download complete!\n\n{result.completed_items}/{result.total_items} items downloaded successfully."
        else:
            msg = "Download completed successfully!"

        self.status_label.configure(text="✅ " + msg.split('\n')[0])
        messagebox.showinfo("Success", msg)
        self._reset_progress()
        self.status_label.configure(text="Ready to download")

    def _download_failed(self, error: str):
        """Handle download failure."""
        self.is_downloading = False
        self.download_btn.configure(
            text="⬇ Download",
            fg_color=Theme.get_accent_color()
        )
        self.status_label.configure(text="❌ Download failed")
        messagebox.showerror("Download Failed", f"An error occurred:\n\n{error}")
        self._reset_progress()
        self.status_label.configure(text="Ready to download")

    def _download_cancelled(self):
        """Handle download cancellation."""
        self.is_downloading = False
        self.cancel_requested = False
        self.download_btn.configure(
            text="⬇ Download",
            fg_color=Theme.get_accent_color()
        )
        self.status_label.configure(text="Download cancelled")
        messagebox.showinfo("Cancelled", "Download was cancelled.")
        self._reset_progress()
        self.status_label.configure(text="Ready to download")

    # -----------------------------------------------------------------------
    # Queue Tab
    # -----------------------------------------------------------------------

    def _create_queue_tab(self):
        """Create the Queue management tab."""
        tab = self.tabview.tab("Queue")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkLabel(
            tab,
            text="📋 Download Queue",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Queue list (placeholder for future implementation)
        queue_frame = ctk.CTkScrollableFrame(tab)
        queue_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        queue_frame.grid_columnconfigure(0, weight=1)

        placeholder = ctk.CTkLabel(
            queue_frame,
            text="Queue management coming soon!\n\nFuture features:\n• Add multiple URLs to download queue\n• Pause and resume downloads\n• Reorder queue items\n• Batch operations",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        placeholder.grid(row=0, column=0, pady=50)

    # -----------------------------------------------------------------------
    # Settings Tab
    # -----------------------------------------------------------------------

    def _create_settings_tab(self):
        """Create the Settings configuration tab."""
        tab = self.tabview.tab("Settings")
        tab.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkLabel(
            tab,
            text="⚙ Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Settings sections
        settings_container = ctk.CTkScrollableFrame(tab)
        settings_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        settings_container.grid_columnconfigure(0, weight=1)

        # Default Download Path
        path_section = ctk.CTkFrame(settings_container)
        path_section.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        path_section.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            path_section,
            text="Default Download Path:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="w")

        self.default_path_entry = ctk.CTkEntry(
            path_section,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        self.default_path_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        self.default_path_entry.insert(0, self.config.get("download_directory", str(get_download_dir())))

        ctk.CTkButton(
            path_section,
            text="Browse",
            width=100,
            height=35,
            command=self._browse_default_path
        ).grid(row=1, column=2, padx=(0, 10), pady=(0, 10))

        # Theme Settings
        theme_section = ctk.CTkFrame(settings_container)
        theme_section.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(
            theme_section,
            text="Theme:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.theme_var = tk.StringVar(value=self.config.get("theme", "system"))
        theme_menu = ctk.CTkOptionMenu(
            theme_section,
            variable=self.theme_var,
            values=["System", "Dark", "Light"],
            width=200,
            height=35,
            command=self._on_theme_changed
        )
        theme_menu.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        # Auto Update Toggle
        update_section = ctk.CTkFrame(settings_container)
        update_section.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(
            update_section,
            text="Auto-Update Check:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.auto_update_var = tk.BooleanVar(value=self.config.get("check_updates", True))
        auto_update_switch = ctk.CTkSwitch(
            update_section,
            text="Enable automatic update checking",
            variable=self.auto_update_var,
            command=self._save_settings
        )
        auto_update_switch.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        # Save Button
        save_btn = ctk.CTkButton(
            settings_container,
            text="💾 Save Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color=Theme.get_success_color(),
            command=self._save_settings
        )
        save_btn.grid(row=3, column=0, padx=10, pady=20, sticky="ew")

        # About Section
        about_section = ctk.CTkFrame(settings_container)
        about_section.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(
            about_section,
            text="About Downloadyha",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        about_text = f"""Version: 1.0.0
Author: Ahmed Tarek Zaher
Description: Modern YouTube Downloader

A powerful cross-platform desktop application for downloading
YouTube videos and audio with support for playlists, multiple
quality options, and real-time progress tracking."""

        ctk.CTkLabel(
            about_section,
            text=about_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        ).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

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
            messagebox.showinfo("Success", "Settings saved successfully!")
            # Update main download tab destination
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, self.config["download_directory"])
        else:
            messagebox.showerror("Error", "Failed to save settings")


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

def main():
    """Launch the Downloadyha GUI application."""
    app = DownloadyhaGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
