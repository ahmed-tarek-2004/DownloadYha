"""
cards.py - Modern Card and Surface Components for Downloadyha GUI

Features:
- ModernCard: Rounded card surface with subtle border, padding, and adaptive Light/Dark styling.
- GlassCard: Elevated glassmorphism card (alias and backward-compatible implementation).
- StatCard: Compact metric tile for statistics, speed, format tags, and status displays.
"""

from __future__ import annotations

from typing import Optional
import customtkinter as ctk

from ..theme.palette import Theme, Fonts


class ModernCard(ctk.CTkFrame):
    """
    Elevated card container with modern rounded corners, adaptive surface color,
    and a subtle low-contrast border.
    """

    def __init__(
        self,
        master,
        corner_radius: int = Theme.CORNER_RADIUS_MD,
        border_width: int = 1,
        border_color=Theme.CARD_BORDER,
        fg_color=Theme.CARD_BG,
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=corner_radius,
            border_width=border_width,
            border_color=border_color,
            fg_color=fg_color,
            **kwargs
        )


class GlassCard(ModernCard):
    """Alias and backward-compatible card component."""
    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS_MD)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Theme.CARD_BORDER)
        kwargs.setdefault("fg_color", Theme.CARD_BG)
        super().__init__(master, **kwargs)


class StatCard(ModernCard):
    """
    Compact stat badge / metric card for displaying properties like
    Duration, View Count, Resolution tag, or Download Speed.
    """

    def __init__(
        self,
        master,
        title: str,
        value: str,
        icon: Optional[str] = None,
        accent_color=Theme.TEXT_PRIMARY,
        **kwargs
    ):
        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS_SM)
        kwargs.setdefault("fg_color", Theme.BG_LIGHT)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Theme.CARD_BORDER)
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1)

        header_text = f"{icon}  {title}" if icon else title
        self.header_label = ctk.CTkLabel(
            self,
            text=header_text,
            font=Fonts.caption(10, weight="bold"),
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        )
        self.header_label.pack(anchor="w", padx=8, pady=(6, 2))

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=Fonts.body_bold(12),
            text_color=accent_color,
            anchor="w",
        )
        self.value_label.pack(anchor="w", padx=8, pady=(0, 6))

    def update_value(self, value: str):
        """Update the displayed value."""
        self.value_label.configure(text=value)
