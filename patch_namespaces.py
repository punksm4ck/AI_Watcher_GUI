import os
import re

dir_path = os.path.expanduser("~/Downloads/ai_limit_tracker")

w_path = os.path.join(dir_path, "watcher.py")
g_path = os.path.join(dir_path, "gui.py")
s_path = os.path.join(dir_path, "storage.py")

with open(w_path, 'r') as f: code = f.read()
code = code.replace(
    "    event = storage.append_event(\n        account=resolved_account,",
    "    namespaced_account = f\"{proc.lower()}:{resolved_account}\"\n    event = storage.append_event(\n        account=namespaced_account,"
)
with open(w_path, 'w') as f: f.write(code)

with open(g_path, 'r') as f: code = f.read()
code = code.replace("info = accounts.get(account)", "info = accounts.get(f\"claude:{account}\")")
code = code.replace("info = accounts_state.get(account, {})", "info = accounts_state.get(f\"gemini:{account}\", {})")

clear_tab_regex = re.compile(r'    def _clear_all_active_tab\(self\):.*?((?=    def )|\Z)', re.DOTALL)
new_clear = """    def _clear_all_active_tab(self):
        current_tab = self.notebook.index(self.notebook.select())
        prefix = "claude:" if current_tab == 0 else "gemini:"
        storage.clear_prefix(prefix)
        if current_tab == 1:
            try:
                for tracker in gemini_trackers.values():
                    tracker.request_timestamps.clear()
                    tracker.token_history.clear()
            except NameError:
                pass
        self._refresh_log()

"""
code = clear_tab_regex.sub(new_clear, code)
with open(g_path, 'w') as f: f.write(code)

with open(s_path, 'r') as f: code = f.read()
mark_patch = """def mark_account_available(account):
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
            json.dump(state, f, indent=2)"""
code = re.sub(r'def mark_account_available\(account\):.*?(?=\n\ndef )', mark_patch, code, flags=re.DOTALL)

if "def clear_prefix(" not in code:
    code += """

def clear_prefix(prefix):
    _ensure_dirs()
    with _lock:
        state = read_state()
        accounts = state.get("accounts", {})
        keys_to_delete = [k for k in accounts if k.startswith(prefix)]
        for k in keys_to_delete:
            del accounts[k]
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        if LOG_FILE.exists():
            import json
            lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
            kept = []
            for line in lines:
                try:
                    if not json.loads(line).get("account", "").startswith(prefix):
                        kept.append(line)
                except:
                    pass
            LOG_FILE.write_text("\\n".join(kept) + ("\\n" if kept else ""), encoding="utf-8")
"""
with open(s_path, 'w') as f: f.write(code)

app_dir = os.path.expanduser("~/Library/Application Support/AILimitTracker")
state_file = os.path.join(app_dir, "current_state.json")
log_file = os.path.join(app_dir, "limit_events.jsonl")
if os.path.exists(state_file): os.remove(state_file)
if os.path.exists(log_file): os.remove(log_file)
