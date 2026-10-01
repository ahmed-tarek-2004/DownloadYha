# 🖥️ Downloadyha Desktop GUI - Download & Installation Guide

The standalone desktop GUI version of Downloadyha for non-technical users who prefer a graphical interface over command-line tools.

---

## 📥 Download

### Windows (Recommended)

**Direct Download:**

> 🔗 **[Download downloadyha-gui-windows.zip](https://github.com/ahmed-tarek-2004/DownloadYha/releases/latest/download/downloadyha-gui-windows.zip)**
>
> **Size:** ~80-100MB | **Platform:** Windows 10/11 (64-bit)

**Alternative Download Methods:**

1. **Via GitHub Releases Page:**
   - Visit [Releases](https://github.com/ahmed-tarek-2004/DownloadYha/releases/latest)
   - Download `downloadyha-gui-windows.zip` from Assets section

2. **Via CLI (if installed):**
   ```cmd
   downloadyha gui
   ```
   The CLI version can launch the GUI interface directly.

---

## 🚀 Installation & Running

### Simple 3-Step Installation:

#### **Step 1: Extract the ZIP**
- Right-click `downloadyha-gui-windows.zip`
- Select "Extract All..." 
- Choose destination (e.g., `C:\Program Files\DownloadyhaGUI`)
- Click "Extract"

#### **Step 2: Launch the Application**
- Navigate to the extracted folder
- Double-click `downloadyha-gui.exe`
- The application launches immediately - no installation wizard needed!

#### **Step 3: Start Downloading**
- Paste a YouTube URL (video or playlist)
- Select download type (Video/Audio)
- Choose quality settings
- Pick your download folder
- Click "Download"

**That's it!** No Python, no FFmpeg, no dependencies required.

---

## 🎨 Interface Overview

### Main Window

The GUI features a clean, modern interface with:

- **URL Input Field**: Paste YouTube video or playlist URLs
- **Download Type Selection**: 
  - 🎬 Video (MP4) - Downloads video with audio
  - 🎵 Audio (MP3) - Extracts audio only
- **Quality Selection**:
  - Videos: Best, 1080p, 720p, 480p, 360p
  - Audio: 320kbps, 192kbps, 128kbps
- **Folder Selection**: Browse button to choose download location
- **Theme Toggle**: Switch between Light and Dark themes
- **Progress Display**: Real-time progress bar with speed and ETA

### Screenshots

**Light Theme - Main Interface:**
> Modern, clean interface with intuitive controls and real-time URL validation. Perfect for daytime use.

**Dark Theme - Downloading:**
> Eye-friendly dark mode with smooth progress tracking, download speed, and estimated time remaining.

**Playlist Download:**
> Batch download interface showing multi-file progress with per-item tracking and automatic folder organization.

---

## ⚙️ Features

### Download Capabilities
- ✅ **Single Video Downloads**: Up to 4K resolution (2160p) with merged audio
- ✅ **Audio Extraction**: High-quality MP3 export (up to 320kbps)
- ✅ **Full Playlist Support**: Download entire playlists with auto-indexing
- ✅ **Quality Selection**: Choose optimal quality for your needs
- ✅ **Format Options**: MP4 for videos, MP3 for audio

### User Interface
- 🎨 **Dual Themes**: Light and Dark mode with instant switching
- ✅ **Real-time URL Validation**: Visual feedback on URL validity
- 📊 **Progress Tracking**: Speed, ETA, percentage, and file counter
- 💾 **Settings Persistence**: Remembers preferences between sessions
- 🖱️ **Intuitive Controls**: Point-and-click simplicity

### Technical Features
- 🚀 **Non-blocking Downloads**: UI remains responsive during downloads
- 📂 **Smart Folder Management**: Auto-creates organized playlist folders
- 🔄 **Error Resilience**: Handles private/restricted videos gracefully
- 💪 **Standalone**: All dependencies bundled (FFmpeg, yt-dlp)

---

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10 (64-bit) or Windows 11
- **RAM**: 4GB minimum
- **Storage**: 100MB for application + space for downloads
- **Internet**: Broadband connection recommended
- **Display**: 1280x720 minimum resolution

### Recommended
- **OS**: Windows 11 (64-bit)
- **RAM**: 8GB or more
- **Storage**: SSD with adequate space for downloads
- **Internet**: High-speed connection for faster downloads
- **Display**: 1920x1080 or higher

---

## ❓ Troubleshooting

### Application Won't Launch

**Problem:** Double-clicking the .exe does nothing or shows an error.

**Solutions:**
1. **Windows SmartScreen Warning**:
   - Click "More info" 
   - Click "Run anyway"
   - This is normal for unsigned applications

2. **Antivirus Blocking**:
   - Add exception for `downloadyha-gui.exe`
   - Temporarily disable antivirus to test
   - The app is safe - false positives are common with PyInstaller

3. **Missing Visual C++ Redistributables**:
   - Download from [Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - Install and restart

4. **Check Event Viewer** (Advanced):
   - Windows Key + X → Event Viewer
   - Look under Windows Logs → Application
   - Search for errors from `downloadyha-gui.exe`

### Download Failures

**Problem:** Downloads start but fail partway through.

**Solutions:**
1. **Check Internet Connection**: Ensure stable connection
2. **Firewall Settings**: Allow `downloadyha-gui.exe` through firewall
3. **Disk Space**: Verify adequate free space in destination folder
4. **URL Validity**: Ensure the YouTube video is not private/deleted
5. **Retry**: Some videos have temporary access issues

### Slow Download Speeds

**Problem:** Downloads are slower than expected.

**Solutions:**
1. **Internet Speed**: Check your actual connection speed
2. **Lower Quality**: Select lower resolution/bitrate
3. **VPN/Proxy**: Disable if using, may throttle speeds
4. **YouTube Throttling**: YouTube may limit download speeds
5. **Peak Times**: Try downloading during off-peak hours

### Progress Bar Stuck

**Problem:** Progress bar stops moving but download continues.

**Solutions:**
1. **Wait**: Some videos process in chunks - progress may pause briefly
2. **Check Task Manager**: Verify `downloadyha-gui.exe` is active
3. **Restart Application**: Close and relaunch if truly frozen
4. **Disk Speed**: Slow HDDs may cause delays during file writing

### URL Not Recognized

**Problem:** Valid YouTube URL shows as invalid.

**Solutions:**
1. **URL Format**: Use standard YouTube URLs:
   - Video: `https://www.youtube.com/watch?v=VIDEO_ID`
   - Playlist: `https://www.youtube.com/playlist?list=PLAYLIST_ID`
2. **Remove Extra Parameters**: Strip tracking parameters after `&`
3. **Shortened URLs**: Expand bit.ly or youtu.be links first
4. **Update**: Use latest version (may have improved URL parsing)

### GUI Theme Issues

**Problem:** Theme switching doesn't work or looks broken.

**Solutions:**
1. **Restart Application**: Close and relaunch
2. **Delete Settings**: Remove `%LOCALAPPDATA%\Downloadyha\gui_settings.json`
3. **Windows Theme**: Try changing Windows theme settings
4. **Display Scaling**: Ensure Windows scaling is 100-150%

---

## 🆘 Getting Help

### Report an Issue

If you encounter a bug or problem:

1. **Check Existing Issues**: [GitHub Issues](https://github.com/ahmed-tarek-2004/DownloadYha/issues)
2. **Create New Issue**: Include:
   - Windows version (run `winver` to check)
   - Application version
   - Steps to reproduce
   - Error messages or screenshots
   - Sample URL (if applicable)

### Feature Requests

Have an idea for improvement? Open a feature request on GitHub Issues.

### Community Support

- **Discussions**: [GitHub Discussions](https://github.com/ahmed-tarek-2004/DownloadYha/discussions)
- **Documentation**: See `README.txt` in the application folder

---

## 🔄 Updates

### Checking for Updates

The GUI application includes built-in update checking:

1. **Automatic Check**: Checks on launch (if enabled in CLI config)
2. **Manual Check**: Use CLI version: `downloadyha update`

### Updating the Application

1. Download the latest `downloadyha-gui-windows.zip`
2. Close the running application
3. Extract and replace old executable
4. Settings and preferences are preserved

---

## 🗑️ Uninstallation

### Simple Removal

1. **Close Application**: Ensure `downloadyha-gui.exe` is not running
2. **Delete Folder**: Remove the folder containing the executable
3. **Optional - Clean Settings**:
   - Press `Win + R`
   - Type: `%LOCALAPPDATA%\Downloadyha`
   - Delete the folder

That's it - no registry entries or system modifications to clean up.

---

## 🔒 Privacy & Security

### Data Collection
- ❌ **No Telemetry**: Zero data collection or tracking
- ❌ **No Analytics**: No usage statistics transmitted
- ❌ **No Accounts**: No login or registration required

### Download Security
- 🔒 **Direct Downloads**: Content streams directly from YouTube
- 🛡️ **No Intermediaries**: No third-party servers involved
- ✅ **Open Source**: Code is publicly auditable on GitHub

### File Safety
- ✅ **Virus-Free**: Built from clean source code
- ⚠️ **Antivirus Warnings**: May trigger false positives (PyInstaller characteristic)
- 🔍 **VirusTotal**: Check hash against VirusTotal if concerned

---

## 📚 Additional Resources

- **Main Repository**: [github.com/ahmed-tarek-2004/DownloadYha](https://github.com/ahmed-tarek-2004/DownloadYha)
- **CLI Version**: Full command-line interface with more features
- **GUI User Guide**: [GUI_USER_GUIDE.md](https://github.com/ahmed-tarek-2004/DownloadYha/blob/master/GUI_USER_GUIDE.md)
- **Development Guide**: [GUI_DEVELOPMENT.md](https://github.com/ahmed-tarek-2004/DownloadYha/blob/master/GUI_DEVELOPMENT.md)
- **Changelog**: [CHANGELOG_GUI.md](https://github.com/ahmed-tarek-2004/DownloadYha/blob/master/CHANGELOG_GUI.md)

---

## 📄 License

Downloadyha is free and open-source software distributed under the MIT License.

```
MIT License

Copyright (c) 2026 Ahmed Tarek Zaher

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

**Enjoy fast, beautiful YouTube downloads with Downloadyha!** 🚀
