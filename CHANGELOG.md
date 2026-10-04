# Changelog

All notable changes to Downloadyha will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Partial Video & Audio Clipping**: Download specific sections/highlights using start and end timestamps (`-s` / `--start-time`, `-e` / `--end-time`).
- Timestamp parser supporting `MM:SS`, `HH:MM:SS`, total seconds (`90`, `90s`), and fractional seconds (`01:15.5`).
- Desktop GUI section clipping controls with dynamic reveal checkbox and input validation.
- Interactive CLI prompt for clipping single video and audio downloads.
- **Subtitle & Transcript Support**: Download, embed, and convert subtitles in multiple formats (SRT, VTT, ASS, LRC) with language selection and auto-generated caption support.
- Subtitle options: write official subtitles (`--write-subs`), auto-generated captions (`--write-auto-subs`), embed in video (`--embed-subs`), language selection (`--sub-langs`), format selection (`--sub-format`), and format conversion (`--convert-subs`).
- Desktop GUI subtitle controls with checkboxes for all options, language input, format dropdown, and embed/convert toggles.
- Interactive CLI subtitle prompts with format and language selection.
- Full playlist subtitle support for both video and audio playlist downloads.

### Fixed

- Fixed `tmp_dir: unbound variable` error in Linux installation script (`install.sh`).
- Fixed SSL certificate validation failures during dependency downloads on Linux distributions lacking system CA bundles by adding multi-path bundle discovery and SHA-256 integrity verification in `network.py`.
- Fixed Desktop GUI layout issue where toggling section clipping could push footer action buttons off-screen. Fixed by docking action buttons and implementing a scrollable form container.

## [1.0.0] - 2026-09-30

### Added

- Initial standalone release
- Download YouTube videos as MP4
- Download audio as MP3 (Best, 128, 192, 320 kbps)
- Dynamic video quality detection based on available formats
- Custom download directory selection
- Progress tracking with speed and ETA display
- Self-updating via `downloadyha update`
- Self-repairing via `downloadyha repair`
- Bundled dependencies (no Python, FFmpeg, Deno, or yt-dlp installation required)
- Cross-platform support:
  - Windows 10/11 x64
  - Linux x64
  - Linux ARM64
- Automatic update check (once per 24 hours)
- User configuration persistence
- Structured logging
- SHA-256 checksum verification for all downloads

### Security

- HTTPS-only downloads for all components
- SHA-256 verification before executing any downloaded binary
- Atomic file operations for safe updates

---

## Release Notes Template

For future releases, use this template:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing features

### Deprecated
- Features to be removed in future releases

### Removed
- Features removed in this release

### Fixed
- Bug fixes

### Security
- Security improvements
```

---

[Unreleased]: https://github.com/ahmed-tarek-2004/DownloadYha/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ahmed-tarek-2004/DownloadYha/releases/tag/v1.0.0
