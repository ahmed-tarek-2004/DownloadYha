"""
settings_view.py - Settings & System Diagnostics Workspace View for Downloadyha

Features:
- Appearance & Theme Mode selection (Light, Dark, System Default).
- Default download directory selection with native directory picker.
- System Diagnostics & Helper binary versions (FFmpeg, Deno, yt-dlp).
- About & Author information with high-DPI vector icons.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional
import os
import sys
import tkinter as tk
import customtkinter as ctk

from ..theme.palette import Theme, Fonts
from ..components.cards import ModernCard, GlassCard
from ..components.buttons import CrimsonButton, SecondaryButton
from ..components.inputs import ModernEntry
from ..components.icons import IconManager

if TYPE_CHECKING:
    from ..app import DownloadyhaGUI


class SettingsView(ctk.CTkFrame):
    """
    Settings & System Diagnostics workspace view.
    """

    def __init__(self, master, app: DownloadyhaGUI, **kwargs):
        kwargs.setdefault("fg_color", Theme.BG_LIGHT)
        super().__init__(master, **kwargs)
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()

    def _build_ui(self):
        """Construct the Settings layout."""
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.grid(row=0, column=0, padx=20, pady=16, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        # 1. Appearance & Theme Card
        theme_card = GlassCard(self.scroll)
        theme_card.grid(row=0, column=0, padx=4, pady=(0, 12), sticky="ew")
        theme_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            theme_card,
            text=" Appearance & Theme",
            image=IconManager.get("sun", size=(16, 16), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.section(14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(14, 4), sticky="w")

        ctk.CTkLabel(
            theme_card,
            text="Choose between Frost Porcelain (Light), Obsidian Zinc (Dark), or System Default.",
            font=Fonts.caption(11),
            text_color=Theme.TEXT_SECONDARY,
        ).grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        theme_select_frame = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_select_frame.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")
        theme_select_frame.grid_columnconfigure(0, weight=1)

        saved_mode = self.app.config.get("appearance_mode", self.app.config.get("theme", "light"))
        settings_mode_val_map = {
            "light": "Light Mode",
            "dark": "Dark Mode",
            "system": "System Default",
            "☀️ Light Mode": "Light Mode",
            "🌙 Dark Mode": "Dark Mode",
            "💻 System Default": "System Default",
        }
        settings_initial_val = settings_mode_val_map.get(saved_mode, "Light Mode")

        self.settings_theme_var = tk.StringVar(value=settings_initial_val)
        self.settings_theme_segmented = ctk.CTkSegmentedButton(
            theme_select_frame,
            values=["Light Mode", "Dark Mode", "System Default"],
            variable=self.settings_theme_var,
            font=Fonts.body_bold(12),
            height=36,
            selected_color=Theme.CRIMSON_PRIMARY,
            selected_hover_color=Theme.CRIMSON_HOVER,
            unselected_color=Theme.BTN_SUBTLE_BG,
            unselected_hover_color=Theme.BTN_SUBTLE_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            command=self.app._on_settings_theme_change,
        )
        self.settings_theme_segmented.pack(fill="x")

        # 2. Download Preferences Card
        general_card = GlassCard(self.scroll)
        general_card.grid(row=1, column=0, padx=4, pady=(0, 12), sticky="ew")
        general_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            general_card,
            text=" Download Preferences",
            image=IconManager.get("folder", size=(16, 16), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.section(14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        ctk.CTkLabel(
            general_card,
            text="Default Download Directory:",
            font=Fonts.caption(11, weight="bold"),
            text_color=Theme.TEXT_SECONDARY,
        ).grid(row=1, column=0, padx=16, pady=(0, 4), sticky="w")

        path_frame = ctk.CTkFrame(general_card, fg_color="transparent")
        path_frame.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")
        path_frame.grid_columnconfigure(0, weight=1)

        self.settings_path_entry = ModernEntry(
            path_frame,
            height=38,
        )
        self.settings_path_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        browse_btn = SecondaryButton(
            path_frame,
            text=" Browse",
            icon_name="folder",
            icon_size=(14, 14),
            width=95,
            height=38,
            command=self.app._browse_settings_path,
        )
        browse_btn.grid(row=0, column=1)

        # 3. System Diagnostics & Installed Versions Card
        diag_card = GlassCard(self.scroll)
        diag_card.grid(row=2, column=0, padx=4, pady=(0, 12), sticky="ew")
        diag_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            diag_card,
            text=" System & Dependency Diagnostics",
            image=IconManager.get("shield_check", size=(16, 16), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.section(14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        self.diag_label = ctk.CTkLabel(
            diag_card,
            text="",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=Theme.TEXT_SECONDARY,
            justify="left",
            anchor="w",
        )
        self.diag_label.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="w")

        # 4. About & Ownership Card
        about_card = GlassCard(self.scroll)
        about_card.grid(row=3, column=0, padx=4, pady=(0, 12), sticky="ew")
        about_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            about_card,
            text=" About & Ownership",
            image=IconManager.get("sparkles", size=(16, 16), color_light=Theme.TEXT_PRIMARY[0], color_dark=Theme.TEXT_PRIMARY[1]),
            compound="left",
            font=Fonts.section(14, weight="bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        self.about_label = ctk.CTkLabel(
            about_card,
            text="",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=Theme.TEXT_SECONDARY,
            justify="left",
            anchor="w",
        )
        self.about_label.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="w")

        # 5. Save Settings Button
        self.save_settings_btn = CrimsonButton(
            self.scroll,
            text=" Save Preferences",
            icon_name="check",
            icon_size=(16, 16),
            height=42,
            font=Fonts.section(13, weight="bold"),
            command=self.app._save_settings,
        )
        self.save_settings_btn.grid(row=4, column=0, padx=4, pady=(4, 16), sticky="ew")

        # Inline confirmation label
        self.settings_feedback_label = ctk.CTkLabel(
            self.scroll,
            text="",
            font=Fonts.body_bold(11),
            text_color=Theme.SUCCESS_GREEN,
        )
        self.settings_feedback_label.grid(row=5, column=0, pady=(0, 8))
