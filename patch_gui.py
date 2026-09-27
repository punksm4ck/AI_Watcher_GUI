import os

def patch_gui():
    try:
        with open("gui.py", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: gui.py not found in the current directory.")
        return

    # 1. Inject Imports and the Tracker Class
    import_hook = "from config import TRACKED_ACCOUNTS\n"
    injection_1 = """
import time
from collections import deque

class GeminiProTracker:
    def __init__(self, account_name):
        self.account_name = account_name
        self.MAX_RPM = 2
        self.MAX_TPM = 32000
        self.MAX_RPD = 50
        self.request_timestamps = deque()
        self.token_history = deque()

    def add_request(self, token_count):
        current_time = time.time()
        self.request_timestamps.append(current_time)
        self.token_history.append((current_time, token_count))
        self._cleanup_old_requests(current_time)

    def _cleanup_old_requests(self, current_time):
        while self.request_timestamps and current_time - self.request_timestamps[0] > 86400:
            self.request_timestamps.popleft()
        while self.token_history and current_time - self.token_history[0][0] > 60:
            self.token_history.popleft()

    def get_status(self):
        current_time = time.time()
        self._cleanup_old_requests(current_time)
        requests_last_minute = sum(1 for t in self.request_timestamps if current_time - t <= 60)
        tokens_last_minute = sum(tokens for t, tokens in self.token_history if current_time - t <= 60)
        daily_requests = len(self.request_timestamps)
        
        if daily_requests >= self.MAX_RPD:
            return "LOCKED", self.request_timestamps[0] + 86400, "Daily limit"
        if requests_last_minute >= self.MAX_RPM or tokens_last_minute >= self.MAX_TPM:
            relevant_times = [t for t in self.request_timestamps if current_time - t <= 60]
            free_time = relevant_times[0] + 60 if relevant_times else current_time + 60
            return "LOCKED", free_time, "Minute limit"
            
        return "ONLINE", None, "Available"

GEMINI_ACCOUNTS = [
    "tsannasardo@gmail.com", "tsannasardo2@gmail.com", "punksm4ck@gmail.com", 
    "punksm4ck2@gmail.com", "ts7605689@gmail.com", "t420x710s@gmail.com", 
    "tom@desklogix.app", "tom@visitlog.app", "tom1@visitlog.app"
]
gemini_trackers = {email: GeminiProTracker(email) for email in GEMINI_ACCOUNTS}
"""
    if "GeminiProTracker" not in content:
        content = content.replace(import_hook, import_hook + injection_1)

    # 2. Increase window height to accommodate 9 new accounts
    geometry_hook = 'self.geometry("780x580")'
    content = content.replace(geometry_hook, 'self.geometry("780x950")')

    # 3. Inject Init Call
    init_hook = "self._refresh()\n"
    injection_2 = "        self._refresh_gemini()\n"
    if "_refresh_gemini" not in content.split("def __init__")[1].split("def _build_layout")[0]:
        content = content.replace(init_hook, init_hook + injection_2)

    # 4. Inject Layout Frame for Gemini
    layout_hook = "        log_label = tk.Label(self, text=\"EVENT LOG\""
    injection_3 = """
        # --- GEMINI UI ---
        gemini_header = tk.Label(
            self, text="[ GEMINI PRO 1.5 LIMITS ]", bg=BG, fg="#00aaff", font=("Menlo", 12, "bold")
        )
        gemini_header.pack(pady=(12, 4))
        
        self.gemini_frame = tk.Frame(self, bg=BG)
        self.gemini_frame.pack(fill="x", padx=16, pady=4)
        
        self.gemini_widgets = {}
        for account in GEMINI_ACCOUNTS:
            row = tk.Frame(self.gemini_frame, bg=PANEL_BG, highlightbackground="#00aaff", highlightthickness=1)
            row.pack(fill="x", pady=3)
            
            name = tk.Label(row, text=account, bg=PANEL_BG, fg=FG, font=FONT, width=28, anchor="w")
            name.pack(side="left", padx=8, pady=6)
            
            status = tk.Label(row, text="ONLINE", bg=PANEL_BG, fg=ACCENT, font=FONT_BOLD, width=10)
            status.pack(side="left", padx=8)
            
            reset = tk.Label(row, text="", bg=PANEL_BG, fg=FG, font=FONT, width=26, anchor="w")
            reset.pack(side="left", padx=8)
            
            self.gemini_widgets[account] = {"status": status, "reset": reset}
        # -----------------
"""
    if "GEMINI PRO 1.5 LIMITS" not in content:
        content = content.replace(layout_hook, injection_3 + layout_hook)

    # 5. Inject the Refresh Loop logic
    refresh_hook = "    def _do_reassign(self, detected_at, account, picker):\n"
    injection_4 = """
    def _refresh_gemini(self):
        for account, tracker in gemini_trackers.items():
            status, free_time, reason = tracker.get_status()
            widgets = self.gemini_widgets[account]
            
            if status == "LOCKED":
                widgets["status"].configure(text="LOCKED", fg=WARN)
                unlock_time_str = datetime.fromtimestamp(free_time).strftime('%I:%M:%S %p').lstrip('0')
                widgets["reset"].configure(text=f"free at {unlock_time_str} ({reason})")
            else:
                widgets["status"].configure(text="ONLINE", fg=ACCENT)
                widgets["reset"].configure(text="")
                
        self.after(1000, self._refresh_gemini)

"""
    if "def _refresh_gemini" not in content:
        content = content.replace(refresh_hook, injection_4 + refresh_hook)

    # Write patched content back to file
    with open("gui.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("gui.py successfully patched! (Window geometry expanded to 780x950).")

if __name__ == "__main__":
    patch_gui()
