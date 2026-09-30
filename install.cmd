@echo off
REM ============================================================================
REM Downloadyha Windows Installer (Command Prompt / CMD)
REM Repository: https://github.com/ahmed-tarek-2004/DownloadYha
REM ============================================================================

setlocal EnableDelayedExpansion

echo.
echo   Downloadyha Installer (Windows CMD)
echo   ====================================
echo.

where powershell >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo   [ERR] PowerShell is required to run the installer script.
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/ahmed-tarek-2004/DownloadYha/master/install.ps1 | iex"

if %ERRORLEVEL% neq 0 (
    echo   [ERR] Installation failed.
    exit /b %ERRORLEVEL%
)

endlocal
