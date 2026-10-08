"""
thumbnail.py - Asynchronous Thumbnail Downloader & Image Cache for Downloadyha GUI

Handles:
- Downloading video/playlist thumbnails in background threads without UI blocking.
- Resizing & applying smooth rounded corner masks using Pillow (PIL).
- In-memory LRU caching to prevent redundant network fetches.
"""

from __future__ import annotations

import io
import threading
import urllib.request
from typing import Callable, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageTk
import customtkinter as ctk


class ThumbnailManager:
    """Thread-safe image downloader and Pillow cache."""

    _cache: Dict[str, ctk.CTkImage] = {}
    _lock = threading.Lock()

    @classmethod
    def create_placeholder(
        cls,
        width: int = 160,
        height: int = 90,
        corner_radius: int = 8,
        bg_color: str = "#1E293B",
        text: str = "🎬 Media",
    ) -> ctk.CTkImage:
        """Generate a clean placeholder image."""
        img = Image.new("RGBA", (width, height), color=(30, 41, 59, 255))
        return ctk.CTkImage(light_image=img, dark_image=img, size=(width, height))

    @classmethod
    def apply_rounded_corners(cls, image: Image.Image, radius: int = 10) -> Image.Image:
        """Apply anti-aliased rounded corners to a PIL Image."""
        try:
            image = image.convert("RGBA")
            mask = Image.new("L", image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle([(0, 0), image.size], radius=radius, fill=255)
            image.putalpha(mask)
            return image
        except Exception:
            return image

    @classmethod
    def fetch_async(
        cls,
        url: str,
        size: Tuple[int, int] = (160, 90),
        corner_radius: int = 8,
        callback: Optional[Callable[[ctk.CTkImage], None]] = None,
    ) -> None:
        """
        Asynchronously download, resize, and round a thumbnail image.
        Invokes callback with the CTkImage once ready.
        """
        if not url:
            return

        cache_key = f"{url}_{size[0]}x{size[1]}_{corner_radius}"
        with cls._lock:
            if cache_key in cls._cache:
                if callback:
                    callback(cls._cache[cache_key])
                return

        def worker():
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    img_data = response.read()

                pil_img = Image.open(io.BytesIO(img_data))
                pil_img = pil_img.resize(size, Image.Resampling.LANCZOS)
                pil_img = cls.apply_rounded_corners(pil_img, radius=corner_radius)

                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)

                with cls._lock:
                    cls._cache[cache_key] = ctk_img

                if callback:
                    callback(ctk_img)

            except Exception:
                # Silently ignore failed thumbnail loads
                pass

        threading.Thread(target=worker, daemon=True).start()
