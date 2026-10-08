"""
media_preview.py - Media Preview Card with Asynchronous Thumbnail Rendering

Features:
- Displays video/playlist thumbnail with smooth rounded corners.
- Shows Title, Channel/Author, Duration badge, View Count, and Quality stream tags.
- Uses high-DPI vector badges and clean modern typography.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import customtkinter as ctk

from ..theme.palette import Theme, ThemeColors, Fonts
from .cards import ModernCard
from .thumbnail import ThumbnailManager
from .icons import IconManager


class MediaPreviewCard(ModernCard):
    """
    Card presenting rich media metadata, channel info, duration badge,
    and video thumbnail.
    """

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", Theme.CARD_BG)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Theme.CARD_BORDER)
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(1, weight=1)

        # 1. Left: Thumbnail preview with duration badge
        self.thumb_container = ctk.CTkFrame(
            self,
            fg_color=Theme.BG_SECONDARY,
            width=160,
            height=90,
            corner_radius=8,
            border_width=1,
            border_color=Theme.CARD_BORDER,
        )
        self.thumb_container.grid(row=0, column=0, rowspan=3, padx=14, pady=14, sticky="nw")
        self.thumb_container.grid_propagate(False)

        self.thumb_label = ctk.CTkLabel(
            self.thumb_container,
            text="",
            image=IconManager.get("video", size=(32, 32), color_light=Theme.TEXT_MUTED[0], color_dark=Theme.TEXT_MUTED[1]),
        )
        self.thumb_label.place(relx=0.5, rely=0.5, anchor="center")

        self.duration_badge = ctk.CTkLabel(
            self.thumb_container,
            text="",
            font=Fonts.caption(9, weight="bold"),
            text_color="#FFFFFF",
            fg_color=ThemeColors.DARK["bg_primary"],
            corner_radius=4,
            height=18,
            padx=4,
        )

        # 2. Right: Details Container
        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.details_frame.grid(row=0, column=1, padx=(0, 14), pady=12, sticky="nsew")
        self.details_frame.grid_columnconfigure(0, weight=1)

        # Type & Status Badge Row
        badge_row = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        badge_row.pack(fill="x", anchor="w", pady=(0, 4))

        self.type_badge = ctk.CTkLabel(
            badge_row,
            text=" Ready",
            image=IconManager.get("sparkles", size=(12, 12), color_light=Theme.TEXT_SECONDARY[0], color_dark=Theme.TEXT_SECONDARY[1]),
            compound="left",
            font=Fonts.caption(10, weight="bold"),
            text_color=Theme.TEXT_SECONDARY,
            fg_color=Theme.BG_SECONDARY,
            corner_radius=6,
            height=22,
            padx=8,
        )
        self.type_badge.pack(side="left", padx=(0, 8))

        self.channel_label = ctk.CTkLabel(
            badge_row,
            text="Paste a link above to inspect details",
            font=Fonts.caption(11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        )
        self.channel_label.pack(side="left", fill="x", expand=True)

        # Title Label
        self.title_label = ctk.CTkLabel(
            self.details_frame,
            text="No media analyzed yet",
            font=Fonts.body_bold(13),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
            wraplength=480,
            justify="left",
        )
        self.title_label.pack(fill="x", anchor="w", pady=(2, 4))

        # Metadata Tags Bar
        self.tags_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.tags_frame.pack(fill="x", anchor="w")

        self.meta_text_label = ctk.CTkLabel(
            self.tags_frame,
            text="Available resolutions and format options will load automatically",
            font=Fonts.caption(10),
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        )
        self.meta_text_label.pack(side="left", fill="x")

    def update_media(
        self,
        title: str,
        channel: str,
        duration_str: str = "",
        media_type_badge: str = "Single Video",
        meta_info_str: str = "",
        thumbnail_url: Optional[str] = None,
        is_error: bool = False,
    ):
        """Populate the preview card with fetched media details."""
        if is_error:
            self.type_badge.configure(
                text=" Error",
                image=IconManager.get("close", size=(11, 11), color_light=Theme.ERROR_RED[0], color_dark=Theme.ERROR_RED[1]),
                fg_color=Theme.ERROR_LIGHT,
                text_color=Theme.ERROR_RED,
            )
            self.title_label.configure(text=title, text_color=Theme.ERROR_RED)
            self.channel_label.configure(text="Inspection failed")
            self.meta_text_label.configure(text=meta_info_str)
            self.duration_badge.place_forget()
            return

        icon_name = "playlist" if "Playlist" in media_type_badge else "video"
        accent_light = Theme.CRIMSON_LIGHT
        accent_color = Theme.CRIMSON_PRIMARY

        clean_badge = media_type_badge.replace("🎬", "").replace("📑", "").strip()

        self.type_badge.configure(
            text=f" {clean_badge}",
            image=IconManager.get(icon_name, size=(12, 12), color_light=accent_color[0], color_dark=accent_color[1]),
            fg_color=accent_light,
            text_color=accent_color,
        )
        self.title_label.configure(text=title, text_color=Theme.TEXT_PRIMARY)
        self.channel_label.configure(text=f"Channel: {channel}")
        self.meta_text_label.configure(text=meta_info_str)

        if duration_str:
            self.duration_badge.configure(text=duration_str)
            self.duration_badge.place(relx=0.96, rely=0.92, anchor="se")
        else:
            self.duration_badge.place_forget()

        # Fetch and display thumbnail if available
        if thumbnail_url:
            def on_thumb_ready(ctk_img):
                self.after(0, lambda: self._apply_thumbnail(ctk_img))
            ThumbnailManager.fetch_async(thumbnail_url, size=(160, 90), corner_radius=8, callback=on_thumb_ready)
        else:
            self.thumb_label.configure(
                image=IconManager.get("video", size=(32, 32), color_light=Theme.TEXT_MUTED[0], color_dark=Theme.TEXT_MUTED[1]),
                text="",
            )

    def _apply_thumbnail(self, ctk_img):
        """Apply fetched CTkImage to the thumbnail label."""
        self.thumb_label.configure(image=ctk_img, text="")

    def reset(self):
        """Reset preview back to initial placeholder state."""
        self.type_badge.configure(
            text=" Ready",
            image=IconManager.get("sparkles", size=(12, 12), color_light=Theme.TEXT_SECONDARY[0], color_dark=Theme.TEXT_SECONDARY[1]),
            fg_color=Theme.BG_SECONDARY,
            text_color=Theme.TEXT_SECONDARY,
        )
        self.title_label.configure(text="No media analyzed yet", text_color=Theme.TEXT_PRIMARY)
        self.channel_label.configure(text="Paste a link above to inspect details")
        self.meta_text_label.configure(text="Available resolutions and format options will load automatically")
        self.thumb_label.configure(
            image=IconManager.get("video", size=(32, 32), color_light=Theme.TEXT_MUTED[0], color_dark=Theme.TEXT_MUTED[1]),
            text="",
        )
        self.duration_badge.place_forget()
