"""
Tests for downloader.py and ui.py modules.
"""

import unittest
from pathlib import Path
import sys

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
    def test_format_duration(self):
        self.assertEqual(ui.format_duration(0), "Unknown")
        self.assertEqual(ui.format_duration(None), "Unknown")
        self.assertEqual(ui.format_duration(65), "01:05")
        self.assertEqual(ui.format_duration(3665), "01:01:05")

    def test_format_progress_bar(self):
        bar_50 = ui.format_progress_bar(50.0, width=10)
        self.assertIn("50.0%", bar_50)
        bar_100 = ui.format_progress_bar(100.0, width=10)
        self.assertIn("100.0%", bar_100)


if __name__ == "__main__":
    unittest.main()
