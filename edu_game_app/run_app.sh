#!/bin/bash
# Startup script for Learn & Play Educational App
# Works both from terminal and when launched automatically at login.

# Change to the directory this script lives in
cd "$(dirname "$0")"

# Load .env so ANTHROPIC_API_KEY is available
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Find python3 (handles Homebrew on Apple Silicon and Intel Macs)
PYTHON=""
for candidate in python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    osascript -e 'display alert "Learn & Play" message "Python 3 is not installed. Please install it from python.org." as critical' 2>/dev/null
    exit 1
fi

# Install dependencies silently if missing
"$PYTHON" -m pip install -r requirements.txt --quiet 2>/dev/null

exec "$PYTHON" app.py
