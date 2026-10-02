#Requires -Version 5.1
<#
.SYNOPSIS
    Installer for downloadyha on Windows.

.DESCRIPTION
    - Detects Windows architecture (x64)
    - Downloads the latest release from GitHub
    - Verifies SHA-256 checksum
    - Installs to %LOCALAPPDATA%\Programs\Downloadyha\
    - Adds the install directory to the user PATH if needed
    - No administrator privileges required
    - Verifies the installation works after install

.NOTES
    Repository: https://github.com/ahmed-tarek-2004/DownloadYha
#>

[CmdletBinding()]
param (
    # Override the release tag to install (default: latest)
    [string]$Version = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Configuration ────────────────────────────────────────────────────────────
$REPO       = "ahmed-tarek-2004/DownloadYha"
$APP_NAME   = "downloadyha"
$INSTALL_DIR = Join-Path $env:LOCALAPPDATA "Programs\Downloadyha"
$API_BASE   = "https://api.github.com/repos/$REPO"
$RELEASES   = "https://github.com/$REPO/releases"

# ── Helpers ──────────────────────────────────────────────────────────────────
function Write-Step  { param([string]$Msg) Write-Host "  ==> $Msg" -ForegroundColor Cyan   }
function Write-Ok    { param([string]$Msg) Write-Host "  [OK] $Msg" -ForegroundColor Green  }
function Write-Fail  { param([string]$Msg) Write-Host "  [ERR] $Msg" -ForegroundColor Red; exit 1 }

function Stop-RunningApp {
    param([string]$ProcessName = $APP_NAME)

    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Step "Closing running $ProcessName processes..."
        $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500

        # If any processes are still lingering, try once more
        $lingering = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
        if ($lingering) {
            $lingering | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        }
    }
}

function Install-ArchiveSafe {
    param(
        [string]$ZipPath,
        [string]$DestinationDir,
        [string]$TempDirectory
    )

    # 1. Stop running processes to prevent file locking
    Stop-RunningApp -ProcessName $APP_NAME

    # 2. Clean up leftover .old and .tmp files from prior installations
    Get-ChildItem -Path $DestinationDir -Filter "${APP_NAME}*.old*" -File -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $DestinationDir -Filter "${APP_NAME}*.tmp*" -File -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue

    # 3. Handle existing binary: rename to .old so replacement works cleanly even if locked
    $existingExe = Join-Path $DestinationDir "${APP_NAME}.exe"
    $backupExe   = $null
    if (Test-Path $existingExe) {
        $backupExe = Join-Path $DestinationDir "${APP_NAME}.exe.old"
        if (Test-Path $backupExe) {
            Remove-Item -Path $backupExe -Force -ErrorAction SilentlyContinue
        }
        try {
            Rename-Item -Path $existingExe -NewName "${APP_NAME}.exe.old" -Force -ErrorAction SilentlyContinue
        } catch {
            # Continue even if rename fails; fallback extraction will handle it
        }
    }

    Write-Step "Extracting archive..."
    $extracted = $false

    try {
        Expand-Archive -Path $ZipPath -DestinationPath $DestinationDir -Force
        $extracted = $true
    } catch {
        # Fallback approach: extract to staging directory and copy files
        Write-Step "Standard extraction encountered an issue; retrying with resilient fallback..."
        Stop-RunningApp -ProcessName $APP_NAME

        try {
            $stageDir = Join-Path $TempDirectory "extracted"
            if (-not (Test-Path $stageDir)) {
                New-Item -ItemType Directory -Path $stageDir -Force | Out-Null
            }

            # Try Expand-Archive to staging directory, or fallback to .NET ZipFile
            try {
                Expand-Archive -Path $ZipPath -DestinationPath $stageDir -Force
            } catch {
                Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
                [System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $stageDir)
            }

            # Copy extracted files to destination directory with safe renaming
            Get-ChildItem -Path $stageDir -Recurse -File | ForEach-Object {
                $relativePath = $_.FullName.Substring($stageDir.Length).TrimStart('\', '/')
                $targetFile = Join-Path $DestinationDir $relativePath
                $targetParent = [System.IO.Path]::GetDirectoryName($targetFile)
                if (-not (Test-Path $targetParent)) {
                    New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
                }

                if (Test-Path $targetFile) {
                    $tmpBackup = "$targetFile.old"
                    if (Test-Path $tmpBackup) {
                        Remove-Item -Path $tmpBackup -Force -ErrorAction SilentlyContinue
                    }
                    try {
                        Rename-Item -Path $targetFile -NewName "$($_.Name).old" -Force -ErrorAction SilentlyContinue
                    } catch {}
                }

                Copy-Item -Path $_.FullName -Destination $targetFile -Force

                if (Test-Path "$targetFile.old") {
                    Remove-Item -Path "$targetFile.old" -Force -ErrorAction SilentlyContinue
                }
            }
            $extracted = $true
        } catch {
            Write-Fail @"
Failed to extract archive to '$DestinationDir': $_

Troubleshooting:
  1. Ensure no instances of '$APP_NAME' are running (check Task Manager).
  2. Check if you have write permissions to: $DestinationDir
  3. Temporarily disable any antivirus or security software locking '$DestinationDir'.
  4. Try restarting your terminal or running PowerShell as Administrator.
"@
        }
    }

    if ($extracted) {
        # Clean up the backup file if extraction succeeded
        if ($backupExe -and (Test-Path $backupExe)) {
            Remove-Item -Path $backupExe -Force -ErrorAction SilentlyContinue
        }
        Write-Ok "Files extracted to $DestinationDir"
    }
}

function Get-Architecture {
    $is64 = [System.Environment]::Is64BitOperatingSystem
    $archEnv = [System.Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITEW6432")
    if (-not $archEnv) {
        $archEnv = [System.Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITECTURE")
    }

    if ($archEnv -eq "AMD64" -or $archEnv -eq "x86_64" -or ($is64 -and $archEnv -ne "ARM64")) {
        return "x86_64"
    } elseif ($archEnv -eq "ARM64") {
        Write-Fail "Unsupported architecture: ARM64. Only x64 is currently supported."
    } else {
        Write-Fail "Unsupported architecture: $archEnv. Only x64 is supported."
    }
}

function Invoke-SafeWebRequest {
    param([string]$Uri, [string]$OutFile)
    try {
        $ProgressPreference = "SilentlyContinue"   # speeds up downloads significantly
        Invoke-WebRequest -Uri $Uri -OutFile $OutFile -UseBasicParsing
    } catch {
        Write-Fail "Failed to download '$Uri': $_"
    }
}

function Get-LatestVersion {
    Write-Step "Fetching latest release information..."
    try {
        $ProgressPreference = "SilentlyContinue"
        $response = Invoke-RestMethod -Uri "$API_BASE/releases/latest" -UseBasicParsing
        return $response.tag_name
    } catch {
        Write-Fail "Could not fetch latest release from GitHub. Check your internet connection or the repository URL ($REPO)."
    }
}

function Test-Checksum {
    param([string]$FilePath, [string]$SumsFile, [string]$FileName)

    Write-Step "Verifying SHA-256 checksum..."

    if (-not (Test-Path $SumsFile)) {
        Write-Fail "Checksum file not found: $SumsFile"
    }

    # Parse SHA256SUMS file (format: "<hash>  <filename>" or "<hash> *<filename>")
    $expected = $null
    foreach ($line in (Get-Content $SumsFile)) {
        $parts = $line -split '\s+', 2
        if ($parts.Count -eq 2 -and $parts[1].TrimStart('*') -eq $FileName) {
            $expected = $parts[0].ToLower()
            break
        }
    }

    if (-not $expected) {
        Write-Fail "No checksum entry found for '$FileName' in SHA256SUMS."
    }

    $actual = $null
    if (Get-Command Get-FileHash -ErrorAction SilentlyContinue) {
        $actual = (Get-FileHash -Path $FilePath -Algorithm SHA256).Hash.ToLower()
    } else {
        $sha256 = [System.Security.Cryptography.SHA256]::Create()
        $fileStream = [System.IO.File]::OpenRead($FilePath)
        try {
            $hashBytes = $sha256.ComputeHash($fileStream)
            $actual = [System.BitConverter]::ToString($hashBytes).Replace("-", "").ToLower()
        } finally {
            $fileStream.Close()
            $sha256.Dispose()
        }
    }

    if ($actual -ne $expected) {
        Write-Fail "Checksum mismatch!`n  Expected : $expected`n  Actual   : $actual"
    }

    Write-Ok "Checksum verified."
}

function Add-ToUserPath {
    param([string]$Directory)

    $userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
    if (-not $userPath) {
        $userPath = ""
    }

    $cleanDir = $Directory.Trim().TrimEnd('\', '/')
    $rawEntries = $userPath -split ";" | Where-Object { $_ -and $_.Trim() -ne "" }
    $filteredEntries = @()

    foreach ($entry in $rawEntries) {
        $entryClean = $entry.Trim().TrimEnd('\', '/')
        if ($entryClean -and ($entryClean.ToLowerInvariant() -ne $cleanDir.ToLowerInvariant())) {
            $filteredEntries += $entry.Trim()
        }
    }

    Write-Step "Configuring '$Directory' in user PATH..."
    if ($filteredEntries.Count -gt 0) {
        $newPath = "$cleanDir;" + ($filteredEntries -join ";")
    } else {
        $newPath = $cleanDir
    }

    [System.Environment]::SetEnvironmentVariable("PATH", $newPath, "User")

    # Also update the current session PATH
    $env:PATH = "$cleanDir;$env:PATH"

    Write-Ok "Added to user PATH with priority."
}

function Remove-ConflictingPythonStubs {
    param([string]$DestinationDir)

    # Look for stale pip wrappers in user's Python Scripts directories
    $allCommands = @(Get-Command -Name $APP_NAME -All -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
    foreach ($cmdPath in $allCommands) {
        if ($cmdPath -and ($cmdPath -notlike "$DestinationDir*")) {
            if ($cmdPath -like "*\Python*\Scripts\*" -or $cmdPath -like "*\site-packages\*") {
                Write-Step "Cleaning up conflicting old Python wrapper: $cmdPath"
                try {
                    Remove-Item -Path $cmdPath -Force -ErrorAction SilentlyContinue
                } catch {}
            }
        }
    }
}

# ── Main ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Downloadyha Installer (Windows)" -ForegroundColor Yellow
Write-Host "  ================================" -ForegroundColor Yellow
Write-Host ""

# 1. Architecture check
$arch = Get-Architecture
Write-Ok "Architecture: $arch"

# 2. Resolve version
if ($Version -eq "") {
    $Version = Get-LatestVersion
}
Write-Ok "Version: $Version"

# 3. Build asset names
#    Expected release asset pattern:  downloadyha-<version>-windows-x86_64.zip
$assetName  = "${APP_NAME}-${Version}-windows-${arch}.zip"
$sumsName   = "SHA256SUMS"
$assetUrl   = "$RELEASES/download/$Version/$assetName"
$sumsUrl    = "$RELEASES/download/$Version/$sumsName"

# 4. Download to a temp directory
$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) "downloadyha-install-$([guid]::NewGuid().ToString('N').Substring(0,8))"
New-Item -ItemType Directory -Path $tmpDir | Out-Null

$assetPath = Join-Path $tmpDir $assetName
$sumsPath  = Join-Path $tmpDir $sumsName

try {
    Write-Step "Downloading release asset: $assetUrl"
    Invoke-SafeWebRequest -Uri $assetUrl -OutFile $assetPath

    Write-Step "Downloading checksum file: $sumsUrl"
    Invoke-SafeWebRequest -Uri $sumsUrl -OutFile $sumsPath

    # 5. Verify checksum
    Test-Checksum -FilePath $assetPath -SumsFile $sumsPath -FileName $assetName

    # 6. Create install directory
    Write-Step "Installing to: $INSTALL_DIR"
    if (-not (Test-Path $INSTALL_DIR)) {
        New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
    }

    # 7. Extract archive
    Install-ArchiveSafe -ZipPath $assetPath -DestinationDir $INSTALL_DIR -TempDirectory $tmpDir

    # 8. Add to PATH with priority
    Add-ToUserPath -Directory $INSTALL_DIR

    # 9. Clean up any conflicting old python pip wrappers
    Remove-ConflictingPythonStubs -DestinationDir $INSTALL_DIR

    # 10. Verify the binary runs
    Write-Step "Verifying installation..."
    $binary = Join-Path $INSTALL_DIR "${APP_NAME}.exe"
    if (-not (Test-Path $binary)) {
        # Fallback: look for the executable anywhere under the install dir
        $binary = Get-ChildItem -Path $INSTALL_DIR -Filter "${APP_NAME}.exe" -Recurse -ErrorAction SilentlyContinue |
                  Select-Object -ExpandProperty FullName -First 1
    }
    if (-not $binary -or -not (Test-Path $binary)) {
        Write-Fail "Binary '${APP_NAME}.exe' was not found under $INSTALL_DIR after extraction."
    }

    $verOutput = & $binary --version 2>&1
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
        Write-Fail "Binary ran but exited with code $LASTEXITCODE. Output: $verOutput"
    }
    Write-Ok "Installation verified: $verOutput"

} finally {
    # Clean up temp files regardless of outcome
    Remove-Item -Recurse -Force -Path $tmpDir -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "  Downloadyha $Version has been installed successfully!" -ForegroundColor Green
Write-Host "  Run 'downloadyha --help' in a new terminal to get started." -ForegroundColor Green
Write-Host ""
