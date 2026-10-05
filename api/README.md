# Downloadyha API (Vercel Serverless Edition)

High-performance, stateless serverless REST API and modern web dashboard for video and audio metadata extraction, stream resolution, subtitle parsing, and playlist inspection built with **FastAPI** and **yt-dlp**.

Deployable on **Vercel**, **AWS Lambda**, **Render**, or **Docker** with zero external binary dependencies required.

---

## 🌟 Key Highlights

- ⚡ **Stateless Serverless Ready**: Optimized for Vercel Python Functions without requiring local disk writes or persistent FFmpeg background processes.
- 🎬 **Direct Stream CDN Resolution**: Extracts direct signed streaming URLs for video (up to 4K / 1080p / 720p) and audio streams (MP3/M4A 320k) for immediate browser playback or client-side downloading.
- ✂️ **Timestamp Clipping Validation**: Full timestamp parsing (`MM:SS`, `HH:MM:SS`, or raw seconds) with duration boundaries validation.
- 📝 **Subtitles & Transcripts**: Extract official and auto-generated subtitle tracks with multi-language format conversions (`SRT`, `VTT`, `ASS`, `LRC`).
- 📑 **Playlist Inspection**: Fast batch playlist retrieval and entry indexing.
- 🌐 **Multi-Platform Support**: YouTube, Shorts, TikTok, Instagram Reels, Facebook Video, Twitter/X, Reddit, SoundCloud, and generic video links.
- 🎨 **Built-In Glassmorphism Dashboard**: Interactive single-page dashboard served directly from the root path (`/`).

---

## 🚀 Quick Deployment Guide

### Option 1: 1-Click Deploy via Vercel Web Dashboard

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

1. Fork or push this repository to your GitHub account.
2. In the [Vercel Dashboard](https://vercel.com/new), select **Import Project** and choose your repository.
3. Keep the Root Directory as `./` (or `./api` if deploying API subtree only).
4. Vercel will automatically detect `vercel.json` and deploy your FastAPI application to serverless edge functions.

---

### Option 2: Deploy using Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Login and Deploy**:
   ```bash
   # From the project root
   vercel login
   vercel
   ```

3. **Deploy to Production**:
   ```bash
   vercel --prod
   ```

---

### Option 3: Local Development Server

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

2. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI server with Uvicorn**:
   ```bash
   uvicorn api.index:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Open your browser**:
   - Interactive Dashboard: `http://localhost:8000/`
   - Interactive Swagger Docs: `http://localhost:8000/docs`
   - ReDoc OpenAPI Specs: `http://localhost:8000/redoc`

---

## 🏗️ Serverless Architecture & Considerations

### 1. Direct Stream URLs vs. Heavy Binary Transcoding
In traditional CLI or desktop environments (like Downloadyha CLI), FFmpeg runs locally to download separate video and audio streams and merge them into a single `.mp4` file.

On serverless platforms (such as Vercel Serverless Functions with a 10s–60s maximum execution budget and read-only ephemeral storage):
- The API resolves and returns **direct CDN stream URLs** (`video_stream.url`, `audio_stream.url`, and `direct_download_url`).
- Clients (web browsers, mobile apps, curl, or download managers) stream or download the media directly from the host CDN at maximum speed without routing heavy binary payloads through the serverless function.
- This prevents timeout bottlenecks, reduces egress bandwidth costs, and scales indefinitely.

### 2. Execution Timeout Handling
- The extraction engine uses optimized `socket_timeout=15`, stateless in-memory processing (`skip_download=True`), and disabled certificate checks for lightning-fast responses (~500ms–1500ms).
- For playlists with hundreds of entries, use the `limit` query parameter (default 50) to maintain low latency.

---

## 📖 Complete API Reference

### 1. Health & Diagnostics
**Endpoint:** `GET /api/health`

Checks the operational status of the API, runtime details, and yt-dlp core version.

#### Response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "app_name": "Downloadyha API",
  "ytdlp_version": "2026.03.01",
  "serverless": true,
  "supported_platforms": [
    "YouTube",
    "YouTube Shorts",
    "TikTok",
    "Instagram",
    "Facebook",
    "Twitter/X",
    "Reddit",
    "SoundCloud"
  ],
  "uptime_seconds": 124.5,
  "timestamp": 1728100000.0
}
```

#### Examples:
- **cURL:**
  ```bash
  curl -X GET "https://your-domain.vercel.app/api/health"
  ```
- **Python (requests):**
  ```python
  import requests
  res = requests.get("https://your-domain.vercel.app/api/health")
  print(res.json())
  ```
- **JavaScript (fetch):**
  ```javascript
  const res = await fetch("https://your-domain.vercel.app/api/health");
  const data = await res.json();
  console.log(data);
  ```

---

### 2. Extract Media Metadata
**Endpoint:** `POST /api/info` or `GET /api/info?url={url}`

Extracts complete metadata for a video or audio URL including title, channel, duration, thumbnail, available video resolutions, format streams, and subtitle tracks.

#### Request Body (`POST /api/info`):
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "include_subtitles": true,
  "extract_flat": false
}
```

#### Response (`200 OK`):
```json
{
  "success": true,
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "id": "dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
  "uploader": "Rick Astley",
  "channel": "Rick Astley",
  "duration": 213.0,
  "duration_formatted": "03:33",
  "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  "view_count": 1500000000,
  "is_playlist": false,
  "available_resolutions": [1080, 720, 480, 360, 240, 144],
  "available_audio_qualities": ["best", "320", "192", "128"],
  "formats": [
    {
      "format_id": "137",
      "ext": "mp4",
      "resolution": "1920x1080",
      "height": 1080,
      "width": 1920,
      "filesize_formatted": "45.2 MB",
      "has_video": true,
      "has_audio": false
    }
  ],
  "subtitles": [
    {
      "lang": "en",
      "name": "English",
      "is_auto": false,
      "formats": ["srt", "vtt", "ass"]
    }
  ]
}
```

#### Examples:
- **cURL:**
  ```bash
  curl -X POST "https://your-domain.vercel.app/api/info" \
    -H "Content-Type: application/json" \
    -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","include_subtitles":true}'
  ```
- **Python (requests):**
  ```python
  import requests

  payload = {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "include_subtitles": True
  }
  res = requests.post("https://your-domain.vercel.app/api/info", json=payload)
  print(res.json())
  ```
- **JavaScript (fetch):**
  ```javascript
  const res = await fetch("https://your-domain.vercel.app/api/info", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      include_subtitles: true
    })
  });
  const data = await res.json();
  console.log(data);
  ```

---

### 3. Extract Formats & Resolutions
**Endpoint:** `POST /api/formats`

Extracts all available video resolutions (4K, 1440p, 1080p, 720p, etc.) and stream formats without retrieving extra metadata.

#### Request Body:
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

#### Response (`200 OK`):
```json
{
  "success": true,
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "available_resolutions": [1080, 720, 480, 360],
  "available_audio_qualities": ["best", "320", "192", "128"],
  "formats_count": 18,
  "formats": [...]
}
```

#### Examples:
- **cURL:**
  ```bash
  curl -X POST "https://your-domain.vercel.app/api/formats" \
    -H "Content-Type: application/json" \
    -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
  ```
- **Python (requests):**
  ```python
  import requests
  res = requests.post("https://your-domain.vercel.app/api/formats", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
  print(res.json())
  ```

---

### 4. Extract Subtitles & Captions
**Endpoint:** `POST /api/subtitles`

Retrieves all official and auto-generated subtitle tracks with available format downloads (SRT, VTT, ASS, LRC).

#### Request Body:
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

#### Response (`200 OK`):
```json
{
  "success": true,
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "subtitles_count": 12,
  "subtitles": [
    {
      "lang": "en",
      "name": "English (United States)",
      "is_auto": false,
      "formats": ["srt", "vtt", "ass"],
      "display": "en (manual) [ass, srt, vtt]"
    },
    {
      "lang": "es",
      "name": "Spanish",
      "is_auto": true,
      "formats": ["vtt", "srt"],
      "display": "es (auto) [srt, vtt]"
    }
  ]
}
```

#### Examples:
- **cURL:**
  ```bash
  curl -X POST "https://your-domain.vercel.app/api/subtitles" \
    -H "Content-Type: application/json" \
    -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
  ```
- **Python (requests):**
  ```python
  import requests
  res = requests.post("https://your-domain.vercel.app/api/subtitles", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
  print(res.json())
  ```

---

### 5. Resolve Direct Stream & Download URLs
**Endpoint:** `POST /api/resolve` (or `POST /api/download`)

Resolves direct CDN streaming URLs for requested resolution, audio bitrate, optional timestamp clipping, and subtitles.

#### Request Body:
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "media_type": "video",
  "quality": "1080",
  "output_format": "mp4",
  "start_time": "00:30",
  "end_time": "02:00",
  "write_subtitles": true,
  "sub_langs": "en",
  "sub_format": "srt"
}
```

#### Response (`200 OK`):
```json
{
  "success": true,
  "message": "Stream resolved successfully",
  "title": "Rick Astley - Never Gonna Give You Up",
  "id": "dQw4w9WgXcQ",
  "uploader": "Rick Astley",
  "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  "media_type": "video",
  "requested_quality": "1080",
  "selected_format": "137",
  "duration": 213.0,
  "duration_formatted": "03:33",
  "direct_download_url": "https://rr2---sn-xxxx.googlevideo.com/videoplayback?expire=...",
  "video_stream": {
    "url": "https://rr2---sn-xxxx.googlevideo.com/videoplayback?expire=...",
    "format_id": "137",
    "ext": "mp4",
    "resolution": "1920x1080",
    "height": 1080,
    "width": 1920,
    "filesize_formatted": "45.2 MB"
  },
  "audio_stream": {
    "url": "https://rr2---sn-xxxx.googlevideo.com/videoplayback?expire=...",
    "format_id": "140",
    "ext": "m4a",
    "filesize_formatted": "3.5 MB"
  },
  "clip_info": {
    "start_time": "00:30",
    "end_time": "02:00",
    "start_seconds": 30.0,
    "end_seconds": 120.0,
    "clip_duration_seconds": 90.0,
    "clip_duration_formatted": "01:30"
  },
  "subtitles": [...]
}
```

#### Examples:
- **cURL:**
  ```bash
  curl -X POST "https://your-domain.vercel.app/api/resolve" \
    -H "Content-Type: application/json" \
    -d '{
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "media_type": "video",
      "quality": "1080",
      "output_format": "mp4"
    }'
  ```
- **Python (requests):**
  ```python
  import requests

  payload = {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "media_type": "video",
      "quality": "1080",
      "start_time": "00:15",
      "end_time": "01:00"
  }
  res = requests.post("https://your-domain.vercel.app/api/resolve", json=payload)
  data = res.json()
  print("Direct Stream URL:", data["direct_download_url"])
  ```
- **JavaScript (fetch):**
  ```javascript
  const res = await fetch("https://your-domain.vercel.app/api/resolve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      media_type: "audio",
      quality: "320"
    })
  });
  const data = await res.json();
  console.log("Audio Stream URL:", data.direct_download_url);
  ```

---

### 6. Direct Media Binary Streaming & Download Proxies

The API provides direct streaming and attachment download endpoints with zero client-side assembly required:

#### A. Direct Media Playback Proxy / Stream
**Endpoint:** `GET /api/stream`

Stream video or audio bytes directly with `Content-Disposition: inline` for browser HTML5 players or proxy client playback.

```bash
# Direct stream proxy
curl -L "https://your-domain.vercel.app/api/stream?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=720&media_type=video"

# Redirect (307) directly to high-speed CDN URL
curl -I "https://your-domain.vercel.app/api/stream?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&redirect=true"
```

#### B. Direct File Attachment Download
**Endpoint:** `GET /api/download/file`

Download video or audio directly with sanitized `Content-Disposition: attachment; filename="{filename}"` header for one-click saving to disk.

```bash
# Save directly as Rick_Astley_Never_Gonna_Give_You_Up.mp4
curl -OJ "https://your-domain.vercel.app/api/download/file?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=1080"

# Download MP3 audio directly
curl -OJ "https://your-domain.vercel.app/api/download/file?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&media_type=audio&quality=320"
```

#### C. Direct Subtitle Track Download
**Endpoint:** `GET /api/subtitles/download`

Download subtitle and caption files directly in `.srt`, `.vtt`, `.ass`, or `.lrc` formats.

```bash
# Download English SRT subtitle
curl -OJ "https://your-domain.vercel.app/api/subtitles/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&lang=en&sub_format=srt"

# Download Arabic Auto-generated Caption
curl -OJ "https://your-domain.vercel.app/api/subtitles/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&lang=ar&sub_format=vtt&is_auto=true"
```

---

### 7. Playlist Inspection & Batch Stream Resolution

#### A. Inspect Playlist Details
**Endpoint:** `POST /api/playlist` or `GET /api/playlist?url={url}&limit=50`

Inspects playlist entries, returns the playlist title, total items, and metadata for each entry.

#### B. Batch Resolve Playlist Streams
**Endpoint:** `POST /api/playlist/resolve` or `GET /api/playlist/resolve?url={url}&media_type=video&quality=1080&limit=50`

Batch-resolves direct streaming and download URLs for all entries in a playlist with CLI/Desktop matching indexed file naming conventions (`01 - Title.mp4`, `02 - Title.mp4`).

#### Request Body (`POST /api/playlist/resolve`):
```json
{
  "url": "https://www.youtube.com/playlist?list=PLrEnWoR732-BHrPp_QLTQhGWcyg67PCZO"
}
```

#### Response (`200 OK`):
```json
{
  "success": true,
  "id": "PLrEnWoR732-BHrPp_QLTQhGWcyg67PCZO",
  "title": "Favorite Music Tracks",
  "uploader": "Example Channel",
  "folder_name": "Favorite Music Tracks",
  "total_items": 25,
  "resolved_items": 25,
  "media_type": "video",
  "entries": [
    {
      "id": "dQw4w9WgXcQ",
      "playlist_index": 1,
      "title": "Rick Astley - Never Gonna Give You Up",
      "filename": "01 - Rick Astley - Never Gonna Give You Up.mp4",
      "duration": 213.0,
      "duration_formatted": "03:33",
      "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "direct_download_url": "https://rr2---sn-xxxx.googlevideo.com/videoplayback?expire=...",
      "quality": "1080p",
      "format": "mp4"
    }
  ]
}
```

---

### 8. Validate Media URL
**Endpoint:** `POST /api/validate/url`

Validates media URL syntax and identifies the hosting platform.

#### Request Body:
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

#### Response (`200 OK`):
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "is_valid": true,
  "platform": "YouTube",
  "is_playlist": false,
  "normalized_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "error_message": null
}
```

---

### 9. Validate Clipping Timestamps
**Endpoint:** `POST /api/validate/clip`

Validates start and end timestamps (e.g. `"01:30"`, `"90"`, `"00:02:45"`), ensures `start < end`, and verifies range against media duration.

#### Request Body:
```json
{
  "start_time": "01:30",
  "end_time": "03:45",
  "media_duration": 300
}
```

#### Response (`200 OK`):
```json
{
  "is_valid": true,
  "start_seconds": 90.0,
  "end_seconds": 225.0,
  "start_formatted": "01:30",
  "end_formatted": "03:45",
  "clip_duration_seconds": 135.0,
  "clip_duration_formatted": "02:15",
  "error_message": null
}
```

#### Examples:
- **cURL:**
  ```bash
  curl -X POST "https://your-domain.vercel.app/api/validate/clip" \
    -H "Content-Type: application/json" \
    -d '{"start_time":"00:45","end_time":"02:30","media_duration":180}'
  ```
- **Python (requests):**
  ```python
  import requests

  payload = {
      "start_time": "00:45",
      "end_time": "02:30",
      "media_duration": 180
  }
  res = requests.post("https://your-domain.vercel.app/api/validate/clip", json=payload)
  print(res.json())
  ```

---

## 🔒 Security & CORS Headers

The API is preconfigured with production-ready security headers in `vercel.json`:
- **CORS Support**: `Access-Control-Allow-Origin: *` for direct frontend web integration.
- **Content Security**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`.
- **Edge Caching**: Configured cache-control on static and health metadata endpoints.

---

## 📄 License

This project is licensed under the **MIT License**.
