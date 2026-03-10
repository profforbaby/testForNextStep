#!/bin/bash
# Run this script ONCE on the Mac Mini to set up auto-start at login.
# Usage:  bash setup_mac_autostart.sh

set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.learnandplay.app"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

echo "=== Learn & Play — macOS Auto-Start Setup ==="
echo ""

# ── 1. Find Python 3 ──────────────────────────────────────────────────────────
PYTHON=""
for candidate in \
    "$(command -v python3 2>/dev/null)" \
    /usr/bin/python3 \
    /usr/local/bin/python3 \
    /opt/homebrew/bin/python3; do
    if [ -x "$candidate" ]; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: python3 not found. Install Python 3 first."
    exit 1
fi
echo "Python:      $PYTHON"
echo "App folder:  $APP_DIR"

# ── 2. Install Python dependencies ────────────────────────────────────────────
echo ""
echo "Installing Python dependencies..."
"$PYTHON" -m pip install -r "$APP_DIR/edu_game_app/requirements.txt" --quiet

# ── 3. Write the LaunchAgent plist ────────────────────────────────────────────
mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$HOME/Library/Logs/LearnAndPlay"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$APP_DIR/run_edu_app.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$APP_DIR</string>

    <!-- Start automatically when the user logs in -->
    <key>RunAtLoad</key>
    <true/>

    <!-- Restart if it crashes -->
    <key>KeepAlive</key>
    <false/>

    <!-- Log output -->
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/LearnAndPlay/app.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/LearnAndPlay/app_error.log</string>
</dict>
</plist>
PLIST

echo "LaunchAgent: $PLIST_PATH"

# ── 4. Load (activate) the LaunchAgent right now ─────────────────────────────
# Unload first in case an old version is already loaded
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

echo ""
echo "✓ Done!  The app will now launch automatically every time you log in."
echo "  It is also starting right now — check your Dock."
echo ""
echo "To remove auto-start later, run:"
echo "  launchctl unload $PLIST_PATH"
echo "  rm $PLIST_PATH"
