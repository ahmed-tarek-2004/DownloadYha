"""
test_api_core.py - Unit tests for the Downloadyha API models, validators, and service layer.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from api.models import (
    AudioFormat,
    ClipInfo,
    ClipValidationRequest,
    ClipValidationResponse,
    DownloadRequest,
    DownloadStreamResponse,
    ErrorResponse,
    FormatInfo,
    HealthResponse,
    MediaInfoRequest,
    MediaInfoResponse,
    MediaType,
    PlaylistEntry,
    PlaylistInfoResponse,
    SubtitleFormat,
    SubtitleTrack,
    UrlValidationRequest,
    UrlValidationResponse,
    VideoFormat,
)
from api.validators import (
    SUPPORTED_AUDIO_BITRATES,
    SUPPORTED_PLATFORMS,
    SUPPORTED_SUBTITLE_FORMATS,
    SUPPORTED_VIDEO_RESOLUTIONS,
    detect_platform,
    format_bytes,
    format_seconds,
    is_playlist_url,
    parse_time_str,
    validate_audio_bitrate,
    validate_clip_range,
    validate_media_url,
    validate_output_format,
    validate_subtitle_format,
    validate_video_quality,
)
from api.services.ytdlp_service import (
    AgeRestrictedError,
    DownloadyhaException,
    ExtractionError,
    GeoBlockedError,
    InvalidUrlError,
    MediaNotFoundError,
    PrivateMediaError,
    RateLimitError,
    ValidationError,
    build_serverless_ytdlp_options,
    get_formats_breakdown,
    get_health_status,
    get_playlist_details,
    get_structured_media_info,
    get_subtitles_info_from_dict,
    map_ytdlp_exception,
    parse_format_item,
    resolve_download_streams,
)


class TestApiValidators(unittest.TestCase):
    """Tests for API validator functions."""

    def test_parse_time_str(self):
        self.assertIsNone(parse_time_str(None))
        self.assertIsNone(parse_time_str(""))
        self.assertIsNone(parse_time_str("   "))
        self.assertEqual(parse_time_str(90), 90.0)
        self.assertEqual(parse_time_str(0), 0.0)
        self.assertEqual(parse_time_str("90"), 90.0)
        self.assertEqual(parse_time_str("90.5"), 90.5)
        self.assertEqual(parse_time_str("90s"), 90.0)
        self.assertEqual(parse_time_str("01:30"), 90.0)
        self.assertEqual(parse_time_str("1:30"), 90.0)
        self.assertEqual(parse_time_str("01:30.5"), 90.5)
        self.assertEqual(parse_time_str("01:15:30"), 4530.0)
        self.assertEqual(parse_time_str("1:00:00"), 3600.0)

        # Invalid formats
        with self.assertRaises(ValueError):
            parse_time_str(-10)
        with self.assertRaises(ValueError):
            parse_time_str("-01:30")
        with self.assertRaises(ValueError):
            parse_time_str("01:65")
        with self.assertRaises(ValueError):
            parse_time_str("01:30:75")
        with self.assertRaises(ValueError):
            parse_time_str("invalid:format")
        with self.assertRaises(ValueError):
            parse_time_str("1:2:3:4")

    def test_format_seconds(self):
        self.assertEqual(format_seconds(None), "00:00")
        self.assertEqual(format_seconds(-1), "00:00")
        self.assertEqual(format_seconds(0), "00:00")
        self.assertEqual(format_seconds(45), "00:45")
        self.assertEqual(format_seconds(90), "01:30")
        self.assertEqual(format_seconds(3600), "01:00:00")
        self.assertEqual(format_seconds(3661), "01:01:01")

    def test_format_bytes(self):
        self.assertEqual(format_bytes(None), "N/A")
        self.assertEqual(format_bytes(0), "N/A")
        self.assertEqual(format_bytes(-100), "N/A")
        self.assertEqual(format_bytes(500), "500.0 B")
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1048576 * 15), "15.0 MB")
        self.assertEqual(format_bytes(1073741824 * 2.5), "2.5 GB")

    def test_validate_clip_range(self):
        # Valid range
        res = validate_clip_range("01:00", "02:00", "05:00")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.start_seconds, 60.0)
        self.assertEqual(res.end_seconds, 120.0)
        self.assertEqual(res.start_time, "01:00")
        self.assertEqual(res.end_time, "02:00")
        self.assertEqual(res.clip_duration_seconds, 60.0)
        self.assertEqual(res.clip_duration_formatted, "01:00")

        # Start only
        res_start = validate_clip_range("01:00", None, 300)
        self.assertTrue(res_start.is_valid)
        self.assertEqual(res_start.start_seconds, 60.0)
        self.assertEqual(res_start.clip_duration_seconds, 240.0)

        # End only
        res_end = validate_clip_range(None, "02:00", 300)
        self.assertTrue(res_end.is_valid)
        self.assertEqual(res_end.end_seconds, 120.0)
        self.assertEqual(res_end.clip_duration_seconds, 120.0)

        # Start >= End (Invalid)
        res_inv = validate_clip_range("03:00", "02:00")
        self.assertFalse(res_inv.is_valid)
        self.assertIn("greater than", res_inv.error_message)

        # Start >= Duration (Invalid)
        res_dur = validate_clip_range("06:00", "07:00", "05:00")
        self.assertFalse(res_dur.is_valid)
        self.assertIn("cannot exceed", res_dur.error_message)

    def test_platform_detection(self):
        self.assertEqual(detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "YouTube")
        self.assertEqual(detect_platform("https://youtu.be/dQw4w9WgXcQ"), "YouTube")
        self.assertEqual(detect_platform("https://www.youtube.com/shorts/abc123xyz"), "YouTube Shorts")
        self.assertEqual(detect_platform("https://music.youtube.com/watch?v=abc"), "YouTube Music")
        self.assertEqual(detect_platform("https://www.tiktok.com/@user/video/123456"), "TikTok")
        self.assertEqual(detect_platform("https://www.instagram.com/p/Cxyz/"), "Instagram")
        self.assertEqual(detect_platform("https://www.facebook.com/watch/?v=123"), "Facebook")
        self.assertEqual(detect_platform("https://fb.watch/xyz/"), "Facebook")
        self.assertEqual(detect_platform("https://twitter.com/user/status/123"), "Twitter/X")
        self.assertEqual(detect_platform("https://x.com/user/status/123"), "Twitter/X")
        self.assertEqual(detect_platform("https://www.reddit.com/r/videos/comments/abc/"), "Reddit")
        self.assertEqual(detect_platform("https://vimeo.com/123456"), "Vimeo")
        self.assertEqual(detect_platform("https://soundcloud.com/artist/track"), "SoundCloud")
        self.assertEqual(detect_platform("https://twitch.tv/streamer"), "Twitch")
        self.assertEqual(detect_platform("https://dailymotion.com/video/x123"), "Dailymotion")
        self.assertEqual(detect_platform("https://pinterest.com/pin/123"), "Pinterest")
        self.assertEqual(detect_platform("https://threads.net/@user/post/123"), "Threads")
        self.assertEqual(detect_platform("https://example.com/video.mp4"), "Generic Media URL")

    def test_is_playlist_url(self):
        self.assertTrue(is_playlist_url("https://www.youtube.com/playlist?list=PL1234567890"))
        self.assertTrue(is_playlist_url("https://www.youtube.com/watch?v=abc&list=PL1234567890"))
        self.assertFalse(is_playlist_url("https://www.youtube.com/watch?v=abc"))
        self.assertTrue(is_playlist_url("https://soundcloud.com/artist/sets/my-album"))

    def test_validate_media_url(self):
        v1 = validate_media_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertTrue(v1.is_valid)
        self.assertEqual(v1.platform, "YouTube")
        self.assertFalse(v1.is_playlist)

        v2 = validate_media_url("youtube.com/playlist?list=PL12345")
        self.assertTrue(v2.is_valid)
        self.assertEqual(v2.platform, "YouTube")
        self.assertTrue(v2.is_playlist)
        self.assertTrue(v2.normalized_url.startswith("https://"))

        v3 = validate_media_url("not a url")
        self.assertFalse(v3.is_valid)
        self.assertIsNotNone(v3.error_message)

    def test_quality_and_format_validators(self):
        self.assertEqual(validate_video_quality("1080p"), 1080)
        self.assertEqual(validate_video_quality("4K"), 2160)
        self.assertEqual(validate_video_quality("8k"), 4320)
        self.assertEqual(validate_video_quality("720"), 720)
        self.assertEqual(validate_video_quality("best"), 0)
        self.assertEqual(validate_video_quality(0), 0)
        self.assertEqual(validate_video_quality(1080), 1080)

        self.assertEqual(validate_audio_bitrate("320k"), "320")
        self.assertEqual(validate_audio_bitrate("320kbps"), "320")
        self.assertEqual(validate_audio_bitrate("192"), "192")
        self.assertEqual(validate_audio_bitrate("best"), "0")
        self.assertEqual(validate_audio_bitrate(128), "128")

        self.assertEqual(validate_subtitle_format("srt"), "srt")
        self.assertEqual(validate_subtitle_format(".vtt"), "vtt")
        self.assertEqual(validate_subtitle_format("ass"), "ass")
        self.assertEqual(validate_subtitle_format("lrc"), "lrc")
        self.assertEqual(validate_subtitle_format("unknown"), "srt")

        self.assertEqual(validate_output_format("mp4", "video"), "mp4")
        self.assertEqual(validate_output_format("mkv", "video"), "mkv")
        self.assertEqual(validate_output_format("webm", "video"), "webm")
        self.assertEqual(validate_output_format("mp3", "audio"), "mp3")
        self.assertEqual(validate_output_format("m4a", "audio"), "m4a")
        self.assertEqual(validate_output_format("wav", "audio"), "wav")


class TestApiModels(unittest.TestCase):
    """Tests for Pydantic v2 API models."""

    def test_format_info_model(self):
        fmt = FormatInfo(
            id="137",
            ext="mp4",
            resolution="1920x1080",
            height=1080,
            width=1920,
            fps=30.0,
            filesize=15000000,
            vcodec="avc1.640028",
            acodec="none",
            tbr=2500.0,
            url="https://stream.example.com/video.mp4",
            note="1080p",
        )
        self.assertEqual(fmt.id, "137")
        self.assertEqual(fmt.format_id, "137")
        self.assertTrue(fmt.has_video)
        self.assertFalse(fmt.has_audio)
        self.assertIsNotNone(fmt.filesize_formatted)
        self.assertIn("MB", fmt.filesize_formatted)

    def test_subtitle_track_model(self):
        sub = SubtitleTrack(
            lang="en",
            name="English",
            is_auto=False,
            ext="srt",
            formats=["srt", "vtt"],
            url="https://subs.example.com/en.srt"
        )
        self.assertEqual(sub.lang, "en")
        self.assertFalse(sub.is_auto)
        self.assertIn("en (manual)", sub.display)

    def test_download_request_model(self):
        req = DownloadRequest(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            media_type="video",
            quality="1080",
            output_format="mp4",
            start_time="01:00",
            end_time="02:30",
            write_subtitles=True,
            sub_langs="en,ar"
        )
        self.assertEqual(req.media_type, "video")
        self.assertEqual(req.quality, "1080")
        self.assertEqual(req.output_format, "mp4")
        self.assertEqual(req.sub_format, "srt")

    def test_health_response_model(self):
        health = get_health_status()
        self.assertEqual(health.status, "ok")
        self.assertTrue(health.serverless)
        self.assertGreater(len(health.supported_platforms), 5)
        self.assertEqual(health.version, "2.0.0")

    def test_error_response_model(self):
        err = ErrorResponse(
            detail="Video unavailable",
            error_code="MEDIA_NOT_FOUND"
        )
        self.assertFalse(err.success)
        self.assertEqual(err.error_code, "MEDIA_NOT_FOUND")
        self.assertIn("Video unavailable", err.errors)


class TestApiServiceLayer(unittest.TestCase):
    """Tests for the yt-dlp service functions and custom exceptions."""

    def test_exception_mapping(self):
        e1 = Exception("ERROR: [youtube] 12345: Video unavailable. This video has been removed")
        mapped1 = map_ytdlp_exception(e1, "https://youtube.com/watch?v=12345")
        self.assertIsInstance(mapped1, MediaNotFoundError)
        self.assertEqual(mapped1.status_code, 404)
        self.assertEqual(mapped1.error_code, "MEDIA_NOT_FOUND")

        e2 = Exception("ERROR: [youtube] 12345: Private video. Sign in if you've been granted access")
        mapped2 = map_ytdlp_exception(e2, "https://youtube.com/watch?v=12345")
        self.assertIsInstance(mapped2, PrivateMediaError)
        self.assertEqual(mapped2.status_code, 403)

        e3 = Exception("ERROR: [youtube] 12345: Sign in to confirm your age")
        mapped3 = map_ytdlp_exception(e3, "https://youtube.com/watch?v=12345")
        self.assertIsInstance(mapped3, AgeRestrictedError)
        self.assertEqual(mapped3.status_code, 403)

        e4 = Exception("ERROR: [youtube] 12345: This video is not available in your country")
        mapped4 = map_ytdlp_exception(e4, "https://youtube.com/watch?v=12345")
        self.assertIsInstance(mapped4, GeoBlockedError)
        self.assertEqual(mapped4.status_code, 403)

        e5 = Exception("HTTP Error 429: Too Many Requests")
        mapped5 = map_ytdlp_exception(e5, "https://youtube.com/watch?v=12345")
        self.assertIsInstance(mapped5, RateLimitError)
        self.assertEqual(mapped5.status_code, 429)

        e6 = Exception("ERROR: 'not-a-url' is not a valid URL")
        mapped6 = map_ytdlp_exception(e6, "not-a-url")
        self.assertIsInstance(mapped6, InvalidUrlError)
        self.assertEqual(mapped6.status_code, 400)

    def test_build_serverless_ytdlp_options(self):
        opts = build_serverless_ytdlp_options(extract_flat=True, socket_timeout=20)
        self.assertTrue(opts["skip_download"])
        self.assertTrue(opts["quiet"])
        self.assertTrue(opts["nocheckcertificate"])
        self.assertFalse(opts["cachedir"])
        self.assertEqual(opts["socket_timeout"], 20)
        self.assertEqual(opts["extract_flat"], True)
        self.assertIn("User-Agent", opts["http_headers"])

    def test_subtitles_parsing_from_dict(self):
        mock_info = {
            "subtitles": {
                "en": [{"ext": "vtt", "url": "https://subs.com/en.vtt", "name": "English"}],
                "ar": [{"ext": "srt", "url": "https://subs.com/ar.srt", "name": "Arabic"}],
            },
            "automatic_captions": {
                "es": [{"ext": "vtt", "url": "https://subs.com/es.vtt", "name": "Spanish"}],
            }
        }
        tracks = get_subtitles_info_from_dict(mock_info)
        self.assertEqual(len(tracks), 3)
        langs = {t.lang: t for t in tracks}
        self.assertIn("en", langs)
        self.assertFalse(langs["en"].is_auto)
        self.assertIn("ar", langs)
        self.assertFalse(langs["ar"].is_auto)
        self.assertIn("es", langs)
        self.assertTrue(langs["es"].is_auto)

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_resolve_download_streams_mock(self, mock_raw_extract):
        mock_raw_extract.return_value = {
            "id": "test1234",
            "title": "Test Video Title",
            "uploader": "Test Channel",
            "duration": 300,
            "thumbnail": "https://img.youtube.com/vi/test1234/0.jpg",
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "height": 360,
                    "width": 640,
                    "vcodec": "avc1.42001E",
                    "acodec": "mp4a.40.2",
                    "url": "https://stream.example.com/progressive_360.mp4",
                    "filesize": 10000000,
                },
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "height": 1080,
                    "width": 1920,
                    "vcodec": "avc1.640028",
                    "acodec": "none",
                    "url": "https://stream.example.com/video_1080.mp4",
                    "filesize": 35000000,
                },
                {
                    "format_id": "140",
                    "ext": "m4a",
                    "height": None,
                    "width": None,
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "abr": 128,
                    "url": "https://stream.example.com/audio_140.m4a",
                    "filesize": 5000000,
                }
            ],
            "subtitles": {
                "en": [{"ext": "srt", "url": "https://subs.example.com/en.srt", "name": "English"}]
            }
        }

        # Video request
        req = DownloadRequest(
            url="https://www.youtube.com/watch?v=test1234",
            media_type="video",
            quality="1080",
            output_format="mp4",
            start_time="00:30",
            end_time="01:30",
            write_subtitles=True,
            sub_langs="en"
        )
        stream_res = resolve_download_streams(req)
        self.assertTrue(stream_res.success)
        self.assertEqual(stream_res.title, "Test Video Title")
        self.assertEqual(stream_res.quality, "1080p")
        self.assertIsNotNone(stream_res.direct_url)
        self.assertIsNotNone(stream_res.audio_url)
        self.assertIsNotNone(stream_res.clip_info)
        self.assertEqual(stream_res.clip_info.duration_seconds, 60.0)
        self.assertEqual(len(stream_res.subtitles), 1)

        # Audio request
        req_audio = DownloadRequest(
            url="https://www.youtube.com/watch?v=test1234",
            media_type="audio",
            quality="320",
            output_format="mp3"
        )
        stream_audio_res = resolve_download_streams(req_audio)
        self.assertTrue(stream_audio_res.success)
        self.assertEqual(stream_audio_res.media_type, "audio")
        self.assertEqual(stream_audio_res.direct_url, "https://stream.example.com/audio_140.m4a")

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_get_structured_media_info_mock(self, mock_raw_extract):
        mock_raw_extract.return_value = {
            "id": "abc12345",
            "title": "Sample Mock Title",
            "uploader": "Uploader Name",
            "channel": "Channel Name",
            "duration": 125,
            "thumbnail": "https://img.youtube.com/vi/abc12345/0.jpg",
            "description": "Sample description text",
            "view_count": 45678,
            "tags": ["python", "serverless", "api"],
            "upload_date": "20260101",
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "height": 360,
                    "width": 640,
                    "vcodec": "avc1.42001E",
                    "acodec": "mp4a.40.2",
                    "url": "https://stream.example.com/progressive_360.mp4",
                    "filesize": 10000000,
                },
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "height": 1080,
                    "width": 1920,
                    "vcodec": "avc1.640028",
                    "acodec": "none",
                    "url": "https://stream.example.com/video_1080.mp4",
                    "filesize": 35000000,
                },
                {
                    "format_id": "140",
                    "ext": "m4a",
                    "height": None,
                    "width": None,
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                    "abr": 128,
                    "url": "https://stream.example.com/audio_140.m4a",
                    "filesize": 5000000,
                }
            ],
            "subtitles": {
                "en": [{"ext": "srt", "url": "https://subs.example.com/en.srt", "name": "English"}]
            }
        }

        media_info = get_structured_media_info("https://www.youtube.com/watch?v=abc12345")
        self.assertEqual(media_info.id, "abc12345")
        self.assertEqual(media_info.title, "Sample Mock Title")
        self.assertEqual(media_info.duration_formatted, "02:05")
        self.assertIn(1080, media_info.available_resolutions)
        self.assertIn(360, media_info.available_resolutions)
        self.assertEqual(len(media_info.subtitles), 1)

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_get_formats_breakdown_mock(self, mock_raw_extract):
        mock_raw_extract.return_value = {
            "id": "fmt123",
            "title": "Formats Test",
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "height": 360,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                },
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "height": 1080,
                    "vcodec": "avc1",
                    "acodec": "none",
                },
                {
                    "format_id": "140",
                    "ext": "m4a",
                    "vcodec": "none",
                    "acodec": "mp4a",
                    "abr": 128,
                }
            ]
        }

        breakdown = get_formats_breakdown("https://www.youtube.com/watch?v=fmt123")
        self.assertEqual(breakdown["id"], "fmt123")
        self.assertEqual(len(breakdown["video_formats"]), 1)
        self.assertEqual(len(breakdown["audio_formats"]), 1)
        self.assertEqual(len(breakdown["progressive_formats"]), 1)

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_get_playlist_details_mock(self, mock_raw_extract):
        mock_raw_extract.return_value = {
            "id": "PL1234567890",
            "title": "Test Playlist",
            "uploader": "Test Playlist Creator",
            "_type": "playlist",
            "entries": [
                {
                    "id": "vid1",
                    "title": "Video 1",
                    "duration": 180,
                    "thumbnail": "https://img.youtube.com/vi/vid1/0.jpg",
                    "url": "https://www.youtube.com/watch?v=vid1"
                },
                {
                    "id": "vid2",
                    "title": "Video 2",
                    "duration": 240,
                    "thumbnail": "https://img.youtube.com/vi/vid2/0.jpg",
                    "url": "https://www.youtube.com/watch?v=vid2"
                }
            ]
        }

        pl = get_playlist_details("https://www.youtube.com/playlist?list=PL1234567890", limit=10)
        self.assertEqual(pl.id, "PL1234567890")
        self.assertEqual(pl.title, "Test Playlist")
        self.assertEqual(pl.count, 2)
        self.assertEqual(len(pl.entries), 2)
        self.assertEqual(pl.entries[0].title, "Video 1")
        self.assertEqual(pl.entries[0].duration_formatted, "03:00")
        self.assertEqual(pl.entries[1].duration_formatted, "04:00")

    def test_resolve_download_streams_invalid_clip(self):
        req = DownloadRequest(
            url="https://www.youtube.com/watch?v=test1234",
            start_time="05:00",
            end_time="02:00"
        )
        with self.assertRaises(ValidationError) as ctx:
            resolve_download_streams(req)
        self.assertEqual(ctx.exception.error_code, "VALIDATION_ERROR")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_extract_info_invalid_url(self):
        from api.services.ytdlp_service import extract_info
        with self.assertRaises(InvalidUrlError) as ctx:
            extract_info("not_a_valid_url")
        self.assertEqual(ctx.exception.error_code, "INVALID_URL")
        self.assertEqual(ctx.exception.status_code, 400)

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_extract_info_none_result_raises_not_found(self, mock_raw_extract):
        from api.services.ytdlp_service import extract_info
        mock_raw_extract.return_value = None
        with self.assertRaises(MediaNotFoundError) as ctx:
            extract_info("https://www.youtube.com/watch?v=missing1234")
        self.assertEqual(ctx.exception.error_code, "MEDIA_NOT_FOUND")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_filename_and_folder_sanitization(self):
        from api.validators import sanitize_filename, sanitize_folder_name
        self.assertEqual(sanitize_filename("valid_name"), "valid_name")
        self.assertEqual(sanitize_filename("invalid/file:name*?"), "invalid_file_name")
        self.assertEqual(sanitize_filename(""), "download")
        self.assertEqual(sanitize_folder_name("My: Playlist / Best?"), "My_ Playlist _ Best")
        self.assertEqual(sanitize_folder_name(None), "Media_Download")

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_resolve_playlist_streams(self, mock_raw_extract):
        from api.services.ytdlp_service import resolve_playlist_streams
        playlist_data = {
            "id": "PL_TEST",
            "title": "My Test Playlist",
            "_type": "playlist",
            "entries": [
                {
                    "id": "item1",
                    "title": "First Song",
                    "duration": 120,
                    "url": "https://www.youtube.com/watch?v=item1",
                }
            ]
        }
        item_data = {
            "id": "item1",
            "title": "First Song",
            "duration": 120,
            "formats": [
                {"format_id": "18", "ext": "mp4", "height": 360, "url": "https://cdn.example.com/1.mp4", "vcodec": "avc1", "acodec": "mp4a"}
            ]
        }

        def mock_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            if "item1" in url:
                return item_data
            return playlist_data

        mock_raw_extract.side_effect = mock_side_effect

        res = resolve_playlist_streams("https://www.youtube.com/playlist?list=PL_TEST", media_type="video", quality="360")
        self.assertTrue(res.success)
        self.assertEqual(res.id, "PL_TEST")
        self.assertEqual(res.title, "My Test Playlist")
        self.assertEqual(res.folder_name, "My Test Playlist")
        self.assertEqual(res.total_items, 1)
        self.assertEqual(res.entries[0].filename, "01 - First Song.mp4")
        self.assertEqual(res.entries[0].direct_url, "https://cdn.example.com/1.mp4")

    @patch("api.services.ytdlp_service.raw_extract_info")
    def test_resolve_subtitle_stream(self, mock_raw_extract):
        from api.services.ytdlp_service import resolve_subtitle_stream
        mock_raw_extract.return_value = {
            "id": "vid_sub",
            "title": "Subtitle Video",
            "formats": [],
            "subtitles": {
                "en": [
                    {"ext": "srt", "url": "https://cdn.example.com/sub_en.srt"},
                    {"ext": "vtt", "url": "https://cdn.example.com/sub_en.vtt"}
                ]
            }
        }

        sub = resolve_subtitle_stream("https://www.youtube.com/watch?v=vid_sub", lang="en", sub_format="srt")
        self.assertEqual(sub["lang"], "en")
        self.assertEqual(sub["format"], "srt")
        self.assertEqual(sub["url"], "https://cdn.example.com/sub_en.srt")
        self.assertIn(".srt", sub["filename"])
        self.assertEqual(sub["content_type"], "application/x-subrip")


if __name__ == "__main__":
    unittest.main()
