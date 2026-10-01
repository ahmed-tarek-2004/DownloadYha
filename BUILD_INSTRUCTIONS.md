# GUI Distribution Package Build Instructions

This document explains how to build and create the standalone GUI distribution package.

## Prerequisites

### System Requirements
- Windows 10 or Windows 11 (64-bit)
- Python 3.10 or later (3.11+ recommended)
- PowerShell (included with Windows)
- ~500MB free disk space for build process

### Python Dependencies
Install the required packages:

```powershell
pip install --upgrade pip setuptools wheel
pip install pyinstaller customtkinter pillow
```

## Building the GUI Executable

### Method 1: Using PowerShell Script (Recommended)

```powershell
.\build-gui-windows.ps1
```

**Options:**
- `-Clean`: Remove previous build artifacts before building
- `-SkipTests`: Skip smoke tests after build

**Example:**
```powershell
.\build-gui-windows.ps1 -Clean
```

### Method 2: Using Batch File

Double-click `build-gui.bat` or run:

```cmd
build-gui.bat
```

This is a wrapper that calls the PowerShell script.

### Method 3: Manual PyInstaller

```powershell
pyinstaller --clean --noconfirm downloadyha-gui.spec
```

## Build Output

After successful build, you'll find:

```
dist/
├── downloadyha-gui.exe              (Standalone executable, ~80-100MB)
├── downloadyha-gui-windows.zip      (Distribution archive)
├── README.txt                       (Package documentation)
└── QUICKSTART.txt                   (Quick start guide)
```

## Creating the Distribution Package

The build script automatically creates a distribution ZIP with:

1. **downloadyha-gui.exe** - Standalone executable
2. **README.txt** - Complete user documentation
3. **QUICKSTART.txt** - 3-step quick start guide

The package is ready for distribution at: `dist/downloadyha-gui-windows.zip`

## Manual Package Creation

If you need to create the package manually:

```powershell
# Create temporary directory
New-Item -ItemType Directory -Path "dist/temp_package" -Force

# Copy files
Copy-Item "dist/downloadyha-gui.exe" "dist/temp_package/"
Copy-Item "dist/README.txt" "dist/temp_package/"
Copy-Item "dist/QUICKSTART.txt" "dist/temp_package/"

# Create ZIP
Compress-Archive -Path "dist/temp_package/*" -DestinationPath "dist/downloadyha-gui-windows.zip" -Force

# Clean up
Remove-Item -Recurse -Force "dist/temp_package"
```

## Verifying the Build

### Check Executable
```powershell
# Check file exists
Test-Path "dist/downloadyha-gui.exe"

# Check file size (should be ~80-100MB)
(Get-Item "dist/downloadyha-gui.exe").Length / 1MB

# Run executable (launches GUI)
.\dist\downloadyha-gui.exe
```

### Test the Package
1. Extract `dist/downloadyha-gui-windows.zip` to a test folder
2. Run the executable from the test folder
3. Test basic functionality:
   - Launch application
   - Paste a YouTube URL
   - Toggle theme
   - Select download folder
   - (Optional) Download a short video

## Troubleshooting Build Issues

### Python Version Too Old

**Error:** `Python 3.10+ required, found 3.8`

**Solution:**
1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Restart terminal and verify: `python --version`

### PyInstaller Not Found

**Error:** `pyinstaller: command not found`

**Solution:**
```powershell
pip install --upgrade pyinstaller
```

### Missing customtkinter

**Error:** `ModuleNotFoundError: No module named 'customtkinter'`

**Solution:**
```powershell
pip install customtkinter pillow
```

### Build Fails with Import Errors

**Solution:**
1. Ensure all dependencies are installed:
   ```powershell
   pip install -r requirements.txt
   ```
2. Clean previous builds:
   ```powershell
   Remove-Item -Recurse -Force build, dist
   ```
3. Rebuild:
   ```powershell
   .\build-gui-windows.ps1
   ```

### Executable Won't Run After Build

**Solution:**
1. Check for antivirus quarantine
2. Test on a clean Windows 10/11 VM
3. Install Visual C++ Redistributables:
   - [vc_redist.x64.exe](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Large Executable Size

The executable is large (~80-100MB) because it bundles:
- Python interpreter
- customtkinter and dependencies
- Pillow (image processing)
- All required DLLs

This is normal for PyInstaller builds and ensures the app is truly standalone.

## Distribution Checklist

Before distributing the package:

- [ ] Build completes without errors
- [ ] Executable runs on build machine
- [ ] Test on clean Windows 10/11 system (no Python installed)
- [ ] Verify GUI launches and displays correctly
- [ ] Test basic download functionality
- [ ] Check theme switching works
- [ ] Verify README.txt and QUICKSTART.txt are included
- [ ] Test extraction and running from ZIP
- [ ] Check file size (~80-100MB for ZIP)
- [ ] Scan with antivirus (expect false positives, verify clean)
- [ ] Update GitHub release notes with download link

## GitHub Release Process

1. **Create Git Tag:**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0 with GUI"
   git push origin v1.0.0
   ```

2. **Create GitHub Release:**
   - Go to: https://github.com/ahmed-tarek-2004/DownloadYha/releases/new
   - Choose tag: v1.0.0
   - Title: `Downloadyha v1.0.0 - GUI Edition`
   - Description: Release notes (see CHANGELOG_GUI.md)
   - Upload: `dist/downloadyha-gui-windows.zip`
   - Check "Create a discussion for this release"
   - Publish release

3. **Update Documentation:**
   - Verify download links work in README.md
   - Update GUI_DOWNLOAD.md with release URL
   - Test download link from documentation

## Continuous Integration (Future)

Consider setting up GitHub Actions to automate builds:

```yaml
name: Build GUI
on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install pyinstaller customtkinter pillow
      - name: Build executable
        run: .\build-gui-windows.ps1
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: downloadyha-gui-windows
          path: dist/downloadyha-gui-windows.zip
```

## Signing the Executable (Optional)

For production releases, consider code signing to avoid Windows SmartScreen warnings:

1. **Obtain Code Signing Certificate:**
   - Purchase from DigiCert, Sectigo, or similar CA
   - Cost: ~$200-500/year

2. **Sign the Executable:**
   ```powershell
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist/downloadyha-gui.exe
   ```

3. **Verify Signature:**
   ```powershell
   signtool verify /pa dist/downloadyha-gui.exe
   ```

**Note:** Code signing is optional but recommended for wider distribution to reduce SmartScreen warnings.

## Support

For build issues:
- Check [GitHub Issues](https://github.com/ahmed-tarek-2004/DownloadYha/issues)
- Review [GUI_DEVELOPMENT.md](GUI_DEVELOPMENT.md)
- Create new issue with build logs

---

**Last Updated:** 2026-10-01
**Build System Version:** 1.0.0
