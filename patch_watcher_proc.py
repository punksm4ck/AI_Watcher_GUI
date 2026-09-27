import os

w_path = os.path.expanduser("~/Downloads/ai_limit_tracker/watcher.py")
with open(w_path, 'r') as f:
    code = f.read()

# Replace the strict 'proc == "Claude"' check with a broader substring check
old_check = 'platform_prefix = "claude" if proc == "Claude" else "gemini"'
new_check = 'platform_prefix = "claude" if ("claude" in proc.lower()) else "gemini"'
code = code.replace(old_check, new_check)

with open(w_path, 'w') as f:
    f.write(code)

app_dir = os.path.expanduser("~/Library/Application Support/AILimitTracker")
for filename in ["current_state.json", "limit_events.jsonl"]:
    filepath = os.path.join(app_dir, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
