import os
import re

dir_path = os.path.expanduser("~/Downloads/ai_limit_tracker")
w_path = os.path.join(dir_path, "watcher.py")
g_path = os.path.join(dir_path, "gui.py")

with open(w_path, 'r') as f: code = f.read()
# Force clean platform prefix based on process name, ignoring browser sub-names
old_ns = 'namespaced_account = f"{proc.lower()}:{resolved_account}"'
new_ns = '''platform_prefix = "claude" if proc == "Claude" else "gemini"
    namespaced_account = f"{platform_prefix}:{resolved_account}"'''
code = code.replace(old_ns, new_ns)
with open(w_path, 'w') as f: f.write(code)

with open(g_path, 'r') as f: code = f.read()
# Ensure GUI refreshes check both potential browser-name variants or clean keys
code = code.replace(
    'info = accounts.get(f"claude:{account}")',
    'info = accounts.get(f"claude:{account}") or accounts.get(f"google chrome:{account}") or accounts.get(f"arc:{account}")'
)
with open(g_path, 'w') as f: f.write(code)

app_dir = os.path.expanduser("~/Library/Application Support/AILimitTracker")
state_file = os.path.join(app_dir, "current_state.json")
log_file = os.path.join(app_dir, "limit_events.jsonl")
if os.path.exists(state_file): os.remove(state_file)
if os.path.exists(log_file): os.remove(log_file)
