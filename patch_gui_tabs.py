import os

g_path = os.path.expanduser("~/Downloads/ai_limit_tracker/gui.py")
with open(g_path, 'r') as f:
    code = f.read()

# Make sure the GUI status lookup checks the correct platform prefix based on the active tab
old_lookup = 'info = accounts.get(f"claude:{account}")'
new_lookup = '''prefix = "claude" if current_tab == "claude" else "gemini"
        info = accounts.get(f"{prefix}:{account}") or accounts.get(account)'''

code = code.replace(old_lookup, new_lookup)

with open(g_path, 'w') as f:
    f.write(code)

app_dir = os.path.expanduser("~/Library/Application Support/AILimitTracker")
state_file = os.path.join(app_dir, "current_state.json")
if os.path.exists(state_file):
    os.remove(state_file)
