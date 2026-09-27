#!/bin/bash
# One-shot setup + launch for AI Limit Tracker.
#
# By default this copies the project from Downloads into ~/Applications
# (created if needed) before installing, since the watcher is meant to
# run persistently and Downloads is a bad place for that long-term.
#
# Usage:
#   bash setup_and_launch.sh              # copies to ~/Applications, installs, launches
#   bash setup_and_launch.sh --in-place   # installs and runs right where it is (Downloads)
set -e

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$HOME/Applications/ai_limit_tracker"

if [[ "$1" == "--in-place" ]]; then
    TARGET_DIR="$SOURCE_DIR"
    echo "==> Running in place: $TARGET_DIR"
else
    echo "==> Copying project to: $DEST_DIR"
    mkdir -p "$HOME/Applications"
    if [ -d "$DEST_DIR" ]; then
        echo "    ($DEST_DIR already exists -- overwriting its code files, keeping any existing .venv)"
        rsync -a --exclude '.venv' --exclude '__pycache__' "$SOURCE_DIR/" "$DEST_DIR/"
    else
        cp -R "$SOURCE_DIR" "$DEST_DIR"
    fi
    TARGET_DIR="$DEST_DIR"
fi

cd "$TARGET_DIR"
chmod +x install.sh watcher.py

echo "==> Running install.sh"
./install.sh

PYTHON_BIN="$TARGET_DIR/.venv/bin/python3"

echo ""
echo "==> Launching dashboard"
"$PYTHON_BIN" "$TARGET_DIR/main.py" &

cat <<EOF

==> All set.

Project location : $TARGET_DIR
Dashboard         : launched just now (relaunch anytime with)
                    $PYTHON_BIN $TARGET_DIR/main.py
Watcher           : running now via launchd, and will auto-start at every login

Don't forget: grant Accessibility permission to
  $PYTHON_BIN
under System Settings -> Privacy & Security -> Accessibility,
or the watcher can't read any on-screen text.
EOF
