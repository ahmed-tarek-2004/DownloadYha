"""
buttons.py - Modern Button Components for Downloadyha GUI

Features:
- PrimaryButton: Eye-pleasing CTA button with rounded corners and modern accent.
- CrimsonButton / ModernButton: Deep crimson button with safe hover handlers.
- SecondaryButton: Subtle, low-contrast background with adaptive dark/light styling.
- SubtleButton: Minimalist button for secondary navigation or inline actions.
- IconButton: Compact icon action button using vector icons from IconManager.
"""

from __future__ import annotations

from typing import Optional
import customtkinter as ctk

from ..theme.palette import Theme, Fonts
from .icons import IconManager


class PrimaryButton(ctk.CTkButton):
    """Primary Action CTA button with modern accent styling."""

    def __init__(
        self,
        master,
        icon_name: Optional[str] = None,
        icon_size: tuple[int, int] = (16, 16),
        **kwargs
    ):
        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS_SM)
        kwargs.setdefault("height", 38)
        kwargs.setdefault("font", Fonts.body_bold(12))
        kwargs.setdefault("fg_color", Theme.INDIGO_PRIMARY)
        kwargs.setdefault("hover_color", Theme.INDIGO_HOVER)
        kwargs.setdefault("text_color", "#FFFFFF")
        if icon_name and "image" not in kwargs:
            kwargs["image"] = IconManager.get(
                icon_name, size=icon_size, color_light="#FFFFFF", color_dark="#FFFFFF"
            )
            kwargs.setdefault("compound", "left")
        super().__init__(master, **kwargs)


class CrimsonButton(ctk.CTkButton):
    """Primary Action Button with Deep Crimson styling."""

    def __init__(
        self,
        master,
        icon_name: Optional[str] = None,
        icon_size: tuple[int, int] = (16, 16),
        **kwargs
    ):
        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS_SM)
        kwargs.setdefault("height", 38)
        kwargs.setdefault("font", Fonts.body_bold(12))
        kwargs.setdefault("fg_color", Theme.CRIMSON_PRIMARY)
        kwargs.setdefault("hover_color", Theme.CRIMSON_HOVER)
        kwargs.setdefault("text_color", "#FFFFFF")
        if icon_name and "image" not in kwargs:
            kwargs["image"] = IconManager.get(
                icon_name, size=icon_size, color_light="#FFFFFF", color_dark="#FFFFFF"
            )
            kwargs.setdefault("compound", "left")
        super().__init__(master, **kwargs)

    def _on_leave(self, event=None):
        """Handle mouse leave safely (handles 0 or 1 args)."""
        try:
            super()._on_leave(event)
        except TypeError:
            super()._on_leave()

    def _on_enter(self, event=None):
        """Handle mouse enter safely (handles 0 or 1 args)."""
        try:
            super()._on_enter(event)
        except TypeError:
            super()._on_enter()


class ModernButton(CrimsonButton):
    """Alias for backwards compatibility with test suites."""
    pass


class SecondaryButton(ctk.CTkButton):
    """Secondary Action Button with adaptive Light/Dark styling."""

    def __init__(
        self,
        master,
        icon_name: Optional[str] = None,
        icon_size: tuple[int, int] = (16, 16),
        **kwargs
    ):
        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS_SM)
        kwargs.setdefault("height", 36)
        kwargs.setdefault("font", Fonts.body(12))
        kwargs.setdefault("fg_color", Theme.BTN_SECONDARY_BG)
        kwargs.setdefault("hover_color", Theme.BTN_SECONDARY_HOVER)
        kwargs.setdefault("text_color", Theme.BTN_SECONDARY_TEXT)
        if icon_name and "image" not in kwargs:
            kwargs["image"] = IconManager.get(icon_name, size=icon_size)
            kwargs.setdefault("compound", "left")
        super().__init__(master, **kwargs)


class SubtleButton(ctk.CTkButton):
    """Minimal button with transparent or subtle background."""

    def __init__(
        self,
        master,
        icon_name: Optional[str] = None,
        icon_size: tuple[int, int] = (16, 16),
        **kwargs
    ):
        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS_SM)
        kwargs.setdefault("height", 32)
        kwargs.setdefault("font", Fonts.body(11))
        kwargs.setdefault("fg_color", Theme.BTN_SUBTLE_BG)
        kwargs.setdefault("hover_color", Theme.BTN_SUBTLE_HOVER)
        kwargs.setdefault("text_color", Theme.TEXT_PRIMARY)
        if icon_name and "image" not in kwargs:
            kwargs["image"] = IconManager.get(icon_name, size=icon_size)
            kwargs.setdefault("compound", "left")
        super().__init__(master, **kwargs)


class IconButton(ctk.CTkButton):
    """Compact square icon button using high-DPI vector icons."""

    def __init__(
        self,
        master,
        icon_name: Optional[str] = None,
        icon: str = "",
        size: int = 32,
        **kwargs
    ):
        kwargs.setdefault("width", size)
        kwargs.setdefault("height", size)
        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS_SM)
        kwargs.setdefault("fg_color", Theme.BTN_SUBTLE_BG)
        kwargs.setdefault("hover_color", Theme.BTN_SUBTLE_HOVER)
        kwargs.setdefault("text_color", Theme.TEXT_PRIMARY)

        if icon_name and "image" not in kwargs:
            kwargs["image"] = IconManager.get(icon_name, size=(size - 12, size - 12))
            kwargs.setdefault("text", "")
        else:
            kwargs.setdefault("text", icon)
            kwargs.setdefault("font", Fonts.body(12))

        super().__init__(master, **kwargs)
