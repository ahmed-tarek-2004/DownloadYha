# GUI Changelog

All notable changes to the Downloadyha Desktop GUI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Placeholder for future GUI enhancements

---

## [1.0.0] - 2026-10-01

### Added

#### Core GUI Features

- **Desktop GUI Application**: Full-featured graphical interface using tkinter
  - Cross-platform support (Windows, Linux, macOS)
  - Native look and feel with themed widgets (ttk)
  - No additional dependencies required beyond Python standard library

- **URL Input and Validation**
  - Real-time URL validation as user types
  - Visual feedback with colored indicators (✓ for valid, ✗ for invalid)
  - Support for multiple YouTube URL formats:
    - Standard video URLs: `youtube.com/watch?v=...`
    - Short URLs: `youtu.be/...`
    - Playlist URLs: `youtube.com/playlist?list=...`
    - Video with playlist: `youtube.com/watch?v=...&list=...`

- **Download Type Selection**
  - Video download mode (MP4 format)
  - Audio extraction mode (MP3 format)
  - Radio button selection with automatic quality option updates

- **Quality Selection**
  - **Video Quality Options**:
    - Best Available (Maximum Quality)
    - 2160p (4K UHD)
    - 1440p (2K QHD)
    - 1080p (Full HD)
    - 720p (HD)
    - 480p (SD)
    - 360p (Low)
  - **Audio Quality Options**:
    - Best (Variable Bitrate ~256-320 kbps)
    - 320 kbps (High Quality CBR)
    - 192 kbps (Standard Quality)
    - 128 kbps (Compact Size)
  - Last selected quality saved and restored automatically

- **Download Directory Management**
  - Default to user's Downloads folder
  - Custom directory selection via Browse button
  - Directory persistence across sessions
  - Open folder button to view downloads in file explorer

- **Media Information Display**
  - "Fetch Info" button to retrieve video/playlist metadata
  - Display card showing:
    - Video title
    - Channel/uploader name
    - Duration (for videos)
    - Playlist item count (for playlists)
    - Content type (Single Video or Playlist)
  - Background fetching with non-blocking UI

- **Progress Tracking**
  - Real-time progress bar with percentage display
  - Download speed indicator (e.g., "18.5 MB/s")
  - Estimated time remaining (ETA) display
  - Current item title during download
  - Playlist progress indicator (e.g., "[Video 3/15]")
  - Smooth progress updates (throttled to prevent flickering)

- **Theme Support**
  - Light theme (default):
    - White/light gray backgrounds
    - Dark text
    - Cyan accent colors
  - Dark theme:
    - Dark gray backgrounds (#1E1E2E)
    - Light text
    - Cyan accent colors
  - Theme toggle button in header
  - Theme preference persisted across sessions

- **Settings Persistence**
  - Automatic save/load of user preferences
  - Persisted settings include:
    - Download directory
    - Theme preference (light/dark)
    - Last video quality selection
    - Last audio quality selection
    - Window geometry (size and position)
  - Config stored in platform-specific location:
    - Windows: `%LOCALAPPDATA%\Downloadyha\config.json`
    - Linux: `~/.local/share/downloadyha/config.json`

- **Action Buttons**
  - **Fetch Info**: Retrieve media metadata without downloading
  - **Download**: Start the download process
  - **Cancel**: Cancel in-progress download
  - **Open Folder**: Open download directory in file explorer

- **Status Indicators**
  - Status bar showing current application state
  - Success/error messages with color coding
  - Download completion notifications
  - Error dialogs with descriptive messages

#### Thread Safety and Performance

- **Background Download Threads**
  - Downloads run in separate threads to prevent UI freezing
  - Thread-safe communication via queue-based message passing
  - Graceful cancellation support

- **Progress Callback Integration**
  - `ProgressCallback` class for thread-safe progress updates
  - Queue-based event system for main thread UI updates
  - Cancellation token support for user-initiated cancel

- **UI Responsiveness**
  - Non-blocking media info fetching
  - Throttled progress updates (max 10 FPS for smoothness)
  - Efficient event polling mechanism

#### User Experience

- **Input Validation Feedback**
  - Immediate visual feedback on URL validity
  - Clear error messages for invalid inputs
  - Success indicators with green color coding

- **Error Handling**
  - Graceful handling of network errors
  - Descriptive error messages in dialogs
  - Fallback to defaults for corrupted settings

- **Accessibility**
  - Clear, readable fonts (Segoe UI)
  - High contrast text in both themes
  - Logical tab order for keyboard navigation

- **Window Management**
  - Centered window on launch
  - Remember window size and position
  - Prevent closing during active download (with confirmation)

### Technical Implementation

- **Module Structure**
  - New `gui.py` module (1,100+ lines)
  - Integration with existing `cli.py` via `downloadyha gui` command
  - Integration with `downloader.py` engine

- **Dependencies**
  - Uses only Python standard library (tkinter)
  - No additional packages required
  - Compatible with Python 3.8+

- **Testing**
  - Comprehensive test suite (`tests/test_gui.py`)
  - 21 unit tests covering:
    - URL validation logic
    - Settings management
    - Progress callback integration
    - Theme color definitions
    - Quality options validation
    - GUI initialization and methods
    - Download integration
  - Tests runnable via `python -m unittest tests.test_gui`

- **Documentation**
  - `GUI_DEVELOPMENT.md`: Developer guide (500+ lines)
  - `GUI_USER_GUIDE.md`: End-user guide (600+ lines)
  - Inline docstrings for all public functions
  - Type hints throughout the codebase

### Integration

- **CLI Integration**
  - Launch GUI via `downloadyha gui` command
  - Added to help message: `downloadyha --help`
  - Graceful fallback if GUI import fails

- **Configuration Integration**
  - Reuses existing `config.py` module
  - Settings compatible with CLI version
  - Shared download directory preference

- **Downloader Engine Integration**
  - Uses `download_video()` and `download_audio()` functions
  - Progress callback integration with core engine
  - Support for both single videos and playlists

### Platform Support

- **Windows 10/11**
  - Native Windows look with ttk themes
  - Proper file explorer integration ("Open Folder")
  - High DPI awareness (planned)

- **Linux (x86_64 and ARM64)**
  - GTK-based theming via ttk
  - XDG-compliant config locations
  - xdg-open for folder opening

- **macOS** (Experimental)
  - Basic support via tkinter
  - Native menu bar integration (planned)

### Known Limitations

- No thumbnail preview in media info
- No download queue management (one download at a time)
- No bandwidth limiting option
- No proxy configuration in GUI
- No keyboard shortcuts (planned for future)
- No system tray integration
- No multi-language support (English only)

---

## Release Notes Template

For future GUI releases, use this template:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New GUI features

### Changed
- Changes to existing GUI features

### Deprecated
- Features to be removed in future releases

### Removed
- Features removed in this release

### Fixed
- Bug fixes in GUI

### Security
- Security improvements in GUI
```

---

## Future Roadmap

### Planned for v1.1.0

- [ ] Thumbnail preview in media info card
- [ ] Download queue management (multiple URLs)
- [ ] Keyboard shortcuts
- [ ] Improved high DPI support on Windows
- [ ] System tray integration (minimize to tray)

### Planned for v1.2.0

- [ ] Bandwidth limiting option
- [ ] Proxy configuration UI
- [ ] Download history viewer
- [ ] Custom output filename templates
- [ ] Batch URL input (paste multiple URLs)

### Planned for v2.0.0

- [ ] Multi-language support (i18n)
- [ ] Custom theme editor
- [ ] Advanced settings panel
- [ ] Integration with browser extensions
- [ ] Alternative backend support (other video sites)

---

## Version History Summary

| Version | Release Date | Key Features |
|---------|--------------|--------------|
| 1.0.0 | 2026-10-01 | Initial GUI release with core features |

---

## Migration Guides

### Upgrading from CLI-only to GUI

The GUI was introduced in v1.0.0. No migration is needed as both CLI and GUI versions:

- Share the same configuration file
- Use the same download engine
- Can be used interchangeably

To start using the GUI:

```bash
downloadyha gui
```

---

## Contributing to GUI Development

See `GUI_DEVELOPMENT.md` for:

- Architecture overview
- Development setup instructions
- Code style guidelines
- Testing procedures
- Adding new features

---

## Related Documentation

- **User Documentation**: `GUI_USER_GUIDE.md`
- **Developer Documentation**: `GUI_DEVELOPMENT.md`
- **Main Changelog**: `CHANGELOG.md`
- **Project Summary**: `PROJECT_SUMMARY.md`

---

**Maintainer**: Ahmed Tarek Zaher

**Last Updated**: 2026-10-01
