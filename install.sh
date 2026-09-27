#!/bin/bash
# Installs AI Limit Tracker: creates a virtualenv, installs deps, and
# registers the watcher as a launchd agent that starts at login and
# restarts automatically if it ever crashes.
set -e

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_SUPPORT_DIR="$HOME/Library/Application Support/AILimitTracker"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.punksm4ck.ai-limit-watcher.plist"

echo "==> Installing into: $INSTALL_DIR"
mkdir -p "$APP_SUPPORT_DIR"
mkdir -p "$LAUNCH_AGENTS_DIR"

echo "==> Creating virtualenv (.venv)"
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

PYTHON_BIN="$INSTALL_DIR/.venv/bin/python3"

echo "==> Writing launchd agent"
sed \
    -e "s|__PYTHON_BIN__|$PYTHON_BIN|g" \
    -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    -e "s|__APP_SUPPORT_DIR__|$APP_SUPPORT_DIR|g" \
    "$INSTALL_DIR/launchagents/$PLIST_NAME" > "$LAUNCH_AGENTS_DIR/$PLIST_NAME"

echo "==> Loading launchd agent"
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true
launchctl load -w "$LAUNCH_AGENTS_DIR/$PLIST_NAME"

cat <<EOF

==> Done.

IMPORTANT -- grant Accessibility permission, or the watcher will never
see any on-screen text (it will still know Claude is *running*, just
not what's on screen):
  System Settings -> Privacy & Security -> Accessibility
  Add and enable this exact binary:
    $PYTHON_BIN

To launch the dashboard:
  $INSTALL_DIR/.venv/bin/python3 $INSTALL_DIR/main.py

To confirm the watcher is alive:
  launchctl list | grep ai-limit-watcher
  tail -f "$APP_SUPPORT_DIR/watcher.log"

To uninstall:
  launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
  rm "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
EOF
