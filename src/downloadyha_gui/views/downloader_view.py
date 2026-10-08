"""
downloader_view.py - Single Downloader Workspace View for Downloadyha

Features:
- Hero URL Input Bar with high-DPI vector icons, clipboard auto-detect, and quick inspect.
- Media Preview Card with asynchronous thumbnail rendering, duration badge, and metadata pills.
- Sleek Segmented Format & Dynamic Quality resolution picker.
- Expandable accordions for Partial Clipping and Subtitles/Transcripts with vector indicators.
- Fixed docked bottom action bar with prominent CTA, cancellation, and folder actions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
import tkinter as tk
import customtkinter as ctk

from ..theme.palette import Theme, Fonts
from ..components.cards import ModernCard, GlassCard
from ..components.buttons import CrimsonButton, PrimaryButton, SecondaryButton, SubtleButton
from ..components.inputs import ModernEntry
from ..components.progress import StyledProgressBar, StatusBadge
from ..components.collapsible import CollapsibleFrame
from ..components.media_preview import MediaPreviewCard
from ..components.icons import IconManager

if TYPE_CHECKING:
    from ..app import DownloadyhaGUI


class DownloaderView(ctk.CTkFrame):
    """
    Main Single Downloader Workspace View containing hero input, preview,
    options, collapsible settings, and docked action bar.
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
        """Construct the Downloader layout with scrollable form and docked action bar."""
        # Scrollable form container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        # 1. Hero URL Input Card
        self._build_url_card()

        # 2. Media Preview Card
        self._build_media_preview_card()

        # 3. Format & Dynamic Quality Card
        self._build_options_card()

        # 4. Destination Directory Card
        self._build_destination_card()

        # 5. Live Progress & Status Card
        self._build_status_card()

        # 6. Fixed Docked Action Bar
        self._build_action_bar()

    def _build_url_card(self):
        """Construct Hero URL Input Card with vector icons and modern layout."""
        self.url_card = GlassCard(self.scroll)
        self.url_card.grid(row=0, column=0, padx=4, pady=(0, 12), sticky="ew")
        self.url_card.grid_columnconfigure(0, weight=1)

        # Header Row
        header_row = ctk.CTkFrame(self.url_card, fg_color="transparent")
        header_row.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        header_row.grid_columnconfigure(1, weight=1)

        url_header = ctk.CTkLabel(
            header_row,
            text=" Media or Playlist URL",
            image=IconManager.get("link", size=(16, 16), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.section(13, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        )
        url_header.grid(row=0, column=0, sticky="w")

        # Input Row
        url_input_frame = ctk.CTkFrame(self.url_card, fg_color="transparent")
        url_input_frame.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")
        url_input_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ModernEntry(
            url_input_frame,
            placeholder_text="Paste YouTube, TikTok, Facebook, Instagram, or media URL...",
            height=42,
        )
        self.url_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.url_entry.bind("<Return>", lambda event: self.app._fetch_media_info())

        self.paste_btn = SecondaryButton(
            url_input_frame,
            text=" Paste",
            icon_name="paste",
            icon_size=(14, 14),
            width=85,
            height=42,
            command=self.app._paste_url,
        )
        self.paste_btn.grid(row=0, column=1, padx=(0, 6))

        self.fetch_btn = CrimsonButton(
            url_input_frame,
            text=" Inspect Media",
            icon_name="search",
            icon_size=(14, 14),
            width=135,
            height=42,
            command=self.app._fetch_media_info,
        )
        self.fetch_btn.grid(row=0, column=2)

        # Inline URL Feedback / Error label
        self.url_feedback_label = ctk.CTkLabel(
            self.url_card,
            text="",
            font=Fonts.caption(11),
            text_color=Theme.TEXT_SECONDARY,
        )
        self.url_feedback_label.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")

    def _build_media_preview_card(self):
        """Construct Media Inspection Details / Preview Card."""
        self.media_preview_card = MediaPreviewCard(self.scroll)
        self.media_preview_card.grid(row=1, column=0, padx=4, pady=(0, 12), sticky="ew")

        # Expose legacy labels for backwards compatibility with tests
        self.media_card = self.media_preview_card
        self.media_badge = self.media_preview_card.type_badge
        self.media_channel_label = self.media_preview_card.channel_label
        self.media_title_label = self.media_preview_card.title_label
        self.media_meta_label = self.media_preview_card.meta_text_label

    def _build_options_card(self):
        """Construct Format, Dynamic Quality, and Collapsible Accordions."""
        self.options_card = GlassCard(self.scroll)
        self.options_card.grid(row=2, column=0, padx=4, pady=(0, 12), sticky="ew")
        self.options_card.grid_columnconfigure(0, weight=1)
        self.options_card.grid_columnconfigure(1, weight=1)

        # Headers Row
        headers_row = ctk.CTkFrame(self.options_card, fg_color="transparent")
        headers_row.grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 6), sticky="ew")
        headers_row.grid_columnconfigure(0, weight=1)
        headers_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            headers_row,
            text=" Media Format:",
            image=IconManager.get("video", size=(14, 14), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.body_bold(12),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            headers_row,
            text=" Quality / Bitrate:",
            image=IconManager.get("sparkles", size=(14, 14), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.body_bold(12),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=1, padx=(10, 0), sticky="w")

        # Format Segmented Selector
        self.media_type_var = tk.StringVar(value="Video")
        self.media_type_selector = ctk.CTkSegmentedButton(
            self.options_card,
            values=["Video", "Audio", "Subtitles"],
            variable=self.media_type_var,
            font=Fonts.body_bold(11),
            command=self.app._on_media_type_changed,
            corner_radius=Theme.CORNER_RADIUS_SM,
            height=36,
            selected_color=Theme.CRIMSON_PRIMARY,
            selected_hover_color=Theme.CRIMSON_HOVER,
            unselected_color=Theme.BTN_SUBTLE_BG,
            unselected_hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
        )
        self.media_type_selector.grid(row=1, column=0, padx=(16, 10), pady=(0, 14), sticky="ew")

        # Dynamic Quality Dropdown
        self.quality_var = tk.StringVar(value="Best Available (Maximum Quality)")
        self.quality_menu = ctk.CTkOptionMenu(
            self.options_card,
            variable=self.quality_var,
            values=["Best Available (Maximum Quality)"],
            font=Fonts.body(11),
            dropdown_font=Fonts.body(11),
            corner_radius=Theme.CORNER_RADIUS_SM,
            height=36,
            fg_color=Theme.BTN_SUBTLE_BG,
            button_color=Theme.BTN_SECONDARY_BG,
            button_hover_color=Theme.BTN_SECONDARY_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_fg_color=Theme.CARD_BG,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            dropdown_hover_color=Theme.BTN_SUBTLE_HOVER,
        )
        self.quality_menu.grid(row=1, column=1, padx=(10, 16), pady=(0, 14), sticky="ew")

        # Checkbox Row for Toggling Collapsibles
        toggles_frame = ctk.CTkFrame(self.options_card, fg_color="transparent")
        toggles_frame.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 12), sticky="ew")

        self.section_toggle_var = tk.BooleanVar(value=False)
        self.section_toggle = ctk.CTkCheckBox(
            toggles_frame,
            text=" Clip specific section (Start / End)",
            variable=self.section_toggle_var,
            font=Fonts.body_bold(11),
            text_color=Theme.TEXT_PRIMARY,
            command=self.app._on_section_toggled,
            fg_color=Theme.CRIMSON_PRIMARY,
            hover_color=Theme.CRIMSON_HOVER,
            checkmark_color="#FFFFFF",
        )
        self.section_toggle.pack(side="left", padx=(0, 24))

        self.transcript_toggle_var = tk.BooleanVar(value=False)
        self.transcript_toggle = ctk.CTkCheckBox(
            toggles_frame,
            text=" Subtitles & Captions",
            variable=self.transcript_toggle_var,
            font=Fonts.body_bold(11),
            text_color=Theme.TEXT_PRIMARY,
            command=self.app._on_transcript_toggled,
            fg_color=Theme.CRIMSON_PRIMARY,
            hover_color=Theme.CRIMSON_HOVER,
            checkmark_color="#FFFFFF",
        )
        self.transcript_toggle.pack(side="left")

        # Collapsible Section Inputs (Clipping)
        self.section_frame = ctk.CTkFrame(self.options_card, fg_color=Theme.BG_LIGHT, corner_radius=Theme.CORNER_RADIUS_SM)
        self.section_frame.grid_columnconfigure(0, weight=1)
        self.section_frame.grid_columnconfigure(1, weight=1)

        start_box = ctk.CTkFrame(self.section_frame, fg_color="transparent")
        start_box.grid(row=0, column=0, padx=(12, 6), pady=(8, 2), sticky="ew")
        start_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(start_box, text="Start Time:", font=Fonts.body_bold(11), text_color=Theme.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self.start_time_entry = ModernEntry(start_box, placeholder_text="00:00 (e.g. 01:30)", height=32)
        self.start_time_entry.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        end_box = ctk.CTkFrame(self.section_frame, fg_color="transparent")
        end_box.grid(row=0, column=1, padx=(6, 12), pady=(8, 2), sticky="ew")
        end_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(end_box, text="End Time:", font=Fonts.body_bold(11), text_color=Theme.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self.end_time_entry = ModernEntry(end_box, placeholder_text="Leave blank for end (e.g. 03:45)", height=32)
        self.end_time_entry.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        self.section_hint_label = ctk.CTkLabel(
            self.section_frame,
            text="Formats: MM:SS, HH:MM:SS, or seconds (e.g. 01:30, 90, 01:15:30)",
            font=Fonts.caption(10),
            text_color=Theme.TEXT_SECONDARY,
        )
        self.section_hint_label.grid(row=1, column=0, columnspan=2, padx=12, pady=(2, 8), sticky="w")

        # Collapsible Subtitles Frame
        self.transcript_frame = ctk.CTkFrame(self.options_card, fg_color=Theme.BG_LIGHT, corner_radius=Theme.CORNER_RADIUS_SM)
        self.transcript_frame.grid_columnconfigure(0, weight=1)
        self.transcript_frame.grid_columnconfigure(1, weight=1)

        lang_box = ctk.CTkFrame(self.transcript_frame, fg_color="transparent")
        lang_box.grid(row=0, column=0, padx=(12, 6), pady=(8, 2), sticky="ew")
        lang_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lang_box, text="Subtitle Language:", font=Fonts.body_bold(11), text_color=Theme.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self.sub_langs_var = tk.StringVar(value="en (English)")
        self.sub_langs_menu = ctk.CTkOptionMenu(
            lang_box,
            variable=self.sub_langs_var,
            values=["en (English)", "ar (Arabic)", "es (Spanish)", "all (All Available)"],
            height=32,
            font=Fonts.body(11),
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
        ctk.CTkLabel(fmt_box, text="Subtitle Format:", font=Fonts.body_bold(11), text_color=Theme.TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        self.sub_format_var = tk.StringVar(value="srt")
        self.sub_format_menu = ctk.CTkOptionMenu(
            fmt_box,
            variable=self.sub_format_var,
            values=["srt", "vtt", "ass", "lrc"],
            font=Fonts.body(11),
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
            font=Fonts.body(11),
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
            font=Fonts.body(11),
            text_color=Theme.TEXT_PRIMARY,
            fg_color=Theme.CRIMSON_PRIMARY,
            hover_color=Theme.CRIMSON_HOVER,
            checkmark_color="#FFFFFF",
        )
        self.embed_subs_check.pack(side="left")

        # Collapsible Playlist Scope Frame
        self.playlist_scope_frame = ctk.CTkFrame(self.options_card, fg_color=Theme.BG_LIGHT, corner_radius=Theme.CORNER_RADIUS_SM)
        self.playlist_scope_frame.grid_columnconfigure(0, weight=1)

        scope_header_box = ctk.CTkFrame(self.playlist_scope_frame, fg_color="transparent")
        scope_header_box.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            scope_header_box,
            text=" Video in Playlist Detected — Choose Download Scope:",
            image=IconManager.get("playlist", size=(14, 14), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.body_bold(11),
            text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left")

        self.playlist_scope_var = tk.StringVar(value="single")
        self.playlist_scope_segmented = ctk.CTkSegmentedButton(
            self.playlist_scope_frame,
            values=["Single Video (Recommended)", "Entire Playlist Batch"],
            font=Fonts.body_bold(11),
            height=32,
            selected_color=Theme.CRIMSON_PRIMARY,
            selected_hover_color=Theme.CRIMSON_HOVER,
            unselected_color=Theme.BTN_SUBTLE_BG,
            unselected_hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            command=self.app._on_playlist_scope_changed,
        )
        self.playlist_scope_segmented.pack(fill="x", padx=12, pady=(0, 8))
        self.playlist_scope_segmented.set("Single Video (Recommended)")

    def _build_destination_card(self):
        """Construct Destination Directory Card."""
        dest_card = GlassCard(self.scroll)
        dest_card.grid(row=3, column=0, padx=4, pady=(0, 12), sticky="ew")
        dest_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dest_card,
            text=" Save Location:",
            image=IconManager.get("folder", size=(15, 15), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.body_bold(12),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(14, 6), sticky="w")

        dest_input_frame = ctk.CTkFrame(dest_card, fg_color="transparent")
        dest_input_frame.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")
        dest_input_frame.grid_columnconfigure(0, weight=1)

        self.dest_entry = ModernEntry(
            dest_input_frame,
            height=38,
        )
        self.dest_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        browse_btn = SecondaryButton(
            dest_input_frame,
            text=" Browse",
            icon_name="folder",
            icon_size=(14, 14),
            width=95,
            height=38,
            command=self.app._browse_destination,
        )
        browse_btn.grid(row=0, column=1)

    def _build_status_card(self):
        """Construct Active Download & Status Card."""
        self.active_status_card = GlassCard(self.scroll)
        self.active_status_card.grid(row=4, column=0, padx=4, pady=(0, 12), sticky="ew")
        self.active_status_card.grid_columnconfigure(0, weight=1)

        status_header = ctk.CTkFrame(self.active_status_card, fg_color="transparent")
        status_header.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="ew")
        status_header.grid_columnconfigure(0, weight=1)

        self.status_title_label = ctk.CTkLabel(
            status_header,
            text=" Download Progress & Status",
            image=IconManager.get("download", size=(14, 14), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.body_bold(12),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.status_title_label.grid(row=0, column=0, sticky="w")

        self.active_status_badge = StatusBadge(
            status_header,
            text="Idle",
            status="idle",
            width=80,
            height=22,
        )
        self.active_status_badge.grid(row=0, column=1, sticky="e")

        self.active_item_label = ctk.CTkLabel(
            self.active_status_card,
            text="Ready to download",
            font=Fonts.body(12),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        )
        self.active_item_label.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="ew")

        self.main_progress_bar = StyledProgressBar(self.active_status_card)
        self.main_progress_bar.grid(row=2, column=0, padx=16, pady=(2, 6), sticky="ew")
        self.main_progress_bar.set(0)

        # Metrics bar
        metrics_bar = ctk.CTkFrame(self.active_status_card, fg_color="transparent")
        metrics_bar.grid(row=3, column=0, padx=16, pady=(0, 12), sticky="ew")
        metrics_bar.grid_columnconfigure(0, weight=1)
        metrics_bar.grid_columnconfigure(1, weight=1)
        metrics_bar.grid_columnconfigure(2, weight=1)

        self.main_percent_label = ctk.CTkLabel(
            metrics_bar,
            text="0%",
            font=Fonts.body_bold(11),
            text_color=Theme.CRIMSON_PRIMARY,
            anchor="w",
        )
        self.main_percent_label.grid(row=0, column=0, sticky="w")

        self.main_speed_label = ctk.CTkLabel(
            metrics_bar,
            text="Speed: --",
            font=Fonts.caption(11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="center",
        )
        self.main_speed_label.grid(row=0, column=1, sticky="ew")

        self.main_eta_label = ctk.CTkLabel(
            metrics_bar,
            text="ETA: --",
            font=Fonts.caption(11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="e",
        )
        self.main_eta_label.grid(row=0, column=2, sticky="e")

        # INLINE ERROR CONTAINER (100% Zero-Popup Policy)
        self.main_error_banner = ctk.CTkFrame(
            self.active_status_card,
            fg_color=Theme.ERROR_LIGHT,
            border_width=1,
            border_color=Theme.ERROR_RED,
            corner_radius=Theme.CORNER_RADIUS_SM,
        )
        self.main_error_banner.grid_columnconfigure(0, weight=1)

        self.main_error_label = ctk.CTkLabel(
            self.main_error_banner,
            text="",
            font=Fonts.body_bold(11),
            text_color=Theme.ERROR_RED,
            wraplength=600,
            justify="left",
            anchor="w",
        )
        self.main_error_label.grid(row=0, column=0, padx=12, pady=8, sticky="ew")

        self.main_retry_btn = CrimsonButton(
            self.main_error_banner,
            text=" Retry Download",
            icon_name="refresh",
            icon_size=(13, 13),
            width=140,
            height=32,
            command=self.app._retry_active_download,
        )
        self.main_retry_btn.grid(row=0, column=1, padx=(0, 10), pady=8)

    def _build_action_bar(self):
        """Construct Fixed Docked Bottom Action Bar with vector icons."""
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
        action_bar.grid_columnconfigure(2, weight=1)

        self.start_download_btn = CrimsonButton(
            action_bar,
            text=" START DOWNLOAD",
            icon_name="download",
            icon_size=(16, 16),
            font=Fonts.section(13, weight="bold"),
            height=44,
            command=self.app._start_download,
        )
        self.start_download_btn.grid(row=0, column=0, padx=(16, 8), pady=12, sticky="ew")

        self.cancel_download_btn = ctk.CTkButton(
            action_bar,
            text=" Cancel",
            image=IconManager.get("close", size=(14, 14), color_light=Theme.ERROR_RED[0], color_dark=Theme.ERROR_RED[1]),
            compound="left",
            font=Fonts.body_bold(12),
            height=44,
            corner_radius=Theme.CORNER_RADIUS_SM,
            fg_color=Theme.ERROR_LIGHT,
            hover_color=("#FECACA", "#5C1111"),
            text_color=Theme.ERROR_RED,
            command=self.app._cancel_download,
            state="disabled",
        )
        self.cancel_download_btn.grid(row=0, column=1, padx=4, pady=12, sticky="ew")

        self.open_folder_btn = SecondaryButton(
            action_bar,
            text=" Open Folder",
            icon_name="folder",
            icon_size=(15, 15),
            font=Fonts.body_bold(12),
            height=44,
            command=self.app._open_download_folder,
        )
        self.open_folder_btn.grid(row=0, column=2, padx=(8, 16), pady=12, sticky="ew")
