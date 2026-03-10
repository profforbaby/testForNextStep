#!/bin/bash
# Mac Mini setup script for Time Limit Agent
# Run once on the Mac Mini to install and configure auto-start

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_PY="$SCRIPT_DIR/mac_time_agent.py"
PLIST_SRC="$SCRIPT_DIR/com.eduapp.timeagent.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.eduapp.timeagent.plist"
LOG_DIR="$HOME/Library/Logs/EduApp"

echo "======================================"
echo "  Mac Time Agent 安裝程式"
echo "======================================"
echo ""

# 1. Ask for Windows PC IP
read -rp "請輸入 Windows PC 的 IP 位址（例如 192.168.1.100）: " WIN_IP
SERVER_URL="http://${WIN_IP}:5050"

# 2. Ask for session limit
read -rp "每次最長使用幾分鐘後彈出提醒？（預設 60）: " SESSION_LIMIT
SESSION_LIMIT="${SESSION_LIMIT:-60}"

# 3. Write config.json
python3 "$AGENT_PY" --server "$SERVER_URL" --limit "$SESSION_LIMIT" &
AGENT_PID=$!
sleep 1
kill $AGENT_PID 2>/dev/null || true

echo ""
echo "✅ 設定已儲存：$SERVER_URL，每 ${SESSION_LIMIT} 分鐘提醒一次"

# 4. Create log directory
mkdir -p "$LOG_DIR"

# 5. Write LaunchAgent plist
PYTHON_PATH="$(which python3)"

cat > "$PLIST_DST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.eduapp.timeagent</string>

  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON_PATH}</string>
    <string>${AGENT_PY}</string>
  </array>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>${LOG_DIR}/agent.log</string>

  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/agent-error.log</string>
</dict>
</plist>
EOF

echo "✅ LaunchAgent plist 已寫入：$PLIST_DST"

# 6. Load the agent now
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"

echo ""
echo "======================================"
echo "  安裝完成！Agent 已在背景執行"
echo "======================================"
echo ""
echo "  日誌位置：$LOG_DIR/agent.log"
echo "  手動停止：launchctl unload '$PLIST_DST'"
echo "  手動啟動：launchctl load '$PLIST_DST'"
echo ""
