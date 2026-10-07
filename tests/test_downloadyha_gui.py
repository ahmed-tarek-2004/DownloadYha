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
    SUBTITLE_QUALITIES,
    DownloadHistory,
    DownloadyhaGUI,
    ModernButton,
    Theme,
    format_height_label,
    format_language_option,
    get_language_name,
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

    def test_language_name_and_formatting(self):
        """Test language code resolution and option formatting."""
        self.assertEqual(get_language_name("en"), "English")
        self.assertEqual(get_language_name("ar"), "Arabic")
        self.assertEqual(get_language_name("es"), "Spanish")
        self.assertEqual(get_language_name("fr"), "French")
        self.assertEqual(get_language_name("de"), "German")
        self.assertEqual(get_language_name("ja"), "Japanese")
        self.assertEqual(get_language_name("zh-Hans"), "Chinese (Simplified)")
        self.assertEqual(get_language_name("en-US"), "English")
        self.assertEqual(get_language_name("all"), "All Available")
        self.assertEqual(get_language_name("unknown_xyz"), "UNKNOWN_XYZ")

        self.assertEqual(format_language_option("en"), "en (English)")
        self.assertEqual(format_language_option("ar"), "ar (Arabic)")
        self.assertEqual(format_language_option("es"), "es (Spanish)")
        self.assertEqual(format_language_option("all"), "all (All Available)")

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
        self.gui.tk = MagicMock()
        self.gui._w = "."
        self.gui.children = {}
        self.gui.media_info = None
        self.gui.last_fetched_url = ""
        self.gui.is_fetching_info = False
        self.gui.is_downloading = False
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
        self.gui.main_error_banner = MagicMock()
        self.gui.url_feedback_label = MagicMock()
        self.gui.start_download_btn = MagicMock()
        self.gui.cancel_download_btn = MagicMock()
        self.gui.active_status_badge = MagicMock()
        self.gui.active_item_label = MagicMock()
        self.gui.main_progress_bar = MagicMock()
        self.gui.main_percent_label = MagicMock()
        self.gui.main_speed_label = MagicMock()
        self.gui.main_eta_label = MagicMock()
        self.gui.btn_nav_queue = MagicMock()
        self.gui.download_queue = []
        self.gui.active_task = None
        self.gui.active_card = None
        self.gui.config = {"download_directory": "/tmp/downloads"}
        self.gui.transcript_toggle_var = MagicMock()
        self.gui.transcript_toggle_var.get.return_value = False
        self.gui.sub_langs_var = MagicMock()
        self.gui.auto_subs_var = MagicMock()
        self.gui.sub_format_var = MagicMock()
        self.gui.embed_subs_var = MagicMock()
        self.gui.playlist_scope_frame = None

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

    def test_parse_subtitle_format(self):
        """Test parsing subtitle quality/format string to format parameter."""
        self.assertEqual(self.gui._parse_subtitle_format("SRT (.srt)"), "srt")
        self.assertEqual(self.gui._parse_subtitle_format("VTT (.vtt)"), "vtt")
        self.assertEqual(self.gui._parse_subtitle_format("ASS (.ass)"), "ass")
        self.assertEqual(self.gui._parse_subtitle_format("LRC (.lrc)"), "lrc")
        self.assertEqual(self.gui._parse_subtitle_format(""), "srt")

    def test_update_quality_options_audio(self):
        """Test dropdown population when audio mode is selected."""
        self.gui.media_type_var.get.return_value = "🎵 Audio"
        self.gui._update_quality_options()
        self.gui.quality_menu.configure.assert_called_with(values=AUDIO_QUALITIES)

    def test_update_quality_options_subtitles(self):
        """Test dropdown population when subtitles mode is selected."""
        self.gui.media_type_var.get.return_value = "📝 Subtitles"
        self.gui._update_quality_options()
        self.gui.quality_menu.configure.assert_called_with(values=SUBTITLE_QUALITIES)

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

    def test_section_toggle_visibility(self):
        """Test section time input container shows/hides on checkbox toggle."""
        self.gui.section_toggle_var = MagicMock()
        self.gui.section_frame = MagicMock()

        # When toggle checked (True)
        self.gui.section_toggle_var.get.return_value = True
        self.gui._on_section_toggled()
        self.gui.section_frame.grid.assert_called_with(row=7, column=0, padx=10, pady=(2, 6), sticky="ew")

        # When toggle unchecked (False)
        self.gui.section_toggle_var.get.return_value = False
        self.gui._on_section_toggled()
        self.gui.section_frame.grid_forget.assert_called_once()

    @patch("downloadyha_gui.app.messagebox.showerror")
    def test_start_download_invalid_time_range(self, mock_error):
        """Test start_download prevents execution when end_time <= start_time."""
        self.gui.url_entry = MagicMock()
        self.gui.url_entry.get.return_value = "https://youtube.com/watch?v=123"
        self.gui.dest_entry = MagicMock()
        self.gui.dest_entry.get.return_value = "/tmp/downloads"
        self.gui.section_toggle_var = MagicMock()
        self.gui.section_toggle_var.get.return_value = True
        self.gui.start_time_entry = MagicMock()
        self.gui.start_time_entry.get.return_value = "03:00"
        self.gui.end_time_entry = MagicMock()
        self.gui.end_time_entry.get.return_value = "01:00"
        self.gui.download_btn = MagicMock()
        self.gui._set_ui_state = MagicMock()

        self.gui._start_download()
        mock_error.assert_called_once()
        self.assertIn("End time (01:00) must be greater than start time (03:00)", mock_error.call_args[0][1])

    @patch("downloadyha_gui.app.save_config")
    @patch("downloadyha_gui.app.ctk.set_appearance_mode")
    def test_set_theme_mode(self, mock_set_mode, mock_save):
        """Test setting theme mode updates config, appearance mode, and UI widgets."""
        self.gui.config = {"appearance_mode": "light", "theme": "light"}
        self.gui.theme_segmented = MagicMock()
        self.gui.theme_segmented.get.return_value = "☀️ Light"
        self.gui.settings_theme_segmented = MagicMock()
        self.gui.settings_theme_segmented.get.return_value = "☀️ Light Mode"

        # Switch to dark mode
        self.gui.set_theme_mode("dark")
        mock_set_mode.assert_called_with("dark")
        self.assertEqual(self.gui.config["appearance_mode"], "dark")
        self.assertEqual(self.gui.config["theme"], "dark")
        mock_save.assert_called_with(self.gui.config)
        self.gui.theme_segmented.set.assert_called_with("🌙 Dark")
        self.gui.settings_theme_segmented.set.assert_called_with("🌙 Dark Mode")

        # Switch to system mode
        self.gui.set_theme_mode("system")
        mock_set_mode.assert_called_with("system")
        self.assertEqual(self.gui.config["appearance_mode"], "system")
        self.gui.theme_segmented.set.assert_called_with("💻 Auto")
        self.gui.settings_theme_segmented.set.assert_called_with("💻 System Default")

    @patch.object(DownloadyhaGUI, "set_theme_mode")
    def test_theme_event_callbacks(self, mock_set_theme):
        """Test segmented button event handlers map correctly to theme modes."""
        # Sidebar callback
        self.gui._on_theme_segmented_change("🌙 Dark")
        mock_set_theme.assert_called_with("dark")

        self.gui._on_theme_segmented_change("💻 Auto")
        mock_set_theme.assert_called_with("system")

        self.gui._on_theme_segmented_change("☀️ Light")
        mock_set_theme.assert_called_with("light")

        # Settings panel callback
        self.gui._on_settings_theme_change("🌙 Dark Mode")
        mock_set_theme.assert_called_with("dark")

        self.gui._on_settings_theme_change("💻 System Default")
        mock_set_theme.assert_called_with("system")

        self.gui._on_settings_theme_change("☀️ Light Mode")
        mock_set_theme.assert_called_with("light")

    def test_on_update_installed_success(self):
        """Test on_update_installed handles success correctly."""
        self.gui.btn_check_updates = MagicMock()
        self.gui.health_feedback_label = MagicMock()

        self.gui._on_update_installed(True, "Successfully updated to v2.0.1.")
        self.gui.health_feedback_label.configure.assert_called_with(
            text="✓ Successfully updated to v2.0.1.",
            text_color=Theme.SUCCESS_GREEN,
        )

    def test_on_update_installed_failure(self):
        """Test on_update_installed displays descriptive error message on failure."""
        self.gui.btn_check_updates = MagicMock()
        self.gui.health_feedback_label = MagicMock()

        self.gui._on_update_installed(False, "Integrity check failed: Checksum mismatch.")
        self.gui.health_feedback_label.configure.assert_called_with(
            text="❌ Update failed: Integrity check failed: Checksum mismatch.",
            text_color=Theme.ERROR_RED,
        )

    def test_on_repair_result(self):
        """Test on_repair_result handles success and failure."""
        self.gui.btn_verify_repair = MagicMock()
        self.gui.health_status_dot = MagicMock()
        self.gui.health_feedback_label = MagicMock()

        self.gui._on_repair_result(True)
        self.gui.health_feedback_label.configure.assert_called_with(
            text="✓ All helper binaries verified and ready!",
            text_color=Theme.SUCCESS_GREEN,
        )

        self.gui._on_repair_result(False)
        self.gui.health_feedback_label.configure.assert_called_with(
            text="⚠️ Some dependencies could not be repaired.",
            text_color=Theme.ERROR_RED,
        )

    @patch("downloadyha_gui.app.filedialog.askdirectory")
    def test_browse_destination_success(self, mock_askdir):
        """Test browsing destination updates dest_entry with normalized path."""
        mock_askdir.return_value = "/custom/download/path"
        self.gui.dest_entry = MagicMock()
        self.gui.dest_entry.get.return_value = "/initial/path"
        self.gui.lift = MagicMock()
        self.gui.focus_force = MagicMock()

        self.gui._browse_destination()

        self.gui.dest_entry.delete.assert_called_with(0, unittest.mock.ANY)
        self.gui.dest_entry.insert.assert_called_with(0, "/custom/download/path" if sys.platform != "win32" else "\\custom\\download\\path")
        self.gui.lift.assert_called()
        self.gui.focus_force.assert_called()

    @patch("downloadyha_gui.app.filedialog.askdirectory")
    def test_browse_destination_cancelled_or_error(self, mock_askdir):
        """Test browsing destination handles cancellation and errors gracefully."""
        # Cancelled
        mock_askdir.return_value = ""
        self.gui.dest_entry = MagicMock()
        self.gui.dest_entry.get.return_value = "/initial/path"
        self.gui.lift = MagicMock()
        self.gui.focus_force = MagicMock()

        self.gui._browse_destination()
        self.gui.dest_entry.insert.assert_not_called()

        # Exception during dialog
        mock_askdir.side_effect = Exception("Dialog error")
        self.gui._browse_destination()
        # Should not raise exception
        self.gui.dest_entry.insert.assert_not_called()

    @patch("downloadyha_gui.app.filedialog.askdirectory")
    def test_browse_settings_path(self, mock_askdir):
        """Test browsing settings default path."""
        mock_askdir.return_value = "/custom/settings/path"
        self.gui.settings_path_entry = MagicMock()
        self.gui.settings_path_entry.get.return_value = ""
        self.gui.lift = MagicMock()
        self.gui.focus_force = MagicMock()

        self.gui._browse_settings_path()

        self.gui.settings_path_entry.delete.assert_called_with(0, unittest.mock.ANY)
        self.gui.settings_path_entry.insert.assert_called_with(0, "/custom/settings/path" if sys.platform != "win32" else "\\custom\\settings\\path")

    def test_populate_subtitles_with_language_names(self):
        """Test populating subtitle languages dropdown with language name beside description."""
        self.gui.sub_langs_menu = MagicMock()
        self.gui.sub_langs_var = MagicMock()

        sample_subtitles = [
            {"lang": "en", "is_auto": False, "formats": ["vtt"]},
            {"lang": "ar", "is_auto": True, "formats": ["vtt"]},
            {"lang": "es", "is_auto": False, "formats": ["srt"]},
        ]

        self.gui._populate_subtitles(sample_subtitles)

        expected_options = [
            "all (All Available)",
            "ar (Arabic)",
            "en (English)",
            "es (Spanish)",
        ]
        self.gui.sub_langs_menu.configure.assert_called_once_with(values=expected_options)
        self.gui.sub_langs_var.set.assert_called_once_with("ar (Arabic)")


if __name__ == "__main__":
    unittest.main()
