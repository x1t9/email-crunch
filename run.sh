#!/usr/bin/env bash
# =============================================================================
# Email Crunch v0.1-alpha — Launcher for Linux & macOS
# =============================================================================

set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check Python 3
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.10+ (e.g. via brew install python or apt install python3)."
    exit 1
fi

echo "Launching Email Crunch using $PYTHON_CMD..."
exec "$PYTHON_CMD" "$DIR/main.py" "$@"
