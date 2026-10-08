"""
playlist_view.py - Dedicated Playlist & Batch Download Workspace View for Downloadyha

Features:
- Dedicated Playlist & Channel URL analysis with vector icons.
- Batch options: range selection, format selection (Video / Audio / Subtitles), max resolution.
- Multi-item batch progress tracking and docked action bar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
import tkinter as tk
import customtkinter as ctk

from ..theme.palette import Theme, Fonts
from ..components.cards import ModernCard, GlassCard
from ..components.buttons import CrimsonButton, PrimaryButton, SecondaryButton
from ..components.inputs import ModernEntry
from ..components.progress import StyledProgressBar, StatusBadge
from ..components.media_preview import MediaPreviewCard
from ..components.icons import IconManager

if TYPE_CHECKING:
    from ..app import DownloadyhaGUI


class PlaylistView(ctk.CTkFrame):
    """
    Dedicated view for Playlist, Album, and Channel batch downloading.
    """

    def __init__(self, master, app: DownloadyhaGUI, **kwargs):
        kwargs.setdefault("fg_color", Theme.BG_LIGHT)
        super().__init__(master, **kwargs)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._build_ui()

    def _build_ui(self):
        """Construct the Playlist layout."""
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        # 1. URL Input Card
        url_card = GlassCard(self.scroll)
        url_card.grid(row=0, column=0, padx=4, pady=(0, 12), sticky="ew")
        url_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            url_card,
            text=" Playlist or Channel Link",
            image=IconManager.get("playlist", size=(16, 16), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.section(13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        input_frame = ctk.CTkFrame(url_card, fg_color="transparent")
        input_frame.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.pl_url_entry = ModernEntry(
            input_frame,
            placeholder_text="Paste YouTube Playlist, Album, or Course URL...",
            height=42,
        )
        self.pl_url_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.pl_url_entry.bind("<Return>", lambda event: self._fetch_playlist_info())

        paste_btn = SecondaryButton(
            input_frame,
            text=" Paste",
            icon_name="paste",
            icon_size=(14, 14),
            width=85,
            height=42,
            command=self._paste_playlist_url,
        )
        paste_btn.grid(row=0, column=1, padx=(0, 6))

        self.pl_fetch_btn = CrimsonButton(
            input_frame,
            text=" Inspect Playlist",
            icon_name="search",
            icon_size=(14, 14),
            width=145,
            height=42,
            command=self._fetch_playlist_info,
        )
        self.pl_fetch_btn.grid(row=0, column=2)

        self.pl_feedback_label = ctk.CTkLabel(
            url_card,
            text="",
            font=Fonts.caption(11),
            text_color=Theme.TEXT_SECONDARY,
        )
        self.pl_feedback_label.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")

        # 2. Playlist Preview Card
        self.pl_preview_card = MediaPreviewCard(self.scroll)
        self.pl_preview_card.grid(row=1, column=0, padx=4, pady=(0, 12), sticky="ew")

        # 3. Batch Options Card
        options_card = GlassCard(self.scroll)
        options_card.grid(row=2, column=0, padx=4, pady=(0, 12), sticky="ew")
        options_card.grid_columnconfigure(0, weight=1)
        options_card.grid_columnconfigure(1, weight=1)

        headers_row = ctk.CTkFrame(options_card, fg_color="transparent")
        headers_row.grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 6), sticky="ew")
        headers_row.grid_columnconfigure(0, weight=1)
        headers_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            headers_row,
            text=" Batch Format:",
            image=IconManager.get("video", size=(14, 14), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.body_bold(12),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            headers_row,
            text=" Max Quality:",
            image=IconManager.get("sparkles", size=(14, 14), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.body_bold(12),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=1, padx=(10, 0), sticky="w")

        self.pl_format_var = tk.StringVar(value="Video")
        self.pl_format_selector = ctk.CTkSegmentedButton(
            options_card,
            values=["Video", "Audio", "Subtitles"],
            variable=self.pl_format_var,
            font=Fonts.body_bold(11),
            height=36,
            selected_color=Theme.CRIMSON_PRIMARY,
            selected_hover_color=Theme.CRIMSON_HOVER,
            unselected_color=Theme.BTN_SUBTLE_BG,
            unselected_hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
        )
        self.pl_format_selector.grid(row=1, column=0, padx=(16, 10), pady=(0, 14), sticky="ew")

        self.pl_quality_var = tk.StringVar(value="Best Available (Maximum Quality)")
        self.pl_quality_menu = ctk.CTkOptionMenu(
            options_card,
            variable=self.pl_quality_var,
            values=[
                "Best Available (Maximum Quality)",
                "1080p (Full HD)",
                "720p (HD)",
                "480p (SD)",
                "360p (Low)",
            ],
            font=Fonts.body(11),
            height=36,
            fg_color=Theme.BTN_SUBTLE_BG,
            button_color=Theme.BTN_SECONDARY_BG,
            button_hover_color=Theme.BTN_SECONDARY_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_fg_color=Theme.CARD_BG,
            dropdown_text_color=Theme.TEXT_PRIMARY,
        )
        self.pl_quality_menu.grid(row=1, column=1, padx=(10, 16), pady=(0, 14), sticky="ew")

        # 4. Action Bar
        action_bar = ctk.CTkFrame(
            self,
            fg_color=Theme.CARD_BG,
            corner_radius=0,
            border_width=1,
            border_color=Theme.CARD_BORDER,
        )
        action_bar.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        action_bar.grid_columnconfigure(0, weight=2)
        action_bar.grid_columnconfigure(1, weight=1)

        self.pl_download_btn = CrimsonButton(
            action_bar,
            text=" DOWNLOAD PLAYLIST BATCH",
            icon_name="download",
            icon_size=(16, 16),
            font=Fonts.section(13, weight="bold"),
            height=44,
            command=self._start_playlist_download,
        )
        self.pl_download_btn.grid(row=0, column=0, padx=(16, 8), pady=12, sticky="ew")

        open_folder_btn = SecondaryButton(
            action_bar,
            text=" Open Folder",
            icon_name="folder",
            icon_size=(15, 15),
            font=Fonts.body_bold(12),
            height=44,
            command=self.app._open_download_folder,
        )
        open_folder_btn.grid(row=0, column=1, padx=(8, 16), pady=12, sticky="ew")

    def _paste_playlist_url(self):
        """Paste clipboard text into playlist URL entry."""
        try:
            txt = self.clipboard_get()
            if txt:
                self.pl_url_entry.delete(0, tk.END)
                self.pl_url_entry.insert(0, txt.strip())
                self._fetch_playlist_info()
        except Exception:
            pass

    def _fetch_playlist_info(self):
        """Forward URL to main app and inspect playlist."""
        url = self.pl_url_entry.get().strip()
        if not url:
            self.pl_feedback_label.configure(text="Please enter a valid playlist URL.", text_color=Theme.WARNING_AMBER)
            return

        self.app.url_entry.delete(0, tk.END)
        self.app.url_entry.insert(0, url)
        self.app._fetch_media_info()
        self.pl_feedback_label.configure(text="Playlist details fetched in Single Downloader tab.", text_color=Theme.SUCCESS_GREEN)

    def _start_playlist_download(self):
        """Forward to main app download trigger."""
        url = self.pl_url_entry.get().strip()
        if url:
            self.app.url_entry.delete(0, tk.END)
            self.app.url_entry.insert(0, url)
        self.app.show_view("downloader")
        self.app._start_download()
