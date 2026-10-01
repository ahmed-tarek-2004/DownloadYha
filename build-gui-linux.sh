#!/usr/bin/env bash
#
# build-gui-linux.sh
#
# Linux build script for downloadyha-gui standalone executable.
#
# Prerequisites:
#   - Python 3.10 or later
#   - Virtual environment (recommended)
#   - PyInstaller and customtkinter (installed via: pip install pyinstaller customtkinter)
#
# Usage:
#   chmod +x build-gui-linux.sh
#   ./build-gui-linux.sh
#
# Output:
#   dist/downloadyha-gui  — standalone GUI executable
#   dist/downloadyha-gui-linux.tar.gz — distribution archive

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Parse arguments
CLEAN=false
SKIP_TESTS=false

for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
    esac
done

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Building downloadyha-gui for Linux${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Step 1: Clean previous builds if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}[1/6] Cleaning previous build artifacts...${NC}"

    rm -rf build
    echo -e "${GRAY}  - Removed build/${NC}"

    rm -f dist/downloadyha-gui
    echo -e "${GRAY}  - Removed dist/downloadyha-gui${NC}"

    rm -f dist/downloadyha-gui-linux.tar.gz
    echo -e "${GRAY}  - Removed dist/downloadyha-gui-linux.tar.gz${NC}"

    echo -e "${GREEN}  Clean complete.${NC}"
    echo ""
else
    echo -e "${GRAY}[1/6] Skipping clean (use --clean to remove old builds)${NC}"
    echo ""
fi

# Step 2: Check Python version
echo -e "${YELLOW}[2/6] Checking Python version...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}  ERROR: Python3 not found. Install Python 3.10+ first.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GRAY}  $PYTHON_VERSION${NC}"

# Parse version (e.g., "Python 3.11.4")
VERSION_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
VERSION_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$VERSION_MAJOR" -lt 3 ] || { [ "$VERSION_MAJOR" -eq 3 ] && [ "$VERSION_MINOR" -lt 10 ]; }; then
    echo -e "${RED}  ERROR: Python 3.10+ required, found $VERSION_MAJOR.$VERSION_MINOR${NC}"
    exit 1
fi

echo -e "${GREEN}  Python version OK.${NC}"
echo ""

# Step 3: Install/check dependencies
echo -e "${YELLOW}[3/6] Installing build dependencies...${NC}"
python3 -m pip install --upgrade pip setuptools wheel --quiet
python3 -m pip install pyinstaller customtkinter pillow --quiet
echo -e "${GREEN}  Dependencies installed.${NC}"
echo ""

# Step 4: Run PyInstaller
echo -e "${YELLOW}[4/6] Running PyInstaller...${NC}"
echo -e "${GRAY}  Using spec file: downloadyha-gui.spec${NC}"
echo ""

pyinstaller --clean --noconfirm downloadyha-gui.spec

echo ""
echo -e "${GREEN}  Build complete.${NC}"
echo ""

# Step 5: Verify executable
echo -e "${YELLOW}[5/6] Verifying executable...${NC}"

EXE_PATH="dist/downloadyha-gui"

if [ ! -f "$EXE_PATH" ]; then
    echo -e "${RED}  ERROR: Executable not found at $EXE_PATH${NC}"
    exit 1
fi

FILE_SIZE=$(stat -c%s "$EXE_PATH" 2>/dev/null || stat -f%z "$EXE_PATH" 2>/dev/null)
FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1048576" | bc)

echo -e "${GRAY}  Executable: $EXE_PATH${NC}"
echo -e "${GRAY}  Size: $FILE_SIZE_MB MB${NC}"

# Make executable
chmod +x "$EXE_PATH"

# Optional: Quick smoke test
if [ "$SKIP_TESTS" = false ]; then
    echo ""
    echo -e "${GRAY}  Running smoke test...${NC}"
    echo -e "${YELLOW}  Smoke test skipped for GUI (manual testing recommended).${NC}"
fi

echo ""

# Step 6: Create distribution archive
echo -e "${YELLOW}[6/6] Creating distribution archive...${NC}"

ARCHIVE_PATH="dist/downloadyha-gui-linux.tar.gz"

# Create a temporary directory for the archive contents
TEMP_DIR="dist/temp_package"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Copy executable
cp "$EXE_PATH" "$TEMP_DIR/downloadyha-gui"

# Create README for the package
cat > "$TEMP_DIR/README.txt" << 'EOF'
# Downloadyha GUI - Linux

Fast & Beautiful YouTube Downloader - Desktop GUI Edition

## Installation

1. Extract this archive: tar -xzf downloadyha-gui-linux.tar.gz
2. Make executable: chmod +x downloadyha-gui
3. Run: ./downloadyha-gui
4. No installation or dependencies required!

## Usage

1. Paste a YouTube video or playlist URL
2. Choose video or audio download
3. Select quality (for videos)
4. Choose your download folder
5. Click Download!

## Features

- Single video downloads (up to 4K)
- Audio extraction to MP3
- Full playlist downloads
- Modern, easy-to-use interface
- Real-time progress tracking

## System Requirements

- Linux x86_64 (glibc 2.31+)
- Linux ARM64 (glibc 2.31+)
- X11 or Wayland display server
- Internet connection

## Uninstallation

Simply delete the downloadyha-gui file

## Support

Report issues at: https://github.com/ahmed-tarek-2004/DownloadYha/issues

---
Version: 1.0.0
License: MIT
EOF

# Create the tar.gz archive
cd dist
tar -czf "downloadyha-gui-linux.tar.gz" -C temp_package .
cd ..

# Clean up temp directory
rm -rf "$TEMP_DIR"

ARCHIVE_SIZE=$(stat -c%s "$ARCHIVE_PATH" 2>/dev/null || stat -f%z "$ARCHIVE_PATH" 2>/dev/null)
ARCHIVE_SIZE_MB=$(echo "scale=2; $ARCHIVE_SIZE / 1048576" | bc)

echo -e "${GRAY}  Archive: $ARCHIVE_PATH${NC}"
echo -e "${GRAY}  Size: $ARCHIVE_SIZE_MB MB${NC}"
echo -e "${GREEN}  Archive created successfully.${NC}"

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}  Build successful!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "Executable: ${EXE_PATH}"
echo -e "Archive: ${ARCHIVE_PATH}"
echo ""
echo "Notes:"
echo -e "${GRAY}  - The executable is standalone and manages its own dependencies.${NC}"
echo -e "${GRAY}  - Test the GUI: ./${EXE_PATH}${NC}"
echo -e "${GRAY}  - Distribute the tar.gz file for easy installation.${NC}"
echo ""
