# 🎬 Downloadyha — Project Summary & Architecture

## 📋 Executive Overview

**Downloadyha** is a fast, modern, zero-configuration media downloader ecosystem engineered for **Videos (up to 8K/4K/1080p)**, **Audio (MP3)**, **Partial Video & Audio Clips (Highlights)**, **Subtitles & Transcripts**, and **Full Playlists**.

The project delivers three complementary interface surfaces powered by a shared core engine:

1. **Modern Desktop GUI (`downloadyha-gui`)**: A rich CustomTkinter desktop application featuring a Light Grey & Crimson aesthetic, persistent sidebar navigation, 3 distinct workspace views (**Downloader**, **Download Queue & History**, **Settings**), real-time metadata inspection, inline error handling with one-click retry, dynamic theme modes (**Light**, **Dark**, **System Default**), and integrated **System Health** diagnostics.
2. **Interactive Terminal CLI (`downloadyha`)**: A colored, step-by-step interactive CLI wizard with live progress metrics (percentage, size, speed, ETA, batch counter), summary cards, and comprehensive non-interactive scripting flags.
3. **Serverless REST API & Web Dashboard (`api/`)**: A stateless FastAPI backend deployable on **Vercel Serverless Functions**, **AWS Lambda**, **Render**, or **Docker**, accompanied by interactive OpenAPI/Swagger documentation (`/docs`, `/redoc`), direct CDN stream URL resolution, and a built-in single-page web dashboard.

---

## 🏗️ Architectural Overview

```
                                 ┌──────────────────────────────────────────────┐
                                 │                 Downloadyha                  │
                                 │              Ecosystem Surfaces              │
                                 └──────────────────────┬───────────────────────┘
                                                        │
         ┌──────────────────────────────────────────────┼──────────────────────────────────────────────┐
         │                                              │                                              │
         ▼                                              ▼                                              ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐   ┌──────────────────────────────────┐
│       Desktop GUI Client        │   │      Terminal CLI Client        │   │    Serverless REST API & Web     │
│    (src/downloadyha_gui/)       │   │     (src/downloadyha/cli.py)    │   │             (api/)               │
│                                 │   │                                 │   │                                  │
│ • CustomTkinter Desktop App     │   │ • Interactive Wizard UI         │   │ • FastAPI Serverless Application │
│ • 3 Views (Downloader/Queue/Set)│   │ • Live Progress Meters & ETA    │   │ • Direct CDN Stream Resolution   │
│ • Persistent Sidebar & Health   │   │ • Scripting Flags (-s, -e, -f)  │   │ • Single-Page Web Dashboard      │
│ • Inline Error Cards & Retries  │   │ • Color-Coded Summary Cards     │   │ • Swagger (/docs) & ReDoc Specs  │
└────────────────┬────────────────┘   └────────────────┬────────────────┘   └────────────────┬─────────────────┘
                 │                                     │                                     │
                 └──────────────────────┬──────────────┴─────────────────────────────────────┘
                                        │
                                        ▼
                        ┌─────────────────────────────────┐
                        │        Core Engine Backend      │
                        │    (src/downloadyha/downloader) │
                        │                                 │
                        │ • Smart Codec Prioritization    │
                        │ • Partial Media Range Clipping  │
                        │ • Subtitle Handling & Parsing   │
                        │ • Full Playlist & Mix Manager   │
                        │ • yt-dlp Python Backend Engine  │
                        └────────────────┬────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
                 ▼                                               ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│     Dependency Subsystems       │             │   Self-Maintenance & Config     │
│   (dependencies, network, paths)│             │ (updater, uninstaller, config)  │
│                                 │             │                                 │
│ • Bundled Essential FFmpeg (~40M│             │ • GitHub Releases Self-Updater  │
│ • Bundled Deno JS Engine Runtime│             │ • Dependency Auto-Repair Engine │
│ • SHA-256 Checksum Verification │             │ • JSON Preference Persistence   │
│ • Multi-Bundle TLS CA Discovery │             │ • Clean System Uninstaller      │
└─────────────────────────────────┘             └─────────────────────────────────┘
```

---

## 🌟 Core Features & Capabilities

### 1. Smart Codec & Container Resolution
- **$\le$ 1080p Full HD (or Default Video)**: Strictly prioritizes native H.264 (`avc`) video and AAC (`m4a`) audio directly from YouTube, merging them into standard `.mp4` containers via stream copy. This guarantees 100% universal playback compatibility across legacy and modern media players, Smart TVs, QuickTime, mobile devices, and editing software without requiring third-party codec packs.
- **Ultra-HD (1440p, 4K, 8K)**: YouTube serves Ultra-HD streams exclusively in VP9 or AV1 codecs. Downloadyha automatically acquires these optimal high-efficiency streams and packages them into standard `.mkv` or `.webm` containers.
- **Lossless Stream-Copy Muxing**: Container packaging utilizes FFmpeg stream copy (`-c copy`) whenever possible, eliminating CPU-heavy re-encoding and finishing muxing in seconds.

### 2. Partial Video & Audio Clipping (Highlights)
- Allows downloading only a designated section of a video or audio track instead of the entire file.
- **Supported Timestamp Formats**:
  - `MM:SS` (e.g., `01:30`)
  - `HH:MM:SS` (e.g., `01:15:30`)
  - Raw seconds (e.g., `90`, `90s`, `120.5`)
  - Fractional/decimal seconds (e.g., `01:15.5`)
- Supported across CLI arguments (`-s` / `--start-time`, `-e` / `--end-time`), interactive CLI prompts, Desktop GUI controls, and REST API validation endpoints.

### 3. Comprehensive Subtitle System + Subtitle-Only Mode
- **Official & Auto-Generated Subtitles**: Extracts manual creator subtitles as well as YouTube auto-generated captions.
- **Multi-Language Mapping**: Includes an extensive language dictionary mapping language codes to English names (e.g., `en (English)`, `ar (Arabic)`, `es (Spanish)`, `ja (Japanese)`, `zh-Hans (Chinese Simplified)`).
- **Subtitle-Only Mode (`-f subtitles`)**: Instantly downloads subtitle files and transcripts without downloading heavy video or audio streams.
- **Container Embedding (`--embed-subs`)**: Embeds subtitle tracks directly into MP4/MKV video files.
- **Format Conversion (`--convert-subs`)**: Converts subtitle tracks between **SRT**, **VTT**, **ASS**, and **LRC**.
- **Audio Subtitle Integration**: Supports pairing audio downloads (MP3) with subtitle transcript files for podcast and lecture study workflows.

### 4. High-Fidelity MP3 Audio Extractor
- One-click extraction from video streams to MP3.
- Supported bitrates: **320 kbps** (CBR High), **192 kbps** (CBR Standard), **128 kbps** (CBR Compact), and **Best Quality** (VBR ~256–320 kbps).

### 5. Playlists & Video-in-Playlist Context Handling
- **Organized Playlist Hierarchy**: Batch downloads entire playlists into a dedicated subfolder named after the playlist, with sequential file numbering (`01 - Title.mp4`, `02 - Title.mp4`).
- **Context Detection**: When a user inputs a URL containing a video ID and playlist parameter (e.g. `https://www.youtube.com/watch?v=...&list=...`), Downloadyha detects the embedded context and offers a prompt or GUI selector to choose between downloading only the **Single Video** or the **Entire Playlist Batch**.
- **Error Resilience (`ignoreerrors`)**: If an individual item in a playlist is private, blocked, or deleted, Downloadyha logs the issue and seamlessly continues downloading the remaining items.

---

## 🖥️ Desktop GUI Architecture (`src/downloadyha_gui/`)

Built with **CustomTkinter**, the GUI provides a modern desktop application:

### Layout Structure
- **Persistent Left Sidebar**:
  - Brand header and application version.
  - Navigation tab switcher (**Downloader**, **Download Queue**, **Settings**).
  - Quick **Theme Mode** switcher (**☀️ Light**, **🌙 Dark**, **💻 Auto**).
  - **System Health** module with real-time status indicator, **Check for Updates** button, and **Verify & Repair App** button.
  - Copyright and author branding (*Ahmed Tarek Zaher*).
- **Workspace Views**:
  1. **Downloader View**:
     - URL input with clipboard paste button and automatic metadata analysis.
     - Media Information card displaying Title, Channel, Duration, View Count, and maximum detected resolution.
     - Format segmented selector (**🎥 Video**, **🎵 Audio**, **📝 Subtitles**).
     - Dynamic quality dropdown menu (populates resolutions up to 4K detected from media info).
     - Collapsible **Partial Section Clipping** inputs (Start/End timestamps).
     - Collapsible **Subtitle & Transcript** controls (Language dropdown, format selection, auto-caption toggle, embed toggle).
     - Collapsible **Playlist Scope** selector (appears when video-in-playlist/mix links are detected).
     - Save destination path entry with directory browse button.
     - Active Download Status card with live progress bar, speed, percentage, and ETA metrics.
     - **Docked Action Bar** (fixed at the bottom) with **Start Download**, **Cancel**, and **Open Folder** buttons.
  2. **Download Queue & History View**:
     - Scrollable list of active, completed, and failed downloads.
     - Item-specific progress bars, speed, ETA, and timestamps.
     - Action buttons per card: **📁 Open Folder**, **▶️ Open File**, and **🗑️ Remove**.
     - **100% Inline Error Cards**: Errors are displayed directly inside the task card with an inline **↺ Retry** button — no blocking pop-up dialogs.
  3. **Settings View**:
     - Appearance theme configuration (Light, Dark, System Default).
     - Default download folder configuration with browse dialog.
     - System Diagnostics card showing installed versions of Downloadyha, FFmpeg, Deno, yt-dlp, and Python runtime.
     - About & Ownership card.

### GUI Reliability & Threading
- **Strict Thread Safety**: Network requests, yt-dlp operations, update checks, and dependency repairs run on dedicated daemon threads. UI updates are dispatched back to the main thread via `root.after()`.
- **Cancellation Management**: Clean download cancellation using yt-dlp cancellation hooks and background socket termination, immediately releasing UI state locks and restoring buttons to ready states.
- **Modal Dialog Stability**: File and folder dialogs use explicit parent window anchoring to prevent crashes or lost focus across Windows and Linux window managers.

---

## ⚡ Terminal CLI Architecture (`src/downloadyha/cli.py`)

The CLI provides an interactive experience as well as non-interactive command-line scripting:

- **Interactive Wizard**: Step-by-step guidance covering URL input, folder selection, format choice, quality preset, optional clipping, and subtitle configuration.
- **Non-Interactive Arguments**: Full suite of flags (`-s`, `-e`, `-f`, `-q`, `-d`, `--write-subs`, `--write-auto-subs`, `--sub-langs`, `--sub-format`, `--embed-subs`, `--convert-subs`).
- **Maintenance Subcommands**:
  - `downloadyha gui` — Launch Desktop GUI.
  - `downloadyha update` — Check and install updates.
  - `downloadyha repair` — Re-download missing/corrupted dependencies.
  - `downloadyha uninstall` — Completely uninstall the application.
  - `downloadyha --verify` — Run dependency diagnostics.
- **Live Terminal Metrics**: Real-time progress updates showing download percentage, downloaded/total size, transfer speed, and ETA without terminal flicker.

---

## 🌐 Serverless REST API Architecture (`api/`)

The API enables headless deployments, web applications, and microservice integrations:

- **FastAPI Framework**: High-throughput async web framework with automatic OpenAPI documentation.
- **Stateless Serverless Execution**: Designed for Vercel Python Serverless Functions. Resolves signed direct CDN stream URLs so client browsers or downloaders fetch media directly without passing heavy payloads through the serverless function.
- **Direct Streaming & Proxying**:
  - `/api/stream`: Direct browser playback proxy with inline Content-Disposition.
  - `/api/download/file`: Direct file attachment download with sanitized filename headers.
  - `/api/subtitles/download`: Direct subtitle track download in `.srt`, `.vtt`, `.ass`, or `.lrc`.
- **Validation Endpoints**:
  - `/api/validate/url`: Syntactic URL validation and platform identification.
  - `/api/validate/clip`: Validation of start/end timestamps and boundary checking against video duration.
- **Built-In Web Dashboard**: Single-page responsive web dashboard served at the root `/` path.

---

## 📦 Dependency Subsystem & Optimization

### Optimized FFmpeg Binaries (~40MB vs ~150MB)
Earlier versions bundled full GPL builds (~150MB), leading to long initial download times. Downloadyha uses optimized builds containing only the essential utilities (`ffmpeg` and `ffprobe`):
- **Windows**: Gyan.dev Essentials build (~40MB).
- **Linux (x86_64 / arm64)**: John Van Sickle Static build (~40MB).
- **Reduction**: ~75% smaller footprint, cutting setup time from 10–15 minutes down to 1–2 minutes.

### Deno JavaScript Runtime
- Used as the JavaScript runtime engine for yt-dlp to resolve complex streaming signatures.
- Automatically downloaded, placed in the application binary directory, and verified with SHA-256 checksums.

### Real-Time Dependency Progress Tracking
- Downloadyha provides live progress indicators (percentage, downloaded/total MB, speed in MB/s, and ETA) for all internal downloads (initial setup, updates, and dependency repairs) via `network.py`.

---

## 📁 Repository & Codebase Structure

```
youtube_Downloader/
├── README.md                      # Primary user documentation & quick start guide
├── PROJECT_SUMMARY.md             # Complete architectural & feature summary (this file)
├── LICENSE                        # MIT License
├── CHANGELOG.md                   # Core & CLI changelog
├── CHANGELOG_GUI.md               # Desktop GUI changelog
├── GUI_USER_GUIDE.md              # Detailed GUI user guide
├── GUI_DOWNLOAD.md                # Standalone GUI installation instructions
├── GUI_DEVELOPMENT.md             # Developer & styling guidelines for GUI
├── install.ps1                    # Automated Windows PowerShell installer
├── install.sh                     # Automated Linux/macOS Bash installer
├── build-windows.ps1              # Windows standalone binary build script
├── build-linux.sh                 # Linux standalone binary build script
├── pyproject.toml                 # Python package specification & dependencies
├── setup.py                       # Package setup configuration
│
├── api/                           # FastAPI Serverless REST API & Web Dashboard
│   ├── README.md                  # API documentation, Swagger specs & deployment guide
│   ├── index.py                   # FastAPI application instance & routing
│   ├── models.py                  # Pydantic data schemas for requests & responses
│   ├── validators.py              # URL & timestamp clipping validators
│   ├── vercel.json                # Vercel serverless deployment configuration
│   ├── services/
│   │   └── ytdlp_service.py       # Stateless yt-dlp stream resolution & extraction service
│   └── static/
│       └── index.html             # Built-in single-page web dashboard
│
├── src/
│   ├── downloadyha/               # Core Engine & Terminal CLI Package
│   │   ├── __init__.py            # Version & metadata exports
│   │   ├── __main__.py            # CLI entry point
│   │   ├── cli.py                 # CLI argument parser & interactive wizard
│   │   ├── downloader.py          # Core yt-dlp downloader, codecs & clipping engine
│   │   ├── subtitle_utils.py      # Subtitle language mapping & extraction helpers
│   │   ├── dependencies.py        # Dependency discovery, download & verification
│   │   ├── network.py             # HTTP utilities with download progress & CA discovery
│   │   ├── config.py              # User configuration loading & persistence
│   │   ├── updater.py             # GitHub Releases self-updater
│   │   ├── uninstaller.py         # Application uninstaller
│   │   ├── ui.py                  # Terminal UI components, colors & progress bars
│   │   ├── platform.py            # Platform detection utilities
│   │   ├── platform_utils.py      # OS-specific helper functions
│   │   ├── paths.py               # Application data, binary & cache paths
│   │   ├── logging.py             # Application logging configuration
│   │   ├── versions.json          # Dependency download URLs and SHA-256 checksums
│   │   └── gui.py                 # Fallback GUI launcher module
│   │
│   └── downloadyha_gui/           # Modern CustomTkinter Desktop GUI Package
│       ├── __init__.py            # GUI package initializer
│       ├── app.py                 # CustomTkinter Desktop GUI application
│       ├── launcher.py            # GUI launcher entry point
│       └── resources/
│           └── icon.ico           # Application icon
│
└── assets/                        # Icons, graphics, and documentation assets
    └── icons/
```

---

## ⚙️ Configuration & Storage Locations

Downloadyha persists user preferences (default download folder, appearance mode, update checks) across runs:

- **Windows**: `%LOCALAPPDATA%\Downloadyha\config.json`
- **Linux / macOS**: `~/.local/share/downloadyha/config.json` (or `~/.config/downloadyha/config.json`)
- **Bundled Helper Binaries**:
  - Windows: `%LOCALAPPDATA%\Downloadyha\bin\` (`ffmpeg.exe`, `ffprobe.exe`, `deno.exe`)
  - Linux: `~/.local/share/downloadyha/bin/` (`ffmpeg`, `ffprobe`, `deno`)

---

## 👤 Author & Code Ownership

- **Author & Developer**: Ahmed Tarek Zaher ([@ahmed-tarek-2004](https://github.com/ahmed-tarek-2004))
- **Copyright**: © 2026 Ahmed Tarek Zaher. All rights reserved.
- **License**: MIT License
