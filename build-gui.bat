@echo off
REM Build script wrapper for build-gui-windows.ps1
REM This allows double-clicking to build the GUI on Windows

echo ========================================
echo   Downloadyha GUI Build Script
echo ========================================
echo.
echo This will build the standalone GUI executable.
echo.
echo Requirements:
echo   - Python 3.10 or later
echo   - PyInstaller and customtkinter
echo.
echo Press Ctrl+C to cancel, or
pause

powershell -ExecutionPolicy Bypass -File "%~dp0build-gui-windows.ps1"
if errorlevel 1 (
    echo.
    echo ========================================
    echo   Build Failed with error code %errorlevel%
    echo ========================================
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================
echo   Build Complete
echo ========================================
echo.
echo Check the dist\ folder for output files.
echo.
pause
