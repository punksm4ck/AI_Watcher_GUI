#!/bin/bash
cd "$HOME/Downloads/ai_limit_tracker"
pkill -f watcher.py
pkill -f main.py
pkill -f gui.py
nohup python3 watcher.py >/dev/null 2>&1 &
nohup python3 gui.py >/dev/null 2>&1 &
exit
