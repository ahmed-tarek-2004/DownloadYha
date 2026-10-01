# Downloadyha Desktop GUI

A beautiful, modern desktop application for downloading YouTube videos and audio, built with CustomTkinter.

![Downloadyha GUI](https://img.shields.io/badge/GUI-CustomTkinter-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

## Features

### 🎨 Modern Interface
- **Dark/Light/System Theme Support** - Automatically detects and matches your system theme
- **Cyber-Themed Color Palette** - Electric Cyan, Cyber Purple, and Emerald Green accents matching the CLI
- **Responsive Layout** - Adapts to different window sizes

### ⬇️ Download Tab
- **URL Input** with paste button for quick clipboard insertion
- **Quality Selection** with presets:
  - **Video Mode**: Best, 4K, 2K, 1080p, 720p, 480p, 360p
  - **Audio Mode**: Best, 320kbps, 192kbps, 128kbps
- **Folder Picker** with browse dialog
- **Real-time Progress Bar** showing:
  - Download percentage
  - Download speed
  - Estimated time remaining (ETA)
- **Cancel Button** - Stop downloads in progress

### 📋 Queue Tab
- Queue management interface (coming soon)
- Future support for batch downloads

### ⚙️ Settings Tab
- **Default Download Path** configuration
- **Theme Selector** (Dark/Light/System)
- **Auto-Update Toggle** for background update checking
- **About Section** with version and author information

## Installation

### 1. Install Dependencies

```bash
# Install GUI requirements
pip install -r requirements-gui.txt
```

The GUI requires:
- `customtkinter>=5.2.0` - Modern UI framework
- `pillow>=10.0.0` - Image processing
- `yt-dlp>=2026.8.19` - YouTube download engine

### 2. Verify Installation

```bash
# Check if customtkinter is installed
python -c "import customtkinter; print('CustomTkinter installed successfully')"
```

## Usage

### Launch the GUI

There are multiple ways to launch the GUI:

#### Method 1: Direct Python Execution
```bash
python src/downloadyha_gui/app.py
```

#### Method 2: Using the Launcher
```bash
python src/downloadyha_gui/launcher.py
```

#### Method 3: Module Execution
```bash
python -m downloadyha_gui.app
```

### Quick Start Guide

1. **Enter URL**: Paste or type a YouTube video/playlist URL
2. **Select Mode**: Choose Video or Audio
3. **Pick Quality**: Select desired quality from the dropdown
4. **Choose Destination**: Browse to select where files should be saved
5. **Click Download**: Press the download button to start
6. **Monitor Progress**: Watch real-time progress with speed and ETA
7. **Cancel if Needed**: Click the Cancel button to stop

### Configuration

Settings are automatically saved to:
- **Windows**: `%LOCALAPPDATA%\Downloadyha\config.json`
- **Linux**: `~/.config/downloadyha/config.json`

## Architecture

### Integration with Core Engine

The GUI seamlessly integrates with the existing Downloadyha core:

```python
from downloadyha.config import load, save, get_download_dir
from downloadyha.downloader import download_video, download_audio
```

### Threading Model

Downloads run in background threads to prevent UI freezing:
- Main thread handles UI rendering and user interactions
- Worker threads execute downloads with progress callbacks
- Thread-safe updates to UI via `after()` method

### Progress Callback

Real-time progress updates through callback mechanism:

```python
def progress_callback(data: Dict[str, Any]):
    percent = data.get("percent", 0.0)
    speed_str = data.get("speed_str", "--")
    eta_str = data.get("eta_str", "--")
    # Update UI elements...
```

## Color Palette

The GUI uses the same cyber-themed palette as the CLI:

| Color | RGB | Hex | Usage |
|-------|-----|-----|-------|
| Electric Cyan | (0, 210, 255) | #00D2FF | Primary accent, buttons |
| Cyber Purple | (155, 81, 224) | #9B51E0 | Secondary accent, hover states |
| Emerald Green | (46, 204, 113) | #2ECC71 | Success messages |
| Amber Yellow | (241, 196, 15) | #F1C40F | Warnings |
| Crimson Red | (231, 76, 60) | #E7484C | Errors, cancel button |

## Troubleshooting

### CustomTkinter Not Found
```bash
pip install customtkinter --upgrade
```

### Theme Not Applying
- Ensure you're using Python 3.10+
- Check system theme settings
- Try manually selecting Dark or Light mode

### Progress Not Updating
- Ensure downloads are running in background thread
- Check that `progress_callback` is properly connected
- Verify yt-dlp is installed and up to date

### Download Fails
- Verify the YouTube URL is valid
- Check internet connection
- Ensure destination folder has write permissions
- Try updating yt-dlp: `pip install yt-dlp --upgrade`

## Development

### Project Structure

```
src/downloadyha_gui/
├── __init__.py          # Package initialization
├── app.py               # Main GUI application
└── launcher.py          # Cross-platform launcher script
```

### Running in Development Mode

```bash
# From project root
cd src
python -m downloadyha_gui.app
```

### Future Enhancements

- [ ] Download queue management with pause/resume
- [ ] Batch URL processing from file
- [ ] Download history tracking
- [ ] Thumbnail preview
- [ ] Format conversion options
- [ ] Subtitle download support
- [ ] Custom output filename templates
- [ ] System tray integration
- [ ] Notification support

## Credits

**Author**: Ahmed Tarek Zaher  
**Framework**: CustomTkinter by Tom Schimansky  
**Engine**: yt-dlp by yt-dlp contributors  

## License

This GUI application is part of the Downloadyha project.

---

**Crafted with ⚡ by Ahmed Tarek Zaher**
