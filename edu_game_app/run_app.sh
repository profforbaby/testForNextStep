#!/bin/bash
# Startup script for Learn & Play Educational App
# Works both from terminal and when launched automatically at login.
# Runs equivalently to: python run_edu_app.py from the project root.

# Resolve the project root (one level above this script's edu_game_app/ folder)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root so package imports (edu_game_app.*) work correctly
cd "$PROJECT_ROOT"

# Load .env from edu_game_app/ before any imports read env vars
ENV_FILE="$PROJECT_ROOT/edu_game_app/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
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
"$PYTHON" -m pip install -r "$PROJECT_ROOT/edu_game_app/requirements.txt" --quiet 2>/dev/null

# Launch via run_edu_app.py from the project root (same as running it directly)
exec "$PYTHON" "$PROJECT_ROOT/run_edu_app.py"
