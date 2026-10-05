"""
index.py - FastAPI Application Entry Point for Downloadyha Vercel API.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import httpx
import yt_dlp.version

from .models import (
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
    PlaylistInfoResponse,
    PlaylistResolvedEntry,
    PlaylistResolveResponse,
    SubtitleTrack,
    UrlValidationRequest,
    UrlValidationResponse,
)
from .services.ytdlp_service import (
    ApiException,
    ExtractionError,
    InvalidUrlError,
    MediaNotFoundError,
    get_playlist_details,
    get_structured_media_info,
    raw_extract_info,
    resolve_download_streams,
    resolve_playlist_streams,
    resolve_subtitle_stream,
)
from .validators import (
    SUPPORTED_PLATFORMS,
    sanitize_filename,
    validate_clip_range,
    validate_media_url,
)

START_TIME = time.time()

app = FastAPI(
    title="Downloadyha API",
    description=(
        "⚡ High-performance Serverless Media & Video Downloader API built on yt-dlp.\n\n"
        "Features:\n"
        "- **Direct Stream & Download URLs**: Multi-resolution video (up to 4K) & high-bitrate MP3/audio streams\n"
        "- **Timestamp Clipping Validation**: Validate and generate precise highlight timestamps\n"
        "- **Subtitles & Transcripts**: Extract official and auto-generated captions across languages\n"
        "- **Playlist Inspection**: Fast playlist extraction and metadata parsing\n"
        "- **Multi-Platform Support**: YouTube, Shorts, TikTok, Instagram, Facebook, Twitter/X, Reddit, and more"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS for cross-origin frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------

@app.exception_handler(ApiException)
async def handle_api_exception(request: Request, exc: ApiException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=exc.message,
            error_code=exc.error_code,
            detail=str(exc),
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors_list = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors_list.append(f"{loc}: {err.get('msg')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            success=False,
            error="Request validation failed",
            error_code="VALIDATION_ERROR",
            detail="; ".join(errors_list),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            success=False,
            error="Internal server error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            detail=str(exc),
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Static Web Dashboard Mount & Root Route
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"], summary="Interactive API Dashboard")
async def root(request: Request):
    """
    Serve the interactive Downloadyha Web UI Dashboard, or JSON info if requested via Accept header.
    """
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return JSONResponse({
            "name": "Downloadyha API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
            "status": "online"
        })

    index_html_path = STATIC_DIR / "index.html"
    if index_html_path.exists():
        with open(index_html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    # Fallback minimal welcome page if static file not mounted
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head><title>Downloadyha API</title></head>
    <body style="font-family:sans-serif;padding:40px;background:#0f172a;color:#fff;">
      <h1>Downloadyha API is Running 🚀</h1>
      <p>Visit <a href="/docs" style="color:#38bdf8;">/docs</a> for interactive OpenAPI documentation.</p>
    </body>
    </html>
    """)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse, tags=["Health"], summary="API Health and Diagnostics")
async def health_check():
    """
    Check API operational health, yt-dlp version, serverless runtime state, and supported platforms.
    """
    return HealthResponse(
        status="ok",
        version="1.0.0",
        app_name="Downloadyha API",
        ytdlp_version=getattr(yt_dlp.version, "__version__", "unknown"),
        serverless=True,
        supported_platforms=SUPPORTED_PLATFORMS,
        uptime_seconds=round(time.time() - START_TIME, 2),
    )


@app.post("/api/validate/url", response_model=UrlValidationResponse, tags=["Validation"], summary="Validate Media URL")
async def validate_url_endpoint(req: UrlValidationRequest):
    """
    Validate URL syntax and recognize the media platform (YouTube, TikTok, Facebook, Instagram, Twitter/X, etc.).
    """
    return validate_media_url(req.url)


@app.post("/api/validate/clip", response_model=ClipValidationResponse, tags=["Validation"], summary="Validate Clipping Timestamps")
async def validate_clip_endpoint(req: ClipValidationRequest):
    """
    Validate start and end timestamps (e.g. '01:30', '90', '00:02:45'), verify start < end, and check against media duration.
    """
    return validate_clip_range(req.start_time, req.end_time, req.media_duration)


@app.post("/api/info", response_model=MediaInfoResponse, tags=["Metadata"], summary="Extract Complete Media Metadata")
async def get_media_info_post(req: MediaInfoRequest):
    """
    Fetch comprehensive media metadata: title, uploader, duration, thumbnail, available qualities, format streams, and subtitle tracks.
    """
    return get_structured_media_info(req.url, include_subtitles=req.include_subtitles)


@app.get("/api/info", response_model=MediaInfoResponse, tags=["Metadata"], summary="Extract Media Metadata (GET)")
async def get_media_info_get(
    url: str = Query(..., description="Media video or playlist URL"),
    include_subtitles: bool = Query(True, description="Whether to include subtitle tracks")
):
    """
    GET shortcut to extract media metadata by providing the URL as a query parameter.
    """
    return get_structured_media_info(url, include_subtitles=include_subtitles)


@app.post("/api/formats", tags=["Metadata"], summary="Get Available Resolutions and Formats")
async def get_formats_endpoint(req: MediaInfoRequest):
    """
    Extract available video resolutions (4K, 1440p, 1080p, 720p, 480p, 360p) and detailed stream formats.
    """
    info = get_structured_media_info(req.url, include_subtitles=False)
    return {
        "success": True,
        "url": req.url,
        "title": info.title,
        "available_resolutions": info.available_resolutions,
        "available_audio_qualities": info.available_audio_qualities,
        "formats_count": len(info.formats),
        "formats": info.formats,
    }


@app.post("/api/subtitles", tags=["Subtitles"], summary="Get Available Subtitle and Caption Tracks")
async def get_subtitles_endpoint(req: MediaInfoRequest):
    """
    List all official subtitles and auto-generated captions with language codes and formats (SRT, VTT, ASS, LRC).
    """
    info = get_structured_media_info(req.url, include_subtitles=True)
    return {
        "success": True,
        "url": req.url,
        "title": info.title,
        "subtitles_count": len(info.subtitles),
        "subtitles": info.subtitles,
    }


@app.post("/api/resolve", response_model=DownloadStreamResponse, tags=["Stream & Download"], summary="Resolve Direct Stream & Download URLs")
async def resolve_stream_endpoint(req: DownloadRequest):
    """
    Resolve direct streaming / download URLs with quality selection, audio extraction, timestamp clipping, and subtitles.
    """
    return resolve_download_streams(req)


@app.post("/api/download", response_model=DownloadStreamResponse, tags=["Stream & Download"], summary="Download / Stream Resolver Alias")
async def download_alias_endpoint(req: DownloadRequest):
    """
    Convenient alias for `/api/resolve`. Resolves media stream and download URLs.
    """
    return resolve_download_streams(req)


@app.post("/api/playlist", response_model=PlaylistInfoResponse, tags=["Playlists"], summary="Inspect Playlist Details")
async def playlist_details_endpoint(
    req: MediaInfoRequest,
    limit: int = Query(50, ge=1, le=200, description="Max entries to return")
):
    """
    Inspect playlist items, total video count, and individual entry details.
    """
    return get_playlist_details(req.url, limit=limit)


@app.get("/api/playlist", response_model=PlaylistInfoResponse, tags=["Playlists"], summary="Inspect Playlist Details (GET)")
async def playlist_details_get(
    url: str = Query(..., description="Playlist URL"),
    limit: int = Query(50, ge=1, le=200, description="Max entries to return")
):
    """
    GET shortcut to inspect playlist items and video entries.
    """
    return get_playlist_details(url, limit=limit)


@app.post("/api/playlist/resolve", response_model=PlaylistResolveResponse, tags=["Playlists"], summary="Resolve All Streams in Playlist")
async def playlist_resolve_post(
    req: MediaInfoRequest,
    media_type: str = Query("video", description="'video' or 'audio'"),
    quality: str = Query("best", description="Quality height (1080, 720) or audio bitrate (320, 192, best)"),
    output_format: Optional[str] = Query(None, description="Container format ('mp4', 'mp3', etc.)"),
    limit: int = Query(50, ge=1, le=100, description="Max playlist entries to resolve")
):
    """
    Batch-resolve direct streaming and download URLs for playlist entries with indexed filenames (01 - Title.mp4).
    """
    return resolve_playlist_streams(
        url=req.url,
        media_type=media_type,
        quality=quality,
        output_format=output_format,
        limit=limit
    )


@app.get("/api/playlist/resolve", response_model=PlaylistResolveResponse, tags=["Playlists"], summary="Resolve All Streams in Playlist (GET)")
async def playlist_resolve_get(
    url: str = Query(..., description="Playlist URL"),
    media_type: str = Query("video", description="'video' or 'audio'"),
    quality: str = Query("best", description="Quality height or audio bitrate"),
    output_format: Optional[str] = Query(None, description="Container format ('mp4', 'mp3', etc.)"),
    limit: int = Query(50, ge=1, le=100, description="Max playlist entries to resolve")
):
    """
    GET shortcut to batch-resolve direct streams for all items in a playlist.
    """
    return resolve_playlist_streams(
        url=url,
        media_type=media_type,
        quality=quality,
        output_format=output_format,
        limit=limit
    )


@app.get("/api/stream", tags=["Stream & Download"], summary="Direct Media Stream / Playback Proxy")
async def stream_media_endpoint(
    url: str = Query(..., description="Media URL"),
    media_type: str = Query("video", description="'video' or 'audio'"),
    quality: str = Query("best", description="Quality resolution or bitrate"),
    output_format: Optional[str] = Query(None, description="Container format (mp4, mp3, etc.)"),
    start_time: Optional[str] = Query(None, description="Optional start timestamp (MM:SS or seconds)"),
    end_time: Optional[str] = Query(None, description="Optional end timestamp (MM:SS or seconds)"),
    redirect: bool = Query(False, description="Whether to 307 redirect directly to CDN stream URL")
):
    """
    Directly stream media audio or video binary content for browser playback or client streaming.
    """
    req = DownloadRequest(
        url=url,
        media_type=media_type,
        quality=quality,
        output_format=output_format,
        start_time=start_time,
        end_time=end_time,
    )
    res = resolve_download_streams(req)
    if not res.direct_url:
        raise HTTPException(status_code=404, detail="No direct streaming URL found for this media.")

    if redirect:
        return RedirectResponse(url=res.direct_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    media_ext = res.format or ("mp3" if media_type == "audio" else "mp4")
    content_type = f"audio/{media_ext}" if media_type == "audio" else f"video/{media_ext}"
    safe_filename = res.filename or f"{sanitize_filename(res.title)}.{media_ext}"

    async def stream_generator():
        hdrs = dict(res.headers or {})
        hdrs.pop("Host", None)
        hdrs.pop("host", None)
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            async with client.stream("GET", res.direct_url, headers=hdrs) as upstream:
                async for chunk in upstream.aiter_bytes(chunk_size=65536):
                    yield chunk

    response_headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'inline; filename="{safe_filename}"',
    }
    if res.filesize:
        response_headers["Content-Length"] = str(res.filesize)

    return StreamingResponse(
        stream_generator(),
        media_type=content_type,
        headers=response_headers,
    )


@app.get("/api/download/file", tags=["Stream & Download"], summary="Direct Media File Download")
async def download_file_endpoint(
    url: str = Query(..., description="Media URL to download"),
    media_type: str = Query("video", description="'video' or 'audio'"),
    quality: str = Query("best", description="Quality resolution or bitrate"),
    output_format: Optional[str] = Query(None, description="Container format (mp4, mp3, etc.)"),
    start_time: Optional[str] = Query(None, description="Optional start timestamp"),
    end_time: Optional[str] = Query(None, description="Optional end timestamp"),
    redirect: bool = Query(False, description="Redirect to CDN directly instead of proxy streaming")
):
    """
    Download media file directly with 'Content-Disposition: attachment' for saving straight to local disk.
    """
    req = DownloadRequest(
        url=url,
        media_type=media_type,
        quality=quality,
        output_format=output_format,
        start_time=start_time,
        end_time=end_time,
    )
    res = resolve_download_streams(req)
    if not res.direct_url:
        raise HTTPException(status_code=404, detail="No direct download stream found for this media.")

    if redirect:
        return RedirectResponse(url=res.direct_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    media_ext = res.format or ("mp3" if media_type == "audio" else "mp4")
    content_type = f"audio/{media_ext}" if media_type == "audio" else f"video/{media_ext}"
    safe_filename = res.filename or f"{sanitize_filename(res.title)}.{media_ext}"

    async def stream_generator():
        hdrs = dict(res.headers or {})
        hdrs.pop("Host", None)
        hdrs.pop("host", None)
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            async with client.stream("GET", res.direct_url, headers=hdrs) as upstream:
                async for chunk in upstream.aiter_bytes(chunk_size=65536):
                    yield chunk

    response_headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'attachment; filename="{safe_filename}"',
    }
    if res.filesize:
        response_headers["Content-Length"] = str(res.filesize)

    return StreamingResponse(
        stream_generator(),
        media_type=content_type,
        headers=response_headers,
    )


@app.get("/api/subtitles/download", tags=["Subtitles"], summary="Download Subtitle File Directly")
async def download_subtitle_file_endpoint(
    url: str = Query(..., description="Video URL"),
    lang: str = Query("en", description="Subtitle language code (e.g., 'en', 'ar', 'es')"),
    sub_format: str = Query("srt", description="Subtitle format ('srt', 'vtt', 'ass', 'lrc')"),
    is_auto: bool = Query(False, description="Whether to fetch auto-generated caption")
):
    """
    Download subtitle file directly (.srt, .vtt, .ass, or .lrc) with attachment headers.
    """
    sub_info = resolve_subtitle_stream(url=url, lang=lang, sub_format=sub_format, is_auto=is_auto)
    sub_url = sub_info["url"]
    filename = sub_info["filename"]
    content_type = sub_info["content_type"]

    async def sub_generator():
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            async with client.stream("GET", sub_url) as upstream:
                async for chunk in upstream.aiter_bytes():
                    yield chunk

    return StreamingResponse(
        sub_generator(),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
