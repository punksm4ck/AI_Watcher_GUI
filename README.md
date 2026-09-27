# AI Limit Tracker

Tracks Claude desktop-app usage-limit hits across your 4 accounts and logs
when each one becomes available again.

- `tsannasardo@gmail.com`
- `tsannasardo2@gmail.com`
- `punksm4ck.com`
- `punksm4ck2@gmail.com`

## How it works

Two pieces:

1. **`watcher.py`** -- a headless background process, installed as a
   `launchd` agent so it starts automatically at login (and restarts
   itself if it ever crashes -- you never have to launch it by hand).
   It polls (every 8s) whether the Claude desktop app is running, and
   while it is, reads the app's on-screen text via the macOS
   **Accessibility API**. When that text matches a usage-limit pattern,
   it extracts a reset time and logs the event.

2. **`gui.py`** (run via `main.py`) -- a Tkinter dashboard showing each
   account's status (`ONLINE` / `LOCKED` + when it frees up) and a
   scrollable event log. It just reads the same log/state files the
   watcher writes -- you can open and close it freely without affecting
   the watcher.

Data lives in `~/Library/Application Support/AILimitTracker/`:
`limit_events.jsonl` (full history), `current_state.json` (latest status
per account), `watcher.log` (diagnostics).

## Install

```bash
cd ai_limit_tracker
chmod +x install.sh
./install.sh
```

This creates a local virtualenv, installs the `pyobjc` accessibility
bindings, and registers + loads the launchd agent.

**Then grant Accessibility permission** (the installer prints the exact
path): System Settings -> Privacy & Security -> Accessibility -> add the
venv's `python3` binary. Without this the watcher can confirm Claude is
*running* but can't read anything on screen, so it will never catch a
limit message.

Launch the dashboard any time with:
```bash
.venv/bin/python3 main.py
```

## Important limitation: account identification

Claude's main chat window doesn't always display which account is signed
in -- there's no public API for "current logged-in account." The watcher
handles this in two layers:

1. If one of your 4 account strings is visible anywhere on screen (e.g.
   during sign-in, or with the account/settings panel open), it's
   captured and remembered as the "last seen account."
2. A limit message that appears afterward gets attributed to that
   remembered account. If none was ever seen, it's logged as
   `"unknown"`.

For "unknown" entries, open the dashboard, select the entry in the event
log, and click **REASSIGN SELECTED ENTRY** to tag it yourself from a
4-button picker. This is the one place full automation isn't realistically
possible without you having previously opened an account/settings panel
that shows the email -- everything else (detecting the limit hit itself,
extracting the reset time, logging it, restarting on crash) is fully
automatic.

## Tuning detection

`config.py` -> `LIMIT_PHRASES` is a best-guess list of substrings
("usage limit", "resets at", "try again", etc.). The exact wording
Claude uses may differ slightly. After the first real limit hit:

```bash
tail -50 "$HOME/Library/Application Support/AILimitTracker/watcher.log"
```

If a real limit message didn't get caught, check
`limit_events.jsonl` -> most recent `raw_text` field wasn't written (since
nothing matched) -- in that case, run the watcher in a terminal
(`.venv/bin/python3 watcher.py`) next time you expect a limit, and watch
for the actual on-screen phrasing so you can add it to `LIMIT_PHRASES`.

The reset-time parser (`detector.try_parse_reset_time`) handles common
`H:MM AM/PM` and `HH:MM` forms. If Claude's actual phrasing is more
unusual (e.g. relative time like "in 3 hours"), the raw text is still
always saved in `reset_time_raw` even when the parser can't turn it into
an exact timestamp -- nothing is lost, it just won't show a clean
countdown in the GUI for that entry.

## Uninstall

```bash
launchctl unload "$HOME/Library/LaunchAgents/com.punksm4ck.ai-limit-watcher.plist"
rm "$HOME/Library/LaunchAgents/com.punksm4ck.ai-limit-watcher.plist"
```
