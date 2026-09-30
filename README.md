# Downloadyha

A fast, standalone YouTube downloader CLI. No Python, FFmpeg, Deno, or yt-dlp installation required.

## Quick Start

### Windows

Open PowerShell and run:

```powershell
irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex
```

Then:

```powershell
downloadyha
```

### Linux

Open terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.sh | bash
```

Then:

```bash
downloadyha
```

That's it. No other installation steps required.

---

## Features

- **Download YouTube videos** in available qualities (144p to 4K+)
- **Download audio as MP3** (Best, 128, 192, or 320 kbps)
- **Dynamic quality selection** based on what's actually available
- **Custom download directory** or use Downloads folder by default
- **Progress tracking** with speed and ETA
- **Self-updating** - update with a single command
- **Self-repairing** - fix corrupted installations automatically
- **Completely standalone** - all dependencies bundled

---

## Requirements

**None.**

Downloadyha is a standalone application. You don't need to install:

- ❌ Python
- ❌ pip
- ❌ FFmpeg
- ❌ Deno
- ❌ yt-dlp
- ❌ Any other runtime or dependency

Everything is bundled and managed automatically.

---

## Supported Platforms

- ✅ Windows 10 (64-bit)
- ✅ Windows 11 (64-bit)
- ✅ Linux x64 (glibc 2.31+)
- ✅ Linux ARM64 (glibc 2.31+)

---

## Usage

### Download a Video or Audio

Simply run:

```bash
downloadyha
```

You'll be prompted for:

1. **YouTube URL** - paste the video link
2. **Download folder** - press Enter for Downloads, or specify a custom path
3. **Download type** - choose Audio or Video
4. **Quality** - select from available options

Example session:

```
=======================================================
                  Downloadyha
=======================================================
              YouTube Downloader
=======================================================

Enter YouTube URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ

Enter download folder (leave empty for Downloads): 

Getting video information...

Title: Rick Astley - Never Gonna Give You Up (Official Video)

Choose download type:
1. Audio
2. Video

Enter your choice: 2

Available video qualities:
1. 144p
2. 240p
3. 360p
4. 480p
5. 720p
6. 1080p

Choose quality: 6

Downloading video...

Downloading 45.2% | Speed: 2.3 MB/s | ETA: 00:15
```

---

## Commands

### Main Command

```bash
downloadyha
```

Launch the interactive downloader.

### Update Downloadyha

```bash
downloadyha update
```

Check for and install the latest version of Downloadyha.

Example output:

```
Current version: 1.0.0
Latest version: 1.1.0

A new version is available.

Updating Downloadyha...

✓ Downloaded downloadyha-linux-x64
✓ Verified checksum
✓ Installed successfully

Downloadyha updated to 1.1.0

Restart your terminal or run 'downloadyha' to use the new version.
```

### Repair Installation

```bash
downloadyha repair
```

If Downloadyha isn't working correctly, repair will:

- Re-download and verify all bundled dependencies
- Fix file permissions (Linux)
- Restore corrupted binaries
- Verify installation integrity

Example output:

```
Repairing Downloadyha installation...

✓ Verified downloadyha executable
✓ Verified FFmpeg (version 7.0.2)
✓ Verified FFprobe
✓ Verified Deno (version 2.0.0)
✓ Verified yt-dlp (version 2026.09.01)

Installation is healthy.
```

---

## Update Policy

Downloadyha checks for updates automatically (at most once per 24 hours) and notifies you when a new version is available. It will **never** update automatically without your permission.

When a new version is available, you'll see:

```
A new version of Downloadyha is available.

Current: 1.0.0
Latest: 1.1.0

Run:

    downloadyha update
```

To disable update checks, edit your configuration file (see Configuration below).

---

## Configuration

Downloadyha stores user settings in:

- **Windows**: `%LOCALAPPDATA%\Downloadyha\config.json`
- **Linux**: `~/.local/share/downloadyha/config.json`

Example configuration:

```json
{
  "download_directory": "C:\\Users\\YourName\\Videos",
  "check_updates": true,
  "last_update_check": "2026-09-30T12:00:00Z"
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `download_directory` | string | `~/Downloads` | Default download folder |
| `check_updates` | boolean | `true` | Enable automatic update checks |

Updating Downloadyha preserves your configuration.

---

## Application Data Locations

Downloadyha stores its managed dependencies and data in platform-specific directories:

### Windows

```
%LOCALAPPDATA%\Downloadyha\
├── bin\              # FFmpeg, Deno binaries
├── logs\             # Application logs
├── cache\            # Temporary download cache
└── config.json       # User configuration
```

### Linux

```
~/.local/share/downloadyha/
├── bin/              # FFmpeg, Deno binaries
├── logs/             # Application logs
├── cache/            # Temporary download cache
└── config.json       # User configuration
```

The executable itself is installed in:

- **Windows**: `%LOCALAPPDATA%\Programs\Downloadyha\downloadyha.exe`
- **Linux**: `~/.local/bin/downloadyha`

---

## Troubleshooting

### "downloadyha: command not found" (Linux)

The installer adds `~/.local/bin` to your PATH. If the command isn't found:

1. Close and reopen your terminal
2. If still not working, add this to your `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then run:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

### "Cannot be loaded because running scripts is disabled" (Windows)

If you see a PowerShell execution policy error:

1. Open PowerShell as Administrator
2. Run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. Try the installation again

### Download fails with "Video unavailable"

- Verify the YouTube URL is correct and the video is publicly accessible
- The video may be region-locked or age-restricted
- Try updating Downloadyha: `downloadyha update`

### Download fails with dependency errors

Run the repair command:

```bash
downloadyha repair
```

This will re-download and verify all bundled dependencies.

### Slow download speeds

- Your network connection speed limits the download
- YouTube may throttle download speeds during peak hours
- Try downloading at a different time
- Check your internet connection

### "Permission denied" (Linux)

If you get permission errors:

```bash
chmod +x ~/.local/bin/downloadyha
```

Or run:

```bash
downloadyha repair
```

### Application crashes or hangs

1. Check the logs:
   - **Windows**: `%LOCALAPPDATA%\Downloadyha\logs\`
   - **Linux**: `~/.local/share/downloadyha/logs/`

2. Try repairing:

```bash
downloadyha repair
```

3. If the issue persists, please [open an issue](https://github.com/<USER>/<REPO>/issues) with:
   - Your operating system and version
   - The YouTube URL (if applicable)
   - Log files from the logs directory
   - The exact error message

---

## Uninstallation

### Windows

Run in PowerShell:

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Downloadyha"
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Programs\Downloadyha"
```

Then remove `%LOCALAPPDATA%\Programs\Downloadyha` from your PATH (optional).

### Linux

Run in terminal:

```bash
rm -rf ~/.local/share/downloadyha
rm ~/.local/bin/downloadyha
```

---

## Privacy

Downloadyha:

- Does **not** collect or transmit any personal data
- Does **not** track your downloads
- Does **not** send analytics
- Only communicates with:
  - **YouTube** (to download videos you request)
  - **GitHub** (to check for updates when you run `downloadyha update` or during automatic update checks)

All downloads are stored locally on your machine. No data is sent to any third-party service.

---

## How It Works

Downloadyha is a self-contained application that bundles all its dependencies:

1. **Python runtime** - bundled and managed internally
2. **FFmpeg** - bundled for audio/video processing
3. **Deno** - bundled for JavaScript extraction (required by yt-dlp for some videos)
4. **yt-dlp** - bundled for YouTube downloading

When you run `downloadyha`:

1. It verifies all bundled dependencies are present and valid
2. Extracts video metadata from YouTube using yt-dlp
3. Downloads the requested quality using yt-dlp
4. Processes audio/video using FFmpeg
5. Saves the final file to your chosen directory

All dependencies are verified with SHA-256 checksums before execution.

---

## Building from Source

See [CONTRIBUTING.md](CONTRIBUTING.md) for developer documentation.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Downloadyha is built on top of excellent open-source projects:

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [FFmpeg](https://ffmpeg.org/) - Media processing
- [Deno](https://deno.land/) - JavaScript runtime

---

## Support

- **Issues**: [GitHub Issues](https://github.com/<USER>/<REPO>/issues)
- **Discussions**: [GitHub Discussions](https://github.com/<USER>/<REPO>/discussions)

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.
