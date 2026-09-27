"""
Headless watcher: monitors Claude and Gemini app/browser processes for rate and usage limits.
"""
import logging
import time

import ax_reader
import detector
import storage
from config import (
    CLAUDE_PROCESS_NAME,
    GEMINI_PROCESS_NAMES,
    POLL_INTERVAL_SECONDS,
    IDLE_CHECK_INTERVAL_SECONDS,
    WATCHER_LOG_FILE,
    APP_SUPPORT_DIR,
)

APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(WATCHER_LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("watcher")

_last_seen_account = {}


def _handle_text(text, proc):
    global _last_seen_account

    if not text:
        return

    account = detector.detect_account(text)
    if account:
        _last_seen_account[proc] = account

    if not detector.looks_like_limit_message(text):
        return

    raw_time = detector.extract_reset_time_raw(text)
    iso_time = detector.try_parse_reset_time(raw_time)

    text_lower = text.lower()

    # Smart Platform Detection: Ignore GUI noise by looking for exact limit phrases
    if any(kw in text_lower for kw in ["limit resets", "pro limit", "switching to flash", "3.6 flash", "flash-lite"]):
        platform_prefix = "gemini"
    elif any(kw in text_lower for kw in ["out of free messages", "limit for claude", "usage limit"]):
        platform_prefix = "claude"
    else:
        platform_prefix = "claude" if ("claude" in proc.lower()) else "gemini"

    # Determine Account based on the DETECTED platform, not the polling process
    resolved_account = account or _last_seen_account.get(proc)
    for profile, email in {"Tsann1": "tsannasardo@gmail.com", "Tsann2": "tsannasardo2@gmail.com", "Tom Sann": "tsannasardo@gmail.com"}.items():
        if profile.lower() in text_lower:
            resolved_account = email
            break

    if not resolved_account:
        resolved_account = "tsannasardo@gmail.com" if platform_prefix == "claude" else "punksm4ck2@gmail.com"

    # Fingerprint Debouncing to ignore OCR noise/clock changes
    fingerprint = f"{platform_prefix}:{resolved_account}-{raw_time}"
    if getattr(_handle_text, "last_fingerprint", None) == fingerprint:
        return
    _handle_text.last_fingerprint = fingerprint

    namespaced_account = f"{platform_prefix}:{resolved_account}"
    event = storage.append_event(
        account=namespaced_account,
        raw_text=text,
        reset_time_iso=iso_time,
        reset_time_raw=raw_time,
    )
    log.info("Logged limit hit: %s", event)


def run():
    log.info("Watcher started.")
    all_target_processes = [CLAUDE_PROCESS_NAME] + GEMINI_PROCESS_NAMES

    while True:
        any_running = False
        for proc in all_target_processes:
            if ax_reader.is_claude_running(proc):
                any_running = True
                text = ax_reader.dump_visible_text(proc)
                try:
                    _handle_text(text, proc)
                except Exception:
                    log.exception("Error while handling AX text dump for process: %s", proc)

        if any_running:
            time.sleep(POLL_INTERVAL_SECONDS)
        else:
            time.sleep(IDLE_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
