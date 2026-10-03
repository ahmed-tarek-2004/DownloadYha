"""
test_downloadyha_gui.py - Unit tests for the Modern CustomTkinter Desktop GUI (downloadyha_gui).

Tests metadata parsing, quality label formatting, video/audio quality parsing,
dynamic quality dropdown population, download history manager, and theme utilities.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from downloadyha_gui.app import (
    AUDIO_QUALITIES,
    DEFAULT_VIDEO_QUALITIES,
    DownloadHistory,
    DownloadyhaGUI,
    ModernButton,
    Theme,
    format_height_label,
)


class TestDownloadyhaGUIHelpers(unittest.TestCase):
    """Test helper and utility functions in downloadyha_gui."""

    def test_format_height_label(self):
        """Test formatting video height resolutions into user-friendly labels."""
        self.assertEqual(format_height_label(2160), "2160p (4K UHD)")
        self.assertEqual(format_height_label(1440), "1440p (2K QHD)")
        self.assertEqual(format_height_label(1080), "1080p (Full HD)")
        self.assertEqual(format_height_label(720), "720p (HD)")
        self.assertEqual(format_height_label(480), "480p (SD)")
        self.assertEqual(format_height_label(360), "360p (Low)")
        self.assertEqual(format_height_label(240), "240p")
        self.assertEqual(format_height_label(144), "144p")

    def test_theme_color_conversions(self):
        """Test theme RGB to Hex conversions and color definitions."""
        cyan_hex = Theme.rgb_to_hex(Theme.ELECTRIC_CYAN)
        self.assertTrue(cyan_hex.startswith("#"))
        self.assertEqual(cyan_hex.upper(), "#00D2FF")

        self.assertEqual(Theme.get_accent_color().upper(), "#00D2FF")
        self.assertEqual(Theme.get_success_color().upper(), "#2ECC71")
        self.assertEqual(Theme.get_error_color().upper(), "#E74C3C")
        self.assertEqual(Theme.get_warning_color().upper(), "#FFA500")

    def test_download_history(self):
        """Test download history manager."""
        history = DownloadHistory(max_items=3)
        self.assertEqual(len(history.get_all()), 0)

        history.add_item("https://youtube.com/watch?v=1", "Video 1", "completed", "/path/1")
        history.add_item("https://youtube.com/watch?v=2", "Video 2", "failed", "/path/2")
        history.add_item("https://youtube.com/watch?v=3", "Video 3", "completed", "/path/3")

        items = history.get_all()
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["title"], "Video 3")  # Newest first

        # Exceed max items
        history.add_item("https://youtube.com/watch?v=4", "Video 4", "completed", "/path/4")
        self.assertEqual(len(history.get_all()), 3)
        self.assertEqual(history.get_all()[0]["title"], "Video 4")

        # Clear history
        history.clear()
        self.assertEqual(len(history.get_all()), 0)

    def test_modern_button_callbacks(self):
        """Test ModernButton initialization and internal Tkinter leave/enter callbacks."""
        try:
            import customtkinter as ctk
            root = ctk.CTk()
            btn = ModernButton(root, text="Test Button")
            # CTkButton internal calls _on_leave() without arguments on click/release
            btn._on_leave()
            btn._on_enter()
            root.destroy()
        except Exception as e:
            # If running in headless environment without display, skip GUI creation error
            if "no display name" not in str(e).lower():
                raise e


class TestDownloadyhaGUILogic(unittest.TestCase):
    """Test GUI logic with mocked CustomTkinter application instance."""

    def setUp(self):
        self.gui = DownloadyhaGUI.__new__(DownloadyhaGUI)
        self.gui.media_info = None
        self.gui.last_fetched_url = ""
        self.gui.is_fetching_info = False
        self.gui.available_video_qualities = []
        self.gui.media_type_var = MagicMock()
        self.gui.quality_var = MagicMock()
        self.gui.quality_menu = MagicMock()
        self.gui.media_badge = MagicMock()
        self.gui.media_channel_label = MagicMock()
        self.gui.media_title_label = MagicMock()
        self.gui.media_meta_label = MagicMock()
        self.gui.status_label = MagicMock()
        self.gui.status_indicator = MagicMock()
        self.gui.fetch_btn = MagicMock()

    def test_parse_video_quality(self):
        """Test parsing quality dropdown string to height integer."""
        self.assertEqual(self.gui._parse_video_quality("Best Available (Maximum Quality)"), 0)
        self.assertEqual(self.gui._parse_video_quality("2160p (4K UHD)"), 2160)
        self.assertEqual(self.gui._parse_video_quality("1440p (2K QHD)"), 1440)
        self.assertEqual(self.gui._parse_video_quality("1080p (Full HD)"), 1080)
        self.assertEqual(self.gui._parse_video_quality("720p (HD)"), 720)
        self.assertEqual(self.gui._parse_video_quality("480p (SD)"), 480)
        self.assertEqual(self.gui._parse_video_quality("360p (Low)"), 360)

    def test_parse_audio_quality(self):
        """Test parsing audio quality string to bitrate parameter."""
        self.assertEqual(self.gui._parse_audio_quality("Best Quality (VBR ~256-320 kbps)"), "0")
        self.assertEqual(self.gui._parse_audio_quality("320 kbps (High Quality)"), "320")
        self.assertEqual(self.gui._parse_audio_quality("192 kbps (Standard Quality)"), "192")
        self.assertEqual(self.gui._parse_audio_quality("128 kbps (Compact Size)"), "128")

    def test_update_quality_options_audio(self):
        """Test dropdown population when audio mode is selected."""
        self.gui.media_type_var.get.return_value = "🎵 Audio"
        self.gui._update_quality_options()
        self.gui.quality_menu.configure.assert_called_with(values=AUDIO_QUALITIES)

    def test_update_quality_options_video_with_extracted_qualities(self):
        """Test dropdown population when video mode is active with extracted available resolutions."""
        self.gui.media_type_var.get.return_value = "🎥 Video"
        self.gui.media_info = {"title": "Test Video"}
        self.gui.available_video_qualities = [1080, 720, 360]
        self.gui._update_quality_options()

        expected_values = [
            "Best Available (Maximum Quality)",
            "1080p (Full HD)",
            "720p (HD)",
            "360p (Low)",
        ]
        self.gui.quality_menu.configure.assert_called_with(values=expected_values)

    def test_on_media_info_fetched_single_video(self):
        """Test on_media_info_fetched handler for a single video."""
        sample_info = {
            "title": "Quantum Physics in 10 Minutes",
            "uploader": "Science Channel",
            "duration": 600,
            "view_count": 1500000,
            "formats": [
                {"height": 1080, "vcodec": "avc1"},
                {"height": 720, "vcodec": "avc1"},
                {"height": 480, "vcodec": "avc1"},
            ]
        }

        self.gui.media_type_var.get.return_value = "🎥 Video"
        self.gui._on_media_info_fetched(sample_info, "https://youtube.com/watch?v=physics123")

        self.assertEqual(self.gui.media_info, sample_info)
        self.assertEqual(self.gui.last_fetched_url, "https://youtube.com/watch?v=physics123")
        self.assertEqual(self.gui.available_video_qualities, [1080, 720, 480])
        self.gui.media_badge.configure.assert_called()
        self.gui.media_title_label.configure.assert_called_with(text="🎬 Quantum Physics in 10 Minutes")

    def test_on_media_info_fetched_playlist(self):
        """Test on_media_info_fetched handler for a playlist."""
        sample_playlist = {
            "_type": "playlist",
            "title": "Awesome Music Playlist",
            "uploader": "DJ Awesome",
            "entries": [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        }

        self.gui.media_type_var.get.return_value = "🎥 Video"
        self.gui._on_media_info_fetched(sample_playlist, "https://youtube.com/playlist?list=PLmusic")

        self.assertEqual(self.gui.media_info, sample_playlist)
        self.gui.media_badge.configure.assert_called()
        self.gui.media_title_label.configure.assert_called_with(text="📑 Awesome Music Playlist")


class TestDownloadyhaGUILauncher(unittest.TestCase):
    """Test launcher dependency checking."""

    def test_check_dependencies_success(self):
        with patch.dict("sys.modules", {"tkinter": MagicMock(), "customtkinter": MagicMock(), "yt_dlp": MagicMock()}):
            from downloadyha_gui import launcher
            self.assertTrue(launcher.check_dependencies())

    def test_check_dependencies_missing_tkinter(self):
        with patch.dict("sys.modules", {"tkinter": None}):
            from downloadyha_gui import launcher
            self.assertFalse(launcher.check_dependencies())

    def test_check_dependencies_missing_customtkinter(self):
        with patch.dict("sys.modules", {"tkinter": MagicMock(), "customtkinter": None, "yt_dlp": MagicMock()}):
            from downloadyha_gui import launcher
            self.assertFalse(launcher.check_dependencies())


if __name__ == "__main__":
    unittest.main()

