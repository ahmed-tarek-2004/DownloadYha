"""
test_api.py - Comprehensive Unit & Integration Tests for Downloadyha Vercel API.
"""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from api.index import app
from api.models import (
    ClipValidationRequest,
    ClipValidationResponse,
    DownloadRequest,
    DownloadStreamResponse,
    HealthResponse,
    MediaInfoRequest,
    MediaType,
    SubtitleFormat,
    UrlValidationRequest,
    UrlValidationResponse,
)
from api.validators import (
    detect_platform,
    format_bytes,
    format_seconds,
    is_playlist_url,
    parse_time_str,
    resolve_audio_bitrate,
    resolve_video_height,
    validate_clip_range,
    validate_media_url,
)


class TestValidators(unittest.TestCase):
    """Test validator and parsing utility functions."""

    def test_parse_time_str(self):
        self.assertIsNone(parse_time_str(None))
        self.assertIsNone(parse_time_str(""))
        self.assertEqual(parse_time_str(90), 90.0)
        self.assertEqual(parse_time_str("90"), 90.0)
        self.assertEqual(parse_time_str("90s"), 90.0)
        self.assertEqual(parse_time_str("01:30"), 90.0)
        self.assertEqual(parse_time_str("1:30"), 90.0)
        self.assertEqual(parse_time_str("01:30.5"), 90.5)
        self.assertEqual(parse_time_str("01:00:00"), 3600.0)
        self.assertEqual(parse_time_str("01:15:30"), 4530.0)

        # Invalid formats
        with self.assertRaises(ValueError):
            parse_time_str("-10")
        with self.assertRaises(ValueError):
            parse_time_str("invalid")
        with self.assertRaises(ValueError):
            parse_time_str("01:99")  # seconds >= 60

    def test_format_seconds(self):
        self.assertEqual(format_seconds(0), "00:00")
        self.assertEqual(format_seconds(90), "01:30")
        self.assertEqual(format_seconds(3665), "01:01:05")
        self.assertEqual(format_seconds(-5), "00:00")
        self.assertEqual(format_seconds(None), "00:00")

    def test_format_bytes(self):
        self.assertEqual(format_bytes(None), "N/A")
        self.assertEqual(format_bytes(0), "N/A")
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1048576), "1.0 MB")
        self.assertEqual(format_bytes(1073741824), "1.0 GB")

    def test_validate_clip_range(self):
        # Valid clip
        res = validate_clip_range("01:00", "02:30", media_duration=300)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.start_seconds, 60.0)
        self.assertEqual(res.end_seconds, 150.0)
        self.assertEqual(res.clip_duration_seconds, 90.0)
        self.assertEqual(res.clip_duration_formatted, "01:30")

        # Invalid start >= end
        res_inv = validate_clip_range("02:30", "01:00")
        self.assertFalse(res_inv.is_valid)
        self.assertIn("must be greater", res_inv.error_message)

        # Start exceeds duration
        res_exceed = validate_clip_range("05:00", "06:00", media_duration=200)
        self.assertFalse(res_exceed.is_valid)
        self.assertIn("cannot exceed total media duration", res_exceed.error_message)

    def test_detect_platform(self):
        self.assertEqual(detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "YouTube")
        self.assertEqual(detect_platform("https://youtu.be/dQw4w9WgXcQ"), "YouTube")
        self.assertEqual(detect_platform("https://www.youtube.com/shorts/abcd123"), "YouTube Shorts")
        self.assertEqual(detect_platform("https://music.youtube.com/watch?v=123"), "YouTube Music")
        self.assertEqual(detect_platform("https://www.tiktok.com/@user/video/123"), "TikTok")
        self.assertEqual(detect_platform("https://www.instagram.com/reel/123"), "Instagram")
        self.assertEqual(detect_platform("https://www.facebook.com/watch/?v=123"), "Facebook")
        self.assertEqual(detect_platform("https://twitter.com/user/status/123"), "Twitter/X")
        self.assertEqual(detect_platform("https://x.com/user/status/123"), "Twitter/X")
        self.assertEqual(detect_platform("https://soundcloud.com/artist/track"), "SoundCloud")
        self.assertEqual(detect_platform("https://example.com/video.mp4"), "Generic Media URL")

    def test_is_playlist_url(self):
        self.assertTrue(is_playlist_url("https://www.youtube.com/playlist?list=PL123456789"))
        self.assertTrue(is_playlist_url("https://www.youtube.com/watch?v=abc&list=PL123456789"))
        self.assertFalse(is_playlist_url("https://www.youtube.com/watch?v=abc"))

    def test_validate_media_url(self):
        res = validate_media_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.platform, "YouTube")

        res_invalid = validate_media_url("not_a_url")
        self.assertFalse(res_invalid.is_valid)

    def test_resolve_video_height(self):
        self.assertEqual(resolve_video_height("1080"), 1080)
        self.assertEqual(resolve_video_height("1080p"), 1080)
        self.assertEqual(resolve_video_height("4k"), 2160)
        self.assertEqual(resolve_video_height("best"), 0)
        self.assertEqual(resolve_video_height(None), 0)

    def test_resolve_audio_bitrate(self):
        self.assertEqual(resolve_audio_bitrate("320"), "320")
        self.assertEqual(resolve_audio_bitrate("320k"), "320")
        self.assertEqual(resolve_audio_bitrate("best"), "0")
        self.assertEqual(resolve_audio_bitrate(None), "0")


class TestApiEndpoints(unittest.TestCase):
    """Test FastAPI endpoints via TestClient."""

    def setUp(self):
        self.client = TestClient(app)

    def test_root_dashboard(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Downloadyha", response.text)

    def test_root_json_accept(self):
        response = self.client.get("/", headers={"Accept": "application/json"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("name"), "Downloadyha API")

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertTrue(data.get("serverless"))
        self.assertIn("YouTube", data.get("supported_platforms"))

    def test_validate_url_endpoint(self):
        payload = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        response = self.client.post("/api/validate/url", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("is_valid"))
        self.assertEqual(data.get("platform"), "YouTube")

    def test_validate_clip_endpoint(self):
        payload = {
            "start_time": "00:30",
            "end_time": "01:45",
            "media_duration": 300
        }
        response = self.client.post("/api/validate/clip", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("is_valid"))
        self.assertEqual(data.get("start_seconds"), 30.0)
        self.assertEqual(data.get("end_seconds"), 105.0)
        self.assertEqual(data.get("clip_duration_seconds"), 75.0)

    def test_validate_clip_invalid(self):
        payload = {
            "start_time": "02:00",
            "end_time": "01:00"
        }
        response = self.client.post("/api/validate/clip", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get("is_valid"))
        self.assertIn("must be greater", data.get("error_message"))

    def test_invalid_url_info_error_handling(self):
        payload = {"url": "invalid_url_without_domain"}
        response = self.client.post("/api/info", json=payload)
        self.assertIn(response.status_code, [400, 422])
        data = response.json()
        self.assertFalse(data.get("success", True))

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_mocked_media_info_post(self, mock_extract):
        mock_extract.return_value = {
            "id": "dQw4w9WgXcQ",
            "title": "Mock Video Title",
            "uploader": "Mock Artist",
            "duration": 213,
            "view_count": 1000000,
            "thumbnail": "https://example.com/thumb.jpg",
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "height": 360,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                    "url": "https://example.com/360p.mp4",
                },
                {
                    "format_id": "22",
                    "ext": "mp4",
                    "height": 720,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                    "url": "https://example.com/720p.mp4",
                }
            ],
            "subtitles": {
                "en": [{"ext": "vtt", "url": "https://example.com/en.vtt"}]
            }
        }

        response = self.client.post("/api/info", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["title"], "Mock Video Title")
        self.assertEqual(data["id"], "dQw4w9WgXcQ")
        self.assertIn(720, data["available_resolutions"])
        self.assertIn(360, data["available_resolutions"])

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_mocked_resolve_stream(self, mock_extract):
        mock_extract.return_value = {
            "id": "dQw4w9WgXcQ",
            "title": "Mock Video Title",
            "duration": 200,
            "thumbnail": "https://example.com/thumb.jpg",
            "formats": [
                {
                    "format_id": "22",
                    "ext": "mp4",
                    "height": 720,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                    "url": "https://example.com/direct_720p.mp4",
                }
            ]
        }

        req_payload = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "media_type": "video",
            "quality": "720",
            "start_time": "00:10",
            "end_time": "00:50"
        }

        response = self.client.post("/api/resolve", json=req_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["direct_download_url"], "https://example.com/direct_720p.mp4")
        self.assertIsNotNone(data.get("clip_info"))
        self.assertEqual(data["clip_info"]["start_seconds"], 10.0)
        self.assertEqual(data["clip_info"]["end_seconds"], 50.0)
        self.assertEqual(data["clip_info"]["clip_duration_seconds"], 40.0)

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_formats_post_endpoint(self, mock_extract):
        mock_extract.return_value = {
            "id": "abc1234",
            "title": "Formats Test Video",
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "height": 360,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                    "url": "https://example.com/360.mp4"
                }
            ]
        }
        response = self.client.post("/api/formats", json={"url": "https://www.youtube.com/watch?v=abc1234"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn(360, data["available_resolutions"])

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_subtitles_post_endpoint(self, mock_extract):
        mock_extract.return_value = {
            "id": "abc1234",
            "title": "Subtitles Test Video",
            "formats": [],
            "subtitles": {
                "en": [{"ext": "srt", "url": "https://example.com/en.srt"}]
            }
        }
        response = self.client.post("/api/subtitles", json={"url": "https://www.youtube.com/watch?v=abc1234"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["subtitles_count"], 1)

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_playlist_endpoints(self, mock_extract):
        playlist_data = {
            "id": "PL123456",
            "title": "Awesome Music Playlist",
            "_type": "playlist",
            "entries": [
                {
                    "id": "item1",
                    "title": "Track 1",
                    "duration": 150,
                    "url": "https://www.youtube.com/watch?v=item1",
                },
                {
                    "id": "item2",
                    "title": "Track 2",
                    "duration": 200,
                    "url": "https://www.youtube.com/watch?v=item2",
                }
            ]
        }
        video1_data = {
            "id": "item1",
            "title": "Track 1",
            "duration": 150,
            "formats": [
                {"format_id": "18", "ext": "mp4", "height": 360, "url": "https://cdn.example.com/1.mp4", "vcodec": "avc1", "acodec": "mp4a"}
            ]
        }
        video2_data = {
            "id": "item2",
            "title": "Track 2",
            "duration": 200,
            "formats": [
                {"format_id": "18", "ext": "mp4", "height": 360, "url": "https://cdn.example.com/2.mp4", "vcodec": "avc1", "acodec": "mp4a"}
            ]
        }

        def mock_extract_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            if "item1" in url:
                return video1_data
            if "item2" in url:
                return video2_data
            return playlist_data

        mock_extract.side_effect = mock_extract_side_effect

        # POST /api/playlist
        res_post = self.client.post("/api/playlist", json={"url": "https://www.youtube.com/playlist?list=PL123456"})
        self.assertEqual(res_post.status_code, 200)
        self.assertEqual(res_post.json()["count"], 2)

        # GET /api/playlist
        res_get = self.client.get("/api/playlist?url=https://www.youtube.com/playlist?list=PL123456")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["title"], "Awesome Music Playlist")

        # POST /api/playlist/resolve
        res_res_post = self.client.post("/api/playlist/resolve", json={"url": "https://www.youtube.com/playlist?list=PL123456"})
        self.assertEqual(res_res_post.status_code, 200)
        res_data = res_res_post.json()
        self.assertTrue(res_data["success"])
        self.assertEqual(res_data["total_items"], 2)
        self.assertEqual(res_data["entries"][0]["filename"], "01 - Track 1.mp4")
        self.assertEqual(res_data["entries"][1]["filename"], "02 - Track 2.mp4")

        # GET /api/playlist/resolve
        res_res_get = self.client.get("/api/playlist/resolve?url=https://www.youtube.com/playlist?list=PL123456&media_type=video")
        self.assertEqual(res_res_get.status_code, 200)
        self.assertEqual(len(res_res_get.json()["entries"]), 2)

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_direct_stream_and_download_redirects(self, mock_extract):
        mock_extract.return_value = {
            "id": "vid999",
            "title": "Streaming Test Video",
            "duration": 180,
            "formats": [
                {
                    "format_id": "22",
                    "ext": "mp4",
                    "height": 720,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                    "url": "https://cdn.example.com/direct_video.mp4"
                }
            ]
        }

        # GET /api/stream?redirect=true
        res_stream = self.client.get(
            "/api/stream?url=https://www.youtube.com/watch?v=vid999&redirect=true",
            follow_redirects=False
        )
        self.assertEqual(res_stream.status_code, 307)
        self.assertEqual(res_stream.headers["location"], "https://cdn.example.com/direct_video.mp4")

        # GET /api/download/file?redirect=true
        res_download = self.client.get(
            "/api/download/file?url=https://www.youtube.com/watch?v=vid999&redirect=true",
            follow_redirects=False
        )
        self.assertEqual(res_download.status_code, 307)
        self.assertEqual(res_download.headers["location"], "https://cdn.example.com/direct_video.mp4")

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_subtitle_download_endpoint(self, mock_extract):
        mock_extract.return_value = {
            "id": "vid999",
            "title": "Subtitle Test Video",
            "formats": [],
            "subtitles": {
                "en": [{"ext": "srt", "url": "https://cdn.example.com/subtitles_en.srt"}]
            }
        }

        with patch("httpx.AsyncClient.stream") as mock_stream:
            # Mock async context manager for httpx client.stream
            mock_upstream = MagicMock()
            async def fake_aiter():
                yield b"1\n00:00:01,000 --> 00:00:04,000\nHello World\n"
            mock_upstream.aiter_bytes = fake_aiter

            class AsyncContextManagerMock:
                async def __aenter__(self):
                    return mock_upstream
                async def __aexit__(self, *args):
                    pass

            mock_stream.return_value = AsyncContextManagerMock()

            res = self.client.get("/api/subtitles/download?url=https://www.youtube.com/watch?v=vid999&lang=en&sub_format=srt")
            self.assertEqual(res.status_code, 200)
            self.assertIn("attachment", res.headers.get("content-disposition", ""))
            self.assertIn(".srt", res.headers.get("content-disposition", ""))
            self.assertIn("application/x-subrip", res.headers.get("content-type", ""))
            self.assertIn(b"Hello World", res.content)


if __name__ == "__main__":
    unittest.main()
