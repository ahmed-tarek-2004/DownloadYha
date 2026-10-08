"""
inputs.py - Modern Input Components for Downloadyha GUI

Features:
- ModernEntry: Sleek, rounded text entry with crisp borders and focus styling.
- URLInputBar: Integrated hero URL input bar with paste button and quick fetch trigger.
- TimeRangeInput: Interactive start & end time range selector with validation tips.
"""

from __future__ import annotations

from typing import Callable, Optional
import tkinter as tk
import customtkinter as ctk

from ..theme.palette import Theme, Fonts
from .buttons import PrimaryButton, CrimsonButton, SecondaryButton
from .icons import IconManager


class ModernEntry(ctk.CTkEntry):
    """Sleek text input with modern rounded corners and low-contrast borders."""

    def __init__(
        self,
        master,
        height: int = 38,
        corner_radius: int = Theme.CORNER_RADIUS_SM,
        border_width: int = 1,
        border_color=Theme.CARD_BORDER,
        fg_color=Theme.ENTRY_BG,
        text_color=Theme.TEXT_PRIMARY,
        placeholder_text_color=Theme.TEXT_MUTED,
        font=None,
        **kwargs
    ):
        font = font or Fonts.body(12)
        super().__init__(
            master,
            height=height,
            corner_radius=corner_radius,
            border_width=border_width,
            border_color=border_color,
            fg_color=fg_color,
            text_color=text_color,
            placeholder_text_color=placeholder_text_color,
            font=font,
            **kwargs
        )


class URLInputBar(ctk.CTkFrame):
    """
    Hero URL input container featuring an auto-paste button and
    a prominent 'Fetch Info' action trigger with vector iconography.
    """

    def __init__(
        self,
        master,
        on_fetch: Optional[Callable[[], None]] = None,
        on_paste: Optional[Callable[[], None]] = None,
        placeholder: str = "Paste YouTube, TikTok, Facebook, Instagram, or media URL...",
        **kwargs
    ):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)

        self.on_fetch = on_fetch
        self.on_paste = on_paste

        self.grid_columnconfigure(0, weight=1)

        # Input row container
        input_row = ctk.CTkFrame(self, fg_color="transparent")
        input_row.grid(row=0, column=0, sticky="ew")
        input_row.grid_columnconfigure(0, weight=1)

        self.entry = ModernEntry(
            input_row,
            placeholder_text=placeholder,
            height=42,
            corner_radius=Theme.CORNER_RADIUS_SM,
        )
        self.entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.entry.bind("<Return>", lambda event: self._handle_fetch())

        self.paste_btn = SecondaryButton(
            input_row,
            text=" Paste",
            icon_name="paste",
            width=85,
            height=42,
            command=self._handle_paste,
        )
        self.paste_btn.grid(row=0, column=1, padx=(0, 6))

        self.fetch_btn = CrimsonButton(
            input_row,
            text=" Inspect Media",
            icon_name="search",
            width=135,
            height=42,
            command=self._handle_fetch,
        )
        self.fetch_btn.grid(row=0, column=2)

        # Inline feedback label
        self.feedback_label = ctk.CTkLabel(
            self,
            text="",
            font=Fonts.caption(11),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        )
        self.feedback_label.grid(row=1, column=0, padx=4, pady=(4, 0), sticky="w")

    def _handle_fetch(self):
        if self.on_fetch:
            self.on_fetch()

    def _handle_paste(self):
        if self.on_paste:
            self.on_paste()
        else:
            try:
                text = self.clipboard_get().strip()
                if text:
                    self.entry.delete(0, tk.END)
                    self.entry.insert(0, text)
                    if self.on_fetch and (text.lower().startswith("http://") or text.lower().startswith("https://")):
                        self.on_fetch()
            except Exception:
                pass

    def get_url(self) -> str:
        return self.entry.get().strip()

    def set_url(self, url: str):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, url)

    def set_feedback(self, text: str, color=Theme.TEXT_SECONDARY):
        self.feedback_label.configure(text=text, text_color=color)

    def set_loading(self, loading: bool):
        if loading:
            self.fetch_btn.configure(text=" Inspecting...", state="disabled")
        else:
            self.fetch_btn.configure(text=" Inspect Media", state="normal")
