#!/usr/bin/env bash
#
# Installer for downloadyha on Linux.
#
# - Detects architecture (x64, arm64)
# - Downloads the latest release from GitHub
# - Verifies SHA-256 checksum
# - Installs to ~/.local/bin/
# - Adds ~/.local/bin/ to PATH if needed
# - Sets executable permissions
# - Verifies the installation works
#
# Repository: https://github.com/ahmed-tarek-2004/DownloadYha

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
REPO="ahmed-tarek-2004/DownloadYha"
APP_NAME="downloadyha"
INSTALL_DIR="${HOME}/.local/bin"
API_BASE="https://api.github.com/repos/${REPO}"
RELEASES="https://github.com/${REPO}/releases"

# ── Colors ───────────────────────────────────────────────────────────────────
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# ── Helpers ──────────────────────────────────────────────────────────────────
step() {
    echo -e "${CYAN}  ==> ${1}${NC}"
}

ok() {
    echo -e "${GREEN}  [OK] ${1}${NC}"
}

fail() {
    echo -e "${RED}  [ERR] ${1}${NC}" >&2
    exit 1
}

# ── Detect Architecture ──────────────────────────────────────────────────────
detect_arch() {
    local arch
    arch="$(uname -m)"

    case "$arch" in
        x86_64|amd64)
            echo "x86_64"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        *)
            fail "Unsupported architecture: $arch. Only x86_64 and arm64 are supported."
            ;;
    esac
}

# ── Get Latest Version ───────────────────────────────────────────────────────
get_latest_version() {
    echo "  ==> Fetching latest release information..." >&2

    local version
    if command -v curl >/dev/null 2>&1; then
        version=$(curl -fsSL "${API_BASE}/releases/latest" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
    elif command -v wget >/dev/null 2>&1; then
        version=$(wget -qO- "${API_BASE}/releases/latest" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
    else
        fail "Neither curl nor wget found. Please install one of them."
    fi

    if [ -z "$version" ]; then
        fail "Could not fetch latest release from GitHub. Check your internet connection or the repository URL (${REPO})."
    fi

    echo "$version"
}

# ── Download File ────────────────────────────────────────────────────────────
download_file() {
    local url="$1"
    local output="$2"

    if command -v curl >/dev/null 2>&1; then
        curl -fsSL -o "$output" "$url" || fail "Failed to download $url"
    elif command -v wget >/dev/null 2>&1; then
        wget -q -O "$output" "$url" || fail "Failed to download $url"
    else
        fail "Neither curl nor wget found. Please install one of them."
    fi
}

# ── Verify Checksum ──────────────────────────────────────────────────────────
verify_checksum() {
    local file_path="$1"
    local sums_file="$2"
    local file_name="$3"

    step "Verifying SHA-256 checksum..."

    if [ ! -f "$sums_file" ]; then
        fail "Checksum file not found: $sums_file"
    fi

    # Extract the expected hash for this file from SHA256SUMS
    # Format: "<hash>  <filename>" or "<hash> *<filename>"
    local expected
    expected=$(grep -E "^[a-fA-F0-9]{64}[[:space:]]+\*?${file_name}$" "$sums_file" | awk '{print $1}' | tr '[:upper:]' '[:lower:]')

    if [ -z "$expected" ]; then
        fail "No checksum entry found for '${file_name}' in SHA256SUMS."
    fi

    # Compute actual hash
    local actual
    if command -v sha256sum >/dev/null 2>&1; then
        actual=$(sha256sum "$file_path" | awk '{print $1}' | tr '[:upper:]' '[:lower:]')
    elif command -v shasum >/dev/null 2>&1; then
        actual=$(shasum -a 256 "$file_path" | awk '{print $1}' | tr '[:upper:]' '[:lower:]')
    else
        fail "Neither sha256sum nor shasum found. Please install coreutils or similar."
    fi

    if [ "$actual" != "$expected" ]; then
        fail "Checksum mismatch!\n  Expected : $expected\n  Actual   : $actual"
    fi

    ok "Checksum verified."
}

# ── Add to PATH ──────────────────────────────────────────────────────────────
add_to_path() {
    local dir="$1"

    # Check if already in PATH
    if [[ ":$PATH:" == *":${dir}:"* ]]; then
        ok "PATH already contains: $dir"
        return
    fi

    step "Adding '${dir}' to PATH..."

    # Determine which shell profile to update
    local profile=""
    if [ -n "${BASH_VERSION:-}" ]; then
        if [ -f "${HOME}/.bashrc" ]; then
            profile="${HOME}/.bashrc"
        elif [ -f "${HOME}/.bash_profile" ]; then
            profile="${HOME}/.bash_profile"
        fi
    elif [ -n "${ZSH_VERSION:-}" ]; then
        profile="${HOME}/.zshrc"
    else
        # Fallback: try common profiles
        if [ -f "${HOME}/.bashrc" ]; then
            profile="${HOME}/.bashrc"
        elif [ -f "${HOME}/.bash_profile" ]; then
            profile="${HOME}/.bash_profile"
        elif [ -f "${HOME}/.zshrc" ]; then
            profile="${HOME}/.zshrc"
        elif [ -f "${HOME}/.profile" ]; then
            profile="${HOME}/.profile"
        fi
    fi

    if [ -n "$profile" ]; then
        # Add to profile if not already there
        if ! grep -qF "export PATH=\"${dir}:\$PATH\"" "$profile" && \
           ! grep -qF "export PATH='${dir}:\$PATH'" "$profile" && \
           ! grep -qF "PATH=\"${dir}:\$PATH\"" "$profile" && \
           ! grep -qF "PATH='${dir}:\$PATH'" "$profile"; then
            echo "" >> "$profile"
            echo "# Added by downloadyha installer" >> "$profile"
            echo "export PATH=\"${dir}:\$PATH\"" >> "$profile"
            ok "Added to PATH in $profile"
        else
            ok "PATH entry already exists in $profile"
        fi
    else
        echo -e "${YELLOW}  [WARN] Could not detect shell profile. Manually add '${dir}' to your PATH.${NC}"
    fi

    # Update PATH for current session
    export PATH="${dir}:$PATH"
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo -e "${YELLOW}  Downloadyha Installer (Linux)${NC}"
    echo -e "${YELLOW}  ==============================${NC}"
    echo ""

    # 1. Detect architecture
    local arch
    arch=$(detect_arch)
    ok "Architecture: $arch"

    # 2. Get latest version (or use VERSION env var if set)
    local version="${VERSION:-}"
    if [ -z "$version" ]; then
        version=$(get_latest_version)
    fi
    ok "Version: $version"

    # 3. Build asset names
    # Expected release asset pattern: downloadyha-<version>-linux-<arch>.tar.gz
    local asset_name="${APP_NAME}-${version}-linux-${arch}.tar.gz"
    local sums_name="SHA256SUMS"
    local asset_url="${RELEASES}/download/${version}/${asset_name}"
    local sums_url="${RELEASES}/download/${version}/${sums_name}"

    # 4. Download to a temp directory
    local tmp_dir
    tmp_dir=$(mktemp -d -t downloadyha-install.XXXXXX)
    trap 'rm -rf "$tmp_dir"' EXIT

    local asset_path="${tmp_dir}/${asset_name}"
    local sums_path="${tmp_dir}/${sums_name}"

    step "Downloading release asset: $asset_url"
    download_file "$asset_url" "$asset_path"

    step "Downloading checksum file: $sums_url"
    download_file "$sums_url" "$sums_path"

    # 5. Verify checksum
    verify_checksum "$asset_path" "$sums_path" "$asset_name"

    # 6. Create install directory
    step "Installing to: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"

    # 7. Extract archive
    step "Extracting archive..."
    tar -xzf "$asset_path" -C "$tmp_dir"

    # Find the binary (might be in a subdirectory after extraction)
    local binary
    binary=$(find "$tmp_dir" -type f -name "$APP_NAME" | head -n 1)

    if [ -z "$binary" ] || [ ! -f "$binary" ]; then
        fail "Binary '${APP_NAME}' was not found in the archive after extraction."
    fi

    # Copy to install directory
    cp "$binary" "${INSTALL_DIR}/${APP_NAME}"
    chmod +x "${INSTALL_DIR}/${APP_NAME}"
    ok "Installed to ${INSTALL_DIR}/${APP_NAME}"

    # 8. Add to PATH
    add_to_path "$INSTALL_DIR"

    # 9. Verify the binary runs
    step "Verifying installation..."
    local ver_output
    ver_output=$("${INSTALL_DIR}/${APP_NAME}" --version 2>&1) || fail "Binary ran but exited with an error. Output: $ver_output"
    ok "Installation verified: $ver_output"

    echo ""
    echo -e "${GREEN}  Downloadyha ${version} has been installed successfully!${NC}"
    echo -e "${GREEN}  Run 'downloadyha --help' in a new terminal to get started.${NC}"
    echo ""
}

main "$@"
