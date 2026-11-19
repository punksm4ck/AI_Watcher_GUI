import os
import re
import time
import json
import subprocess
from datetime import datetime

STATE_FILE = os.path.expanduser("~/Downloads/ai_limit_tracker/current_state.json")
SWIFT_BIN = os.path.expanduser("~/Downloads/ai_limit_tracker/swift_ocr")

ACCOUNT_MAP = {
    "tsann1": "tsannasardo@gmail.com",
    "tsann 1": "tsannasardo@gmail.com",
    "tsannasardo": "tsannasardo@gmail.com",
    "tsannasardo@gmail.com": "tsannasardo@gmail.com",
    "tsann2": "tsannasardo2@gmail.com",
    "tsann 2": "tsannasardo2@gmail.com",
    "tsannasardo2": "tsannasardo2@gmail.com",
    "tsannasardo2@gmail.com": "tsannasardo2@gmail.com",
    "punks1": "punksm4ck@gmail.com",
    "punks 1": "punksm4ck@gmail.com",
    "punksm4ck": "punksm4ck@gmail.com",
    "punksm4ck@gmail.com": "punksm4ck@gmail.com",
    "punks2": "punksm4ck2@gmail.com",
    "punks 2": "punksm4ck2@gmail.com",
    "punksm4ck2": "punksm4ck2@gmail.com",
    "punksm4ck2@gmail.com": "punksm4ck2@gmail.com",
    "ts7605689": "ts7605689@gmail.com",
    "ts7605689@gmail.com": "ts7605689@gmail.com",
    "t420x710s": "t420x710s@gmail.com",
    "t420x710s@gmail.com": "t420x710s@gmail.com",
    "desklogix": "tom@desklogix.app",
    "tom@desklogix.app": "tom@desklogix.app",
    "visitlog": "tom@visitlog.app",
    "tom@visitlog.app": "tom@visitlog.app",
    "tom1": "tom1@visitlog.app",
    "tom1@visitlog.app": "tom1@visitlog.app"
}

def read_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"accounts": {}, "logs": []}

def write_state(data):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def set_limit(provider, account, raw_time):
    state = read_state()
    accs = state.get("accounts", {})
    logs = state.get("logs", [])

    key = f"{provider}:{account}"
    curr = accs.get(key, {})

    if curr.get("status") == "limited" and curr.get("reset_time_raw") == raw_time:
        return

    now = datetime.now()
    accs[key] = {
        "status": "limited",
        "reset_time_raw": raw_time,
        "updated_at": now.isoformat()
    }
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp}  [{key.upper()}]  Limit detected on screen: {raw_time}"
    if log_entry not in logs:
        logs.append(log_entry)

    state["accounts"] = accs
    state["logs"] = logs
    write_state(state)

def get_ocr_text():
    shot_path = "/tmp/ai_limit_shot.png"
    subprocess.run(["screencapture", "-x", "-T", "0", shot_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(shot_path):
        return ""

    if os.path.exists(SWIFT_BIN):
        try:
            res = subprocess.run([SWIFT_BIN, shot_path], capture_output=True, text=True, timeout=5)
            if res.stdout:
                return res.stdout
        except Exception:
            pass

    return ""

def scan_screen():
    ocr_text = get_ocr_text()
    if not ocr_text:
        return

    ocr_lower = ocr_text.lower()

    detected_account = None
    for token, email in ACCOUNT_MAP.items():
        if token in ocr_lower:
            detected_account = email
            break

    claude_triggers = ["out of free messages", "hit your limit", "limit for claude", "messages until", "reset at", "limits will reset"]
    if any(trig in ocr_lower for trig in claude_triggers):
        time_match = re.search(r"(?:until|reset at|reset|at)\s*(\d{1,2}:\d{2}\s*(?:AM|PM)?)", ocr_text, re.IGNORECASE)
        if not time_match:
            time_match = re.search(r"(\d{1,2}:\d{2}\s*(?:AM|PM)?)", ocr_text, re.IGNORECASE)

        raw_time = time_match.group(1).upper() if time_match else "3:10 PM"
        if not detected_account:
            detected_account = "tsannasardo@gmail.com"
        set_limit("claude", detected_account, raw_time)

    gemini_triggers = ["reached your limit", "switched to flash", "quota exceeded", "limit for gemini"]
    if any(trig in ocr_lower for trig in gemini_triggers):
        time_match = re.search(r"(\d{1,2}:\d{2}\s*(?:AM|PM)?)", ocr_text, re.IGNORECASE)
        raw_time = time_match.group(1).upper() if time_match else "Limit Reached"
        if not detected_account:
            detected_account = "tsannasardo@gmail.com"
        set_limit("gemini", detected_account, raw_time)

def main():
    while True:
        try:
            scan_screen()
        except Exception:
            pass
        time.sleep(1.5)

if __name__ == "__main__":
    main()
