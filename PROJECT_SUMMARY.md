# Downloadyha Project Summary

## Overview
Downloadyha is a modern, cross-platform downloader for videos, audio, and playlists from YouTube and other social media platforms. It provides both a Command Line Interface (CLI) and a Desktop Graphical User Interface (GUI). The tool is designed to be zero-configuration, bundling required dependencies (FFmpeg, Deno) and handling their automatic download and verification.

## Key Features
- **Partial Downloads (Clipping)**: Download specific sections of media using start/end timestamps.
- **Playlist Support**: Download entire playlists as video or audio with organized folder structure.
- **Format Selection**: Choose video resolution (up to 4K) or audio bitrate (MP3).
- **Subtitle Handling**: Download, embed, and convert subtitles in multiple formats (SRT, VTT, ASS, LRC) with language selection, auto-generated caption support, and format conversion.
- **Modern UI**: 
  - CLI: Interactive wizard with color-coded steps, progress bars, and summary cards.
  - GUI: CustomTkinter-based interface with light/dark themes, real-time progress, and settings persistence.
- **Self-Maintenance**: Commands for update, repair, dependency verification, and uninstallation.
- **Privacy Focused**: No telemetry, direct connections, SHA-256 verification of binaries.

## Architecture
The project follows a modular structure separating concerns into distinct modules:

### Core Modules (`src/downloadyha/`)
- `__init__.py`: Package metadata and version resolution.
- `__main__.py`: Entry point that launches the CLI.
- `cli.py`: Main CLI implementation (argument parsing, interactive workflow).
- `downloader.py`: Core download logic using yt-dlp, handling video/audio/playlist downloads, progress hooks, and result structures.
- `gui.py`: Desktop GUI implementation using tkinter/CustomTkinter.
- `config.py`: User configuration management (platform-specific config.json).
- `dependencies.py`: Dependency resolution, automatic download, and verification (FFmpeg, Deno, yt-dlp).
- `network.py`: HTTP utilities for downloading dependency binaries.
- `platform.py`: Platform detection helpers.
- `paths.py`: Directory resolution for binaries, logs, cache, etc.
- `logging.py`: Logging configuration.
- `uninstaller.py`: Uninstallation logic.
- `updater.py`: Self-update mechanism via GitHub Releases.

### GUI Module (`src/downloadyha_gui/`)
- Contains the standalone GUI launcher and resources (icon).

## Workflow
1. **Entry Point**: Execution starts via `downloadyha` CLI command or `downloadyha-gui` GUI executable.
2. **Dependency Check**: On startup, the application verifies required dependencies (FFmpeg, Deno, yt-dlp) and can auto-download missing ones.
3. **User Interaction**:
   - **CLI**: Presents an interactive step-by-step wizard (URL input, destination folder, quality/format selection, optional clipping).
   - **GUI**: User enters URL, selects options via form, and starts download.
4. **Processing**:
   - Metadata extraction via yt-dlp to determine if URL is a single video or playlist.
   - Based on user selections, appropriate downloader function is called (`download_video`, `download_audio`, `download_playlist`).
   - yt-dlp is configured with selected options (format, output template, post-processing for MP3/audio extraction, subtitle handling, range selection for clipping).
   - Progress hooks relay real-time updates to CLI/GUI.
5. **Completion**: Structured `DownloadResult` is returned, indicating success/failure and providing statistics.

## Dependency Management
- Bundled binaries for FFmpeg and Deno are stored in the platform-specific app data directory under `bin/`.
- The `dependencies.py` module handles:
  - Locating binaries in the app directory or system PATH.
  - Automatic download from configured URLs (specified in `versions.json`) with SHA-256 verification.
  - Extraction and placement of executables.
  - Making binaries executable on POSIX systems.
- yt-dlp is expected to be available via the Python package installation.

## Configuration
- User preferences (default download directory, theme, update checks, quality preferences) are saved in a `config.json` file located in:
  - Windows: `%LOCALAPPDATA%\Downloadyha\config.json`
  - Linux: `~/.config/downloadyha/config.json`
- The config is loaded at startup and saved on changes; missing keys are filled with defaults.

## Logging
- Application logs are written to a file in the platform-specific log directory (`logs/`) when enabled.
- Logging levels can be adjusted via the `--verbose` flag.

## Self-Update and Repair
- **Update**: Checks GitHub Releases for the latest version and downloads/installs updates.
- **Repair**: Forces re-download and verification of FFmpeg and Deno binaries.
- **Verify**: Checks availability and integrity of all dependencies.

## Installation and Usage
### CLI Installation
- **Windows**: PowerShell script (`irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex`)
- **Linux**: Bash script (`curl -fsSL https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.sh | bash`)
- After installation, run `downloadyha` in terminal.

### GUI Installation
- **Option 1 (Recommended)**: Download pre-built standalone binaries from GitHub Releases.
- **Option 2**: Install via Python/pip: `pip install "downloadyha[gui]"` then run `downloadyha-gui`.

## Extensibility
- The CLI and GUI share the same downloader backend, making it easy to add new features (e.g., additional metadata extraction, new output formats).
- Adding new dependency types would involve extending `dependencies.py` with download/verification logic.

## License
Distributed under the MIT License. See `LICENSE` file for details.
