"""
history_view.py - Download History & Queue Workspace View for Downloadyha

Features:
- Live Queue and completed history cards with high-DPI vector icons.
- Strict INLINE error rendering with Crimson borders and retry buttons (zero modal pop-ups).
- Post-download actions: "Open Folder" and "Remove".
- Clear completed jobs action with trash vector icon.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional
import os
import sys
import customtkinter as ctk

from ..theme.palette import Theme, Fonts
from ..components.cards import ModernCard, GlassCard
from ..components.buttons import CrimsonButton, SecondaryButton, IconButton
from ..components.progress import StyledProgressBar
from ..components.icons import IconManager

if TYPE_CHECKING:
    from ..app import DownloadTask, DownloadyhaGUI


class DownloadQueueCard(ctk.CTkFrame):
    """
    Card representing an individual download task in the Queue / History.
    Features real-time progress, retry trigger on failure, and inline error presentation.
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

        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS_SM)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Theme.CARD_BORDER)
        kwargs.setdefault("fg_color", Theme.CARD_BG)
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(1, weight=1)
        self._build_ui()
        self.update_state()

    def _build_ui(self):
        """Construct the card elements."""
        # Left icon badge container
        self.icon_badge_container = ctk.CTkFrame(
            self,
            width=42,
            height=42,
            fg_color=Theme.BG_LIGHT,
            corner_radius=Theme.CORNER_RADIUS_SM,
        )
        self.icon_badge_container.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=12, sticky="n")
        self.icon_badge_container.grid_propagate(False)

        icon_name = "video" if self.task.media_type == "video" else ("subtitles" if self.task.media_type in ("subtitles", "subtitle", "subs") else "audio")
        self.icon_badge = ctk.CTkLabel(
            self.icon_badge_container,
            text="",
            image=IconManager.get(icon_name, size=(20, 20), color_light=Theme.TEXT_SECONDARY[0], color_dark=Theme.TEXT_SECONDARY[1]),
        )
        self.icon_badge.place(relx=0.5, rely=0.5, anchor="center")

        # Center content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, padx=(0, 10), pady=(10, 8), sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Title label
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text=self.task.title,
            font=Fonts.body_bold(13),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="ew")

        # Metadata line
        if self.task.media_type == "video":
            type_str = "Video"
        elif self.task.media_type in ("subtitles", "subtitle", "subs"):
            type_str = "Subtitles"
        else:
            type_str = "Audio"
        meta_info = f"{type_str} • {self.task.quality_label}"
        if self.task.uploader and self.task.uploader != "Unknown":
            meta_info += f" • {self.task.uploader}"
        if self.task.start_time or self.task.end_time:
            st = self.task.start_time or "00:00"
            et = self.task.end_time or "End"
            meta_info += f" • Clip ({st} - {et})"

        self.meta_label = ctk.CTkLabel(
            self.content_frame,
            text=meta_info,
            font=Fonts.caption(11),
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
            font=Fonts.caption(10),
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
            corner_radius=Theme.CORNER_RADIUS_SM,
        )
        self.error_label = ctk.CTkLabel(
            self.error_container,
            text="",
            font=Fonts.caption(11, weight="bold"),
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
            font=Fonts.caption(11, weight="bold"),
            text_color=Theme.TEXT_SECONDARY,
            fg_color=Theme.BG_SECONDARY,
            corner_radius=Theme.CORNER_RADIUS_SM,
            width=95,
            height=26,
        )
        self.status_badge.pack(side="top", pady=(0, 6))

        # Action buttons container
        self.btn_container = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        self.btn_container.pack(side="top", fill="x")

        # Retry button
        self.retry_btn = CrimsonButton(
            self.btn_container,
            text=" Retry",
            icon_name="refresh",
            icon_size=(12, 12),
            width=76,
            height=28,
            font=Fonts.caption(11, weight="bold"),
            command=lambda: self.on_retry(self.task),
        )

        # Remove button
        self.remove_btn = ctk.CTkButton(
            self.btn_container,
            text="",
            image=IconManager.get("close", size=(12, 12), color_light=Theme.TEXT_SECONDARY[0], color_dark=Theme.TEXT_SECONDARY[1]),
            width=28,
            height=28,
            fg_color=Theme.BTN_SUBTLE_BG,
            hover_color=Theme.BTN_SUBTLE_HOVER,
            command=lambda: self.on_remove(self.task),
        )
        self.remove_btn.pack(side="right", padx=(4, 0))

        # Open folder button
        self.open_btn = SecondaryButton(
            self.btn_container,
            text=" Open",
            icon_name="folder",
            icon_size=(13, 13),
            width=72,
            height=28,
            font=Fonts.caption(11),
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
        """Update styling based on task status."""
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
            self.status_badge.configure(text="Completed", text_color=Theme.SUCCESS_GREEN, fg_color=Theme.SUCCESS_LIGHT)
            self.progress_bar.set(1.0)
            self.metrics_label.configure(text="Download complete • 100%", text_color=Theme.SUCCESS_GREEN)
            self.error_container.grid_forget()
            self.retry_btn.pack_forget()
            self.open_btn.pack(side="left", padx=(0, 4))

        elif status == "failed":
            # Inline error styling, Crimson 2px border, Error box, Retry button
            self.configure(border_color=Theme.ERROR_RED, border_width=2, fg_color=Theme.CARD_BG)
            self.status_badge.configure(text="Failed", text_color=Theme.ERROR_RED, fg_color=Theme.ERROR_LIGHT)
            self.progress_bar.grid_forget()
            self.metrics_label.grid_forget()
            self.open_btn.pack_forget()

            err_text = f"Error: {self.task.error_message or 'Download was interrupted or encountered a network issue.'}"
            self.error_label.configure(text=err_text)
            self.error_container.grid(row=2, column=0, sticky="ew", pady=(4, 2))
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
        """Open the target directory in native file explorer."""
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


class HistoryView(ctk.CTkFrame):
    """
    Download Queue & History workspace view.
    """

    def __init__(self, master, app: DownloadyhaGUI, **kwargs):
        kwargs.setdefault("fg_color", Theme.BG_LIGHT)
        super().__init__(master, **kwargs)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_ui()

    def _build_ui(self):
        """Construct the Queue / History layout."""
        # Header Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text=" Download Queue & History",
            image=IconManager.get("queue", size=(18, 18), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.title(18),
            text_color=Theme.TEXT_PRIMARY,
        )
        title.grid(row=0, column=0, sticky="w")

        clear_btn = SecondaryButton(
            header,
            text=" Clear Finished",
            icon_name="trash",
            icon_size=(14, 14),
            width=135,
            height=34,
            font=Fonts.caption(11, weight="bold"),
            command=self.app._clear_completed_queue,
        )
        clear_btn.grid(row=0, column=1, sticky="e")

        # Scrollable list of cards
        self.queue_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.queue_scroll.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="nsew")
        self.queue_scroll.grid_columnconfigure(0, weight=1)

        # Placeholder label
        self.placeholder_frame = ctk.CTkFrame(self.queue_scroll, fg_color="transparent")
        self.placeholder_frame.grid(row=0, column=0, pady=80)

        self.placeholder_icon = ctk.CTkLabel(
            self.placeholder_frame,
            text="",
            image=IconManager.get("queue", size=(44, 44), color_light=Theme.TEXT_MUTED[0], color_dark=Theme.TEXT_MUTED[1]),
        )
        self.placeholder_icon.pack(pady=(0, 12))

        self.queue_placeholder = ctk.CTkLabel(
            self.placeholder_frame,
            text="No items in queue\nDownloads will appear here with live progress and inline status.",
            font=Fonts.body(13),
            text_color=Theme.TEXT_MUTED,
            justify="center",
        )
        self.queue_placeholder.pack()
