# Downloadyha Desktop GUI - User Guide

## Overview

Downloadyha Desktop GUI provides a user-friendly graphical interface for downloading YouTube videos, audio, and playlists. This guide covers all features and functionality of the desktop application.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Main Interface](#main-interface)
- [Downloading Videos](#downloading-videos)
- [Downloading Audio](#downloading-audio)
- [Downloading Playlists](#downloading-playlists)
- [Settings and Preferences](#settings-and-preferences)
- [Troubleshooting](#troubleshooting)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [FAQ](#faq)

---

## Getting Started

### Installation

#### Windows

1. Open PowerShell or Command Prompt
2. Run the installation command:
   ```powershell
   powershell -Command "irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex"
   ```
3. After installation, launch from Start Menu or run `downloadyha gui`

#### Linux

1. Open terminal
2. Run the installation command:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.sh | bash
   ```
3. After installation, run `downloadyha gui`

### Launching the GUI

**Method 1: Command Line**
```bash
downloadyha gui
```

**Method 2: Desktop Shortcut (Windows)**
- Look for "Downloadyha" in Start Menu
- Click to launch (may open CLI by default; use `downloadyha gui` for GUI)

**Method 3: Direct Execution**
```bash
# If running from source
python -m downloadyha.gui
```

---

## Main Interface

### Window Layout

The main window consists of the following sections:

```
┌─────────────────────────────────────────────────────────────┐
│  Downloadyha v1.0.0                           [🌙 Dark]     │
├─────────────────────────────────────────────────────────────┤
│  YouTube URL                                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ https://www.youtube.com/watch?v=...                 │    │
│  └─────────────────────────────────────────────────────┘    │
│  ✓ Valid YouTube URL                                        │
│                                                             │
│  Title: Rick Astley - Never Gonna Give You Up              │
│  Channel: RickAstleyVEVO                                    │
│  Duration: 03:33                                            │
│  Type: Single Video                                         │
├─────────────────────────────────────────────────────────────┤
│  Download Options                                           │
│                                                             │
│  Download Type:  ○ Video   ● Audio (MP3)                   │
│                                                             │
│  Audio Quality:  [Best (Variable Bitrate ~256-320 kbps) ▼]  │
│                                                             │
│  Save to:  [C:\Users\...\Downloads              ] [Browse]  │
├─────────────────────────────────────────────────────────────┤
│  Progress                                                   │
│  [████████████████████░░░░░░░░░░░░░░░░░░] 65.4%            │
│  Downloading: Rick Astley - Never Gonna Give You Up        │
│  Speed: 18.5 MB/s                          ETA: 00:03      │
├─────────────────────────────────────────────────────────────┤
│  [Fetch Info]  [Download]  [Cancel]           [Open Folder]│
├─────────────────────────────────────────────────────────────┤
│  Ready                                                      │
└─────────────────────────────────────────────────────────────┘
```

### Sections Explained

#### 1. Header Bar
- **Application Title**: Shows version number
- **Theme Toggle**: Switch between Light and Dark themes

#### 2. URL Input Section
- **Text Field**: Paste YouTube video or playlist URL
- **Validation Indicator**: Shows if URL is valid (✓) or invalid (✗)
- **Media Info Card**: Displays video/playlist information after fetching

#### 3. Download Options
- **Download Type**: Choose Video (MP4) or Audio (MP3)
- **Quality Selection**: Choose resolution for video or bitrate for audio
- **Save Location**: Set download destination folder

#### 4. Progress Section
- **Progress Bar**: Visual progress indicator
- **Status Text**: Current download status
- **Speed & ETA**: Real-time download statistics

#### 5. Action Buttons
- **Fetch Info**: Get video/playlist information before downloading
- **Download**: Start the download
- **Cancel**: Cancel an in-progress download
- **Open Folder**: Open download folder in file explorer

#### 6. Status Bar
- Shows current application status and results

---

## Downloading Videos

### Step-by-Step Guide

**Step 1: Enter URL**
1. Copy a YouTube video URL from your browser
2. Paste into the URL field (Ctrl+V or right-click → Paste)
3. Wait for validation (green checkmark indicates valid URL)

**Screenshot Description**: 
> The URL field shows "https://www.youtube.com/watch?v=dQw4w9WgXcQ" with a green checkmark and "✓ Valid YouTube URL" message below it.

**Step 2: Fetch Media Info (Optional but Recommended)**
1. Click "Fetch Info" button
2. Wait for video information to load
3. Review title, channel, duration, and type

**Screenshot Description**:
> Media info card displays:
> - Title: Rick Astley - Never Gonna Give You Up
> - Channel: RickAstleyVEVO
> - Duration: 03:33
> - Type: Single Video

**Step 3: Configure Download Options**
1. Select "Video" as download type
2. Choose video quality from dropdown:
   - **Best Available**: Maximum quality (recommended)
   - **2160p (4K UHD)**: Ultra HD (if available)
   - **1440p (2K QHD)**: Quad HD
   - **1080p (Full HD)**: Standard Full HD
   - **720p (HD)**: Standard HD
   - **480p (SD)**: Standard Definition
   - **360p (Low)**: Lower quality, smaller file

3. Verify or change download location:
   - Default: Your Downloads folder
   - Click "Browse" to select a different folder

**Step 4: Start Download**
1. Click "Download" button
2. Watch progress in real-time:
   - Progress bar updates
   - Speed shows download rate
   - ETA shows estimated time remaining

**Screenshot Description**:
> Progress bar shows 65% complete with "Downloading: Rick Astley - Never Gonna Give You Up", Speed: 18.5 MB/s, ETA: 00:03

**Step 5: Completion**
1. When download finishes, success dialog appears
2. Click "Open Folder" to view downloaded file
3. File is saved as MP4 in your chosen location

**Screenshot Description**:
> Success dialog shows "Download complete! Saved to: C:\Users\...\Downloads"

### Video Quality Guide

| Quality | Resolution | Use Case | File Size (approx. for 5 min) |
|---------|-----------|----------|------------------------------|
| Best Available | Up to 4K | Best quality, large display | 500MB - 2GB |
| 2160p (4K) | 3840×2160 | 4K displays | 400MB - 1.5GB |
| 1440p (2K) | 2560×1440 | High-end monitors | 250MB - 800MB |
| 1080p (Full HD) | 1920×1080 | Standard HD viewing | 150MB - 500MB |
| 720p (HD) | 1280×720 | General use, mobile | 75MB - 250MB |
| 480p (SD) | 854×480 | Smaller screens, saving space | 40MB - 100MB |
| 360p (Low) | 640×360 | Minimal storage | 20MB - 60MB |

---

## Downloading Audio

### Step-by-Step Guide

**Step 1: Enter URL**
- Same as video download (see above)

**Step 2: Configure Audio Options**
1. Select "Audio (MP3)" as download type
2. Quality dropdown changes to audio options:
   - **Best (VBR ~256-320 kbps)**: Highest quality, variable bitrate
   - **320 kbps**: Maximum constant bitrate
   - **192 kbps**: Standard quality
   - **128 kbps**: Compact size

**Step 3: Download**
1. Click "Download"
2. Progress shows audio extraction
3. MP3 file saved to chosen location

### Audio Quality Guide

| Quality | Bitrate | Use Case | File Size (approx. for 5 min) |
|---------|---------|----------|------------------------------|
| Best (VBR) | ~256-320 kbps | Audiophiles, best quality | 8-12 MB |
| 320 kbps | 320 kbps CBR | High quality audio | ~12 MB |
| 192 kbps | 192 kbps CBR | Standard listening | ~7 MB |
| 128 kbps | 128 kbps CBR | Portable devices, saving space | ~5 MB |

### Audio Use Cases

- **Music Downloads**: Extract songs from music videos
- **Podcasts**: Save audio content for offline listening
- **Lectures**: Download educational content
- **Background Music**: Extract audio for personal use

---

## Downloading Playlists

### Automatic Playlist Detection

Downloadyha automatically detects playlist URLs:
- `https://www.youtube.com/playlist?list=...`
- `https://www.youtube.com/watch?v=...&list=...`

### Step-by-Step Guide

**Step 1: Paste Playlist URL**
1. Copy playlist URL from YouTube
2. Paste into URL field
3. Validation shows valid URL

**Step 2: Fetch Playlist Info**
1. Click "Fetch Info"
2. Review playlist information:
   - Playlist title
   - Channel/uploader
   - Total number of items
   - Type: Playlist

**Screenshot Description**:
> Media info card displays:
> - Title: Synthwave & Cyberpunk Mix 2026
> - Channel: RetroWave Records
> - Type: Playlist (15 items)

**Step 3: Choose Download Type**

For **Video Playlist**:
1. Select "Video"
2. Choose maximum video quality
3. All videos download at or below selected quality

For **Audio Playlist**:
1. Select "Audio (MP3)"
2. Choose audio quality
3. All items convert to MP3 at selected bitrate

**Step 4: Start Download**
1. Click "Download"
2. Watch progress for each item:
   - Progress bar shows current item progress
   - Status shows "[Video X/Y]" for current item
   - Speed and ETA update in real-time

**Screenshot Description**:
> Progress shows "[Video 3/15] Downloading: Synthwave Track 03", Speed: 22.1 MB/s, ETA: 00:45

**Step 5: Completion**
1. All items download sequentially
2. Final summary shows total completed
3. Files saved in subfolder named after playlist

### Playlist Features

- **Organized Storage**: Creates a subfolder with playlist name
- **Numbered Files**: Items numbered (01, 02, 03...)
- **Error Resilience**: Private/restricted videos skipped without failing entire playlist
- **Progress Tracking**: Real-time progress for each item

### Playlist Output Structure

```
Downloads/
└── Synthwave & Cyberpunk Mix 2026/
    ├── 01 - Introduction.mp4
    ├── 02 - Track One.mp4
    ├── 03 - Track Two.mp4
    ├── 04 - Track Three.mp4
    └── ... (remaining items)
```

---

## Settings and Preferences

### Theme Selection

**Light Theme** (Default)
- Clean white background
- Dark text
- Cyan accent colors

**Dark Theme**
- Dark gray background (#1E1E2E)
- Light text
- Cyan accent colors (easier on eyes)

**How to Switch Themes**:
1. Click theme toggle button (🌙 Dark / ☀ Light) in header
2. Theme preference is saved automatically

**Screenshot Description**:
> Left: Light theme with white background. Right: Dark theme with dark gray background.

### Download Location

**Default Location**:
- Windows: `C:\Users\[Username]\Downloads`
- Linux: `/home/[username]/Downloads`

**Changing Download Location**:
1. Click "Browse" button next to "Save to" field
2. Select desired folder in file dialog
3. Click "Select Folder"
4. Location saved for future downloads

**Setting via Config File**:
Edit `config.json`:
- Windows: `%LOCALAPPDATA%\Downloadyha\config.json`
- Linux: `~/.local/share/downloadyha/config.json`

```json
{
  "download_directory": "D:\\MyVideos\\YouTube"
}
```

### Quality Preferences

Your last selected quality is saved and used as default for future downloads:
- Last video quality (e.g., "1080p")
- Last audio quality (e.g., "320 kbps")

### Window Geometry

Window size and position are saved:
- Resized windows remember dimensions
- Position restored on next launch

---

## Troubleshooting

### Common Issues

#### Issue: GUI Won't Launch

**Symptom**: Nothing happens when running `downloadyha gui`

**Solutions**:

1. **Check tkinter installation**:
   ```bash
   python -m tkinter
   ```
   If this fails, tkinter is not installed.

2. **Install tkinter**:
   - **Windows**: Reinstall Python with "tcl/tk and IDLE" checked
   - **Linux (Ubuntu/Debian)**: `sudo apt-get install python3-tk`
   - **Linux (Fedora)**: `sudo dnf install python3-tkinter`

3. **Run from source**:
   ```bash
   pip install -e .
   python -m downloadyha.gui
   ```

#### Issue: URL Shows as Invalid

**Symptom**: Red X and "Invalid YouTube URL format" message

**Solutions**:

1. Ensure URL starts with `https://www.youtube.com/` or `https://youtu.be/`
2. Check for extra spaces before/after URL
3. Try removing URL parameters (everything after `&`):
   - Before: `https://www.youtube.com/watch?v=abc123&t=120s`
   - After: `https://www.youtube.com/watch?v=abc123`
4. Use the full URL instead of shortened links

#### Issue: Download Fails

**Symptom**: Error message "Download failed" or progress stops

**Solutions**:

1. **Check internet connection**
2. **Verify FFmpeg is installed**:
   ```bash
   downloadyha --verify
   ```
3. **Repair dependencies**:
   ```bash
   downloadyha repair
   ```
4. **Try lower quality**: Some videos don't have all resolutions available
5. **Check disk space**: Ensure enough space for download

#### Issue: Progress Bar Frozen

**Symptom**: Download started but progress bar doesn't update

**Solutions**:

1. **Wait a few seconds**: Initial connection may take time
2. **Check status bar**: May show processing message
3. **Cancel and retry**: Click Cancel, then Download again
4. **Restart application**: Close and reopen

#### Issue: Can't Find Downloaded File

**Symptom**: Download completed but can't find file

**Solutions**:

1. **Click "Open Folder" button** after download
2. **Check default location**: `Downloads` folder
3. **Check config file** for custom location:
   - Windows: `%LOCALAPPDATA%\Downloadyha\config.json`
   - Linux: `~/.local/share/downloadyha/config.json`
4. **Search for filename**: Use system search

#### Issue: Playlist Download Incomplete

**Symptom**: Not all playlist items downloaded

**Reasons**:
- Private videos cannot be downloaded
- Region-restricted videos unavailable
- Deleted videos skipped

**Solution**: This is expected behavior. Check status bar for count of completed items.

### Display Issues on Linux

#### Issue: Blurry or Distorted UI

**Symptom**: GUI looks pixelated or blurry on Linux

**Solutions**:

1. **Install recommended fonts**:
   ```bash
   sudo apt-get install fonts-liberation fonts-noto
   ```

2. **Set environment variable**:
   ```bash
   export GDK_SCALE=2
   downloadyha gui
   ```

3. **Check display scaling**: Adjust in system display settings

#### Issue: High DPI Not Working

**Symptom**: UI elements too small on high-DPI display

**Solution**:
```bash
export GDK_SCALE=2
downloadyha gui
```

### Missing Dependencies

#### Issue: "FFmpeg not found"

**Symptom**: Error about missing FFmpeg

**Solution**:
```bash
downloadyha repair
```

This automatically downloads and configures FFmpeg.

#### Issue: "Deno not found"

**Symptom**: Error about missing Deno runtime

**Solution**:
```bash
downloadyha repair
```

---

## Keyboard Shortcuts

Currently, keyboard shortcuts are limited. Use mouse for all actions.

### Planned Shortcuts (Future Version)

| Shortcut | Action |
|----------|--------|
| Ctrl+V | Paste URL from clipboard |
| Enter | Start download (when URL field focused) |
| Escape | Cancel download |
| Ctrl+O | Open download folder |
| Ctrl+, | Open settings |
| F5 | Refresh/fetch media info |
| F11 | Toggle fullscreen |

---

## FAQ

### General Questions

**Q: Is Downloadyha free to use?**

A: Yes, Downloadyha is completely free and open-source under the MIT License.

**Q: Can I download copyrighted content?**

A: Downloadyha is a tool for downloading publicly available content. Respect copyright laws and YouTube's Terms of Service. Only download content you have permission to use.

**Q: Where are my downloaded files saved?**

A: By default, files are saved to your Downloads folder. You can change this in the interface or config file.

**Q: Does Downloadyha support other video sites?**

A: Currently, Downloadyha supports YouTube only (including YouTube Music). Support for other platforms may be added in future versions.

### Technical Questions

**Q: What video formats are supported?**

A: Videos are downloaded as MP4 (H.264 video + AAC audio). Playlists can optionally be saved as MKV.

**Q: What audio formats are supported?**

A: Audio is extracted and converted to MP3 format with selectable bitrate.

**Q: Why do I need FFmpeg?**

A: FFmpeg is required for:
- Merging video and audio streams
- Converting to MP3
- Processing media files

Downloadyha automatically manages FFmpeg for you.

**Q: What's the maximum video quality?**

A: Up to 4K (2160p) if the source video supports it. "Best Available" automatically selects the highest quality.

**Q: How do I update Downloadyha?**

A: Run `downloadyha update` in terminal, or check for updates from CLI.

### Troubleshooting Questions

**Q: Why is my download slow?**

A: Download speed depends on:
- Your internet connection speed
- YouTube server response
- Video file size
- Server load

Try a lower quality for faster downloads.

**Q: Why can't I download some videos?**

A: Some videos cannot be downloaded due to:
- Privacy settings (private videos)
- Age restrictions
- Region locking
- Copyright restrictions
- Live streams (must wait until finished)

**Q: How do I report bugs or request features?**

A: Visit the GitHub repository:
https://github.com/ahmed-tarek-2004/DownloadYha/issues

---

## Tips and Best Practices

### Download Management

1. **Organize Downloads**: Create separate folders for different content types
2. **Check Quality First**: Use "Fetch Info" to verify video quality before downloading
3. **Playlist Naming**: Playlist names become folder names, so check the name first
4. **Disk Space**: Ensure sufficient space before downloading large playlists

### Quality Selection

- **For archiving**: Use "Best Available" or 1080p+
- **For mobile viewing**: 720p or 480p
- **For audio**: 192kbps or higher for music, 128kbps for speech
- **To save space**: Use lower quality settings

### Performance Tips

1. **Close other applications** during large downloads
2. **Use wired connection** for faster speeds
3. **Download during off-peak hours** (early morning/late night)
4. **Clear cache** if experiencing issues: Delete contents of downloadyha cache folder

---

## Getting Help

### Documentation

- **User Guide**: This document
- **Development Guide**: See `GUI_DEVELOPMENT.md`
- **Main README**: Project overview and installation

### Community

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Repository**: https://github.com/ahmed-tarek-2004/DownloadYha

### Support

If you encounter issues:

1. Check this Troubleshooting section
2. Run `downloadyha --verify` to check dependencies
3. Try `downloadyha repair` to fix common issues
4. Search GitHub Issues for similar problems
5. Create a new Issue with:
   - Error message
   - Steps to reproduce
   - Operating system and version
   - Downloadyha version (`downloadyha --version`)

---

## Version History

### v1.0.0 (Initial GUI Release)

- Desktop GUI interface
- Video and audio downloads
- Playlist support
- Light and dark themes
- Real-time progress tracking
- Settings persistence

---

## License

Downloadyha is released under the MIT License. See LICENSE file for details.

---

## Acknowledgments

- **yt-dlp**: YouTube download engine
- **FFmpeg**: Media processing
- **tkinter**: GUI framework

---

**Last Updated**: 2026-10-01

**Author**: Ahmed Tarek Zaher
