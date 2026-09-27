"""Central configuration for AI Limit Tracker."""
from pathlib import Path

APP_NAME = "AILimitTracker"

TRACKED_ACCOUNTS = [
    "tsannasardo@gmail.com",
    "tsannasardo2@gmail.com",
    "punksm4ck@gmail.com",
    "punksm4ck2@gmail.com",
    "ts7605689@gmail.com",
    "t420x710s@gmail.com",
    "tom@desklogix.app",
    "tom@visitlog.app",
    "tom1@visitlog.app",
]

CLAUDE_PROCESS_NAME = "Claude"
GEMINI_PROCESS_NAMES = [
    "Gemini",
    "Google Gemini",
    "Google Chrome",
    "Safari",
    "Arc",
    "Brave Browser",
]

POLL_INTERVAL_SECONDS = 8
IDLE_CHECK_INTERVAL_SECONDS = 15

APP_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
LOG_FILE = APP_SUPPORT_DIR / "limit_events.jsonl"
STATE_FILE = APP_SUPPORT_DIR / "current_state.json"
WATCHER_LOG_FILE = APP_SUPPORT_DIR / "watcher.log"

LIMIT_PHRASES = [
    "usage limit",
    "message limit",
    "reached your limit",
    "you've hit your",
    "you have hit your",
    "try again",
    "limit will reset",
    "limit resets",
    "out of free messages",
    "resets at",
    "resets on",
    "pro limits reached",
    "switching to flash",
    "pro limit reached",
    "switching to gemini flash", "flash-lite", "flash",
]
