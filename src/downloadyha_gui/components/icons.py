"""
icons.py - High-DPI Vector-Rendered Icon Engine for Downloadyha GUI

Renders razor-sharp, geometric vector icons (Feather / Lucide / SF Symbols style)
using Pillow supersampling (4x scale with Lanczos filtering) and caches CTkImage objects
dynamically for Light and Dark modes.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple
from PIL import Image, ImageDraw
import customtkinter as ctk

from ..theme.palette import ThemeColors


class IconManager:
    """
    Renders and caches modern, anti-aliased vector icons.
    """

    _cache: Dict[str, ctk.CTkImage] = {}

    @classmethod
    def get(
        cls,
        name: str,
        size: Tuple[int, int] = (18, 18),
        color_light: Optional[str] = None,
        color_dark: Optional[str] = None,
        stroke_width: int = 2,
    ) -> ctk.CTkImage:
        """
        Get or generate a CTkImage containing light and dark mode versions of an icon.
        """
        c_light = color_light or ThemeColors.LIGHT["text_primary"]
        c_dark = color_dark or ThemeColors.DARK["text_primary"]
        key = f"{name}_{size[0]}x{size[1]}_{c_light}_{c_dark}_{stroke_width}"

        if key in cls._cache:
            return cls._cache[key]

        img_light = cls._render_icon(name, size, c_light, stroke_width)
        img_dark = cls._render_icon(name, size, c_dark, stroke_width)

        ctk_img = ctk.CTkImage(
            light_image=img_light,
            dark_image=img_dark,
            size=size,
        )
        cls._cache[key] = ctk_img
        return ctk_img

    @classmethod
    def _render_icon(
        cls,
        name: str,
        size: Tuple[int, int],
        color: str,
        stroke_width: int,
    ) -> Image.Image:
        """
        Render a single icon at 4x supersampling resolution and downsample with Lanczos.
        """
        scale = 4
        w, h = size[0] * scale, size[1] * scale
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        sw = stroke_width * scale

        # Standard bounding box with margins: 10% on each side
        pad_x = w * 0.12
        pad_y = h * 0.12
        cx, cy = w / 2, h / 2

        if name == "download":
            # Tray line at bottom
            draw.line([(pad_x, h - pad_y), (w - pad_x, h - pad_y)], fill=color, width=sw)
            # Arrow stem
            draw.line([(cx, pad_y), (cx, h - pad_y - sw * 2)], fill=color, width=sw)
            # Arrow head
            arrow_w = w * 0.28
            arrow_h = h * 0.28
            tip_y = h - pad_y - sw * 2
            draw.line([(cx - arrow_w, tip_y - arrow_h), (cx, tip_y)], fill=color, width=sw)
            draw.line([(cx + arrow_w, tip_y - arrow_h), (cx, tip_y)], fill=color, width=sw)

        elif name == "playlist":
            # 3 horizontal stacked lines with a small play triangle on top or left
            line_spacing = (h - 2 * pad_y) / 3
            # Top line
            draw.line([(pad_x + w * 0.25, pad_y + line_spacing * 0.5), (w - pad_x, pad_y + line_spacing * 0.5)], fill=color, width=sw)
            # Middle line
            draw.line([(pad_x + w * 0.25, pad_y + line_spacing * 1.5), (w - pad_x, pad_y + line_spacing * 1.5)], fill=color, width=sw)
            # Bottom line
            draw.line([(pad_x, pad_y + line_spacing * 2.5), (w - pad_x, pad_y + line_spacing * 2.5)], fill=color, width=sw)
            # Play indicator in top-left
            play_x = pad_x
            play_y = pad_y + line_spacing * 0.1
            play_size = w * 0.22
            draw.polygon([
                (play_x, play_y),
                (play_x + play_size, play_y + play_size * 0.7),
                (play_x, play_y + play_size * 1.4),
            ], fill=color)

        elif name in ("queue", "history"):
            # Circular clock outline + hands
            draw.ellipse([pad_x, pad_y, w - pad_x, h - pad_y], outline=color, width=sw)
            # Center to top (minute)
            draw.line([(cx, cy), (cx, pad_y + h * 0.18)], fill=color, width=sw)
            # Center to right-down (hour)
            draw.line([(cx, cy), (cx + w * 0.2, cy + h * 0.1)], fill=color, width=sw)

        elif name in ("settings", "cog"):
            # Gear center circle
            r_inner = w * 0.18
            draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], outline=color, width=sw)
            # 6 or 8 teeth around perimeter
            num_teeth = 6
            r_outer = (w - 2 * pad_x) / 2
            for i in range(num_teeth):
                angle = i * (2 * math.pi / num_teeth)
                x1 = cx + (r_inner + sw) * math.cos(angle)
                y1 = cy + (r_inner + sw) * math.sin(angle)
                x2 = cx + r_outer * math.cos(angle)
                y2 = cy + r_outer * math.sin(angle)
                draw.line([(x1, y1), (x2, y2)], fill=color, width=int(sw * 1.3))

        elif name == "video":
            # Rounded rectangle monitor/camera + play triangle
            rect_pad_y = pad_y + h * 0.05
            draw.rounded_rectangle(
                [pad_x, rect_pad_y, w - pad_x, h - rect_pad_y],
                radius=int(scale * 3),
                outline=color,
                width=sw,
            )
            # Center play triangle
            pt_w = w * 0.18
            pt_h = h * 0.22
            draw.polygon([
                (cx - pt_w * 0.5, cy - pt_h),
                (cx + pt_w * 0.7, cy),
                (cx - pt_w * 0.5, cy + pt_h),
            ], fill=color)

        elif name in ("audio", "music"):
            # Sleek sound waveform bars (5 vertical bars)
            bar_count = 5
            bar_w = sw
            total_span = w - 2 * pad_x
            spacing = total_span / (bar_count - 1)
            heights = [0.4, 0.75, 1.0, 0.65, 0.35]
            max_h = h - 2 * pad_y
            for idx, rel_h in enumerate(heights):
                bx = pad_x + idx * spacing
                bh = max_h * rel_h
                draw.line([(bx, cy - bh / 2), (bx, cy + bh / 2)], fill=color, width=int(bar_w))

        elif name in ("subtitles", "cc"):
            # Rounded box with "CC" or horizontal lines
            draw.rounded_rectangle(
                [pad_x, pad_y + h * 0.05, w - pad_x, h - pad_y - h * 0.05],
                radius=int(scale * 3),
                outline=color,
                width=sw,
            )
            # Two CC-style arcs or lines
            line_y1 = cy - h * 0.1
            line_y2 = cy + h * 0.1
            draw.line([(pad_x + w * 0.18, line_y1), (w - pad_x - w * 0.18, line_y1)], fill=color, width=sw)
            draw.line([(pad_x + w * 0.18, line_y2), (w - pad_x - w * 0.35, line_y2)], fill=color, width=sw)

        elif name in ("scissors", "clip"):
            # Two intersecting diagonal lines with circles at bottom
            r_finger = w * 0.12
            # Left blade: from bottom-left loop to top-right
            draw.ellipse([pad_x, h - pad_y - 2 * r_finger, pad_x + 2 * r_finger, h - pad_y], outline=color, width=sw)
            draw.ellipse([w - pad_x - 2 * r_finger, h - pad_y - 2 * r_finger, w - pad_x, h - pad_y], outline=color, width=sw)
            draw.line([(pad_x + 2 * r_finger, h - pad_y - r_finger), (w - pad_x, pad_y)], fill=color, width=sw)
            draw.line([(w - pad_x - 2 * r_finger, h - pad_y - r_finger), (pad_x, pad_y)], fill=color, width=sw)
            # Center pivot
            draw.ellipse([cx - sw, cy - sw, cx + sw, cy + sw], fill=color)

        elif name == "search":
            # Magnifying glass circle + diagonal handle
            r_glass = w * 0.28
            cg_x = pad_x + r_glass
            cg_y = pad_y + r_glass
            draw.ellipse([cg_x - r_glass, cg_y - r_glass, cg_x + r_glass, cg_y + r_glass], outline=color, width=sw)
            # Handle from circle bottom-right edge to bottom-right corner
            h_start_x = cg_x + r_glass * 0.7
            h_start_y = cg_y + r_glass * 0.7
            draw.line([(h_start_x, h_start_y), (w - pad_x, h - pad_y)], fill=color, width=int(sw * 1.2))

        elif name == "paste":
            # Clipboard outline with top clip
            clip_w = w * 0.36
            clip_h = h * 0.14
            # Board
            draw.rounded_rectangle([pad_x, pad_y + clip_h * 0.8, w - pad_x, h - pad_y], radius=int(scale * 3), outline=color, width=sw)
            # Top clip
            draw.rounded_rectangle([cx - clip_w / 2, pad_y, cx + clip_w / 2, pad_y + clip_h], radius=int(scale * 2), fill=color)

        elif name == "folder":
            # Modern tabbed folder outline
            tab_w = w * 0.35
            tab_h = h * 0.16
            draw.line([(pad_x, pad_y + tab_h), (pad_x + tab_w, pad_y + tab_h), (pad_x + tab_w + w * 0.1, pad_y + tab_h * 2), (w - pad_x, pad_y + tab_h * 2)], fill=color, width=sw)
            draw.rounded_rectangle([pad_x, pad_y + tab_h * 2, w - pad_x, h - pad_y], radius=int(scale * 3), outline=color, width=sw)

        elif name in ("refresh", "retry"):
            # Circular arrow
            r = (w - 2 * pad_x) / 2
            # Arc from 30 deg to 300 deg
            draw.arc([pad_x, pad_y, w - pad_x, h - pad_y], start=45, end=315, fill=color, width=sw)
            # Arrow head at end (top right)
            arrow_x = cx + r * math.cos(math.radians(315))
            arrow_y = cy + r * math.sin(math.radians(315))
            draw.polygon([
                (arrow_x, arrow_y),
                (arrow_x + w * 0.18, arrow_y - h * 0.05),
                (arrow_x + w * 0.05, arrow_y + h * 0.18),
            ], fill=color)

        elif name in ("close", "remove", "cross"):
            # Crisp X
            m = w * 0.18
            draw.line([(pad_x + m, pad_y + m), (w - pad_x - m, h - pad_y - m)], fill=color, width=sw)
            draw.line([(w - pad_x - m, pad_y + m), (pad_x + m, h - pad_y - m)], fill=color, width=sw)

        elif name == "check":
            # Crisp checkmark
            draw.line([(pad_x + w * 0.05, cy + h * 0.05), (cx - w * 0.05, h - pad_y - h * 0.1)], fill=color, width=sw)
            draw.line([(cx - w * 0.05, h - pad_y - h * 0.1), (w - pad_x, pad_y + h * 0.1)], fill=color, width=sw)

        elif name == "sun":
            # Center sun circle
            r_sun = w * 0.2
            draw.ellipse([cx - r_sun, cy - r_sun, cx + r_sun, cy + r_sun], fill=color)
            # 8 rays
            ray_len = w * 0.12
            for i in range(8):
                ang = i * (math.pi / 4)
                x1 = cx + (r_sun + sw) * math.cos(ang)
                y1 = cy + (r_sun + sw) * math.sin(ang)
                x2 = cx + (r_sun + sw + ray_len) * math.cos(ang)
                y2 = cy + (r_sun + sw + ray_len) * math.sin(ang)
                draw.line([(x1, y1), (x2, y2)], fill=color, width=sw)

        elif name == "moon":
            # Crescent moon
            r_moon = (w - 2 * pad_x) / 2
            # Outer circle
            draw.arc([pad_x, pad_y, w - pad_x, h - pad_y], start=45, end=270, fill=color, width=sw)
            # Inner cutout arc
            draw.arc([pad_x + w * 0.15, pad_y - h * 0.05, w - pad_x + w * 0.15, h - pad_y - h * 0.05], start=75, end=240, fill=color, width=sw)

        elif name in ("monitor", "system"):
            # Display frame + stand
            disp_h = h * 0.58
            draw.rounded_rectangle([pad_x, pad_y, w - pad_x, pad_y + disp_h], radius=int(scale * 2), outline=color, width=sw)
            # Stand stem
            draw.line([(cx, pad_y + disp_h), (cx, h - pad_y - h * 0.08)], fill=color, width=sw)
            # Stand base
            draw.line([(cx - w * 0.2, h - pad_y - h * 0.08), (cx + w * 0.2, h - pad_y - h * 0.08)], fill=color, width=sw)

        elif name in ("shield_check", "repair"):
            # Shield shape
            top_y = pad_y
            mid_y = cy + h * 0.1
            bot_y = h - pad_y
            # Outline
            draw.line([(pad_x, top_y), (w - pad_x, top_y)], fill=color, width=sw)
            draw.line([(w - pad_x, top_y), (w - pad_x, mid_y)], fill=color, width=sw)
            draw.line([(w - pad_x, mid_y), (cx, bot_y)], fill=color, width=sw)
            draw.line([(cx, bot_y), (pad_x, mid_y)], fill=color, width=sw)
            draw.line([(pad_x, mid_y), (pad_x, top_y)], fill=color, width=sw)
            # Inner checkmark
            draw.line([(cx - w * 0.18, cy), (cx - w * 0.02, cy + h * 0.15)], fill=color, width=sw)
            draw.line([(cx - w * 0.02, cy + h * 0.15), (cx + w * 0.2, cy - h * 0.12)], fill=color, width=sw)

        elif name in ("trash", "delete"):
            # Can body + lid
            lid_y = pad_y + h * 0.12
            draw.line([(pad_x, lid_y), (w - pad_x, lid_y)], fill=color, width=sw)
            # Handle on lid
            draw.line([(cx - w * 0.15, lid_y), (cx - w * 0.15, pad_y), (cx + w * 0.15, pad_y), (cx + w * 0.15, lid_y)], fill=color, width=sw)
            # Can body
            draw.line([(pad_x + w * 0.08, lid_y), (pad_x + w * 0.14, h - pad_y), (w - pad_x - w * 0.14, h - pad_y), (w - pad_x - w * 0.08, lid_y)], fill=color, width=sw)

        elif name in ("sparkles", "star", "best"):
            # 4-point sparkle star
            draw.line([(cx, pad_y), (cx, h - pad_y)], fill=color, width=sw)
            draw.line([(pad_x, cy), (w - pad_x, cy)], fill=color, width=sw)
            # Diagonal smaller flares
            m = w * 0.18
            draw.line([(cx - m, cy - m), (cx + m, cy + m)], fill=color, width=int(sw * 0.8))
            draw.line([(cx - m, cy + m), (cx + m, cy - m)], fill=color, width=int(sw * 0.8))

        elif name == "chevron_down":
            # Downward chevron
            draw.line([(pad_x, cy - h * 0.12), (cx, cy + h * 0.18)], fill=color, width=sw)
            draw.line([(cx, cy + h * 0.18), (w - pad_x, cy - h * 0.12)], fill=color, width=sw)

        elif name == "chevron_up":
            # Upward chevron
            draw.line([(pad_x, cy + h * 0.18), (cx, cy - h * 0.12)], fill=color, width=sw)
            draw.line([(cx, cy - h * 0.12), (w - pad_x, cy + h * 0.18)], fill=color, width=sw)

        elif name == "link":
            # Two interlocking chain links
            link_w = w * 0.32
            link_h = h * 0.18
            # First link (rotated 45 deg)
            draw.line([(pad_x + w * 0.1, cy), (cx, pad_y + h * 0.1)], fill=color, width=sw)
            draw.line([(cx, h - pad_y - h * 0.1), (w - pad_x - w * 0.1, cy)], fill=color, width=sw)
            draw.line([(pad_x + w * 0.25, cy + h * 0.15), (w - pad_x - w * 0.25, cy - h * 0.15)], fill=color, width=sw)

        else:
            # Default placeholder circle with dot
            draw.ellipse([pad_x, pad_y, w - pad_x, h - pad_y], outline=color, width=sw)
            draw.ellipse([cx - sw, cy - sw, cx + sw, cy + sw], fill=color)

        # Anti-aliased downsample using LANCZOS
        return canvas.resize(size, Image.Resampling.LANCZOS)
