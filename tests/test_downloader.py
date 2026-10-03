"""
Tests for downloader.py module in downloadyha.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from downloadyha import downloader
from downloadyha.downloader import (
    DownloadResult,
    YtDlpMessageCollector,
    choose_audio_quality,
    choose_video_quality,
    create_progress_hook,
    download_audio,
    download_media,
    download_playlist,
    download_playlist_audio,
    download_playlist_video,
    download_video,
    format_bytes,
    format_eta,
    format_speed,
    get_media_info,
    get_playlist_entries,
    get_playlist_info,
    get_video_info,
    get_video_qualities,
    get_yt_dlp_options,
    is_playlist,
    is_playlist_url,
    parse_time_str,
    resolve_audio_quality,
    resolve_video_format,
    sanitize_filename,
    sanitize_folder_name,
)


class TestTimeParsingAndClipping(unittest.TestCase):
    """Test parse_time_str utility and partial clipping downloads."""

    def test_parse_time_str_none_and_empty(self):
        self.assertIsNone(parse_time_str(None))
        self.assertIsNone(parse_time_str(""))
        self.assertIsNone(parse_time_str("   "))

    def test_parse_time_str_numeric(self):
        self.assertEqual(parse_time_str(90), 90.0)
        self.assertEqual(parse_time_str(120.5), 120.5)
        self.assertEqual(parse_time_str(0), 0.0)

    def test_parse_time_str_seconds_string(self):
        self.assertEqual(parse_time_str("90"), 90.0)
        self.assertEqual(parse_time_str("90s"), 90.0)
        self.assertEqual(parse_time_str("90S"), 90.0)
        self.assertEqual(parse_time_str("45.5"), 45.5)

    def test_parse_time_str_mm_ss(self):
        self.assertEqual(parse_time_str("01:30"), 90.0)
        self.assertEqual(parse_time_str("1:30"), 90.0)
        self.assertEqual(parse_time_str("00:45.5"), 45.5)
        self.assertEqual(parse_time_str("10:00"), 600.0)

    def test_parse_time_str_hh_mm_ss(self):
        self.assertEqual(parse_time_str("01:15:30"), 4530.0)
        self.assertEqual(parse_time_str("00:01:30"), 90.0)
        self.assertEqual(parse_time_str("2:00:00"), 7200.0)

    def test_parse_time_str_invalid(self):
        with self.assertRaises(ValueError):
            parse_time_str(-10)
        with self.assertRaises(ValueError):
            parse_time_str("-01:30")
        with self.assertRaises(ValueError):
            parse_time_str("invalid")
        with self.assertRaises(ValueError):
            parse_time_str("01:60")  # invalid seconds >= 60
        with self.assertRaises(ValueError):
            parse_time_str("01:70:00")  # invalid minutes >= 60
        with self.assertRaises(ValueError):
            parse_time_str("1:2:3:4")  # too many parts


class TestDownloaderHelpers(unittest.TestCase):
    """Test helper functions for sanitation, detection, and formatting."""

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("valid_name"), "valid_name")
        self.assertEqual(sanitize_filename("foo/bar\\baz:qux*1?2<3>4|5"), "foo_bar_baz_qux_1_2_3_4_5")
        self.assertEqual(sanitize_filename("...leading and trailing..."), "leading and trailing")
        self.assertEqual(sanitize_filename(""), "download")
        self.assertEqual(sanitize_filename("A///B:::C"), "A_B_C")

    def test_sanitize_folder_name(self):
        self.assertEqual(sanitize_folder_name("My Playlist? Vol. 1"), "My Playlist_ Vol. 1")
        self.assertEqual(sanitize_folder_name("   "), "Media_Download")

    def test_is_playlist_url(self):
        # Direct playlist URLs
        self.assertTrue(is_playlist_url("https://www.youtube.com/playlist?list=PL1234567890"))
        self.assertTrue(is_playlist_url("https://youtube.com/playlist?list=PL1234567890"))
        self.assertTrue(is_playlist_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL1234567890"))
        self.assertTrue(is_playlist_url("https://youtu.be/dQw4w9WgXcQ?list=PL1234567890"))
        self.assertTrue(is_playlist_url("https://soundcloud.com/artist/sets/album-name"))

        # Single video URLs
        self.assertFalse(is_playlist_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertFalse(is_playlist_url("https://youtu.be/dQw4w9WgXcQ"))
        self.assertFalse(is_playlist_url(""))

    def test_is_playlist_dict(self):
        self.assertTrue(is_playlist({"_type": "playlist", "title": "Test Playlist"}))
        self.assertTrue(is_playlist({"_type": "multi_video", "title": "Multi Video"}))
        self.assertTrue(is_playlist({"title": "Test", "entries": [{"id": "1"}, {"id": "2"}]}))
        self.assertTrue(is_playlist({"title": "Test", "playlist_count": 5}))

        self.assertFalse(is_playlist({"_type": "video", "title": "Single Video", "formats": [{"height": 1080}]}))
        self.assertFalse(is_playlist({"title": "Single Video", "formats": [{"height": 720}]}))
        self.assertFalse(is_playlist({}))
        self.assertFalse(is_playlist(None))

    def test_get_playlist_entries(self):
        single_info = {"title": "Single Video"}
        self.assertEqual(get_playlist_entries(single_info), [single_info])

        pl_info = {
            "_type": "playlist",
            "entries": [{"id": "1", "title": "V1"}, None, {"id": "2", "title": "V2"}]
        }
        entries = get_playlist_entries(pl_info)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["id"], "1")
        self.assertEqual(entries[1]["id"], "2")

    def test_format_bytes(self):
        self.assertEqual(format_bytes(None), "N/A")
        self.assertEqual(format_bytes(0), "N/A")
        self.assertEqual(format_bytes(500), "500.0 B")
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1048576), "1.0 MB")
        self.assertEqual(format_bytes(1073741824 * 2.5), "2.5 GB")

    def test_format_speed(self):
        self.assertEqual(format_speed(None), "N/A")
        self.assertEqual(format_speed(0), "N/A")
        self.assertEqual(format_speed(1048576 * 3.2), "3.2 MB/s")

    def test_format_eta(self):
        self.assertEqual(format_eta(None), "N/A")
        self.assertEqual(format_eta(-1), "N/A")
        self.assertEqual(format_eta(45), "00:45")
        self.assertEqual(format_eta(125), "02:05")
        self.assertEqual(format_eta(3665), "01:01:05")


class TestQualityResolvers(unittest.TestCase):
    """Test video and audio quality resolution."""

    def test_resolve_video_format(self):
        best_fmt = resolve_video_format(0, has_ffmpeg=True)
        self.assertEqual(best_fmt, "bestvideo+bestaudio/best")

        h1080_fmt = resolve_video_format(1080, has_ffmpeg=True)
        self.assertIn("height<=1080", h1080_fmt)
        self.assertIn("bestvideo", h1080_fmt)

        no_ffmpeg_best = resolve_video_format(0, has_ffmpeg=False)
        self.assertEqual(no_ffmpeg_best, "best[acodec!=none]/best")

        no_ffmpeg_1080 = resolve_video_format(1080, has_ffmpeg=False)
        self.assertIn("height<=1080", no_ffmpeg_1080)
        self.assertIn("acodec!=none", no_ffmpeg_1080)

    def test_resolve_audio_quality(self):
        self.assertEqual(resolve_audio_quality("best"), "0")
        self.assertEqual(resolve_audio_quality(None), "0")
        self.assertEqual(resolve_audio_quality("0"), "0")
        self.assertEqual(resolve_audio_quality("320k"), "320")
        self.assertEqual(resolve_audio_quality("320"), "320")
        self.assertEqual(resolve_audio_quality(192), "192")
        self.assertEqual(resolve_audio_quality("128k"), "128")
        self.assertEqual(resolve_audio_quality("invalid"), "0")

    def test_get_video_qualities(self):
        info_single = {
            "formats": [
                {"height": 360},
                {"height": 720},
                {"height": 1080},
                {"height": 720},  # duplicate
                {"height": 100},  # < 144
            ]
        }
        qualities = get_video_qualities(info_single)
        self.assertEqual(qualities, [1080, 720, 360])

        info_playlist = {"_type": "playlist", "entries": []}
        pl_qualities = get_video_qualities(info_playlist)
        self.assertIn(1080, pl_qualities)
        self.assertIn(720, pl_qualities)


class TestDownloadResult(unittest.TestCase):
    """Test DownloadResult structure and backwards compatibility."""

    def test_download_result_boolean_and_attributes(self):
        res_ok = DownloadResult(
            success=True,
            message="Done",
            download_type="video",
            is_playlist=True,
            total_items=10,
            completed_items=10,
            failed_items=0,
            files=["v1.mp4", "v2.mp4"],
            errors=[],
            download_directory="/downloads/test_pl",
            playlist_title="Test Playlist"
        )
        self.assertTrue(bool(res_ok))
        self.assertTrue(res_ok)
        self.assertEqual(res_ok.output_dir, "/downloads/test_pl")
        self.assertEqual(res_ok["output_dir"], "/downloads/test_pl")
        self.assertEqual(res_ok["completed_items"], 10)
        self.assertEqual(res_ok.get("playlist_title"), "Test Playlist")
        self.assertIn("files", res_ok)

        res_fail = DownloadResult(
            success=False,
            message="Failed",
            download_type="audio",
            errors=["Network error"]
        )
        self.assertFalse(bool(res_fail))
        self.assertFalse(res_fail)
        self.assertEqual(len(res_fail.errors), 1)


class TestProgressHooks(unittest.TestCase):
    """Test progress hook creation and callbacks."""

    def test_progress_hook_callback(self):
        events = []

        def on_progress(evt):
            events.append(evt)

        stats = {"total_items": 1, "completed_items": 0, "files": []}
        hook = create_progress_hook(custom_callback=on_progress, stats_tracker=stats)

        # Simulate downloading event
        hook({
            "status": "downloading",
            "downloaded_bytes": 500000,
            "total_bytes": 1000000,
            "_percent_str": " 50.0%",
            "_speed_str": " 1.2MiB/s",
            "_eta_str": "00:05",
            "filename": "video.mp4",
            "info_dict": {"title": "Test Title", "playlist_index": 1, "playlist_count": 3}
        })

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["status"], "downloading")
        self.assertEqual(events[0]["percent"], 50.0)
        self.assertEqual(events[0]["playlist_index"], 1)
        self.assertEqual(events[0]["playlist_count"], 3)
        self.assertEqual(stats["total_items"], 3)

        # Simulate finished event
        hook({
            "status": "finished",
            "filename": "video.mp4",
            "info_dict": {"title": "Test Title"}
        })

        self.assertEqual(len(events), 2)
        self.assertEqual(events[1]["status"], "finished")
        self.assertEqual(stats["completed_items"], 1)
        self.assertIn("video.mp4", stats["files"])


class TestDownloaderMocked(unittest.TestCase):
    """Test full download workflows using mocked yt-dlp."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("downloadyha.downloader.yt_dlp.YoutubeDL")
    def test_get_media_info_single(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Single Video",
            "formats": [{"height": 1080}],
            "_type": "video"
        }
        mock_ydl_class.return_value = mock_ydl

        info = get_media_info("https://www.youtube.com/watch?v=123")
        self.assertIsNotNone(info)
        self.assertEqual(info["title"], "Single Video")
        self.assertFalse(info["is_playlist"])

    @patch("downloadyha.downloader.yt_dlp.YoutubeDL")
    def test_get_media_info_playlist(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "My Great Playlist",
            "_type": "playlist",
            "entries": iter([{"id": "v1", "title": "Vid 1"}, {"id": "v2", "title": "Vid 2"}])
        }
        mock_ydl_class.return_value = mock_ydl

        info = get_media_info("https://www.youtube.com/playlist?list=PL123")
        self.assertIsNotNone(info)
        self.assertEqual(info["title"], "My Great Playlist")
        self.assertTrue(info["is_playlist"])
        self.assertIsInstance(info["entries"], list)
        self.assertEqual(len(info["entries"]), 2)

    @patch("downloadyha.downloader.yt_dlp.YoutubeDL")
    def test_download_single_video_success(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Test Video",
            "formats": [{"height": 1080}]
        }
        mock_ydl.download.return_value = 0
        mock_ydl_class.return_value = mock_ydl

        res = download_video("https://www.youtube.com/watch?v=123", self.test_dir, height=1080)
        self.assertTrue(res)
        self.assertEqual(res.download_type, "video")
        self.assertFalse(res.is_playlist)
        self.assertEqual(res.download_directory, self.test_dir)

    @patch("downloadyha.downloader.yt_dlp.YoutubeDL")
    def test_download_single_audio_success(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Test Song",
            "formats": []
        }
        mock_ydl.download.return_value = 0
        mock_ydl_class.return_value = mock_ydl

        res = download_audio("https://www.youtube.com/watch?v=123", self.test_dir, quality="320")
        self.assertTrue(res)
        self.assertEqual(res.download_type, "audio")
        self.assertFalse(res.is_playlist)

    @patch("downloadyha.downloader.yt_dlp.YoutubeDL")
    def test_download_playlist_video_success(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Top Hits 2026",
            "_type": "playlist",
            "entries": [{"id": "1", "title": "Song 1"}, {"id": "2", "title": "Song 2"}]
        }
        mock_ydl.download.return_value = 0
        mock_ydl_class.return_value = mock_ydl

        res = download_playlist_video("https://www.youtube.com/playlist?list=PL123", self.test_dir, height=720)
        self.assertTrue(res)
        self.assertEqual(res.download_type, "video")
        self.assertTrue(res.is_playlist)
        expected_folder = os.path.join(self.test_dir, "Top Hits 2026")
        self.assertEqual(res.download_directory, expected_folder)
        self.assertTrue(os.path.exists(expected_folder))

    @patch("downloadyha.downloader.yt_dlp.YoutubeDL")
    def test_download_playlist_audio_success(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Audio Playlist",
            "_type": "playlist",
            "entries": [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        }
        mock_ydl.download.return_value = 0
        mock_ydl_class.return_value = mock_ydl

        res = download_playlist_audio("https://www.youtube.com/playlist?list=PL123", self.test_dir, quality="192")
        self.assertTrue(res)
        self.assertEqual(res.download_type, "audio")
        self.assertTrue(res.is_playlist)

    @patch("downloadyha.downloader.yt_dlp.YoutubeDL")
    def test_download_partial_video_success(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Clipped Video",
            "formats": [{"height": 1080}]
        }
        mock_ydl.download.return_value = 0
        mock_ydl_class.return_value = mock_ydl

        res = download_video(
            "https://www.youtube.com/watch?v=123",
            self.test_dir,
            height=1080,
            start_time="01:00",
            end_time="02:30"
        )
        self.assertTrue(res)
        self.assertEqual(res.download_type, "video")
        # Second call is the actual download YoutubeDL instance
        ydl_opts = mock_ydl_class.call_args_list[-1][0][0]
        self.assertIn("download_ranges", ydl_opts)
        self.assertTrue(ydl_opts.get("force_keyframes_at_cuts"))

    @patch("downloadyha.downloader.yt_dlp.YoutubeDL")
    def test_download_partial_audio_success(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Clipped Audio",
            "formats": []
        }
        mock_ydl.download.return_value = 0
        mock_ydl_class.return_value = mock_ydl

        res = download_audio(
            "https://www.youtube.com/watch?v=123",
            self.test_dir,
            quality="320",
            start_time="30",
            end_time="90"
        )
        self.assertTrue(res)
        self.assertEqual(res.download_type, "audio")
        # Second call is the actual download YoutubeDL instance
        ydl_opts = mock_ydl_class.call_args_list[-1][0][0]
        self.assertIn("download_ranges", ydl_opts)
        self.assertTrue(ydl_opts.get("force_keyframes_at_cuts"))

    def test_download_partial_invalid_time_range(self):
        res = download_video(
            "https://www.youtube.com/watch?v=123",
            self.test_dir,
            start_time="03:00",
            end_time="01:00"
        )
        self.assertFalse(res)
        self.assertIn("greater than start time", res.message)


if __name__ == "__main__":
    unittest.main()
