# Downloadyha GUI Installation Guide

Complete installation instructions for both CLI and GUI versions of Downloadyha.

---

## 🖥️ Desktop GUI Version

The GUI version provides a modern, user-friendly desktop interface for downloading YouTube videos and audio.

### Windows

#### Option 1: Pre-built Binary (Recommended)

1. Download `downloadyha-gui-windows.zip` from the [latest release](https://github.com/ahmed-tarek-2004/DownloadYha/releases)
2. Extract the ZIP file to a folder of your choice
3. Double-click `downloadyha-gui.exe` to launch
4. No installation required!

#### Option 2: Install via pip (Developers)

```powershell
# Install with GUI support
pip install downloadyha[gui]

# Launch the GUI
downloadyha-gui
```

### Linux

#### Option 1: Pre-built Binary (Recommended)

1. Download `downloadyha-gui-linux.tar.gz` from the [latest release](https://github.com/ahmed-tarek-2004/DownloadYha/releases)
2. Extract the archive:
   ```bash
   tar -xzf downloadyha-gui-linux.tar.gz
   ```
3. Make it executable:
   ```bash
   chmod +x downloadyha-gui
   ```
4. Run the application:
   ```bash
   ./downloadyha-gui
   ```

#### Option 2: Install via pip (Developers)

```bash
# Install with GUI support
pip install downloadyha[gui]

# Launch the GUI
downloadyha-gui
```

### System Requirements

- **Windows**: Windows 10/11 (64-bit)
- **Linux**: x86_64 or ARM64 with glibc 2.31+ and X11/Wayland
- **Internet connection** for downloads

---

## 💻 CLI Version (Command Line)

The CLI version provides a beautiful terminal interface with rich colors and progress bars.

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
downloadyha
```

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.sh | bash
```

Then run:

```bash
downloadyha
```

---

## 🔄 Side-by-Side Installation

Both CLI and GUI versions can be installed together and share the same configuration:

```bash
# Install base package
pip install downloadyha

# Install with GUI support
pip install downloadyha[gui]

# Launch CLI version
downloadyha

# Launch GUI version
downloadyha-gui
```

### Shared Features

Both versions share:
- ✅ **Configuration**: Same config file (`~/.local/share/downloadyha/config.json`)
- ✅ **Download History**: Shared download tracking
- ✅ **Dependency Management**: Common FFmpeg, yt-dlp, and Deno binaries
- ✅ **Update System**: Both use `downloadyha update` command

---

## 📦 Developer Installation

For developers who want to build from source:

### Prerequisites

- Python 3.10 or later
- pip and virtualenv (recommended)

### Setup

```bash
# Clone the repository
git clone https://github.com/ahmed-tarek-2004/DownloadYha.git
cd DownloadYha

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install in development mode with GUI support
pip install -e .[gui,dev]

# Run CLI
downloadyha

# Run GUI
downloadyha-gui
```

### Building Binaries

#### Windows

```powershell
# Build CLI version
.\build-windows.ps1

# Build GUI version
.\build-gui-windows.ps1

# Output:
# - dist/downloadyha.exe
# - dist/downloadyha-gui.exe
# - dist/downloadyha-gui-windows.zip
```

#### Linux

```bash
# Build CLI version
./build-linux.sh

# Build GUI version
./build-gui-linux.sh

# Output:
# - dist/downloadyha
# - dist/downloadyha-gui
# - dist/downloadyha-gui-linux.tar.gz
```

---

## 🎯 Quick Start

### GUI Usage

1. **Launch the application**
   - Windows: Double-click `downloadyha-gui.exe`
   - Linux: Run `./downloadyha-gui`
   - Or via command: `downloadyha-gui`

2. **Download a video or playlist**
   - Paste YouTube URL
   - Choose video or audio
   - Select quality
   - Choose download folder
   - Click "Download"

3. **Monitor progress**
   - Real-time progress bar
   - Status log with detailed information
   - Cancel anytime with Cancel button

### CLI Usage

Simply run:

```bash
downloadyha
```

Follow the interactive prompts to:
1. Enter YouTube URL (video or playlist)
2. Choose destination folder
3. Select download type (video/audio)
4. Select quality
5. Download with beautiful progress bars

---

## 🛠️ Commands

| Command | CLI | GUI | Description |
|---------|-----|-----|-------------|
| Launch interactive mode | `downloadyha` | `downloadyha-gui` | Start the application |
| Update to latest version | `downloadyha update` | N/A | Self-update from GitHub |
| Repair dependencies | `downloadyha repair` | N/A | Re-verify and restore FFmpeg, yt-dlp |
| Uninstall | `downloadyha uninstall` | N/A | Clean removal of all files |
| Check dependencies | `downloadyha --verify` | N/A | Verify system dependencies |
| Show version | `downloadyha --version` | See window title | Display version info |
| Show help | `downloadyha --help` | N/A | Show usage information |

---

## ⚙️ Configuration

Both CLI and GUI versions use the same configuration file:

**Windows**: `%LOCALAPPDATA%\Downloadyha\config.json`  
**Linux**: `~/.local/share/downloadyha/config.json`

Example configuration:

```json
{
  "download_directory": "C:\\Users\\YourName\\Downloads",
  "check_updates": true
}
```

The GUI automatically updates this file when you change the download folder.

---

## 🗑️ Uninstallation

### GUI Version (Pre-built Binary)

Simply delete the folder or executable.

### CLI Version

Use the built-in uninstaller:

```bash
downloadyha uninstall
```

Or manually:

**Windows:**
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Downloadyha"
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\Downloadyha"
```

**Linux:**
```bash
rm -rf ~/.local/share/downloadyha
rm -f ~/.local/bin/downloadyha
```

### pip Installation

```bash
pip uninstall downloadyha
```

---

## 🔒 Privacy

- 🚫 **Zero Tracking**: No telemetry or analytics
- 🔒 **Direct Downloads**: Streams directly from YouTube to your machine
- 🛡️ **Integrity Verification**: SHA-256 checksums for all updates

---

## ❓ Troubleshooting

### GUI won't start on Linux

Ensure you have the required display libraries:

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

### "customtkinter not found" error

Install the GUI dependencies:

```bash
pip install downloadyha[gui]
# or
pip install customtkinter
```

### CLI and GUI can't find each other

Make sure both are installed:

```bash
pip install downloadyha[gui]
```

### Downloads fail

1. Check your internet connection
2. Verify the YouTube URL is valid
3. Try updating: `downloadyha update` (CLI only)
4. Repair dependencies: `downloadyha repair` (CLI only)

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙋 Support

- **Issues**: [GitHub Issues](https://github.com/ahmed-tarek-2004/DownloadYha/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ahmed-tarek-2004/DownloadYha/discussions)
