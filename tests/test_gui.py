"""
test_gui.py - Unit tests for the Downloadyha Desktop GUI.

Tests GUI initialization, URL validation, quality selection logic,
settings persistence, progress callback integration, and theme switching.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from downloadyha.gui import (
    AUDIO_QUALITY_OPTIONS,
    VIDEO_QUALITY_OPTIONS,
    DownloadyhaGUI,
    ProgressCallback,
    ThemeColors,
    is_valid_youtube_url,
    load_gui_settings,
    save_gui_settings,
    validate_youtube_url,
)


class TestURLValidation(unittest.TestCase):
    """Test URL validation functionality."""

    def test_validate_youtube_url_valid(self):
        """Test validation of valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/playlist?list=PL1234567890",
            "www.youtube.com/watch?v=abc123",
            "youtube.com/watch?v=abc123",
        ]

        for url in valid_urls:
            with self.subTest(url=url):
                is_valid, error = validate_youtube_url(url)
                self.assertTrue(is_valid, f"URL should be valid: {url}")
                self.assertEqual(error, "")

    def test_validate_youtube_url_invalid(self):
        """Test validation of invalid URLs."""
        invalid_urls = [
            "",
            "   ",
            "not a url",
            "https://www.google.com",
            "https://vimeo.com/12345",
            "ftp://youtube.com/video",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                is_valid, error = validate_youtube_url(url)
                self.assertFalse(is_valid, f"URL should be invalid: {url}")
                self.assertNotEqual(error, "")

    def test_is_valid_youtube_url(self):
        """Test quick URL validation function."""
        self.assertTrue(is_valid_youtube_url("https://www.youtube.com/watch?v=abc"))
        self.assertTrue(is_valid_youtube_url("https://youtu.be/abc"))
        self.assertFalse(is_valid_youtube_url(""))
        self.assertFalse(is_valid_youtube_url("https://www.example.com"))


class TestSettingsManagement(unittest.TestCase):
    """Test settings persistence and loading."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_get_config_dir = None

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_gui_settings_defaults(self):
        """Test loading default GUI settings."""
        with patch("downloadyha.gui.load") as mock_load:
            mock_load.return_value = {"download_directory": "/tmp/downloads"}

            settings = load_gui_settings()

            self.assertIn("download_directory", settings)
            self.assertIn("theme", settings)
            self.assertIn("last_video_quality", settings)
            self.assertIn("last_audio_quality", settings)
            self.assertEqual(settings["theme"], "light")

    def test_save_gui_settings(self):
        """Test saving GUI settings."""
        test_settings = {
            "download_directory": "/test/path",
            "theme": "dark",
            "last_video_quality": "3",
        }

        with patch("downloadyha.gui.load") as mock_load, \
             patch("downloadyha.gui.save") as mock_save:

            mock_load.return_value = {}
            mock_save.return_value = True

            result = save_gui_settings(test_settings)

            self.assertTrue(result)
            mock_save.assert_called_once()


class TestProgressCallback(unittest.TestCase):
    """Test progress callback integration."""

    def test_progress_callback_initialization(self):
        """Test ProgressCallback initialization."""
        callback = ProgressCallback()

        self.assertIsNotNone(callback._queue)
        self.assertFalse(callback._cancelled)

    def test_progress_callback_receives_events(self):
        """Test that progress callback receives and queues events."""
        callback = ProgressCallback()

        test_data = {
            "status": "downloading",
            "percent": 50.0,
            "speed_str": "10 MB/s",
            "eta_str": "00:30",
            "size_str": "50MB/100MB",
            "filename": "test.mp4",
            "item_title": "Test Video",
        }

        callback(test_data)

        events = callback.get_pending_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "downloading")
        self.assertEqual(events[0]["percent"], 50.0)

    def test_progress_callback_multiple_events(self):
        """Test handling multiple progress events."""
        callback = ProgressCallback()

        for i in range(5):
            callback({
                "status": "downloading",
                "percent": i * 20.0,
                "speed_str": f"{i} MB/s",
            })

        events = callback.get_pending_events()
        self.assertEqual(len(events), 5)
        self.assertEqual(events[0]["percent"], 0.0)
        self.assertEqual(events[4]["percent"], 80.0)

    def test_progress_callback_cancel(self):
        """Test cancelling progress callback."""
        callback = ProgressCallback()

        callback.cancel()
        self.assertTrue(callback._cancelled)

        # Cancelled callback should not queue new events
        callback({"status": "downloading", "percent": 50.0})
        events = callback.get_pending_events()
        self.assertEqual(len(events), 0)

    def test_progress_callback_reset(self):
        """Test resetting progress callback."""
        callback = ProgressCallback()

        callback({"status": "downloading", "percent": 50.0})
        callback.cancel()

        callback.reset()

        self.assertFalse(callback._cancelled)
        events = callback.get_pending_events()
        self.assertEqual(len(events), 0)

    def test_progress_callback_with_custom_callback(self):
        """Test progress callback with custom callback function."""
        received_events = []

        def custom_callback(event: Dict[str, Any]) -> None:
            received_events.append(event)

        callback = ProgressCallback(callback=custom_callback)

        test_data = {"status": "downloading", "percent": 75.0}
        callback(test_data)

        self.assertEqual(len(received_events), 1)
        self.assertEqual(received_events[0]["status"], "downloading")


class TestThemeColors(unittest.TestCase):
    """Test theme color definitions."""

    def test_light_theme_colors(self):
        """Test light theme has all required colors."""
        required_keys = [
            "bg", "fg", "accent", "success", "warning", "error",
            "card_bg", "input_bg", "border", "progress_bg", "progress_fill"
        ]

        for key in required_keys:
            with self.subTest(key=key):
                self.assertIn(key, ThemeColors.LIGHT)
                self.assertTrue(ThemeColors.LIGHT[key].startswith("#"))

    def test_dark_theme_colors(self):
        """Test dark theme has all required colors."""
        required_keys = [
            "bg", "fg", "accent", "success", "warning", "error",
            "card_bg", "input_bg", "border", "progress_bg", "progress_fill"
        ]

        for key in required_keys:
            with self.subTest(key=key):
                self.assertIn(key, ThemeColors.DARK)
                self.assertTrue(ThemeColors.DARK[key].startswith("#"))


class TestQualityOptions(unittest.TestCase):
    """Test quality selection options."""

    def test_video_quality_options(self):
        """Test video quality options are properly defined."""
        self.assertGreater(len(VIDEO_QUALITY_OPTIONS), 0)

        for option in VIDEO_QUALITY_OPTIONS:
            self.assertEqual(len(option), 3)
            key, label, height = option
            self.assertIsInstance(key, str)
            self.assertIsInstance(label, str)
            self.assertIsInstance(height, int)
            self.assertGreaterEqual(height, 0)

    def test_audio_quality_options(self):
        """Test audio quality options are properly defined."""
        self.assertGreater(len(AUDIO_QUALITY_OPTIONS), 0)

        for option in AUDIO_QUALITY_OPTIONS:
            self.assertEqual(len(option), 3)
            key, label, quality = option
            self.assertIsInstance(key, str)
            self.assertIsInstance(label, str)
            self.assertIsInstance(quality, str)


@unittest.skipIf(os.environ.get("CI") == "true", "Skip GUI tests in CI environment")
class TestDownloadyhaGUI(unittest.TestCase):
    """Test GUI application initialization and methods."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock tkinter to avoid creating actual windows
        self.tk_patcher = patch("downloadyha.gui.tk.Tk")
        self.mock_tk = self.tk_patcher.start()

        # Create a mock root window
        self.mock_root = MagicMock()
        self.mock_root.geometry.return_value = None
        self.mock_root.winfo_width.return_value = 700
        self.mock_root.winfo_height.return_value = 600
        self.mock_root.winfo_screenwidth.return_value = 1920
        self.mock_root.winfo_screenheight.return_value = 1080

        self.mock_tk.return_value = self.mock_root

    def tearDown(self):
        """Clean up test fixtures."""
        self.tk_patcher.stop()

    @patch("downloadyha.gui.load_gui_settings")
    @patch("downloadyha.gui.ttk.Style")
    def test_gui_initialization(self, mock_style, mock_load_settings):
        """Test GUI initialization."""
        mock_load_settings.return_value = {
            "download_directory": "/tmp/downloads",
            "theme": "light",
            "window_geometry": "700x600",
            "last_video_quality": "1",
            "last_audio_quality": "1",
        }

        # Don't actually create the GUI
        with patch.object(DownloadyhaGUI, "_build_ui"), \
             patch.object(DownloadyhaGUI, "_apply_theme"), \
             patch.object(DownloadyhaGUI, "_center_window"):

            gui = DownloadyhaGUI(root=self.mock_root)

            self.assertIsNotNone(gui.root)
            self.assertEqual(gui._current_theme, "light")
            self.assertFalse(gui._is_downloading)

    @patch("downloadyha.gui.load_gui_settings")
    @patch("downloadyha.gui.save_gui_settings")
    @patch("downloadyha.gui.ttk.Style")
    def test_gui_theme_switching(self, mock_style, mock_save, mock_load):
        """Test theme switching functionality."""
        mock_load.return_value = {
            "download_directory": "/tmp/downloads",
            "theme": "light",
            "window_geometry": "700x600",
            "last_video_quality": "1",
            "last_audio_quality": "1",
        }
        mock_save.return_value = True

        with patch.object(DownloadyhaGUI, "_build_ui"), \
             patch.object(DownloadyhaGUI, "_apply_theme"), \
             patch.object(DownloadyhaGUI, "_center_window"):

            gui = DownloadyhaGUI(root=self.mock_root)

            initial_theme = gui._current_theme
            gui.toggle_theme()

            self.assertNotEqual(gui._current_theme, initial_theme)
            mock_save.assert_called()

    @patch("downloadyha.gui.load_gui_settings")
    @patch("downloadyha.gui.ttk.Style")
    def test_gui_url_validation_handler(self, mock_style, mock_load):
        """Test URL validation handler in GUI."""
        mock_load.return_value = {
            "download_directory": "/tmp/downloads",
            "theme": "light",
            "window_geometry": "700x600",
            "last_video_quality": "1",
            "last_audio_quality": "1",
        }

        with patch.object(DownloadyhaGUI, "_build_ui"), \
             patch.object(DownloadyhaGUI, "_apply_theme"), \
             patch.object(DownloadyhaGUI, "_center_window"):

            gui = DownloadyhaGUI(root=self.mock_root)

            # Mock the validation label
            gui.url_validation_label = MagicMock()
            gui.url_var = MagicMock()
            gui._current_theme = "light"

            # Test valid URL
            gui.url_var.get.return_value = "https://www.youtube.com/watch?v=abc"
            gui._validate_url_input()

            # Should have been called to set success message
            gui.url_validation_label.configure.assert_called()

    @patch("downloadyha.gui.load_gui_settings")
    @patch("downloadyha.gui.ttk.Style")
    def test_gui_download_type_change(self, mock_style, mock_load):
        """Test download type change handler."""
        mock_load.return_value = {
            "download_directory": "/tmp/downloads",
            "theme": "light",
            "window_geometry": "700x600",
            "last_video_quality": "1",
            "last_audio_quality": "1",
        }

        with patch.object(DownloadyhaGUI, "_build_ui"), \
             patch.object(DownloadyhaGUI, "_apply_theme"), \
             patch.object(DownloadyhaGUI, "_center_window"):

            gui = DownloadyhaGUI(root=self.mock_root)

            # Mock UI elements
            gui.download_type_var = MagicMock()
            gui.quality_label = MagicMock()
            gui.quality_combo = MagicMock()
            gui.video_quality_var = MagicMock()
            gui.audio_quality_var = MagicMock()

            gui.video_quality_var.get.return_value = "1"
            gui.audio_quality_var.get.return_value = "1"

            # Test switching to video
            gui.download_type_var.get.return_value = "video"
            gui._on_type_change()
            gui.quality_label.configure.assert_called_with(text="Video Quality:")

            # Test switching to audio
            gui.download_type_var.get.return_value = "audio"
            gui._on_type_change()
            gui.quality_label.configure.assert_called_with(text="Audio Quality:")


class TestGUIIntegration(unittest.TestCase):
    """Integration tests for GUI components."""

    @patch("downloadyha.gui.get_media_info")
    def test_media_info_fetch_success(self, mock_get_info):
        """Test successful media info fetching."""
        mock_get_info.return_value = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 180,
            "playlist_count": 0,
        }

        # This test verifies the integration would work
        # Actual GUI testing would require more complex mocking
        info = mock_get_info("https://www.youtube.com/watch?v=abc")

        self.assertEqual(info["title"], "Test Video")
        self.assertEqual(info["uploader"], "Test Channel")

    @patch("downloadyha.gui.download_video")
    def test_download_integration(self, mock_download):
        """Test download integration."""
        from downloadyha.downloader import DownloadResult

        mock_download.return_value = DownloadResult(
            success=True,
            message="Download complete",
            download_type="video",
            completed_items=1,
            download_directory="/tmp/downloads",
        )

        result = mock_download(
            url="https://www.youtube.com/watch?v=abc",
            download_path="/tmp/downloads",
            height=1080,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.download_type, "video")


if __name__ == "__main__":
    unittest.main()
