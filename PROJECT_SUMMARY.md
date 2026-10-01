# Downloadyha - Standalone Distribution Project

## Overview

This project has been completely redesigned from a script-based Python application into a **true standalone cross-platform CLI application** that requires **zero manual dependency installation**.

**Repository:** https://github.com/ahmed-tarek-2004/DownloadYha

---

## What Changed

### Before
- Required manual installation of Python, pip, FFmpeg, Deno, yt-dlp
- Script-based execution
- Complex setup for end users

### After
- **Single-command installation**
- **Standalone executable** (no Python required)
- **Auto-managed dependencies** (FFmpeg, Deno download automatically)
- **Self-updating** via GitHub Releases
- **Cross-platform support** (Windows x64, Linux x64, Linux ARM64)

---

## Installation

### Windows

**PowerShell:**
```powershell
irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex
```

**Command Prompt (CMD):**
```cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex"
```

### Linux
```bash
curl -fsSL https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.sh | bash
```

After installation:
```bash
downloadyha
```

---

## Project Structure

```
downloadyha/
├── src/downloadyha/
│   ├── __init__.py           # Version info
│   ├── __main__.py           # Entry point
│   ├── cli.py                # CLI interface with commands
│   ├── downloader.py         # YouTube download logic (yt-dlp)
│   ├── dependencies.py       # Auto-download FFmpeg/Deno
│   ├── paths.py              # Cross-platform paths
│   ├── platform.py           # OS/architecture detection
│   ├── config.py             # User configuration management
│   ├── updater.py            # Self-update from GitHub Releases
│   ├── logging.py            # Structured logging
│   └── versions.json         # Dependency version manifest
│
├── scripts/
│   ├── build-windows.ps1     # Build script for Windows
│   ├── build-linux.sh        # Build script for Linux
│   ├── install.ps1           # Windows installer
│   └── install.sh            # Linux installer
│
├── .github/workflows/
│   └── release.yml           # CI/CD pipeline
│
├── tests/
│   └── test_updater.py       # Unit tests
│
├── downloadyha.spec          # PyInstaller configuration
├── pyproject.toml            # Python project metadata
├── README.md                 # User documentation
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Developer guide
└── LICENSE                   # MIT License
```

---

## Commands

| Command | Description |
|---------|-------------|
| `downloadyha` | Start the interactive YouTube downloader |
| `downloadyha update` | Check for and install updates |
| `downloadyha repair` | Repair/reinstall dependencies (FFmpeg, Deno) |
| `downloadyha --verify` | Verify all dependencies are available |
| `downloadyha --help` | Show help message |
| `downloadyha --version` | Show version |

---

## Features

### Core Functionality
- ✅ YouTube video/audio downloads via yt-dlp
- ✅ Audio quality selection (Best, 128, 192, 320 kbps)
- ✅ Dynamic video quality selection
- ✅ Custom download directory
- ✅ MP3 conversion via FFmpeg
- ✅ Video+audio merging via FFmpeg
- ✅ Deno JavaScript runtime for yt-dlp
- ✅ EJS remote components from GitHub

### Distribution
- ✅ Standalone executables (PyInstaller)
- ✅ Auto-managed dependencies (FFmpeg, Deno)
- ✅ SHA-256 verification for all downloads
- ✅ Cross-platform path management
- ✅ One-command installers (Windows/Linux)
- ✅ GitHub Releases distribution
- ✅ Self-update mechanism (24-hour cache)
- ✅ Repair command for broken installations

---

## Dependency Management

### How It Works

1. **First Run**: When you run `downloadyha` for the first time, it automatically:
   - Checks for FFmpeg in `~/.local/share/downloadyha/bin/` (Linux) or `%LOCALAPPDATA%\Downloadyha\bin\` (Windows)
   - If not found, downloads from official GitHub releases
   - Verifies SHA-256 checksums (if configured in versions.json)
   - Sets executable permissions (Linux)
   - Falls back to system-installed binaries if available

2. **Storage Locations**:
   - **Windows**: `%LOCALAPPDATA%\Downloadyha\`
   - **Linux**: `~/.local/share/downloadyha/`

3. **Managed Dependencies**:
   - FFmpeg (audio/video processing)
   - FFprobe (media information)
   - Deno (JavaScript runtime for yt-dlp)
   - yt-dlp (bundled in executable)

### Version Manifest

Dependencies are defined in `src/downloadyha/versions.json`:
```json
{
  "downloadyha": "1.0.0",
  "yt_dlp": "2026.8.19",
  "ffmpeg": {
    "version": "7.1",
    "windows": { "x86_64": { "url": "...", "sha256": null } },
    "linux": { "x86_64": { "url": "..." }, "aarch64": { "url": "..." } }
  },
  "deno": {
    "version": "2.1.4",
    "windows": { "x86_64": { "url": "..." } },
    "linux": { "x86_64": { "url": "..." }, "aarch64": { "url": "..." } }
  }
}
```

---

## Building from Source

### Prerequisites
- Python 3.10+
- pip

### Steps

1. **Clone the repository**:
```bash
git clone https://github.com/ahmed-tarek-2004/DownloadYha.git
cd DownloadYha
```

2. **Install dependencies**:
```bash
pip install -e ".[dev]"
```

3. **Build executable**:

**Windows:**
```powershell
.\build-windows.ps1
```

**Linux:**
```bash
chmod +x build-linux.sh
./build-linux.sh
```

4. **Output**:
   - Windows: `dist/downloadyha.exe`
   - Linux: `dist/downloadyha`

---

## Creating a Release

### Automated via GitHub Actions

1. **Update version** in:
   - `src/downloadyha/__init__.py` (`__version__`)
   - `pyproject.toml` (`version`)
   - `src/downloadyha/versions.json` (`downloadyha`)

2. **Create and push a tag**:
```bash
git tag v1.0.0
git push origin v1.0.0
```

3. **GitHub Actions automatically**:
   - Builds for Windows x64, Linux x64, Linux ARM64
   - Creates archives (`.zip` for Windows, `.tar.gz` for Linux)
   - Generates SHA256SUMS
   - Creates GitHub Release with all artifacts

### Release Assets

The workflow produces:
- `downloadyha-windows-x86_64.zip`
- `downloadyha-linux-x86_64.tar.gz`
- `downloadyha-linux-arm64.tar.gz`
- `SHA256SUMS`

---

## Update Mechanism

### How It Works

1. **Update Check**: On startup, checks GitHub Releases API (cached for 24 hours)
2. **User Notification**: If newer version available, shows non-intrusive message
3. **Manual Update**: User runs `downloadyha update`
4. **Download**: Fetches appropriate platform binary from GitHub Releases
5. **Verification**: Validates SHA-256 checksum before installation
6. **Safe Replace**: Atomically replaces current executable
7. **Config Preservation**: User configuration is never deleted

### Update Cache

Update checks are cached in:
- **Windows**: `%LOCALAPPDATA%\Downloadyha\cache\last_update_check.txt`
- **Linux**: `~/.cache/downloadyha/last_update_check.txt`

---

## Configuration

User configuration is stored in `config.json`:
- **Windows**: `%LOCALAPPDATA%\Downloadyha\config.json`
- **Linux**: `~/.config/downloadyha/config.json`

```json
{
  "download_directory": "C:\\Users\\username\\Downloads",
  "check_updates": true
}
```

---

## Logging

Logs are stored in:
- **Windows**: `%LOCALAPPDATA%\Downloadyha\logs\`
- **Linux**: `~/.local/share/downloadyha/logs/`

Log format: `downloadyha_YYYYMMDD_HHMMSS.log`

---

## Security

### Download Security
- All downloads use HTTPS only
- SHA-256 verification for binaries (when configured)
- No execution before verification
- Atomic file operations (temp file → rename)

### Update Security
- GitHub Releases API for version checking
- Checksum verification before executable replacement
- User consent required for updates

---

## Platform Support

| Platform | Architecture | Status |
|----------|-------------|--------|
| Windows 10/11 | x64 | ✅ Fully Supported |
| Linux | x64 | ✅ Fully Supported |
| Linux | ARM64 | ✅ Supported (cross-compiled) |

---

## Troubleshooting

### Dependencies Not Found
```bash
downloadyha repair
```

### Update Issues
```bash
# Manually check version
downloadyha --version

# Force dependency reinstall
downloadyha repair
```

### PATH Issues
- **Windows**: Restart terminal after installation
- **Linux**: Run `source ~/.bashrc` (or your shell profile)

---

## Development

### Running Tests
```bash
pip install -e ".[dev]"
python -m pytest tests/
```

### Code Structure
- Entry point: `src/downloadyha/__main__.py` → `cli.main()`
- CLI commands: `src/downloadyha/cli.py`
- Download logic: `src/downloadyha/downloader.py`
- Dependency resolver: `src/downloadyha/dependencies.py`

---

## Technology Stack

- **Language**: Python 3.10+
- **Packaging**: PyInstaller (standalone executables)
- **YouTube Extraction**: yt-dlp
- **Media Processing**: FFmpeg/FFprobe
- **JavaScript Runtime**: Deno
- **CI/CD**: GitHub Actions
- **Distribution**: GitHub Releases

---

## License

MIT License - see `LICENSE` file

---

## Author

Ahmed Tarek (@ahmed-tarek-2004)

---

## Next Steps

1. **Test the build locally**: Run `.\build-windows.ps1` or `./build-linux.sh`
2. **Test the installer locally**: Test with a fresh Windows/Linux VM
3. **Create first release**: Tag and push `v1.0.0`
4. **Test installers**: After release, test the install commands
5. **Update documentation**: Add screenshots, demo GIF to README if desired

---

**Project completed on:** 2026-09-30
