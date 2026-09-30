# Contributing to Downloadyha

Thank you for your interest in contributing to Downloadyha! This document provides guidelines for building, testing, and contributing to the project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Building from Source](#building-from-source)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Creating a Release](#creating-a-release)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)

---

## Prerequisites

To build Downloadyha from source, you need:

- **Python 3.11+** (for development and building)
- **pip** (Python package manager)
- **Git** (for version control)
- **PyInstaller** (for creating standalone executables)

Optional (for testing bundling):

- **FFmpeg** (for testing media processing)
- **Deno** (for testing JavaScript extraction)

### Install Prerequisites

**Windows:**

```powershell
# Install Python from python.org or via winget
winget install Python.Python.3.11

# Install PyInstaller
pip install pyinstaller
```

**Linux:**

```bash
# Install Python (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3-pip

# Install PyInstaller
pip install pyinstaller
```

---

## Building from Source

### 1. Clone the Repository

```bash
git clone https://github.com/<USER>/<REPO>.git
cd downloadyha
```

### 2. Create Virtual Environment

**Windows:**

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

**Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 4. Build Standalone Executable

**Windows:**

```powershell
.\scripts\build-windows.ps1
```

**Linux:**

```bash
./scripts/build-linux.sh
```

The executable will be created in `dist/downloadyha` (Linux) or `dist\downloadyha.exe` (Windows).

### 5. Test the Build

```bash
# Windows
.\dist\downloadyha.exe

# Linux
./dist/downloadyha
```

---

## Project Structure

```
downloadyha/
│
├── src/
│   └── downloadyha/
│       ├── __init__.py          # Package initialization, version
│       ├── __main__.py          # Entry point
│       ├── cli.py               # Main CLI application
│       ├── dependencies.py      # Dependency management
│       ├── updater.py           # Self-update mechanism
│       ├── config.py            # Configuration handling
│       └── paths.py             # Platform-specific paths
│
├── scripts/
│   ├── build-windows.ps1        # Windows build script
│   ├── build-linux.sh           # Linux build script
│   ├── install.ps1              # Windows installer
│   └── install.sh               # Linux installer
│
├── .github/
│   └── workflows/
│       └── release.yml          # CI/CD pipeline
│
├── tests/                       # Test suite
│
├── pyproject.toml               # Project configuration
├── requirements.txt             # Python dependencies
├── README.md                    # User documentation
├── CONTRIBUTING.md              # This file
├── CHANGELOG.md                 # Version history
├── LICENSE                      # MIT License
└── .gitignore                   # Git ignore patterns
```

### Key Files

| File | Purpose |
|------|---------|
| `src/downloadyha/cli.py` | Main application logic, user interaction |
| `src/downloadyha/dependencies.py` | Manages bundled FFmpeg, Deno, yt-dlp |
| `src/downloadyha/updater.py` | Handles self-updates from GitHub Releases |
| `src/downloadyha/paths.py` | Cross-platform path resolution |
| `src/downloadyha/config.py` | User configuration file handling |
| `pyproject.toml` | Project metadata and build configuration |
| `scripts/install.ps1` | Windows one-command installer |
| `scripts/install.sh` | Linux one-command installer |

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit the source files in `src/downloadyha/`.

### 3. Test Locally

Run the application directly:

```bash
# Activate virtual environment first
python -m downloadyha
```

Or run tests:

```bash
pytest tests/
```

### 4. Build and Test

Build the executable and test it:

```bash
# Windows
.\scripts\build-windows.ps1
.\dist\downloadyha.exe

# Linux
./scripts/build-linux.sh
./dist/downloadyha
```

### 5. Commit and Push

```bash
git add .
git commit -m "Add your feature description"
git push origin feature/your-feature-name
```

### 6. Open Pull Request

Create a pull request on GitHub targeting the `main` or `master` branch.

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_cli.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=downloadyha --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

---

## Creating a Release

Releases are automated via GitHub Actions.

### 1. Update Version

Update the version in:
- `src/downloadyha/__init__.py` (`__version__`)
- `pyproject.toml` (`version`)

### 2. Update Changelog

Add release notes to `CHANGELOG.md`:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing features

### Fixed
- Bug fixes

### Dependencies
- Updated dependency versions
```

### 3. Commit and Tag

```bash
git add .
git commit -m "Release vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin master --tags
```

### 4. GitHub Actions

The `release.yml` workflow will automatically:
1. Run tests
2. Build executables for Windows x64, Linux x64, and Linux ARM64
3. Generate SHA-256 checksums
4. Create a GitHub Release
5. Upload all artifacts

### 5. Verify Release

Check the GitHub Releases page to verify:
- All platform artifacts are uploaded
- Checksums are present in `SHA256SUMS`
- Release notes are displayed correctly

---

## Code Style

### Python

Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines.

Key points:
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black default)
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and under 50 lines when possible

### Formatting with Black

```bash
pip install black
black src/
```

### Linting with Ruff

```bash
pip install ruff
ruff check src/
```

---

## Pull Request Process

1. **Fork the repository** and create your branch from `master`
2. **Make your changes** following the code style guidelines
3. **Add tests** for new functionality
4. **Update documentation** if needed (README.md, CHANGELOG.md)
5. **Ensure all tests pass**: `pytest tests/`
6. **Ensure the build works**: run the appropriate build script
7. **Submit a pull request** with a clear description

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] New functionality is documented
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages are clear and descriptive

---

## Architecture Overview

### Standalone Application Design

Downloadyha is a self-contained executable that bundles all dependencies:

```
downloadyha executable
│
├── Python runtime (embedded)
├── yt-dlp library (vendored)
│
└── External binaries (stored in app data dir):
    ├── ffmpeg
    ├── ffprobe
    └── deno
```

### Dependency Resolution

When Downloadyha starts:

1. Checks for bundled dependencies in `%LOCALAPPDATA%\Downloadyha\bin\` (Windows) or `~/.local/share/downloadyha/bin/` (Linux)
2. Verifies binaries with SHA-256 checksums
3. If missing or corrupted, downloads from trusted sources
4. Passes binary paths to yt-dlp via configuration

Example:

```python
# yt-dlp configuration with custom binary paths
ydl_opts = {
    "ffmpeg_location": get_ffmpeg_path(),
    "js_runtimes": {
        "deno": {
            "path": get_deno_path()
        }
    }
}
```

### Update Mechanism

1. User runs `downloadyha update`
2. Query GitHub Releases API: `https://api.github.com/repos/<USER>/<REPO>/releases/latest`
3. Compare version with current version
4. Download correct platform artifact
5. Verify SHA-256 checksum
6. Replace executable atomically
7. Preserve user configuration

---

## Security Considerations

- **SHA-256 verification**: All downloaded binaries are verified before execution
- **HTTPS-only**: All downloads use HTTPS
- **No execution before verification**: Binaries are never executed until checksums are validated
- **Atomic updates**: Updates replace the executable atomically to prevent corruption
- **User configuration preservation**: Updates never delete user data

---

## Getting Help

- **Open an issue**: [GitHub Issues](https://github.com/<USER>/<REPO>/issues)
- **Start a discussion**: [GitHub Discussions](https://github.com/<USER>/<REPO>/discussions)

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License. See [LICENSE](LICENSE) for details.
