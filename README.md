# Downloadyha

A fast, modern, and beautiful YouTube downloader available in both **Desktop GUI** and **CLI** versions for **Videos**, **Audio (MP3)**, and **Full Playlists**. No Python, FFmpeg, Deno, or yt-dlp setup required.

---

## 🖥️ Desktop GUI - Installation & Quick Start

The **Downloadyha Desktop GUI** provides a sleek graphical interface featuring real-time metadata fetching, dynamic quality selection (up to 4K), audio extraction, download history, and dark/light themes.

### Option 1: Standalone Download (No Python Required — Recommended)

Download the pre-built standalone app for your operating system:

| Platform | Download | Instructions |
|---|---|---|
| **Windows 10/11 (64-bit)** | **[⬇️ Download Windows GUI (ZIP)](https://github.com/ahmed-tarek-2004/DownloadYha/releases/latest/download/downloadyha-gui-windows.zip)** | Extract the ZIP and double-click `downloadyha-gui.exe` |
| **Linux (x86_64)** | **[⬇️ Download Linux GUI (tar.gz)](https://github.com/ahmed-tarek-2004/DownloadYha/releases/latest/download/downloadyha-gui-linux-x86_64.tar.gz)** | Extract archive and run `./downloadyha-gui` |

#### 3-Step Windows Quick Start:
1. **Download & Extract** `downloadyha-gui-windows.zip` to a folder of your choice (e.g. `Downloads` or `C:\Program Files\DownloadyhaGUI`).
2. **Double-click** `downloadyha-gui.exe` to launch.
3. **Paste any YouTube URL** — the app automatically fetches video details (Title, Channel, Duration) and populates the available video/audio resolutions!

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

For terminal power-users, Downloadyha offers a rich, interactive CLI experience with color-coded steps, live progress bars, and batch playlist support.

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

## 🌟 Key Features

### 🖥️ Desktop GUI
- 🎨 **Modern Interface**: CustomTkinter UI with glassmorphism cards and smooth themes (Dark, Light, System).
- 🔍 **Real-Time Metadata Fetching**: Automatically inspects video/playlist URLs to show Title, Channel, Duration, and Type.
- 🎯 **Dynamic Quality Dropdown**: Automatically detects and lists exact available resolutions (4K 2160p, 1440p, 1080p, 720p, 480p, 360p, etc.).
- 🎵 **Audio MP3 Extractor**: One-click MP3 conversion with custom bitrate presets (320 kbps, 192 kbps, 128 kbps).
- 📑 **Full Playlist Downloads**: One-click batch downloading of entire video or audio playlists.
- 📜 **Download History & Management**: Track recent downloads and open downloaded files or destination folders directly.
- 🔄 **Non-Blocking Downloads**: Smooth multithreaded downloading with live progress indicators.

### ⚡ Terminal CLI
- 🎬 **Interactive Wizard**: Step-by-step guidance (`[1/3] Enter URL`, `[2/3] Folder`, `[3/3] Quality`).
- 📊 **Rich Progress Bars**: Displays speed, percentage, ETA, and batch counters (`[3/15]`).
- 📑 **Automated Playlist Indexing**: Organizes batch downloads into numbered subfolders.
- 🔄 **Self-Updater & Repair**: Built-in update checker and dependency repair tools (`downloadyha update`, `downloadyha repair`).

---

## 🛠️ Available Commands

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

---

## ⚙️ Configuration

Downloadyha stores your preferences (default download folder, background update checks) in a standard configuration file:

- **Windows**: `%LOCALAPPDATA%\Downloadyha\config.json`
- **Linux**: `~/.local/share/downloadyha/config.json`

---

## 🗑️ Uninstallation

Uninstall cleanly at any time using:

```bash
downloadyha uninstall
```

For the standalone GUI ZIP, simply delete the extracted folder.

---

## 🔒 Privacy

- 🚫 **Zero Telemetry**: No tracking, analytics, or personal data collection.
- 🔒 **Direct Connection**: Downloads stream directly from YouTube to your local disk.
- 🛡️ **Integrity Verification**: Released binaries and updates are verified against SHA-256 checksums.

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
