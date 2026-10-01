@echo off
REM Downloadyha GUI Launcher for Windows
REM Double-click this file to start the GUI application

echo.
echo ================================================
echo    Downloadyha Desktop GUI Launcher
echo ================================================
echo.

REM Detect best Python command (prefer py -3 launcher for Python 3.10+)
set "PY_CMD=python"
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH
        echo Please install Python 3.10 or later from https://www.python.org/
        echo.
        pause
        exit /b 1
    )
)

echo Starting Downloadyha GUI...
echo.

REM Launch the GUI application
%PY_CMD% src\downloadyha_gui\app.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start the GUI application
    echo.
    echo Possible solutions:
    echo   1. Install requirements: pip install -r requirements-gui.txt
    echo   2. Ensure you're in the correct directory
    echo   3. Check that all dependencies are installed
    echo.
    pause
)

exit /b %errorlevel%
