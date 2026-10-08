"""
collapsible.py - Accordion & Collapsible Containers for Downloadyha GUI

Allows grouping advanced settings (Clipping, Subtitles, Format Tweaks)
into neat collapsible sections to keep the interface uncluttered.
"""

from __future__ import annotations

from typing import Callable, Optional
import tkinter as tk
import customtkinter as ctk

from ..theme.palette import Theme, Fonts
from .icons import IconManager


class CollapsibleFrame(ctk.CTkFrame):
    """
    Collapsible container with a clickable header and expandable body.
    Features vector chevron animations and optional checkbox toggle mode.
    """

    def __init__(
        self,
        master,
        title: str,
        icon: str = "",
        icon_name: Optional[str] = None,
        is_expanded: bool = False,
        has_checkbox: bool = False,
        checkbox_var: Optional[tk.BooleanVar] = None,
        on_toggle: Optional[Callable[[bool], None]] = None,
        **kwargs
    ):
        kwargs.setdefault("fg_color", Theme.CARD_BG)
        kwargs.setdefault("corner_radius", Theme.CORNER_RADIUS_SM)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Theme.CARD_BORDER)
        super().__init__(master, **kwargs)

        self.title = title
        self.icon = icon
        self.icon_name = icon_name
        self.is_expanded = is_expanded
        self.has_checkbox = has_checkbox
        self.checkbox_var = checkbox_var or tk.BooleanVar(value=is_expanded)
        self.on_toggle = on_toggle

        self.grid_columnconfigure(0, weight=1)

        # 1. Header Bar
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=6)
        self.header_frame.grid_columnconfigure(1, weight=1)

        header_img = None
        if self.icon_name:
            header_img = IconManager.get(self.icon_name, size=(16, 16))

        display_title = f"{self.icon} {self.title}" if self.icon else self.title

        if self.has_checkbox:
            self.checkbox = ctk.CTkCheckBox(
                self.header_frame,
                text=f"  {display_title}",
                image=header_img,
                compound="left" if header_img else "none",
                variable=self.checkbox_var,
                font=Fonts.body_bold(12),
                text_color=Theme.TEXT_PRIMARY,
                fg_color=Theme.CRIMSON_PRIMARY,
                hover_color=Theme.CRIMSON_HOVER,
                checkmark_color="#FFFFFF",
                command=self._on_checkbox_clicked,
            )
            self.checkbox.grid(row=0, column=0, sticky="w")
        else:
            self.title_btn = ctk.CTkButton(
                self.header_frame,
                text=f"  {display_title}",
                image=header_img,
                compound="left" if header_img else "none",
                font=Fonts.body_bold(12),
                text_color=Theme.TEXT_PRIMARY,
                fg_color="transparent",
                hover_color=Theme.BTN_SUBTLE_HOVER,
                anchor="w",
                command=self.toggle,
            )
            self.title_btn.grid(row=0, column=0, sticky="w")

        # Vector chevron button
        chevron_name = "chevron_down" if self.is_expanded else "chevron_up"
        self.chevron = ctk.CTkButton(
            self.header_frame,
            text="",
            image=IconManager.get(chevron_name, size=(14, 14), color_light=Theme.TEXT_MUTED[0], color_dark=Theme.TEXT_MUTED[1]),
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=Theme.BTN_SUBTLE_HOVER,
            command=self.toggle,
        )
        self.chevron.grid(row=0, column=2, sticky="e")

        # 2. Content Body
        self.content_frame = ctk.CTkFrame(self, fg_color=Theme.BG_LIGHT, corner_radius=Theme.CORNER_RADIUS_SM)
        self.content_frame.grid_columnconfigure(0, weight=1)

        if self.is_expanded:
            self.content_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

    def _on_checkbox_clicked(self):
        """Handle checkbox change."""
        expanded = self.checkbox_var.get()
        self.set_expanded(expanded)
        if self.on_toggle:
            self.on_toggle(expanded)

    def toggle(self):
        """Toggle expand/collapse state."""
        self.set_expanded(not self.is_expanded)
        if self.has_checkbox:
            self.checkbox_var.set(self.is_expanded)
        if self.on_toggle:
            self.on_toggle(self.is_expanded)

    def set_expanded(self, expand: bool):
        """Programmatically set expanded state with vector chevron."""
        self.is_expanded = expand
        if self.is_expanded:
            self.content_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
            self.chevron.configure(
                image=IconManager.get("chevron_down", size=(14, 14), color_light=Theme.TEXT_MUTED[0], color_dark=Theme.TEXT_MUTED[1])
            )
        else:
            self.content_frame.grid_forget()
            self.chevron.configure(
                image=IconManager.get("chevron_up", size=(14, 14), color_light=Theme.TEXT_MUTED[0], color_dark=Theme.TEXT_MUTED[1])
            )

    def get_content(self) -> ctk.CTkFrame:
        """Return the inner content frame to place child widgets."""
        return self.content_frame
