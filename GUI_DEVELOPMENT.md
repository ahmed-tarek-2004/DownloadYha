# GUI Development Guide

## Overview

This document provides a comprehensive guide for developers working with the Downloadyha Desktop GUI codebase. The GUI is built using Python's `tkinter` library for maximum cross-platform compatibility without requiring additional dependencies.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Module Structure](#module-structure)
- [Key Components](#key-components)
- [Development Setup](#development-setup)
- [Building and Running](#building-and-running)
- [Testing](#testing)
- [Code Style and Standards](#code-style-and-standards)
- [Adding New Features](#adding-new-features)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Design Philosophy

The GUI follows these core principles:

1. **Separation of Concerns**: The GUI module (`gui.py`) handles only presentation logic. Business logic resides in `downloader.py` and related core modules.
2. **Thread Safety**: Download operations run in background threads with thread-safe communication via `queue.Queue`.
3. **Reactive UI**: The UI responds to user actions and updates dynamically based on download progress.
4. **Settings Persistence**: User preferences (theme, download directory, quality selections) are saved and restored automatically.

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     DownloadyhaGUI                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  UI Layer (tkinter/ttk)                               │  │
│  │  - Window management                                  │  │
│  │  - User input handling                                │  │
│  │  - Progress display                                   │  │
│  └────────────────┬──────────────────────────────────────┘  │
│                   │                                          │
│  ┌────────────────▼──────────────────────────────────────┐  │
│  │  State Management                                     │  │
│  │  - Settings (theme, directories, quality)            │  │
│  │  - Download state tracking                           │  │
│  │  - Media information cache                           │  │
│  └────────────────┬──────────────────────────────────────┘  │
│                   │                                          │
│  ┌────────────────▼──────────────────────────────────────┐  │
│  │  Background Operations                                │  │
│  │  - Download threads                                   │  │
│  │  - Progress callbacks                                 │  │
│  │  - Media info fetching                               │  │
│  └────────────────┬──────────────────────────────────────┘  │
└───────────────────┼──────────────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────────────┐
│           Core Downloader Engine                             │
│  (downloader.py, config.py, dependencies.py)                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Module Structure

### File Organization

```
src/downloadyha/
├── gui.py              # Main GUI module
├── downloader.py       # Core download engine
├── config.py           # Configuration management
├── cli.py              # CLI interface (includes GUI launcher)
├── ui.py               # Terminal UI components
└── dependencies.py     # Dependency management

tests/
├── test_gui.py         # GUI unit tests
├── test_downloader.py  # Core engine tests
└── test_downloader_ui.py # Terminal UI tests
```

### Import Dependencies

The GUI module depends on:

- **Standard Library**: `tkinter`, `tkinter.ttk`, `threading`, `queue`, `re`
- **Internal Modules**: `downloader`, `config`
- **Optional**: Platform-specific file explorer commands (`subprocess`)

---

## Key Components

### 1. DownloadyhaGUI Class

The main application class that manages the entire GUI lifecycle.

#### Responsibilities

- **Initialization**: Set up window, load settings, build UI components
- **Event Handling**: Process user interactions (button clicks, text input)
- **State Management**: Track download state, media info, UI state
- **Theme Management**: Apply and switch between light/dark themes
- **Thread Coordination**: Launch background tasks and update UI from callbacks

#### Key Methods

```python
def __init__(self, root: Optional[tk.Tk] = None) -> None:
    """Initialize the GUI application."""

def _build_ui(self) -> None:
    """Build all UI components."""

def _apply_theme(self) -> None:
    """Apply current theme colors to all widgets."""

def _start_download(self) -> None:
    """Start download in background thread."""

def _update_progress(self) -> None:
    """Poll progress queue and update UI (runs on main thread)."""

def toggle_theme(self) -> None:
    """Switch between light and dark themes."""
```

### 2. ProgressCallback Class

Thread-safe progress reporting mechanism.

#### Purpose

Bridges the gap between download threads and the main GUI thread using a queue-based message passing system.

#### Usage

```python
# Create callback
callback = ProgressCallback()

# Pass to downloader
download_video(
    url="https://youtube.com/watch?v=...",
    download_path="/downloads",
    height=1080,
    progress_callback=callback
)

# Poll for updates (in main thread)
events = callback.get_pending_events()
for event in events:
    update_progress_bar(event["percent"])
```

#### Thread Safety

- Uses `queue.Queue` which is thread-safe by design
- No locks required for basic operations
- Cancellation flag (`_cancelled`) uses simple boolean (atomic in CPython)

### 3. Settings Management

Settings are persisted to disk using the existing `config.py` module.

#### Settings Schema

```python
{
    "download_directory": str,      # Default download location
    "theme": str,                    # "light" or "dark"
    "last_video_quality": str,      # Last selected video quality index
    "last_audio_quality": str,      # Last selected audio quality index
    "window_geometry": str,         # Window size and position
    "check_updates": bool           # Whether to check for updates
}
```

#### Functions

```python
def load_gui_settings() -> Dict[str, Any]:
    """Load GUI settings from config file."""

def save_gui_settings(settings: Dict[str, Any]) -> bool:
    """Save GUI settings to config file."""
```

### 4. URL Validation

Real-time URL validation with user feedback.

#### Implementation

```python
def validate_youtube_url(url: str) -> Tuple[bool, str]:
    """
    Validate YouTube URL.
    
    Returns:
        (is_valid, error_message)
    """
    if not url.strip():
        return False, "URL cannot be empty."
    
    if not YOUTUBE_URL_PATTERN.match(url):
        return False, "Invalid YouTube URL format."
    
    return True, ""
```

#### UI Integration

- Validation runs on every keystroke via `StringVar.trace_add()`
- Success/error messages displayed with colored text
- Invalid URLs prevent download button activation

### 5. Theme System

Dual-theme support with comprehensive color definitions.

#### Theme Colors

```python
class ThemeColors:
    LIGHT = {
        "bg": "#F5F5F5",           # Background
        "fg": "#1A1A1A",           # Foreground text
        "accent": "#00D2FF",       # Primary accent color
        "success": "#2ECC71",      # Success states
        "warning": "#F1C40F",      # Warnings
        "error": "#E74C3C",        # Errors
        "card_bg": "#FFFFFF",      # Card backgrounds
        "input_bg": "#FFFFFF",     # Input fields
        "border": "#E0E0E0",       # Borders
        "progress_bg": "#E0E0E0",  # Progress bar background
        "progress_fill": "#00D2FF" # Progress bar fill
    }
    
    DARK = { ... }  # Dark theme variant
}
```

#### Applying Themes

Themes are applied by configuring ttk styles:

```python
def _apply_theme(self) -> None:
    colors = ThemeColors.DARK if self._current_theme == "dark" else ThemeColors.LIGHT
    
    self.style.configure(".", background=colors["bg"], foreground=colors["fg"])
    self.style.configure("TFrame", background=colors["bg"])
    # ... configure all widget styles
```

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- tkinter (usually included with Python)
- Development dependencies from `pyproject.toml`

### Installation

```bash
# Clone repository
git clone https://github.com/ahmed-tarek-2004/DownloadYha.git
cd DownloadYha

# Install in development mode
pip install -e ".[dev]"
```

### IDE Configuration

#### VS Code

Recommended extensions:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)

`.vscode/settings.json`:
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.unittestEnabled": true,
    "python.testing.unittestArgs": ["-v", "-s", "./tests", "-p", "test_*.py"]
}
```

#### PyCharm

1. Open project directory
2. Configure Python interpreter (3.8+)
3. Mark `src` directory as "Sources Root"
4. Mark `tests` directory as "Test Sources Root"

---

## Building and Running

### Running the GUI

#### Development Mode

```bash
# From project root
python -m downloadyha.gui

# Or through CLI
python -m downloadyha.cli gui
```

#### Production Mode

```bash
# After installation
downloadyha gui
```

### Building Executable

The GUI is included in the main executable build:

```bash
# Windows
.\build-windows.ps1

# Linux
./build-linux.sh
```

The resulting executable supports both CLI and GUI modes:

```bash
# Launch GUI
downloadyha gui

# Launch CLI (default)
downloadyha
```

---

## Testing

### Running Tests

```bash
# Run all GUI tests
python -m unittest tests.test_gui

# Run specific test class
python -m unittest tests.test_gui.TestURLValidation

# Run with verbose output
python -m unittest tests.test_gui -v
```

### Test Structure

```python
# tests/test_gui.py structure

class TestURLValidation(unittest.TestCase):
    """Test URL validation logic."""

class TestSettingsManagement(unittest.TestCase):
    """Test settings persistence."""

class TestProgressCallback(unittest.TestCase):
    """Test progress callback integration."""

class TestThemeColors(unittest.TestCase):
    """Test theme definitions."""

class TestQualityOptions(unittest.TestCase):
    """Test quality option definitions."""

@unittest.skipIf(os.environ.get("CI") == "true", "Skip in CI")
class TestDownloadyhaGUI(unittest.TestCase):
    """Test GUI initialization and methods."""
```

### Writing New Tests

#### Testing UI Components

Use mocking to avoid creating actual windows:

```python
@patch("downloadyha.gui.tk.Tk")
def test_my_feature(self, mock_tk):
    mock_root = MagicMock()
    mock_tk.return_value = mock_root
    
    # Patch UI building to avoid widget creation
    with patch.object(DownloadyhaGUI, "_build_ui"):
        gui = DownloadyhaGUI(root=mock_root)
        
        # Test your feature
        result = gui.my_feature()
        self.assertEqual(result, expected_value)
```

#### Testing Callbacks

```python
def test_progress_callback(self):
    callback = ProgressCallback()
    
    # Simulate progress event
    callback({"status": "downloading", "percent": 50.0})
    
    # Verify event was queued
    events = callback.get_pending_events()
    self.assertEqual(len(events), 1)
    self.assertEqual(events[0]["percent"], 50.0)
```

### Test Coverage

Current test coverage for `gui.py`:

- URL validation: 100%
- Settings management: 100%
- Progress callbacks: 100%
- Theme definitions: 100%
- Quality options: 100%
- GUI initialization: ~85% (limited by tkinter mocking)

---

## Code Style and Standards

### Python Style Guide

Follow PEP 8 with these specifics:

- **Line Length**: 100 characters max (120 for long URLs/strings)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings, single for dict keys when appropriate
- **Imports**: Grouped (standard library, third-party, local) and sorted

### Type Hints

All functions must include type hints:

```python
def validate_youtube_url(url: str) -> Tuple[bool, str]:
    """Validate YouTube URL."""
    ...

def load_gui_settings() -> Dict[str, Any]:
    """Load GUI settings."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def create_progress_hook(
    title: Optional[str] = None,
    is_playlist: bool = False
) -> Callable[[Dict[str, Any]], None]:
    """
    Create a progress hook for downloads.
    
    Args:
        title: Optional video title.
        is_playlist: Whether this is a playlist download.
        
    Returns:
        Callable hook function for yt-dlp.
        
    Example:
        hook = create_progress_hook(title="My Video")
        download_video(..., progress_callback=hook)
    """
```

### Naming Conventions

- **Classes**: PascalCase (`DownloadyhaGUI`, `ProgressCallback`)
- **Functions**: snake_case (`validate_youtube_url`, `load_gui_settings`)
- **Constants**: UPPER_SNAKE_CASE (`VIDEO_QUALITY_OPTIONS`, `YOUTUBE_URL_PATTERN`)
- **Private methods**: Leading underscore (`_build_ui`, `_apply_theme`)

### Error Handling

Always handle exceptions gracefully in GUI code:

```python
def _fetch_media_info(self) -> None:
    """Fetch media info in background thread."""
    def fetch_task() -> None:
        try:
            self._media_info = get_media_info(url)
            self.root.after(0, self._on_media_info_fetched)
        except Exception as e:
            self._media_info = None
            self.root.after(0, lambda: self._on_fetch_error(str(e)))
    
    thread = threading.Thread(target=fetch_task, daemon=True)
    thread.start()
```

---

## Adding New Features

### Example: Adding a New Quality Preset

1. **Update quality options**:

```python
# In gui.py
VIDEO_QUALITY_OPTIONS.append(("8", "240p (Very Low)", 240))
```

2. **Update settings schema** (if saving preference):

```python
# In load_gui_settings()
settings["last_video_quality"] = config.get("last_video_quality", "1")
```

3. **Add test coverage**:

```python
# In tests/test_gui.py
def test_new_quality_option(self):
    self.assertIn(("8", "240p (Very Low)", 240), VIDEO_QUALITY_OPTIONS)
```

### Example: Adding a Download Format Option

1. **Add UI widget** in `_build_options_section()`:

```python
format_frame = ttk.Frame(options_frame)
format_frame.pack(fill=tk.X, padx=10, pady=5)

ttk.Label(format_frame, text="Format:").pack(side=tk.LEFT)

self.format_var = tk.StringVar(value="mp4")
ttk.Radiobutton(format_frame, text="MP4", variable=self.format_var, value="mp4").pack(side=tk.LEFT)
ttk.Radiobutton(format_frame, text="MKV", variable=self.format_var, value="mkv").pack(side=tk.LEFT)
```

2. **Use in download**:

```python
def _start_download(self) -> None:
    ...
    output_format = self.format_var.get()
    
    if download_type == "video":
        result = download_video(
            url=url,
            download_path=download_dir,
            height=quality,
            progress_callback=self._progress_callback,
            output_format=output_format  # Pass to downloader
        )
```

3. **Add tests**:

```python
def test_format_selection(self):
    gui = DownloadyhaGUI()
    gui.format_var.set("mkv")
    self.assertEqual(gui.format_var.get(), "mkv")
```

---

## Troubleshooting

### Common Issues

#### 1. GUI Won't Launch

**Symptom**: `ImportError: No module named '_tkinter'`

**Solution**:
- **Windows**: Reinstall Python with tkinter enabled
- **Linux**: `sudo apt-get install python3-tk`
- **macOS**: tkinter included by default

#### 2. Theme Not Applying

**Symptom**: Colors don't change or widgets look wrong

**Cause**: ttk styles not configured for all widget types

**Solution**: Ensure `_apply_theme()` configures all relevant styles:

```python
self.style.configure("TFrame", background=colors["bg"])
self.style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
self.style.configure("TButton", background=colors["accent"])
# ... etc
```

#### 3. Progress Bar Not Updating

**Symptom**: Progress bar frozen during download

**Cause**: GUI not polling progress queue or callback not firing

**Debug**:

```python
def _update_progress(self) -> None:
    events = self._progress_callback.get_pending_events()
    print(f"DEBUG: Received {len(events)} progress events")  # Add logging
    
    for event in events:
        print(f"DEBUG: Event status={event['status']}, percent={event['percent']}")
        # ... update UI
```

#### 4. Download Thread Hangs

**Symptom**: Download never completes or GUI freezes

**Cause**: Blocking operation on main thread or deadlock

**Solution**: Ensure all long-running operations are in background threads:

```python
def _start_download(self) -> None:
    def download_task() -> None:
        # This runs in background thread
        result = download_video(...)
        # Update UI via root.after()
        self.root.after(0, lambda: self._on_download_complete(result))
    
    thread = threading.Thread(target=download_task, daemon=True)
    thread.start()
```

#### 5. Settings Not Persisting

**Symptom**: Theme/directory choices reset on restart

**Cause**: Settings not saved or wrong directory

**Debug**:

```python
from downloadyha.config import get_config_dir

print(f"Config directory: {get_config_dir()}")
print(f"Config file exists: {(get_config_dir() / 'config.json').exists()}")
```

**Solution**: Ensure `save_gui_settings()` is called on changes:

```python
def toggle_theme(self) -> None:
    self._current_theme = "dark" if self._current_theme == "light" else "light"
    self.settings["theme"] = self._current_theme
    save_gui_settings(self.settings)  # Don't forget this!
    self._apply_theme()
```

### Platform-Specific Issues

#### Linux: Missing Dependencies

```bash
# Install tkinter
sudo apt-get install python3-tk

# Install fonts for better appearance
sudo apt-get install fonts-liberation
```

#### Windows: High DPI Scaling

Add DPI awareness to prevent blurry UI:

```python
# In __init__ before creating window
if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
```

#### macOS: Menu Bar Integration

Use native menu bar:

```python
if sys.platform == "darwin":
    self.root.createcommand('::tk::mac::ShowPreferences', self._show_preferences)
```

---

## Performance Optimization

### 1. Lazy Loading

Load heavy resources only when needed:

```python
def _fetch_media_info(self) -> None:
    """Fetch media info only when user clicks 'Fetch Info'."""
    # Don't fetch automatically on URL input
```

### 2. Progress Update Throttling

Limit UI updates to prevent flickering:

```python
def _update_progress(self) -> None:
    if not self._is_downloading:
        return
    
    # Throttle to 10 FPS (100ms)
    self.root.after(100, self._update_progress)
```

### 3. Virtual Event Batching

Batch multiple events before updating UI:

```python
events = self._progress_callback.get_pending_events()

if events:
    # Take only the last event for display
    latest = events[-1]
    self.progress_var.set(latest["percent"])
```

---

## Security Considerations

### 1. URL Validation

Always validate URLs before passing to downloader:

```python
if not is_valid_youtube_url(url):
    messagebox.showerror("Error", "Invalid YouTube URL")
    return
```

### 2. Path Sanitization

Sanitize user-provided paths:

```python
import os
download_dir = os.path.abspath(self.dir_var.get())
```

### 3. Thread Safety

Never share mutable state between threads without synchronization:

```python
# Use queue for communication
self._progress_callback._queue.put(event)

# Or use root.after() to run on main thread
self.root.after(0, lambda: self._update_ui(data))
```

---

## Future Enhancements

Potential features for future versions:

1. **Playlist Queue Management**: Allow queueing multiple URLs
2. **Download History**: Track previously downloaded videos
3. **Thumbnail Preview**: Show video thumbnail in media info
4. **Bandwidth Limiting**: Limit download speed
5. **Proxy Support**: Configure HTTP/SOCKS proxy
6. **Keyboard Shortcuts**: Add hotkeys for common actions
7. **System Tray Integration**: Minimize to system tray
8. **Multi-language Support**: Internationalization (i18n)

---

## Contributing

See `CONTRIBUTING.md` for general contribution guidelines.

### GUI-Specific Guidelines

- Test on all supported platforms (Windows, Linux, macOS)
- Ensure theme changes apply to new widgets
- Add docstrings and type hints to all new functions
- Update tests for new features
- Follow the existing code structure and patterns

---

## Resources

### Official Documentation

- [Python tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [ttk Themed Widgets](https://docs.python.org/3/library/tkinter.ttk.html)
- [threading Module](https://docs.python.org/3/library/threading.html)
- [queue Module](https://docs.python.org/3/library/queue.html)

### Tutorials

- [Real Python: Python GUI Programming With Tkinter](https://realpython.com/python-gui-tkinter/)
- [Tkinter Best Practices](https://www.pythontutorial.net/tkinter/)

### Tools

- [ttkbootstrap](https://ttkbootstrap.readthedocs.io/) - Modern themed widgets (future consideration)
- [PyInstaller](https://pyinstaller.org/) - Create standalone executables

---

## Contact

For questions or issues related to GUI development:

- GitHub Issues: https://github.com/ahmed-tarek-2004/DownloadYha/issues
- Author: Ahmed Tarek Zaher

---

**Last Updated**: 2026-10-01
