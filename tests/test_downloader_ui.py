"""
Tests for downloader.py and ui.py modules.
"""

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from downloadyha import downloader, ui


class TestDownloader(unittest.TestCase):
    def test_sanitize_folder_name(self):
        self.assertEqual(downloader.sanitize_folder_name("Rock & Roll: Greatest Hits?"), "Rock & Roll_ Greatest Hits")
        self.assertEqual(downloader.sanitize_folder_name("My/Cool\\Playlist*<>|"), "My_Cool_Playlist")
        self.assertEqual(downloader.sanitize_folder_name("..."), "YouTube_Download")

    def test_is_playlist(self):
        self.assertTrue(downloader.is_playlist({"_type": "playlist", "entries": []}))
        self.assertTrue(downloader.is_playlist({"entries": [{"title": "Song 1"}]}))
        self.assertFalse(downloader.is_playlist({"title": "Single Video", "formats": []}))
        self.assertFalse(downloader.is_playlist({}))

    def test_get_playlist_entries(self):
        info = {
            "_type": "playlist",
            "entries": [{"id": "1"}, None, {"id": "2"}]
        }
        entries = downloader.get_playlist_entries(info)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["id"], "1")
        self.assertEqual(entries[1]["id"], "2")

    def test_get_video_qualities(self):
        info = {
            "formats": [
                {"height": 360},
                {"height": 1080},
                {"height": 720},
                {"height": 1080},
                {"height": 480},
                {"height": None},
            ]
        }
        qualities = downloader.get_video_qualities(info)
        self.assertEqual(qualities, [1080, 720, 480, 360])


class TestUI(unittest.TestCase):
    def setUp(self):
        ui.set_color_enabled(True)

    def test_format_duration(self):
        self.assertEqual(ui.format_duration(0), "Unknown")
        self.assertEqual(ui.format_duration(None), "Unknown")
        self.assertEqual(ui.format_duration(-10), "Unknown")
        self.assertEqual(ui.format_duration(65), "01:05")
        self.assertEqual(ui.format_duration(3665), "01:01:05")
        self.assertEqual(ui.format_duration("04:20"), "04:20")

    def test_format_bytes(self):
        self.assertEqual(ui.format_bytes(None), "N/A")
        self.assertEqual(ui.format_bytes(-5), "N/A")
        self.assertEqual(ui.format_bytes(500), "500 B")
        self.assertEqual(ui.format_bytes(1024), "1.0 KB")
        self.assertEqual(ui.format_bytes(10485760), "10.0 MB")
        self.assertEqual(ui.format_bytes(1073741824), "1.0 GB")

    def test_format_speed(self):
        self.assertEqual(ui.format_speed(None), "--.- MB/s")
        self.assertEqual(ui.format_speed(0), "--.- MB/s")
        self.assertEqual(ui.format_speed(10485760), "10.0 MB/s")

    def test_format_number(self):
        self.assertEqual(ui.format_number(None), "N/A")
        self.assertEqual(ui.format_number(1234567), "1,234,567")
        self.assertEqual(ui.format_number("invalid"), "invalid")

    def test_strip_ansi_and_visible_length(self):
        styled = f"{ui.Colors.CYAN}{ui.Colors.BOLD}Hello World{ui.Colors.RESET}"
        self.assertEqual(ui.strip_ansi(styled), "Hello World")
        self.assertEqual(ui.get_visible_length(styled), 11)
        self.assertEqual(ui.strip_ansi(None), "")
        self.assertEqual(ui.get_visible_length(None), 0)

    def test_colorize(self):
        ui.set_color_enabled(True)
        res = ui.colorize("Test", ui.Colors.GREEN)
        self.assertIn("\033[32m", res)
        self.assertIn("Test", res)

        ui.set_color_enabled(False)
        res_plain = ui.colorize("Test", ui.Colors.GREEN)
        self.assertEqual(res_plain, "Test")
        ui.set_color_enabled(True)

    def test_rgb_and_gradient(self):
        self.assertEqual(ui.hex_to_rgb("#00D2FF"), (0, 210, 255))
        self.assertEqual(ui.hex_to_rgb("FFF"), (255, 255, 255))
        grad = ui.gradient_text("DOWNLOADYHA", (0, 210, 255), (220, 80, 255))
        self.assertEqual(ui.strip_ansi(grad), "DOWNLOADYHA")

    def test_wrap_and_truncate_text(self):
        text = "This is a long sentence that should wrap properly across several lines"
        wrapped = ui.wrap_text(text, 20)
        self.assertTrue(len(wrapped) > 1)
        for line in wrapped:
            self.assertTrue(ui.get_visible_length(line) <= 20)

        self.assertEqual(ui.truncate_text("Short", 10), "Short")
        self.assertEqual(ui.truncate_text("Very Long String Exceeding Limit", 10), "Very Lo...")

    def test_banner(self):
        banner = ui.get_banner_text(version="1.0.0", author="Ahmed Tarek", subtitle="YouTube Downloader")
        plain_banner = ui.strip_ansi(banner)
        self.assertIn("YouTube Downloader", plain_banner)
        self.assertIn("v1.0.0", plain_banner)
        self.assertIn("Ahmed Tarek", plain_banner)

    def test_render_card_and_media_card(self):
        card = ui.render_card(title="Test Card", lines=["Line 1", "Line 2"])
        self.assertIn("Test Card", card)
        self.assertIn("Line 1", card)

        media_card = ui.render_media_card(
            title="Rick Astley - Never Gonna Give You Up",
            uploader="RickAstleyVEVO",
            duration=213,
            views=1400000000,
            qualities=[1080, 720, 480],
            destination="C:\\Downloads"
        )
        self.assertIn("Rick Astley", media_card)
        self.assertIn("RickAstleyVEVO", media_card)
        self.assertIn("03:33", media_card)
        self.assertIn("1080p, 720p, 480p", media_card)

    def test_render_summary(self):
        summary = ui.render_summary(
            title="Download Summary",
            items=[("Title", "Test Video"), ("Status", "Completed")]
        )
        self.assertIn("Download Summary", summary)
        self.assertIn("Test Video", summary)

    def test_render_menu(self):
        menu = ui.render_menu(
            title="Main Menu",
            options={"1": "Audio", "2": "Video"},
            default="1"
        )
        self.assertIn("Main Menu", menu)
        self.assertIn("Audio", menu)
        self.assertIn("Video", menu)

    def test_format_progress_bar(self):
        bar_50 = ui.format_progress_bar(50.0, width=10, speed="10 MB/s", eta="00:05", downloaded="50 MB", total="100 MB")
        self.assertIn("50.0%", bar_50)
        self.assertIn("10 MB/s", bar_50)
        self.assertIn("ETA 00:05", bar_50)
        self.assertIn("50 MB/100 MB", bar_50)

        bar_100 = ui.format_progress_bar(100.0, width=10)
        self.assertIn("100.0%", bar_100)

    def test_status_messages(self):
        # Capture stdout to ensure no exceptions thrown
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            ui.print_success("Success message")
            ui.print_info("Info message")
            ui.print_warning("Warning message")
            ui.print_error("Error message")
            ui.print_wait("Wait message")
            ui.print_download("Download message")
            ui.print_audio("Audio message")
            ui.print_video("Video message")
            ui.print_folder("Folder message")
            ui.print_alert("Alert message", alert_type="warning")
            ui.print_divider(title="Section Divider")
            ui.print_step(1, 3, "Step Title", description="Step description")
            output = mock_stdout.getvalue()
            self.assertIn("Success message", output)
            self.assertIn("Info message", output)
            self.assertIn("Warning message", output)
            self.assertIn("Error message", output)

    def test_prompt_input(self):
        with patch("builtins.input", side_effect=["test_value"]):
            val = ui.prompt_input("Enter name")
            self.assertEqual(val, "test_value")

        with patch("builtins.input", side_effect=["", "fallback"]):
            val_default = ui.prompt_input("Enter name", default="default_val")
            self.assertEqual(val_default, "default_val")

    def test_prompt_choice(self):
        with patch("builtins.input", side_effect=["1"]):
            choice = ui.prompt_choice("Choose Option", options=[("opt1", "Option One"), ("opt2", "Option Two")])
            self.assertEqual(choice, "opt1")

        with patch("builtins.input", side_effect=["2"]):
            choice = ui.prompt_choice("Choose Option", options={"a": "Alpha", "b": "Beta"})
            self.assertEqual(choice, "b")

    def test_prompt_confirm(self):
        with patch("builtins.input", side_effect=["y"]):
            self.assertTrue(ui.prompt_confirm("Continue?"))
        with patch("builtins.input", side_effect=["n"]):
            self.assertFalse(ui.prompt_confirm("Continue?"))
        with patch("builtins.input", side_effect=["", ""]):
            self.assertTrue(ui.prompt_confirm("Continue?", default=True))
            self.assertFalse(ui.prompt_confirm("Continue?", default=False))


if __name__ == "__main__":
    unittest.main()
