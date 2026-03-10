#!/usr/bin/env python3
"""
Mac Mini Time Limit Agent
--------------------------
Runs on the Mac Mini. Connects to the edu-app Flask server (Windows PC)
and enforces browser time limits with native macOS popups.

Usage:
    python3 mac_time_agent.py --server http://192.168.x.x:5050

Or set SERVER_URL in config.json next to this file.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# ── Default config ────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "server_url": "",          # e.g. "http://192.168.1.100:5050"
    "poll_interval_sec": 20,   # how often to check the server
    "session_limit_min": 60,   # independent 1-hour session limit (0 = disabled)
    "warn_at_minutes": [10, 5, 1],   # show warnings at these remaining minutes
    "close_browsers_on_limit": True, # force-quit browsers when time is up
    "browsers": [              # macOS app names to quit
        "Safari",
        "Google Chrome",
        "Firefox",
        "Microsoft Edge",
        "Opera",
        "Brave Browser",
    ],
}

CONFIG_PATH = Path(__file__).parent / "config.json"

# ── Browsers to kill via pkill (process names) ─────────────────────────────
BROWSER_PROCS = [
    "Safari", "Google Chrome", "firefox-bin",
    "Microsoft Edge", "Opera", "Brave Browser Helper",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            cfg.update(json.load(f))
    return cfg


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def osascript(script: str):
    """Run an AppleScript snippet."""
    subprocess.run(["osascript", "-e", script], capture_output=True)


def show_dialog(title: str, message: str, buttons: list[str] = None) -> str:
    """Show a modal macOS dialog. Returns the button pressed."""
    if buttons is None:
        buttons = ["我知道了"]
    btn_str = ", ".join(f'"{b}"' for b in buttons)
    script = (
        f'display dialog "{message}" '
        f'with title "{title}" '
        f'buttons {{{btn_str}}} '
        f'default button 1 '
        f'with icon stop'
    )
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    # parse "button returned:OK"
    for line in result.stdout.strip().split(","):
        if "button returned" in line:
            return line.split(":")[1].strip()
    return ""


def show_notification(title: str, message: str):
    """Show a macOS notification banner."""
    osascript(
        f'display notification "{message}" '
        f'with title "{title}" '
        f'sound name "Glass"'
    )


def close_browsers(app_names: list[str]):
    """Force-quit listed macOS browser apps."""
    for name in app_names:
        osascript(f'tell application "{name}" to quit')


def get_server_status(server_url: str) -> dict | None:
    """Fetch /api/status from the Windows server. Returns None on error."""
    try:
        url = server_url.rstrip("/") + "/api/status"
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[{_ts()}] ⚠️  Server unreachable: {e}")
        return None


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


# ── Main loop ─────────────────────────────────────────────────────────────────

def run(cfg: dict):
    server_url = cfg.get("server_url", "").strip()
    poll = int(cfg.get("poll_interval_sec", 20))
    session_limit = int(cfg.get("session_limit_min", 60))
    warn_at = sorted(cfg.get("warn_at_minutes", [10, 5, 1]), reverse=True)
    close_on_limit = cfg.get("close_browsers_on_limit", True)
    browsers = cfg.get("browsers", DEFAULT_CONFIG["browsers"])

    if not server_url:
        print("❌ server_url is not set in config.json. Run with --server to set it.")
        sys.exit(1)

    print(f"[{_ts()}] Mac Time Agent started")
    print(f"  Server  : {server_url}")
    print(f"  Poll    : every {poll}s")
    if session_limit > 0:
        print(f"  Session : {session_limit}-minute independent limit enabled")
    print()

    # ── State ─────────────────────────────────────────────────────────────
    warned_thresholds: set[int] = set()   # for server-based balance warnings
    limit_shown = False                   # server balance hit 0

    # Session-based (independent) timer
    session_start: datetime | None = None
    session_warned: set[int] = set()
    session_limit_shown = False

    def reset_session():
        nonlocal session_start, session_warned, session_limit_shown
        session_start = datetime.now()
        session_warned = set()
        session_limit_shown = False
        print(f"[{_ts()}] 🕐 New 1-hour session started")

    reset_session()

    # ── Loop ──────────────────────────────────────────────────────────────
    while True:
        # --- Independent session timer ---
        if session_limit > 0 and session_start:
            elapsed_min = int((datetime.now() - session_start).total_seconds() / 60)
            remaining_session = session_limit - elapsed_min

            for w in warn_at:
                if remaining_session <= w and w not in session_warned:
                    session_warned.add(w)
                    show_notification(
                        "⏰ 快到一小時了！",
                        f"已使用 {elapsed_min} 分鐘，還剩 {remaining_session} 分鐘。"
                    )
                    print(f"[{_ts()}] ⚠️  Session warning: {remaining_session} min left")

            if remaining_session <= 0 and not session_limit_shown:
                session_limit_shown = True
                print(f"[{_ts()}] 🚨 Session 1-hour limit reached")
                if close_on_limit:
                    close_browsers(browsers)
                reply = show_dialog(
                    "⏰ TIME LIMIT",
                    "你已經連續使用瀏覽器超過一個小時了！\n\n"
                    "請休息一下眼睛，並做一些閱讀練習。\n\n"
                    "繼續使用請按「繼續」（需要家長同意）。",
                    buttons=["我知道了", "繼續使用"]
                )
                if reply == "繼續使用":
                    reset_session()
                    show_notification("✅ 計時重新開始", "計時已重設，祝學習愉快！")

        # --- Server-based balance ---
        status = get_server_status(server_url)
        if status:
            balance = status.get("balance", 0)
            browser_on = status.get("browser_running", False)
            print(
                f"[{_ts()}] 📊 Balance={balance}min  "
                f"Browser={'ON' if browser_on else 'off'}  "
                f"Monitor={'✅' if status.get('browser_monitoring') else '❌'}"
            )

            # Warnings for server-based balance
            for w in warn_at:
                if balance <= w and w not in warned_thresholds and (browser_on or balance == 0):
                    warned_thresholds.add(w)
                    show_notification(
                        "⚠️ 遊戲時間快到了",
                        f"剩餘遊戲時間：{balance} 分鐘"
                    )

            # Limit reached
            if balance <= 0 and not limit_shown:
                limit_shown = True
                print(f"[{_ts()}] 🚨 Server balance = 0, showing TIME LIMIT dialog")
                if close_on_limit:
                    close_browsers(browsers)
                show_dialog(
                    "⏰ TIME LIMIT — 時間到！",
                    "你的瀏覽器使用時間已用完！\n\n"
                    "請完成閱讀練習來賺取更多時間。",
                )

            # Reset when parent adds time
            if balance > max(warn_at, default=10):
                warned_thresholds.clear()
                limit_shown = False

        time.sleep(poll)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Mac Mini Time Limit Agent")
    parser.add_argument("--server", help="Server URL, e.g. http://192.168.1.100:5050")
    parser.add_argument("--limit", type=int, help="Independent session limit in minutes (default 60)")
    parser.add_argument("--poll", type=int, help="Poll interval in seconds (default 20)")
    args = parser.parse_args()

    cfg = load_config()

    if args.server:
        cfg["server_url"] = args.server
        save_config(cfg)
        print(f"✅ Server URL saved: {args.server}")

    if args.limit is not None:
        cfg["session_limit_min"] = args.limit
        save_config(cfg)

    if args.poll is not None:
        cfg["poll_interval_sec"] = args.poll
        save_config(cfg)

    if not cfg.get("server_url"):
        print("❌ No server URL configured.")
        print("   Run: python3 mac_time_agent.py --server http://<WINDOWS-PC-IP>:5050")
        sys.exit(1)

    run(cfg)


if __name__ == "__main__":
    main()
