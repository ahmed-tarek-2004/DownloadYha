# 🎬 Downloadyha

A fast, modern, and beautiful media downloader ecosystem available in **Desktop GUI**, **Interactive Terminal CLI**, and **Serverless REST API & Web Dashboard** for **Videos (up to 8K/4K/1080p)**, **Audio (MP3)**, **Partial Clips (Highlights)**, **Subtitles & Transcripts**, and **Full Playlists**.

Zero configuration required — includes automated self-repairing FFmpeg and Deno helper runtimes with SHA-256 verification.

---

## 🌟 Key Features

- 🎬 **Smart Codec & Container Prioritization**:
  - **$\le$ 1080p (Full HD / Standard)**: Strictly prioritizes native H.264 (`avc`) video and AAC (`m4a`) audio directly from YouTube merged into universal `.mp4` containers for 100% compatibility across all media players, TVs, and mobile devices.
  - **Ultra-HD (1440p, 4K, 8K)**: Automatically acquires optimal high-efficiency VP9/AV1 streams in `.mkv` or `.webm` containers without CPU-intensive transcoding.
  - **Zero-Transcoding Stream Copy**: Instant lossless container muxing via FFmpeg (`-c copy`) with minimal CPU overhead.
- ✂️ **Partial Video & Audio Clipping**: Download only the exact section you need by specifying Start and End times (`01:30`, `90`, `00:02:45`, `01:15.5`). Save bandwidth and disk space without downloading full multi-hour videos!
- 📝 **Full Subtitle & Transcript Support + Subtitle-Only Mode**:
  - Download official subtitle tracks or YouTube auto-generated captions.
  - Multi-language support with human-readable language names (e.g. `en (English)`, `ar (Arabic)`).
  - Embed subtitles directly into video containers (MP4, MKV, WebM).
  - Format conversion between **SRT**, **VTT**, **ASS**, and **LRC**.
  - **Subtitles-Only Mode**: Download transcripts and captions in seconds without downloading video or audio streams.
- 🎵 **High-Fidelity Audio MP3 Extractor**: One-click audio extraction with custom bitrate presets (320 kbps CBR High, 192 kbps CBR Standard, 128 kbps CBR Compact, or Best VBR ~256–320 kbps).
- 📑 **Full Playlist & Mix Batch Downloads**:
  - Batch download entire video, audio, or subtitle playlists.
  - Automatic creation of organized subfolders with clean indexed filenames (`01 - Title.mp4`, `02 - Title.mp4`).
  - Intelligent detection of single videos embedded in playlists or mixes, offering a prompt to download only the single item or the entire batch.
  - Per-item error resilience (`ignoreerrors`) so individual unavailable videos don't stop the batch.
- 🎨 **Modern Desktop GUI (CustomTkinter)**:
  - Sleek Light Grey & Crimson design aesthetic with support for **Light Mode**, **Dark Mode**, and **System Default**.
  - Persistent sidebar navigation with 3 dedicated views: **Downloader**, **Download Queue & History**, and **Settings**.
  - Real-time video/playlist metadata inspection (Title, Channel, Duration, View Count, available resolutions up to 4K).
  - 100% Inline error feedback with one-click retry (no intrusive pop-up dialogs).
  - Seamless download cancellation with immediate socket release and UI unlock.
  - Integrated **System Health** dashboard (one-click updater and dependency repair).
- ⚡ **Interactive Terminal CLI**: Color-coded step-by-step wizard, real-time progress indicators (percentage, size, speed, ETA), summary cards, and non-interactive scripting flags.
- 🌐 **Serverless REST API & Web Dashboard**: FastAPI serverless backend (`api/`) deployable on Vercel, AWS Lambda, Render, or Docker with interactive Swagger docs (`/docs`), ReDoc (`/redoc`), direct CDN stream URL resolution, and a built-in single-page web dashboard.
- 📦 **Zero-Config Standalone Runtimes**: Bundled and auto-managed essential FFmpeg (~40MB vs ~150MB) and Deno helper binaries with SHA-256 checksum verification.
- 🌐 **Multi-Platform Compatibility**: Supports YouTube, YouTube Shorts, TikTok, Instagram Reels, Facebook Video, Twitter/X, SoundCloud, Reddit, and direct video links.
- 🔒 **Privacy-First**: No telemetry, no analytics, no third-party tracking. All media streams directly from source CDNs to your local machine.

---

## 🖥️ Desktop GUI — Installation & Overview

The **Downloadyha Desktop GUI** delivers a rich graphical experience with real-time metadata inspection, dynamic quality detection (up to 4K/8K), audio extraction, partial segment clipping, download history, and theme customization.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🎬 Downloadyha Desktop GUI                                  [—] [口] [X]    │
├───────────────────┬─────────────────────────────────────────────────────────┤
│ 🎬 Downloadyha    │ 🔗 Paste Video or Playlist URL                          │
│ Zero-Config v1.0.0│ [ https://www.youtube.com/watch?v=...     ] [🔍 Fetch] │
│                   ├─────────────────────────────────────────────────────────┤
│ ⬇️  Downloader     │ 🎬 Video Information                                    │
│ 📋  Download Queue│ Title: Rick Astley - Never Gonna Give You Up            │
│ ⚙️  Settings       │ Channel: Rick Astley • ⏱ 03:33 • ⚡ Max Quality: 1080p   │
│                   ├─────────────────────────────────────────────────────────┤
│ THEME MODE        │ ⚡ Format: [🎥 Video] [🎵 Audio] [📝 Subtitles]         │
│ [☀️ Light][🌙 Dark]│ 🎯 Quality: [1080p (Full HD)               ▼]           │
│                   │ [✓] ✂️ Download specific section (clip)                  │
│ SYSTEM HEALTH     │     Start: [00:30     ]     End: [02:00     ]           │
│ ● Ready           │ [✓] 📝 Subtitles & Transcripts                           │
│ [🔄 Check Updates]│     Language: [en (English) ▼]  Format: [srt ▼]         │
│ [🛠️ Repair App   ]│     [✓] Auto-captions   [ ] Embed in video              │
│                   ├─────────────────────────────────────────────────────────┤
│ © 2026 Ahmed Tarek│ 💾 Save Location: [C:\Users\...\Downloads   ] [📁 Browse]│
│                   ├─────────────────────────────────────────────────────────┤
│                   │ [⬇ START DOWNLOAD]     [❌ Cancel]     [📁 Open Folder] │
└───────────────────┴─────────────────────────────────────────────────────────┘
```

### Option 1: Standalone App (No Python Required — Recommended)

Download the pre-built standalone package for your operating system:

| Platform | Download | Instructions |
|---|---|---|
| **Windows 10/11 (64-bit)** | **[⬇️ Download Windows GUI (ZIP)](https://github.com/ahmed-tarek-2004/DownloadYha/releases/latest/download/downloadyha-gui-windows.zip)** | Extract ZIP and double-click `downloadyha-gui.exe` |
| **Linux (x86_64)** | **[⬇️ Download Linux GUI (tar.gz)](https://github.com/ahmed-tarek-2004/DownloadYha/releases/latest/download/downloadyha-gui-linux-x86_64.tar.gz)** | Extract archive and run `./downloadyha-gui` |

#### 3-Step Windows Quick Start:
1. **Download & Extract** `downloadyha-gui-windows.zip` to a folder (e.g. `Downloads` or `C:\Program Files\DownloadyhaGUI`).
2. **Double-click** `downloadyha-gui.exe` to launch.
3. **Paste any YouTube URL** — the app automatically fetches video details (Title, Channel, Duration) and populates available resolutions!

---

### Option 2: Install via Python & Pip

If you have Python 3.10+ installed:

```bash
pip install "downloadyha[gui]"
```

Launch the GUI anytime with:

```bash
downloadyha-gui
```
*(or run `downloadyha gui`)*

*(On Linux systems without Tkinter: `sudo apt install python3-tk`)*

📖 **[Complete GUI User Guide →](GUI_USER_GUIDE.md)** | **[GUI Download Documentation →](GUI_DOWNLOAD.md)** | **[GUI Development Guide →](GUI_DEVELOPMENT.md)**

---

## ⚡ Interactive Terminal CLI — Installation & Quick Start

For terminal power-users and server workflows, Downloadyha offers an interactive CLI with color-coded steps, live progress bars, clipping support, and batch playlist handling.

### One-Line Install

#### Windows (PowerShell):
```powershell
irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex
```

#### Windows (Command Prompt / CMD):
```cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex"
```

#### Linux & macOS:
```bash
curl -fsSL https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.sh | bash
```

### Launch CLI:

```bash
downloadyha
```

---

## ✂️ Partial Video & Audio Clipping (Highlights)

Download only the exact segment you need without downloading the whole video.

### Supported Timestamp Formats
- `MM:SS` (e.g. `01:30` for 1 min 30 sec)
- `HH:MM:SS` (e.g. `01:15:30` for 1 hr 15 min 30 sec)
- Total seconds (e.g. `90`, `90s`, `120.5`)
- Fractional / decimal timestamps (e.g. `01:15.5`)

### CLI Clipping Examples

```bash
# Download a 2-minute video clip (01:30 to 03:30) in 1080p Full HD
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -s 01:30 -e 03:30 -f video -q 1080

# Extract a 45-second audio clip (start to 00:45) as 320 kbps MP3
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -s 00:00 -e 00:45 -f audio -q 320

# Download from minute 10:00 to the end of the video
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -s 10:00 -f video -q 720

# Save clip to a custom destination directory
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -s 00:30 -e 01:45 -d "C:\Users\User\Videos\Clips"
```

---

## 📝 Subtitle & Transcript Support

Downloadyha provides flexible subtitle downloading, format conversion, embedding, and subtitle-only extraction:

### Subtitle Capabilities

| Capability | Flag / Option | Description |
|---|---|---|
| **Write Subtitles** | `--write-subs` | Download official subtitle files |
| **Write Auto-Captions** | `--write-auto-subs` | Download YouTube auto-generated captions |
| **Subtitle-Only Mode** | `-f subtitles` | Download transcripts/subtitles only (skips heavy media downloads) |
| **Embed Subtitles** | `--embed-subs` | Embed subtitles directly into MP4/MKV video container |
| **Select Languages** | `--sub-langs "en,ar"` | Download specific languages or `all` |
| **Format Selection** | `--sub-format srt` | Output container format: `srt`, `vtt`, `ass`, `lrc` |
| **Format Conversion** | `--convert-subs vtt` | Automatically convert extracted subtitles to another format |

### CLI Subtitle Examples

```bash
# 1. Download SUBTITLES ONLY (Fast transcript download, no video/audio bytes)
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f subtitles --sub-langs en --sub-format srt

# 2. Download video with official English subtitles (SRT)
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f video -q 1080 --write-subs --sub-langs en

# 3. Download video with auto-generated Arabic captions
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f video -q 720 --write-auto-subs --sub-langs ar

# 4. Download video with subtitles embedded directly into the MP4 file
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f video -q 1080 --write-subs --sub-langs en --embed-subs

# 5. Download audio along with subtitle transcripts (useful for podcasts and lectures)
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f audio -q 320 --write-subs --sub-langs en

# 6. Download all available subtitles for an entire playlist
downloadyha "https://www.youtube.com/playlist?list=PLAYLIST_ID" -f subtitles --sub-langs all
```

---

## 📑 Full Playlists & Mix Handling

Downloadyha effortlessly handles full playlists, albums, and mixes:

- **Organized Output**: Creates a dedicated subfolder named after the playlist and numbers files automatically (`01 - Title.mp4`, `02 - Title.mp4`).
- **Video in Playlist / Mix Detection**: If you paste a link like `https://www.youtube.com/watch?v=...&list=...`, Downloadyha automatically detects the context and asks whether you want to download only the **Single Video** or the **Entire Playlist Batch**.
- **Resilient Batch Processing**: Single unavailable/private videos won't abort the remaining downloads.

```bash
# Download entire playlist as 1080p MP4 videos with embedded subtitles
downloadyha "https://www.youtube.com/playlist?list=PLAYLIST_ID" -f video -q 1080 --write-subs --sub-langs en --embed-subs

# Download entire playlist as 320 kbps MP3 audio tracks
downloadyha "https://www.youtube.com/playlist?list=PLAYLIST_ID" -f audio -q 320
```

---

## 🌐 Serverless REST API & Web Dashboard

Downloadyha includes a high-performance **FastAPI serverless REST API** and interactive web dashboard in `api/`, optimized for deployment on **Vercel**, **AWS Lambda**, **Render**, or **Docker**.

### API Highlights
- ⚡ **Stateless Serverless Execution**: Resolves signed CDN direct streaming URLs without local disk writes or server-side bandwidth bottlenecks.
- 🎨 **Built-In Web Dashboard**: Responsive single-page UI served from `/`.
- 📖 **Interactive Documentation**: Auto-generated Swagger UI at `/docs` and ReDoc at `/redoc`.
- 🛡️ **Production-Ready Security**: Preconfigured CORS (`*`) and security headers in `vercel.json`.

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health, runtime details, and yt-dlp core version |
| `POST` / `GET` | `/api/info` | Extract full metadata (title, uploader, duration, resolutions, streams, subtitles) |
| `POST` | `/api/formats` | Retrieve available video resolutions (4K, 1080p, etc.) and audio streams |
| `POST` | `/api/subtitles` | Extract all manual and auto-generated subtitle tracks with available formats |
| `POST` | `/api/resolve` | Resolve direct CDN streaming and download URLs for requested format, quality, clip, and subtitles |
| `GET` | `/api/stream` | Direct media stream / browser playback proxy with inline Content-Disposition |
| `GET` | `/api/download/file` | One-click attachment file download with clean sanitized filename header |
| `GET` | `/api/subtitles/download` | Direct subtitle track download (`.srt`, `.vtt`, `.ass`, `.lrc`) |
| `POST` / `GET` | `/api/playlist` | Inspect playlist items, count, and entry metadata |
| `POST` | `/api/playlist/resolve` | Batch resolve direct stream URLs for all playlist entries with indexed naming |
| `POST` | `/api/validate/url` | Validate media URL syntax and identify host platform |
| `POST` | `/api/validate/clip` | Validate clipping start/end timestamps against duration boundaries |

📖 **[Complete API Documentation & Deployment Guide →](api/README.md)**

---

## 🛠️ Complete Command & Option Reference

### CLI Subcommands

| Command | Type | Description |
|---|---|---|
| `downloadyha` | Interactive CLI | Start interactive step-by-step terminal downloader |
| `downloadyha-gui` | Desktop App | Launch standalone graphical user interface |
| `downloadyha gui` | CLI Helper | Launch the Desktop GUI from terminal |
| `downloadyha update` | Maintenance | Check for and install latest updates from GitHub Releases |
| `downloadyha repair` | Maintenance | Verify and re-download missing helper binaries (FFmpeg, Deno) |
| `downloadyha uninstall` | Maintenance | Completely remove Downloadyha, configuration, and cache |
| `downloadyha --verify` | Diagnostic | Verify helper binary integrity and dependencies |
| `downloadyha -v` / `--version` | Info | Print version information |
| `downloadyha -h` / `--help` | Info | Print help message and flag reference |

### CLI Options & Flags

| Flag | Short | Description | Example |
|---|---|---|---|
| `--start-time` | `-s` | Clip start timestamp (`MM:SS`, `HH:MM:SS`, or seconds) | `-s 01:30` |
| `--end-time` | `-e` | Clip end timestamp (`MM:SS`, `HH:MM:SS`, or seconds) | `-e 04:15` |
| `--format` | `-f` | Download format: `video`, `audio`, or `subtitles` | `-f video` |
| `--quality` | `-q` | Video height (`1080`, `720`, `0` for best) or Audio bitrate (`320`, `192`, `128`, `0`) | `-q 1080` |
| `--output-dir` / `--dir` | `-o` / `-d` | Custom destination directory | `-d ~/Videos` |
| `--write-subs` | | Write official subtitle files alongside media | `--write-subs` |
| `--write-auto-subs` | | Write auto-generated subtitle files | `--write-auto-subs` |
| `--sub-langs` | | Subtitle languages (comma-separated, e.g. `en,ar` or `all`) | `--sub-langs "en,es"` |
| `--sub-format` | | Subtitle format: `srt`, `vtt`, `ass`, `lrc` (default: `srt`) | `--sub-format vtt` |
| `--embed-subs` | | Embed subtitles into video file (MP4, MKV, WebM) | `--embed-subs` |
| `--convert-subs` | | Convert subtitles to another format after download | `--convert-subs srt` |
| `--gui` | | Launch graphical user interface | `downloadyha --gui` |
| `--update` | | Check for and install updates from GitHub Releases | `downloadyha --update` |
| `--repair` | | Repair and reinstall bundled dependencies | `downloadyha --repair` |
| `--uninstall` | | Completely uninstall Downloadyha | `downloadyha --uninstall` |
| `--verify` | | Verify helper binary integrity and exit | `downloadyha --verify` |
| `--verbose` | | Enable verbose debug logging | `downloadyha --verbose` |
| `--version` | `-v` | Display version | `downloadyha -v` |
| `--help` | `-h` | Display help information | `downloadyha -h` |

---

## ⚙️ Configuration & Storage

Downloadyha saves user preferences (default download folder, appearance theme, update checks) in a standard configuration file:

- **Windows**: `%LOCALAPPDATA%\Downloadyha\config.json`
- **Linux / macOS**: `~/.local/share/downloadyha/config.json` (or `~/.config/downloadyha/config.json`)

---

## 🔄 Self-Updater & Dependency Repair

Keep Downloadyha and all helper tools in top shape with built-in maintenance commands:

```bash
# Update Downloadyha to the latest GitHub release
downloadyha update

# Repair or re-download missing/corrupted FFmpeg and Deno binaries
downloadyha repair

# Verify system readiness and dependencies
downloadyha --verify
```

---

## 🗑️ Uninstallation

Uninstall cleanly at any time:

```bash
downloadyha uninstall
```

For the standalone GUI ZIP, simply delete the extracted folder.

---

## 🔒 Privacy & Security

- 🚫 **Zero Telemetry**: No tracking, analytics, telemetry, or personal data collection.
- 🔒 **Direct Connection**: All downloads stream directly between YouTube / media CDNs and your machine.
- 🛡️ **Integrity Verification**: Released binaries, helper tools, and updates are verified against SHA-256 checksums over secure TLS connections.

---

## 📚 Documentation Index

- **[GUI User Guide](GUI_USER_GUIDE.md)** — Comprehensive Desktop GUI guide, tips, and controls
- **[GUI Download Documentation](GUI_DOWNLOAD.md)** — Standalone GUI installation instructions
- **[GUI Development Guide](GUI_DEVELOPMENT.md)** — GUI architecture and styling specifications
- **[REST API Guide](api/README.md)** — Serverless API documentation, endpoints, and deployment
- **[Project Summary](PROJECT_SUMMARY.md)** — Complete architectural overview and feature summary
- **[Main Changelog](CHANGELOG.md)** — Version release notes and history
- **[GUI Changelog](CHANGELOG_GUI.md)** — Desktop GUI change history
- **[Contributing Guide](CONTRIBUTING.md)** — Guidelines for contributing

---

## 👤 Author & Code Ownership

Crafted with care by **Ahmed Tarek Zaher** ([@ahmed-tarek-2004](https://github.com/ahmed-tarek-2004)).

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
