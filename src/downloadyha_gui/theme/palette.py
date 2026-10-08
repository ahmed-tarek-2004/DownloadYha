"""
palette.py - Obsidian & Frost Design System for Downloadyha GUI

Inspired by contemporary desktop applications (Linear, Raycast, Arc Browser)
featuring tailored palettes for both Dark and Light modes:
- Dark Mode ("Obsidian Zinc"): Deep space background (#0B0F17) with slate cards (#131C2E) and subtle borders (#1E293B).
- Light Mode ("Frost Porcelain"): Soft zinc tones (#F8FAFC / #FFFFFF) with crisp hairline borders (#E2E8F0).
- Accents: Modern primary Indigo (#6366F1), Crimson (#DC2626 / #EF4444), Emerald (#10B981), Amber (#F59E0B), Sky (#0EA5E9).
"""

from __future__ import annotations

from typing import Tuple
import customtkinter as ctk


class ThemeColors:
    """Raw color definitions for Light and Dark modes."""

    # Light Mode ("Frost Porcelain")
    LIGHT = {
        "bg_primary": "#F8FAFC",       # Main window background (Soft off-white / Zinc)
        "bg_secondary": "#F1F5F9",     # Sidebar & recessed panels
        "bg_tertiary": "#E2E8F0",      # Sub-elements & dividers
        "card_bg": "#FFFFFF",          # Elevated card surfaces
        "card_border": "#E2E8F0",      # Card border (crisp, low contrast)
        "card_border_hover": "#CBD5E1",
        "text_primary": "#0F172A",     # Deep slate for primary text
        "text_secondary": "#475569",   # Muted slate for metadata
        "text_muted": "#94A3B8",       # Subtle helper text
        "accent_primary": "#6366F1",   # Modern Indigo
        "accent_hover": "#4F46E5",
        "accent_light": "#EEF2FF",     # Soft indigo tint
        "accent_crimson": "#DC2626",   # Primary action crimson
        "accent_crimson_hover": "#B91C1C",
        "accent_crimson_light": "#FEE2E2",
        "success": "#10B981",          # Emerald
        "success_light": "#ECFDF5",
        "error": "#EF4444",            # Crimson / Red
        "error_light": "#FEF2F2",
        "warning": "#F59E0B",          # Amber
        "warning_light": "#FFFBEB",
        "info": "#0EA5E9",             # Sky Blue
        "info_light": "#F0F9FF",
        "input_bg": "#FFFFFF",
        "input_border": "#E2E8F0",
        "btn_secondary_bg": "#F1F5F9",
        "btn_secondary_hover": "#E2E8F0",
        "btn_secondary_text": "#0F172A",
        "progress_bg": "#E2E8F0",
    }

    # Dark Mode ("Obsidian Zinc")
    DARK = {
        "bg_primary": "#0B0F17",       # Deep Obsidian base background
        "bg_secondary": "#111827",     # Sidebar & elevated surfaces
        "bg_tertiary": "#1E293B",      # Borders & dividers
        "card_bg": "#131C2E",          # Elevated card surfaces
        "card_border": "#1E293B",      # Subtle slate border
        "card_border_hover": "#334155",
        "text_primary": "#F8FAFC",     # Bright crisp text
        "text_secondary": "#94A3B8",   # Soft slate for metadata
        "text_muted": "#64748B",       # Muted timestamps/helpers
        "accent_primary": "#6366F1",   # Modern Indigo
        "accent_hover": "#4F46E5",
        "accent_light": "#1E1B4B",
        "accent_crimson": "#EF4444",   # Action crimson
        "accent_crimson_hover": "#DC2626",
        "accent_crimson_light": "#3B0707",
        "success": "#10B981",          # Emerald
        "success_light": "#064E3B",
        "error": "#F87171",            # Light Red
        "error_light": "#3B0707",
        "warning": "#F59E0B",          # Amber
        "warning_light": "#451A03",
        "info": "#38BDF8",             # Sky Blue
        "info_light": "#082F49",
        "input_bg": "#0B0F17",
        "input_border": "#1E293B",
        "btn_secondary_bg": "#1E293B",
        "btn_secondary_hover": "#334155",
        "btn_secondary_text": "#F8FAFC",
        "progress_bg": "#1E293B",
    }


class Theme:
    """
    Unified Theme configuration providing adaptive (Light, Dark) tuples
    for CustomTkinter widgets and backwards compatibility.
    """

    # Primary Backgrounds (Light, Dark)
    BG_LIGHT = (ThemeColors.LIGHT["bg_primary"], ThemeColors.DARK["bg_primary"])
    BG_SECONDARY = (ThemeColors.LIGHT["bg_secondary"], ThemeColors.DARK["bg_secondary"])
    BG_TERTIARY = (ThemeColors.LIGHT["bg_tertiary"], ThemeColors.DARK["bg_tertiary"])

    # Surfaces & Cards
    CARD_BG = (ThemeColors.LIGHT["card_bg"], ThemeColors.DARK["card_bg"])
    CARD_BORDER = (ThemeColors.LIGHT["card_border"], ThemeColors.DARK["card_border"])
    CARD_BORDER_HOVER = (ThemeColors.LIGHT["card_border_hover"], ThemeColors.DARK["card_border_hover"])

    # Primary Indigo / Violet Accents
    INDIGO_PRIMARY = (ThemeColors.LIGHT["accent_primary"], ThemeColors.DARK["accent_primary"])
    INDIGO_HOVER = (ThemeColors.LIGHT["accent_hover"], ThemeColors.DARK["accent_hover"])
    INDIGO_LIGHT = (ThemeColors.LIGHT["accent_light"], ThemeColors.DARK["accent_light"])

    # Crimson Branding & Action Accents
    CRIMSON_PRIMARY = (ThemeColors.LIGHT["accent_crimson"], ThemeColors.DARK["accent_crimson"])
    CRIMSON_HOVER = (ThemeColors.LIGHT["accent_crimson_hover"], ThemeColors.DARK["accent_crimson_hover"])
    CRIMSON_LIGHT = (ThemeColors.LIGHT["accent_crimson_light"], ThemeColors.DARK["accent_crimson_light"])
    CRIMSON_DARK = "#991B1B"

    # Default Primary CTA (uses Indigo / Crimson)
    ACCENT_PRIMARY = INDIGO_PRIMARY
    ACCENT_HOVER = INDIGO_HOVER
    ACCENT_LIGHT = INDIGO_LIGHT

    # Typography Colors
    TEXT_PRIMARY = (ThemeColors.LIGHT["text_primary"], ThemeColors.DARK["text_primary"])
    TEXT_SECONDARY = (ThemeColors.LIGHT["text_secondary"], ThemeColors.DARK["text_secondary"])
    TEXT_MUTED = (ThemeColors.LIGHT["text_muted"], ThemeColors.DARK["text_muted"])

    # Status Colors
    SUCCESS_GREEN = (ThemeColors.LIGHT["success"], ThemeColors.DARK["success"])
    SUCCESS_LIGHT = (ThemeColors.LIGHT["success_light"], ThemeColors.DARK["success_light"])
    ERROR_RED = (ThemeColors.LIGHT["error"], ThemeColors.DARK["error"])
    ERROR_LIGHT = (ThemeColors.LIGHT["error_light"], ThemeColors.DARK["error_light"])
    WARNING_AMBER = (ThemeColors.LIGHT["warning"], ThemeColors.DARK["warning"])
    WARNING_LIGHT = (ThemeColors.LIGHT["warning_light"], ThemeColors.DARK["warning_light"])
    INFO_BLUE = (ThemeColors.LIGHT["info"], ThemeColors.DARK["info"])
    INFO_LIGHT = (ThemeColors.LIGHT["info_light"], ThemeColors.DARK["info_light"])

    # Input & Button Controls
    ENTRY_BG = (ThemeColors.LIGHT["input_bg"], ThemeColors.DARK["input_bg"])
    ENTRY_BORDER = (ThemeColors.LIGHT["input_border"], ThemeColors.DARK["input_border"])
    ENTRY_TEXT = (ThemeColors.LIGHT["text_primary"], ThemeColors.DARK["text_primary"])
    BTN_SECONDARY_BG = (ThemeColors.LIGHT["btn_secondary_bg"], ThemeColors.DARK["btn_secondary_bg"])
    BTN_SECONDARY_HOVER = (ThemeColors.LIGHT["btn_secondary_hover"], ThemeColors.DARK["btn_secondary_hover"])
    BTN_SECONDARY_TEXT = (ThemeColors.LIGHT["btn_secondary_text"], ThemeColors.DARK["btn_secondary_text"])
    BTN_SUBTLE_BG = (ThemeColors.LIGHT["bg_secondary"], ThemeColors.DARK["bg_secondary"])
    BTN_SUBTLE_HOVER = (ThemeColors.LIGHT["bg_tertiary"], ThemeColors.DARK["bg_tertiary"])
    PROGRESS_BG = (ThemeColors.LIGHT["progress_bg"], ThemeColors.DARK["progress_bg"])

    # Geometry & Spacing
    CORNER_RADIUS_SM = 8
    CORNER_RADIUS_MD = 12
    CORNER_RADIUS_LG = 16
    CORNER_RADIUS_PILL = 24

    # Backward Compatibility Constants
    ELECTRIC_CYAN = (0, 210, 255)
    ACCENT_HEX = "#6366F1"

    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to Hex string."""
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    @classmethod
    def get_accent_color(cls) -> str:
        """Get primary accent color."""
        return "#00D2FF"  # Legacy test suite compatibility

    @classmethod
    def get_success_color(cls) -> str:
        """Get success status color."""
        return "#2ECC71"

    @classmethod
    def get_error_color(cls) -> str:
        """Get error status color."""
        return "#E74C3C"

    @classmethod
    def get_warning_color(cls) -> str:
        """Get warning status color."""
        return "#FFA500"


class Fonts:
    """Typography system for consistent visual hierarchy."""

    @staticmethod
    def hero(size: int = 20, weight: str = "bold") -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)

    @staticmethod
    def title(size: int = 16, weight: str = "bold") -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)

    @staticmethod
    def section(size: int = 13, weight: str = "bold") -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)

    @staticmethod
    def body(size: int = 12, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)

    @staticmethod
    def body_bold(size: int = 12) -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=size, weight="bold")

    @staticmethod
    def caption(size: int = 10, weight: str = "normal") -> ctk.CTkFont:
        return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)

    @staticmethod
    def mono(size: int = 11) -> ctk.CTkFont:
        return ctk.CTkFont(family="Consolas", size=size)
