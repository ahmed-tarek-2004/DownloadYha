#!/bin/bash
# Downloadyha GUI Launcher for Linux/macOS
# Make executable with: chmod +x launch_gui.sh
# Run with: ./launch_gui.sh

echo ""
echo "================================================"
echo "   Downloadyha Desktop GUI Launcher"
echo "================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.10 or later"
    echo ""
    exit 1
fi

echo "Starting Downloadyha GUI..."
echo ""

# Launch the GUI application
python3 src/downloadyha_gui/app.py

exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to start the GUI application"
    echo ""
    echo "Possible solutions:"
    echo "  1. Install requirements: pip3 install -r requirements-gui.txt"
    echo "  2. Ensure you're in the correct directory"
    echo "  3. Check that all dependencies are installed"
    echo ""
fi

exit $exit_code
