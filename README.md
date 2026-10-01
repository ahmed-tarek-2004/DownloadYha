# Downloadyha

A fast, beautiful, and standalone YouTube downloader available in both **CLI** and **Desktop GUI** versions for **Videos**, **Audio (MP3)**, and **Full Playlists**. No Python, FFmpeg, Deno, or yt-dlp setup required.

---

## ⚡ Quick Start

### Windows

**Using Command Prompt (CMD):**

```cmd
powershell -Command "irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex"
```

**Using PowerShell:**

```powershell
irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex
```

Then run:

```cmd
# CLI (Interactive Terminal)
downloadyha

# Desktop GUI
downloadyha gui
```

### Linux

Open your terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.sh | bash
```

Then run:

```bash
# CLI (Interactive Terminal)
downloadyha

# Desktop GUI
downloadyha gui
```

---

## 🖥️ Desktop GUI

Downloadyha now includes a modern desktop GUI application for users who prefer a graphical interface.

### Features

- 🎨 **Modern UI**: Clean, intuitive interface built with tkinter
- 🌓 **Light & Dark Themes**: Switch between themes with one click
- ✅ **Real-time URL Validation**: Instant feedback on URL validity
- 📂 **Easy Folder Selection**: Built-in folder browser with persistence
- ⬇️ **Progress Tracking**: Real-time progress bars with speed and ETA
- 🎬 **All CLI Features**: Video, audio, and playlist downloads
- 💾 **Settings Persistence**: Remembers your preferences and window position
- 🔄 **Background Downloads**: Non-blocking UI during downloads

### Launch GUI

After installation, launch the GUI with:

```bash
downloadyha gui
```

See [GUI_USER_GUIDE.md](GUI_USER_GUIDE.md) for complete GUI documentation.

---

## 🌟 Features

### CLI Features
- 🎬 **Single Video Downloads**: Custom resolutions up to 4K (2160p, 1440p, 1080p, 720p, 480p, 360p) with merged audio in MP4.
- 🎵 **High Quality Audio Extraction**: Convert audio directly to MP3 (Best VBR ~245k, 320 kbps, 192 kbps, 128 kbps).
- 📑 **Full Playlist Downloads**: Download entire video or audio playlists in batch.
  - Automatically organizes tracks into a clean subfolder named after the playlist.
  - Indexes track filenames (`01 - Title.mp4`, `02 - Title.mp4`).
  - Error-resilient: private or restricted videos are skipped without failing the entire batch.
- ✨ **Modern & Pretty Terminal UI**:
  - Beautiful box-framed banners and cards.
  - Visual step-by-step indicator pills (`[1/3]`, `[2/3]`, `[3/3]`).
  - High-resolution dynamic progress bar with speed, ETA, and playlist counter `[3/15]`.
- 🪟 **True Cross-Platform**: Native ANSI and Windows Virtual Terminal Processing (`cmd`, `PowerShell`, `Windows Terminal`, `Linux`).

### GUI Features
- 🖱️ **Point-and-Click Interface**: No command-line knowledge required
- 🎨 **Dual Themes**: Switch between Light and Dark themes instantly
- ✅ **Real-time Validation**: See if your URL is valid as you type
- 📊 **Visual Progress**: Watch downloads with smooth progress bars
- 💾 **Smart Memory**: Remembers your preferences and last used settings
- 🎯 **Quality Presets**: Easy dropdown selection for video and audio quality
- 📂 **Folder Browser**: Select download location with native file dialog

### Universal Features
- 🔄 **Self-Updating & Repairing**: Built-in `downloadyha update` and `downloadyha repair`.
- 🗑️ **One-Command Uninstaller**: Built-in `downloadyha uninstall`.
- 📦 **Completely Standalone**: All dependencies (FFmpeg, Deno, yt-dlp) are self-contained.

---

## 💻 Requirements

**None.**

Downloadyha is fully self-contained. You do **not** need to install:
- ❌ Python
- ❌ pip
- ❌ FFmpeg / FFprobe
- ❌ Deno
- ❌ yt-dlp

---

## 🖥️ Supported Platforms

- ✅ Windows 10 / 11 (64-bit)
- ✅ Linux x86_64 (glibc 2.31+)
- ✅ Linux ARM64 (glibc 2.31+)

---

## 🚀 Usage

Simply launch the interactive CLI:

```bash
downloadyha
```

### Interactive Workflow

```text
╭────────────────────────────────────────────────────────╮
│                       D O W N L O A D Y H A                        │
│                Fast & Beautiful YouTube Downloader                 │
│                       By Ahmed Tarek Zaher  •  v1.0.0                       │
╰────────────────────────────────────────────────────────╯

[1/3] Enter YouTube URL
➜ Paste Video or Playlist URL
╰─> https://www.youtube.com/playlist?list=PLrAXtmErZgOdP_8GzKt...

[2/3] Select Destination Folder
➜ Enter destination folder (default: C:\Users\Ahmed\Downloads)
╰─> 

[3/3] Analyzing Media & Selecting Quality
⏳ Fetching media metadata from YouTube...

╭─ 📑 Playlist Detected ─────────────────────────────────────────╮
│  Title           :  Synthwave & Cyberpunk Mix 2026             │
│  Channel         :  RetroWave Records                          │
│  Total Items     :  15 videos                                  │
│  Type            :  YouTube Playlist                           │
│  Destination     :  C:\Users\Ahmed\Downloads                   │
╰────────────────────────────────────────────────────────────────╯

Select Playlist Download Type:
  [1] Video Playlist (MP4) • Download all videos in playlist
  [2] Audio Playlist (MP3) • Extract all songs/audio to MP3

╰─> Enter choice [1-2]: 1

Select Maximum Video Quality for Playlist:
  [1] Best Available • Maximum resolution per video
  [2] 1080p (Full HD) • 1920x1080 maximum
  [3] 720p (HD) • 1280x720 standard HD
  [4] 480p (SD) • Standard Definition

╰─> Enter choice [1-4]: 2

ℹ Starting Video Playlist Download: Synthwave & Cyberpunk Mix 2026
⬇ [1/15] [████████████████░░░░░░░░]  65.4% │ 18.2MiB/s │ ETA 00:04 │ 85.0/130.0MB

╭─ ✔ Playlist Download Complete ────────────────────────────────╮
│  Playlist          :  Synthwave & Cyberpunk Mix 2026
│  Type              :  VIDEO
│  Saved To          :  C:\Users\Ahmed\Downloads\Synthwave & Cyberpunk Mix 2026
╰───────────────────────────────────────────────────────────────╯
```

---

## 🛠️ Commands

| Command | Description |
|---|---|
| `downloadyha` | Start the interactive CLI downloader (Single Video / Audio / Playlist) |
| `downloadyha gui` | Launch the Desktop GUI interface |
| `downloadyha update` | Check GitHub Releases and update to the newest version |
| `downloadyha repair` | Re-verify and restore bundled dependencies |
| `downloadyha uninstall` | Cleanly remove Downloadyha and all configuration/cache |
| `downloadyha --verify` | Check system dependencies status |
| `downloadyha --version` | Display version information |
| `downloadyha --help` | Show command usage and options |

---

## ⚙️ Configuration

Downloadyha automatically creates and manages a configuration file:

- **Windows**: `%LOCALAPPDATA%\Downloadyha\config.json`
- **Linux**: `~/.local/share/downloadyha/config.json`

Example configuration:

```json
{
  "download_directory": "C:\\Users\\Ahmed\\Downloads",
  "check_updates": true
}
```

---

## 🗑️ Uninstallation

You can uninstall Downloadyha at any time using the built-in command:

```bash
downloadyha uninstall
```

Or manually:

### Windows (PowerShell)
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Downloadyha"
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\Downloadyha"
```

### Linux
```bash
rm -rf ~/.local/share/downloadyha
rm -f ~/.local/bin/downloadyha
```

---

## 🔒 Privacy

- 🚫 **Zero Tracking**: Downloadyha does not collect, log, or transmit personal telemetry or usage statistics.
- 🔒 **Direct Connection**: Downloads stream directly from YouTube to your local machine.
- 🛡️ **Integrity Verification**: Updates and components are checked against SHA-256 digests.

---

## 📚 Documentation

- **[GUI User Guide](GUI_USER_GUIDE.md)** - Complete guide for Desktop GUI usage
- **[GUI Development Guide](GUI_DEVELOPMENT.md)** - Developer documentation for GUI codebase
- **[GUI Changelog](CHANGELOG_GUI.md)** - GUI-specific version history
- **[Main Changelog](CHANGELOG.md)** - Complete project version history
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to the project
- **[Project Summary](PROJECT_SUMMARY.md)** - Technical overview and architecture

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
