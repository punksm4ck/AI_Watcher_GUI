"""Thread-safe append-only JSONL log + a small current-state snapshot file."""
import json
import threading
from datetime import datetime, timezone

from config import APP_SUPPORT_DIR, LOG_FILE, STATE_FILE

_lock = threading.Lock()


def _ensure_dirs():
    APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)


def append_event(account, raw_text, reset_time_iso=None, reset_time_raw=None):
    """Append one limit-hit event to the JSONL log and update current_state."""
    _ensure_dirs()
    event = {
        "account": account,
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "reset_time": reset_time_iso,       # ISO 8601 if we could parse it
        "reset_time_raw": reset_time_raw,   # original on-screen text, always kept
        "raw_text": raw_text[:2000],        # trimmed snippet, useful for debugging
    }
    with _lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        _update_state(account, event)
    return event


def _update_state(account, event):
    state = read_state()
    state.setdefault("accounts", {})
    existing = state["accounts"].get(account, {})

    reset_time = event["reset_time"]
    reset_time_raw = event["reset_time_raw"]

    # Prevent a later scan without a visible timestamp from wiping out a valid existing reset time
    if not reset_time_raw and existing.get("reset_time_raw"):
        reset_time_raw = existing.get("reset_time_raw")
        reset_time = reset_time or existing.get("reset_time")

    state["accounts"][account] = {
        "status": "limited",
        "detected_at": event["detected_at"],
        "reset_time": reset_time,
        "reset_time_raw": reset_time_raw,
    }
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def mark_account_available(account):
    _ensure_dirs()
    with _lock:
        state = read_state()
        state.setdefault("accounts", {})
        if ":" in account:
            state["accounts"][account] = {"status": "available"}
        else:
            state["accounts"][f"claude:{account}"] = {"status": "available"}
            state["accounts"][f"gemini:{account}"] = {"status": "available"}
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)


def clear_all():
    """
    Wipe the event log and reset every account's state entirely. This is
    what the GUI's CLEAR RESULTS button calls -- it was missing before,
    which is why that button crashed with AttributeError.
    """
    _ensure_dirs()
    with _lock:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"accounts": {}, "last_updated": datetime.now(timezone.utc).isoformat()},
                f, indent=2,
            )


def read_state():
    if not STATE_FILE.exists():
        return {"accounts": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"accounts": {}}


def read_events(limit=200):
    if not LOG_FILE.exists():
        return []
    events = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events[-limit:]


def reassign_event(detected_at, new_account):
    """
    Rewrite the account field of a previously logged event, matched by its
    detected_at timestamp (unique per event). Also refreshes current_state
    for the new account, since the reassigned entry becomes its most recent
    known event. Returns True if a matching event was found and updated.
    """
    if not LOG_FILE.exists():
        return False
    with _lock:
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
        rewritten = []
        target_event = None
        for line in lines:
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("detected_at") == detected_at:
                event["account"] = new_account
                target_event = event
            rewritten.append(json.dumps(event))
        if target_event is None:
            return False
        LOG_FILE.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
        _update_state(new_account, target_event)
        return True


def clear_prefix(prefix):
    """Clears state limits and file logs exclusively for the requested platform prefix."""
    _ensure_dirs()
    with _lock:
        state = read_state()
        if "accounts" in state:
            keys_to_destruct = [
                k for k in state["accounts"].keys()
                if str(k).startswith(prefix) or (prefix == "claude:" and not str(k).startswith("gemini:"))
            ]
            for k in keys_to_destruct:
                del state["accounts"][k]

            state["last_updated"] = datetime.now(timezone.utc).isoformat()
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)

        # Force reading and writing strictly to the main LOG_FILE to ensure GUI synchronization
        events = read_events(limit=10000)
        if prefix == "claude:":
            filtered_events = [e for e in events if str(e.get("account", "")).startswith("gemini:")]
        else:
            filtered_events = [e for e in events if not str(e.get("account", "")).startswith(prefix)]

        with open(LOG_FILE, "w", encoding="utf-8") as f:
            for event in filtered_events:
                f.write(json.dumps(event) + "\n")
