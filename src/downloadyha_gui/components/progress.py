"""
progress.py - Progress Indicators & Status Badges for Downloadyha GUI

Features:
- StyledProgressBar / ModernProgressBar: Custom progress bar with rounded corners and vibrant fill.
- StatusBadge: Dynamic pill badge reflecting task state (Idle, Downloading, Saved, Failed, Cancelled).
- LiveProgressCard: Container for real-time progress metrics (percentage, speed, ETA, downloaded size).
"""

from __future__ import annotations

from typing import Optional
import customtkinter as ctk

from ..theme.palette import Theme, Fonts
from .cards import ModernCard


class StyledProgressBar(ctk.CTkProgressBar):
    """Progress bar configured with modern accent styling and rounded corners."""

    def __init__(
        self,
        master,
        height: int = 10,
        corner_radius: int = 6,
        progress_color=Theme.CRIMSON_PRIMARY,
        fg_color=Theme.PROGRESS_BG,
        **kwargs
    ):
        super().__init__(
            master,
            height=height,
            corner_radius=corner_radius,
            progress_color=progress_color,
            fg_color=fg_color,
            **kwargs
        )


class ModernProgressBar(StyledProgressBar):
    """Modern progress bar defaulting to primary Indigo accent."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("progress_color", Theme.INDIGO_PRIMARY)
        super().__init__(master, **kwargs)


class StatusBadge(ctk.CTkLabel):
    """Pill badge displaying current state with color-coded background and text."""

    def __init__(
        self,
        master,
        text: str = "Idle",
        status: str = "idle",
        width: int = 90,
        height: int = 24,
        corner_radius: int = Theme.CORNER_RADIUS_SM,
        **kwargs
    ):
        super().__init__(
            master,
            text=text,
            width=width,
            height=height,
            corner_radius=corner_radius,
            font=Fonts.caption(10, weight="bold"),
            **kwargs
        )
        self.set_status(status, text)

    def set_status(self, status: str, text: Optional[str] = None):
        """Update badge text and colors according to status code."""
        status_map = {
            "idle": ("Idle", Theme.TEXT_MUTED, Theme.BG_LIGHT),
            "queued": ("Queued", Theme.TEXT_SECONDARY, Theme.BG_SECONDARY),
            "downloading": ("Downloading", Theme.CRIMSON_PRIMARY, Theme.CRIMSON_LIGHT),
            "completed": ("✓ Completed", Theme.SUCCESS_GREEN, Theme.SUCCESS_LIGHT),
            "saved": ("✓ Saved", Theme.SUCCESS_GREEN, Theme.SUCCESS_LIGHT),
            "failed": ("✕ Failed", Theme.ERROR_RED, Theme.ERROR_LIGHT),
            "cancelled": ("Cancelled", Theme.WARNING_AMBER, Theme.WARNING_LIGHT),
            "ready": ("● Ready", Theme.SUCCESS_GREEN, Theme.SUCCESS_LIGHT),
            "checking": ("⏳ Checking", Theme.INFO_BLUE, Theme.INFO_LIGHT),
        }

        default_text, text_col, bg_col = status_map.get(
            status.lower(), (status.capitalize(), Theme.TEXT_SECONDARY, Theme.BG_SECONDARY)
        )
        display_text = text if text is not None else default_text

        self.configure(
            text=display_text,
            text_color=text_col,
            fg_color=bg_col,
        )


class LiveProgressCard(ModernCard):
    """
    Live download status card presenting real-time percentage,
    progress bar, transfer rate (speed), ETA, and post-download quick actions.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        # Header with title and status badge
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            header,
            text="📊 Download Progress & Status",
            font=Fonts.section(12, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.badge = StatusBadge(header, text="Idle", status="idle")
        self.badge.grid(row=0, column=1, sticky="e")

        # Current item subtitle
        self.item_label = ctk.CTkLabel(
            self,
            text="Ready to download",
            font=Fonts.body(11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        )
        self.item_label.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="ew")

        # Progress bar
        self.progress_bar = StyledProgressBar(self)
        self.progress_bar.grid(row=2, column=0, padx=16, pady=(2, 4), sticky="ew")
        self.progress_bar.set(0)

        # Metrics row
        metrics_bar = ctk.CTkFrame(self, fg_color="transparent")
        metrics_bar.grid(row=3, column=0, padx=16, pady=(0, 12), sticky="ew")
        metrics_bar.grid_columnconfigure(0, weight=1)
        metrics_bar.grid_columnconfigure(1, weight=1)
        metrics_bar.grid_columnconfigure(2, weight=1)

        self.percent_label = ctk.CTkLabel(
            metrics_bar,
            text="0%",
            font=Fonts.body_bold(11),
            text_color=Theme.CRIMSON_PRIMARY,
            anchor="w",
        )
        self.percent_label.grid(row=0, column=0, sticky="w")

        self.speed_label = ctk.CTkLabel(
            metrics_bar,
            text="Speed: --",
            font=Fonts.caption(11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="center",
        )
        self.speed_label.grid(row=0, column=1, sticky="ew")

        self.eta_label = ctk.CTkLabel(
            metrics_bar,
            text="ETA: --",
            font=Fonts.caption(11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="e",
        )
        self.eta_label.grid(row=0, column=2, sticky="e")

    def update_progress(self, percent: float, speed: str = "--", eta: str = "--", item_name: str = ""):
        """Update metrics in the card."""
        self.progress_bar.set(percent / 100.0)
        self.percent_label.configure(text=f"{percent:.1f}%")
        self.speed_label.configure(text=f"Speed: {speed}")
        self.eta_label.configure(text=f"ETA: {eta}")
        if item_name:
            self.item_label.configure(text=f"Downloading: {item_name}")

    def reset(self):
        """Reset progress back to idle."""
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.speed_label.configure(text="Speed: --")
        self.eta_label.configure(text="ETA: --")
        self.item_label.configure(text="Ready to download", text_color=Theme.TEXT_SECONDARY)
        self.badge.set_status("idle", "Idle")
