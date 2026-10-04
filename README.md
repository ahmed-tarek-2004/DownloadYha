# Downloadyha

A fast, modern, and beautiful YouTube downloader available in both **Desktop GUI** and **CLI** versions for **Videos (up to 4K)**, **Audio (MP3)**, **Partial Video & Audio Clips (Highlights)**, and **Full Playlists**. No Python, FFmpeg, Deno, or yt-dlp setup required.

---

## 🌟 Key Features

- ✂️ **Partial Video & Audio Clipping**: Download only the exact section you need by specifying Start and End times (`01:30`, `90`, `00:02:45`). Save bandwidth and disk space without downloading full multi-hour videos!
- 🎨 **Modern Desktop GUI**: Sleek CustomTkinter interface with glassmorphism cards, light/dark themes, docked persistent action buttons, and scrollable controls.
- 🔍 **Real-Time Metadata Fetching**: Automatically inspects video/playlist URLs to preview Title, Channel, Duration, and Type.
- 🎯 **Dynamic Quality Detection**: Auto-detects and displays available resolutions (4K 2160p, 1440p, 1080p, 720p, 480p, 360p, etc.).
- 🎵 **Audio MP3 Extractor**: One-click high-fidelity MP3 conversion with custom bitrates (320 kbps, 192 kbps, 128 kbps, or Best VBR).
- 📑 **Full Playlist Downloads**: Batch download entire video or audio playlists with automated folder numbering and organization.
- 📜 **Download History & Quick Open**: Track download history and open completed media files or destination folders directly with one click.
- 📝 **Subtitle & Transcript Support**: Download, embed, and convert subtitles in multiple formats (SRT, VTT, ASS, LRC) with language selection and auto-generated caption support.
- ⚡ **Interactive Terminal CLI**: Color-coded step-by-step wizard, live progress bars (speed, ETA, batch counter), and summary cards.
- 📦 **Zero-Config Standalone**: Includes built-in self-repairing FFmpeg and Deno helper binaries with SHA-256 checksum verification.

---

## 🖥️ Desktop GUI - Installation & Quick Start

The **Downloadyha Desktop GUI** provides a sleek graphical interface featuring real-time metadata inspection, dynamic quality selection (up to 4K), audio extraction, partial video clipping, download history, and dark/light themes.

### Option 1: Standalone Download (No Python Required — Recommended)

Download the pre-built standalone app for your operating system:

| Platform | Download | Instructions |
|---|---|---|
| **Windows 10/11 (64-bit)** | **[⬇️ Download Windows GUI (ZIP)](https://github.com/ahmed-tarek-2004/DownloadYha/releases/latest/download/downloadyha-gui-windows.zip)** | Extract the ZIP and double-click `downloadyha-gui.exe` |
| **Linux (x86_64)** | **[⬇️ Download Linux GUI (tar.gz)](https://github.com/ahmed-tarek-2004/DownloadYha/releases/latest/download/downloadyha-gui-linux-x86_64.tar.gz)** | Extract archive and run `./downloadyha-gui` |

#### 3-Step Windows Quick Start:
1. **Download & Extract** `downloadyha-gui-windows.zip` to a folder of your choice (e.g. `Downloads` or `C:\Program Files\DownloadyhaGUI`).
2. **Double-click** `downloadyha-gui.exe` to launch.
3. **Paste any YouTube URL** — the app automatically fetches video details (Title, Channel, Duration) and populates the available resolutions!

---

### Option 2: Install via Python & Pip

If you have Python 3.10+ installed, you can install the GUI package with:

```bash
pip install "downloadyha[gui]"
```

Then launch the GUI anytime with:

```bash
downloadyha-gui
```

*(On Linux systems without Tkinter: `sudo apt install python3-tk`)*

📖 **[Complete GUI User Guide →](GUI_USER_GUIDE.md)** | **[GUI Download Documentation →](GUI_DOWNLOAD.md)**

---

## ⚡ CLI Version - Quick Install

For terminal power-users, Downloadyha offers a rich, interactive CLI experience with color-coded steps, live progress bars, partial clipping support, and batch playlist downloads.

### Windows

#### PowerShell:
```powershell
irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex
```

#### Command Prompt (CMD):
```cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex"
```

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.sh | bash
```

### Run CLI:

```bash
downloadyha
```

---

## ✂️ Partial Video & Audio Clipping (Highlights)

Downloadyha allows you to download only a specific portion or highlight clip of a video or audio track instead of the entire file.

### Supported Timestamp Formats
- `MM:SS` (e.g., `01:30` for 1 minute 30 seconds)
- `HH:MM:SS` (e.g., `01:15:30` for 1 hour 15 minutes 30 seconds)
- Total seconds (e.g., `90` or `90s`)
- Decimals / fractions (e.g., `01:15.5` or `75.5`)

---

### CLI Usage & Examples

You can provide start and end timestamps directly via command-line arguments or follow the interactive wizard prompts.

#### 1. Command-Line Arguments (Non-Interactive / Scripting):

```bash
# Download a 2-minute video clip (from 01:30 to 03:30) in 1080p Full HD
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -s 01:30 -e 03:30 -f video -q 1080

# Extract a 45-second audio clip (from start to 00:45) as high-quality 320 kbps MP3
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -s 00:00 -e 00:45 -f audio -q 320

# Download from minute 10:00 to the end of the video
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -s 10:00 -f video -q 720

# Specify a custom download folder for the clip
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -s 00:30 -e 01:45 -d "C:\Users\User\Videos\Clips"
```

#### 2. Interactive Wizard:
When running `downloadyha` interactively:
1. Paste the URL and select your download folder.
2. When prompted: `Download a specific section only (clip)? [y/N]:`, enter `y`.
3. Enter your desired **Start Time** (e.g., `01:30`) and **End Time** (e.g., `03:45`, or leave blank for end of video).
4. Choose video resolution or audio quality. Downloadyha streams and trims only the requested segment!

---

### Desktop GUI Usage

1. Paste a video URL — video metadata will load automatically.
2. Check the **"✂️ Download specific section (clip)"** box.
3. Enter your **Start Time** (e.g. `00:30`) and **End Time** (e.g. `02:15`).
4. Select your preferred format (🎥 Video or 🎵 Audio) and quality preset.
5. Click **START DOWNLOAD**.

---

## 📝 Subtitle & Transcript Support

Downloadyha provides comprehensive subtitle handling for videos and playlists:

### Subtitle Options

| Option | Description |
|--------|-------------|
| **Write Subtitles** | Download official subtitle tracks alongside the media |
| **Write Auto-Generated Subtitles** | Download YouTube's auto-generated captions |
| **Embed Subtitles** | Embed subtitles directly into the video file (MP4, MKV, WebM) |
| **Subtitle Languages** | Specify comma-separated language codes (e.g., `en,ar,es`) or `all` for all available |
| **Subtitle Format** | Choose output format: `srt` (default), `vtt`, `ass`, `lrc` |
| **Convert Subtitles** | Convert downloaded subtitles to a different format |

### Supported Subtitle Formats

- **SRT** — Most widely compatible subtitle format
- **VTT** — WebVTT format for web playback
- **ASS** — Advanced SubStation Alpha with styling support
- **LRC** — Lyrics/synchronized text format

### CLI Usage & Examples

```bash
# Download video with official English subtitles (SRT)
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f video -q 1080 --write-subs --sub-langs en

# Download video with auto-generated subtitles in Arabic
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f video -q 720 --write-auto-subs --sub-langs ar

# Download video with both official and auto-generated subtitles in multiple languages
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f video -q 1080 --write-subs --write-auto-subs --sub-langs "en,ar,es"

# Download video with subtitles embedded into the MP4 file
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f video -q 1080 --write-subs --sub-langs en --embed-subs

# Download audio with subtitle file (useful for podcasts with transcripts)
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f audio -q 320 --write-subs --sub-langs en

# Convert subtitles to VTT format after download
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -f video -q 1080 --write-subs --sub-langs en --convert-subs vtt

# Combine clipping with subtitles
downloadyha "https://www.youtube.com/watch?v=VIDEO_ID" -s 01:30 -e 03:45 -f video -q 1080 --write-subs --sub-langs en --embed-subs
```

### Desktop GUI Usage

1. Paste a video URL and click **Fetch Info** to load metadata.
2. In the **Subtitle Options** section:
   - Check **Write subtitle files** to download official subtitles
   - Check **Write auto-generated subtitles** for YouTube's auto-captions
   - Enter **Languages** (e.g., `en,ar` or `all`)
   - Select **Format** (SRT, VTT, ASS, LRC)
   - Check **Embed subtitles in video** to burn subtitles into the video file
   - Check **Convert subtitles** and select target format if you want conversion
3. Select Video/Audio format and quality
4. Click **Download**

### Playlist Subtitle Support

Subtitle options work seamlessly with playlist downloads:

```bash
# Download entire playlist as video with English subtitles embedded
downloadyha "https://www.youtube.com/playlist?list=PLAYLIST_ID" -f video -q 1080 --write-subs --sub-langs en --embed-subs

# Download playlist as audio with subtitle files
downloadyha "https://www.youtube.com/playlist?list=PLAYLIST_ID" -f audio -q 192 --write-subs --sub-langs "en,es"
```

---

## 🛠️ Available Commands & CLI Options

### Commands

| Command | Type | Description |
|---|---|---|
| `downloadyha-gui` | Desktop App | Launch the standalone graphical user interface |
| `downloadyha` | Terminal CLI | Start the interactive command-line downloader |
| `downloadyha gui` | Terminal Helper | Launch the Desktop GUI from the CLI |
| `downloadyha update` | Maintenance | Check for and install the latest updates from GitHub Releases |
| `downloadyha repair` | Maintenance | Verify and re-download missing helper binaries (FFmpeg, Deno) |
| `downloadyha uninstall` | Maintenance | Completely remove Downloadyha, configuration, and cache |
| `downloadyha --verify` | Diagnostic | Verify that dependencies and helper binaries are operational |
| `downloadyha --version` | Info | Print version information |

### CLI Options & Flags

| Flag | Short | Description | Example |
|---|---|---|---|
| `--start-time` | `-s` | Clip start timestamp (`MM:SS`, `HH:MM:SS`, or seconds) | `-s 01:30` |
| `--end-time` | `-e` | Clip end timestamp (`MM:SS`, `HH:MM:SS`, or seconds) | `-e 04:15` |
| `--format` | `-f` | Media format: `video` or `audio` | `-f video` |
| `--quality` | `-q` | Video height (`1080`, `720`, `0` for best) or Audio bitrate (`320`, `192`, `128`, `0`) | `-q 1080` |
| `--output-dir` / `--dir` | `-o` / `-d` | Custom destination directory | `-d ~/Videos` |
| `--write-subs` | | Write official subtitle files alongside the media | `--write-subs` |
| `--write-auto-subs` | | Write auto-generated subtitle files | `--write-auto-subs` |
| `--sub-langs` | | Subtitle languages (comma-separated, e.g. `en,ar` or `all`) | `--sub-langs "en,es"` |
| `--sub-format` | | Subtitle format: `srt`, `vtt`, `ass`, `lrc` (default: `srt`) | `--sub-format vtt` |
| `--embed-subs` | | Embed subtitles into the video file (MP4, MKV, WebM) | `--embed-subs` |
| `--convert-subs` | | Convert subtitles to another format after download | `--convert-subs srt` |
| `--gui` | | Launch the graphical user interface | `downloadyha --gui` |
| `--update` | | Check for and install updates from GitHub Releases | `downloadyha --update` |
| `--repair` | | Repair and reinstall bundled dependencies (FFmpeg, Deno) | `downloadyha --repair` |
| `--uninstall` | | Completely uninstall Downloadyha and delete application data | `downloadyha --uninstall` |
| `--verify` | | Verify helper binary integrity and exit | `downloadyha --verify` |
| `--verbose` | | Enable verbose debug logging | `downloadyha --verbose` |
| `--version` | `-v` | Display Downloadyha version | `downloadyha -v` |
| `--help` | `-h` | Display full help and argument list | `downloadyha -h` |

---

## ⚙️ Configuration

Downloadyha stores user preferences (default download folder, background update checks) in a standard configuration file:

- **Windows**: `%LOCALAPPDATA%\Downloadyha\config.json`
- **Linux**: `~/.local/share/downloadyha/config.json`

---

## 🔄 Self-Updater & Repair

Keep Downloadyha and all helper tools in top shape with built-in maintenance commands:

```bash
# Update Downloadyha to the latest release
downloadyha update

# Repair or re-download missing/corrupted dependencies (FFmpeg, Deno)
downloadyha repair

# Verify system readiness and dependencies
downloadyha --verify
```

---

## 🗑️ Uninstallation

Uninstall cleanly at any time using:

```bash
downloadyha uninstall
```

For the standalone GUI ZIP, simply delete the extracted folder.

---

## 🔒 Privacy & Security

- 🚫 **Zero Telemetry**: No tracking, analytics, telemetry, or personal data collection.
- 🔒 **Direct Connection**: Downloads stream directly from YouTube to your local disk.
- 🛡️ **Integrity Verification**: Released binaries, helper tools, and updates are verified against SHA-256 checksums over secure TLS connections.

---

## 📚 Documentation

- **[GUI User Guide](GUI_USER_GUIDE.md)** - Desktop GUI usage, tips, and keyboard shortcuts
- **[GUI Download Guide](GUI_DOWNLOAD.md)** - Standalone GUI download and setup instructions
- **[GUI Development Guide](GUI_DEVELOPMENT.md)** - Architecture and developer documentation
- **[Main Changelog](CHANGELOG.md)** - Complete release notes and version history
- **[Contributing Guide](CONTRIBUTING.md)** - Guidelines for contributing to Downloadyha

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
