# Changelog

All notable changes to Downloadyha will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Items for the next release go here

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
