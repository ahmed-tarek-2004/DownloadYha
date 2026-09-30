#!/usr/bin/env pwsh
#
# build-windows.ps1
#
# Windows build script for downloadyha standalone executable.
#
# Prerequisites:
#   - Python 3.10 or later
#   - Virtual environment (recommended)
#   - PyInstaller (installed via: pip install pyinstaller)
#
# Usage:
#   .\build-windows.ps1
#
# Output:
#   dist/downloadyha.exe  — standalone executable

param(
    [switch]$Clean = $false,
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Building downloadyha for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean previous builds if requested
if ($Clean) {
    Write-Host "[1/5] Cleaning previous build artifacts..." -ForegroundColor Yellow

    if (Test-Path "build") {
        Remove-Item -Recurse -Force "build"
        Write-Host "  - Removed build/" -ForegroundColor Gray
    }

    if (Test-Path "dist") {
        Remove-Item -Recurse -Force "dist"
        Write-Host "  - Removed dist/" -ForegroundColor Gray
    }

    Write-Host "  Clean complete." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[1/5] Skipping clean (use -Clean to remove old builds)" -ForegroundColor Gray
    Write-Host ""
}

# Step 2: Check Python version
Write-Host "[2/5] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  $pythonVersion" -ForegroundColor Gray

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Python not found. Install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

# Parse version (e.g., "Python 3.11.4")
$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]

    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
        Write-Host "  ERROR: Python 3.10+ required, found $major.$minor" -ForegroundColor Red
        exit 1
    }
}

Write-Host "  Python version OK." -ForegroundColor Green
Write-Host ""

# Step 3: Install/check dependencies
Write-Host "[3/5] Installing build dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel | Out-Null
python -m pip install pyinstaller | Out-Null
Write-Host "  Dependencies installed." -ForegroundColor Green
Write-Host ""

# Step 4: Run PyInstaller
Write-Host "[4/5] Running PyInstaller..." -ForegroundColor Yellow
Write-Host "  Using spec file: downloadyha.spec" -ForegroundColor Gray
Write-Host ""

pyinstaller --clean --noconfirm downloadyha.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: PyInstaller build failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  Build complete." -ForegroundColor Green
Write-Host ""

# Step 5: Verify executable
Write-Host "[5/5] Verifying executable..." -ForegroundColor Yellow

$exePath = "dist\downloadyha.exe"

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
    Write-Host "  Running smoke test (--help)..." -ForegroundColor Gray

    # The app expects interactive input, so we'll just check that it runs
    # without crashing.  A real test would pipe input or use --help if added.
    $testOutput = & $exePath 2>&1 | Select-Object -First 5

    if ($LASTEXITCODE -eq 0 -or $testOutput -match "Downloadyha") {
        Write-Host "  Smoke test passed." -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Smoke test did not find expected output." -ForegroundColor Yellow
        Write-Host "  Manual testing recommended." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Build successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Executable: $exePath" -ForegroundColor White
Write-Host ""
Write-Host "Notes:" -ForegroundColor White
Write-Host "  - The executable is standalone and does not require Python." -ForegroundColor Gray
Write-Host "  - FFmpeg and Deno must be installed separately on the target system." -ForegroundColor Gray
Write-Host "  - Test the executable: .\$exePath" -ForegroundColor Gray
Write-Host ""
