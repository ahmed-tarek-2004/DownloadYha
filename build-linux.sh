#!/usr/bin/env bash
#
# build-linux.sh
#
# Linux build script for downloadyha standalone executable.
#
# Prerequisites:
#   - Python 3.10 or later
#   - Virtual environment (recommended)
#   - PyInstaller (installed via: pip install pyinstaller)
#
# Usage:
#   chmod +x build-linux.sh
#   ./build-linux.sh
#
# Output:
#   dist/downloadyha  — standalone executable

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
echo -e "${CYAN}  Building downloadyha for Linux${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Step 1: Clean previous builds if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}[1/5] Cleaning previous build artifacts...${NC}"

    rm -rf build
    echo -e "${GRAY}  - Removed build/${NC}"

    rm -rf dist
    echo -e "${GRAY}  - Removed dist/${NC}"

    echo -e "${GREEN}  Clean complete.${NC}"
    echo ""
else
    echo -e "${GRAY}[1/5] Skipping clean (use --clean to remove old builds)${NC}"
    echo ""
fi

# Step 2: Check Python version
echo -e "${YELLOW}[2/5] Checking Python version...${NC}"

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
echo -e "${YELLOW}[3/5] Installing build dependencies...${NC}"
python3 -m pip install --upgrade pip setuptools wheel --quiet
python3 -m pip install pyinstaller --quiet
echo -e "${GREEN}  Dependencies installed.${NC}"
echo ""

# Step 4: Run PyInstaller
echo -e "${YELLOW}[4/5] Running PyInstaller...${NC}"
echo -e "${GRAY}  Using spec file: downloadyha.spec${NC}"
echo ""

pyinstaller --clean --noconfirm downloadyha.spec

echo ""
echo -e "${GREEN}  Build complete.${NC}"
echo ""

# Step 5: Verify executable
echo -e "${YELLOW}[5/5] Verifying executable...${NC}"

EXE_PATH="dist/downloadyha"

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

    # The app expects interactive input, so we'll just check that it runs
    # without crashing by capturing the first few lines of output.
    TEST_OUTPUT=$(timeout 2 "$EXE_PATH" 2>&1 | head -5 || true)

    if echo "$TEST_OUTPUT" | grep -q "Downloadyha"; then
        echo -e "${GREEN}  Smoke test passed.${NC}"
    else
        echo -e "${YELLOW}  WARNING: Smoke test did not find expected output.${NC}"
        echo -e "${YELLOW}  Manual testing recommended.${NC}"
    fi
fi

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}  Build successful!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "Executable: ${EXE_PATH}"
echo ""
echo "Notes:"
echo -e "${GRAY}  - The executable is standalone and manages its own dependencies.${NC}"
echo -e "${GRAY}  - Test the executable: ./$EXE_PATH${NC}"
echo ""
