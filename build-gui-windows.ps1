#!/usr/bin/env pwsh
#
# build-gui-windows.ps1
#
# Windows build script for downloadyha-gui standalone executable.
#
# Prerequisites:
#   - Python 3.10 or later
#   - Virtual environment (recommended)
#   - PyInstaller and customtkinter (installed via: pip install pyinstaller customtkinter)
#
# Usage:
#   .\build-gui-windows.ps1
#
# Output:
#   dist/downloadyha-gui.exe  — standalone GUI executable
#   dist/downloadyha-gui-windows.zip — distribution archive

param(
    [switch]$Clean = $false,
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Building downloadyha-gui for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean previous builds if requested
if ($Clean) {
    Write-Host "[1/6] Cleaning previous build artifacts..." -ForegroundColor Yellow

    if (Test-Path "build") {
        Remove-Item -Recurse -Force "build"
        Write-Host "  - Removed build/" -ForegroundColor Gray
    }

    if (Test-Path "dist/downloadyha-gui.exe") {
        Remove-Item -Force "dist/downloadyha-gui.exe"
        Write-Host "  - Removed dist/downloadyha-gui.exe" -ForegroundColor Gray
    }

    if (Test-Path "dist/downloadyha-gui-windows.zip") {
        Remove-Item -Force "dist/downloadyha-gui-windows.zip"
        Write-Host "  - Removed dist/downloadyha-gui-windows.zip" -ForegroundColor Gray
    }

    Write-Host "  Clean complete." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[1/6] Skipping clean (use -Clean to remove old builds)" -ForegroundColor Gray
    Write-Host ""
}

# Step 2: Check Python version
Write-Host "[2/6] Checking Python version..." -ForegroundColor Yellow

$pythonCmd = "python"
$pythonVersion = python --version 2>&1

$usePyLauncher = $false
if ($pythonVersion -match "Python (\d+)\.(\d+)") {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
        $usePyLauncher = $true
    }
} else {
    $usePyLauncher = $true
}

if ($usePyLauncher) {
    try {
        $pyVersion = py -3 --version 2>&1
        if ($pyVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 10)) {
                $pythonCmd = "py -3"
                $pythonVersion = $pyVersion
            }
        }
    } catch {
        # Keep original error handling
    }
}

Write-Host "  Using $pythonCmd: $pythonVersion" -ForegroundColor Gray

if ($pythonVersion -match "Python (\d+)\.(\d+)") {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]

    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
        Write-Host "  ERROR: Python 3.10+ required, found $major.$minor" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ERROR: Python not found. Install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

Write-Host "  Python version OK." -ForegroundColor Green
Write-Host ""

# Step 3: Install/check dependencies
Write-Host "[3/6] Installing build dependencies..." -ForegroundColor Yellow
& ($pythonCmd.Split(' ')) -m pip install --upgrade pip setuptools wheel | Out-Null
& ($pythonCmd.Split(' ')) -m pip install pyinstaller customtkinter pillow | Out-Null
Write-Host "  Dependencies installed." -ForegroundColor Green
Write-Host ""

# Step 4: Run PyInstaller
Write-Host "[4/6] Running PyInstaller..." -ForegroundColor Yellow
Write-Host "  Using spec file: downloadyha-gui.spec" -ForegroundColor Gray
Write-Host ""

& ($pythonCmd.Split(' ')) -m PyInstaller --clean --noconfirm downloadyha-gui.spec
$pyinstallerExitCode = $LASTEXITCODE

if ($pyinstallerExitCode -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: PyInstaller build failed with exit code $pyinstallerExitCode." -ForegroundColor Red
    exit $pyinstallerExitCode
}

Write-Host ""
Write-Host "  Build complete." -ForegroundColor Green
Write-Host ""

# Step 5: Verify executable
Write-Host "[5/6] Verifying executable..." -ForegroundColor Yellow

$exePath = "dist\downloadyha-gui.exe"

if (-not (Test-Path $exePath)) {
    Write-Host "  ERROR: Executable not found at $exePath" -ForegroundColor Red
    exit 1
}

$fileSize = (Get-Item $exePath).Length
$fileSizeMB = [math]::Round($fileSize / 1MB, 2)

Write-Host "  Executable: $exePath" -ForegroundColor Gray
Write-Host "  Size: $fileSizeMB MB" -ForegroundColor Gray

# Optional: Quick smoke test
if (-not $SkipTests) {
    Write-Host ""
    Write-Host "  Running smoke test..." -ForegroundColor Gray
    Write-Host "  (GUI will launch briefly and close)" -ForegroundColor Gray

    # For GUI, we just check that it starts without immediate crash
    # Can't do full test without automation framework
    Write-Host "  Smoke test skipped for GUI (manual testing recommended)." -ForegroundColor Yellow
}

Write-Host ""

# Step 6: Create distribution archive
Write-Host "[6/6] Creating distribution archive..." -ForegroundColor Yellow

$archivePath = "dist\downloadyha-gui-windows.zip"

# Create a temporary directory for the archive contents
$tempDir = "dist\temp_package"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy executable
Copy-Item $exePath "$tempDir\downloadyha-gui.exe"

# Create README for the package
$readmeContent = @"
# Downloadyha GUI - Windows

Fast & Beautiful YouTube Downloader - Desktop GUI Edition

## Installation

1. Extract this ZIP file to a folder of your choice
2. Double-click `downloadyha-gui.exe` to launch the application
3. No installation or dependencies required!

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

- Windows 10/11 (64-bit)
- Internet connection

## Uninstallation

Simply delete the folder containing downloadyha-gui.exe

## Support

Report issues at: https://github.com/ahmed-tarek-2004/DownloadYha/issues

---
Version: 1.0.0
License: MIT
"@

Set-Content -Path "$tempDir\README.txt" -Value $readmeContent

# Create QUICKSTART.txt for the package
$quickstartContent = @"
==================================================
  Downloadyha Desktop GUI - Quick Start Guide
==================================================

Step 1: Double-click downloadyha-gui.exe to start.
Step 2: Paste your YouTube video or playlist URL.
Step 3: Choose Video or Audio format, pick your quality, and click START DOWNLOAD!

Files are saved to your Downloads folder by default.
You can change the destination folder anytime in the app.

No installation, Python, or FFmpeg setup required!
==================================================
"@
Set-Content -Path "$tempDir\QUICKSTART.txt" -Value $quickstartContent

# Create the ZIP archive
if (Test-Path $archivePath) {
    Remove-Item -Force $archivePath
}

Compress-Archive -Path "$tempDir\*" -DestinationPath $archivePath

# Clean up temp directory
Remove-Item -Recurse -Force $tempDir

$archiveSize = (Get-Item $archivePath).Length
$archiveSizeMB = [math]::Round($archiveSize / 1MB, 2)

Write-Host "  Archive: $archivePath" -ForegroundColor Gray
Write-Host "  Size: $archiveSizeMB MB" -ForegroundColor Gray
Write-Host "  Archive created successfully." -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Build successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Executable: $exePath" -ForegroundColor White
Write-Host "Archive: $archivePath" -ForegroundColor White
Write-Host ""
Write-Host "Notes:" -ForegroundColor White
Write-Host "  - The executable is standalone and manages its own dependencies." -ForegroundColor Gray
Write-Host "  - Test the GUI: .\$exePath" -ForegroundColor Gray
Write-Host "  - Distribute the ZIP file for easy installation." -ForegroundColor Gray
Write-Host ""
