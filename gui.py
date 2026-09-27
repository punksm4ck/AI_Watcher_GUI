"""Tkinter dashboard for AI Limit Tracker - Dual Tabbed Interface."""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone
import time
from collections import deque

import storage
from config import TRACKED_ACCOUNTS

REFRESH_MS = 2000

BG = "#0d1117"
PANEL_BG = "#161b22"
FG = "#c9d1d9"
ACCENT = "#00ff9c"
GEMINI_ACCENT = "#00aaff"
WARN = "#ff3b3b"
FONT = ("Menlo", 10)
FONT_BOLD = ("Menlo", 11, "bold")

GEMINI_ACCOUNTS = [
    "tsannasardo@gmail.com",
    "tsannasardo2@gmail.com",
    "punksm4ck@gmail.com",
    "punksm4ck2@gmail.com",
    "ts7605689@gmail.com",
    "t420x710s@gmail.com",
    "tom@desklogix.app",
    "tom@visitlog.app",
    "tom1@visitlog.app",
]

class GeminiProTracker:
    def __init__(self, account_name):
        self.account_name = account_name
        self.MAX_RPM = 2
        self.MAX_TPM = 32000
        self.MAX_RPD = 50
        self.request_timestamps = deque()
        self.token_history = deque()

    def add_request(self, token_count=1000):
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
            return "LOCKED", self.request_timestamps[0] + 86400, "Daily limit reached"
        if requests_last_minute >= self.MAX_RPM or tokens_last_minute >= self.MAX_TPM:
            relevant_times = [t for t in self.request_timestamps if current_time - t <= 60]
            free_time = relevant_times[0] + 60 if relevant_times else current_time + 60
            return "LOCKED", free_time, "Minute limit reached"

        return "ONLINE", None, "Available"

gemini_trackers = {email: GeminiProTracker(email) for email in GEMINI_ACCOUNTS}


class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI LIMIT TRACKER // AEGIS-CLASS")
        self.configure(bg=BG)
        self.geometry("840x740")

        self._setup_styles()
        self._build_layout()
        self._refresh_claude()
        self._refresh_gemini()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TNotebook", background=BG, borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            background=PANEL_BG,
            foreground=FG,
            padding=[18, 6],
            font=("Menlo", 10, "bold"),
            borderwidth=0,
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", "#21262d")],
            foreground=[("selected", ACCENT)],
        )

    def _build_layout(self):
        header = tk.Label(
            self,
            text="[ AI LIMIT TRACKER — MULTI-ACCOUNT WATCH ]",
            bg=BG,
            fg=ACCENT,
            font=("Menlo", 13, "bold"),
        )
        header.pack(pady=(12, 6))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=6)

        self.claude_tab = tk.Frame(self.notebook, bg=BG)
        self.gemini_tab = tk.Frame(self.notebook, bg=BG)

        self.notebook.add(self.claude_tab, text=" CLAUDE ACCOUNTS ")
        self.notebook.add(self.gemini_tab, text=" GEMINI PRO ")

        self._build_claude_tab()
        self._build_gemini_tab()

    def _build_claude_tab(self):
        self.claude_status_frame = tk.Frame(self.claude_tab, bg=BG)
        self.claude_status_frame.pack(fill="x", padx=6, pady=6)

        self.claude_account_widgets = {}
        for account in TRACKED_ACCOUNTS:
            self._build_claude_row(account)

        log_label = tk.Label(self.claude_tab, text="CLAUDE EVENT LOG", bg=BG, fg=ACCENT, font=FONT_BOLD)
        log_label.pack(anchor="w", padx=6, pady=(12, 2))

        log_frame = tk.Frame(self.claude_tab, bg=BG)
        log_frame.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        self.claude_log_box = tk.Listbox(
            log_frame,
            bg=PANEL_BG,
            fg=FG,
            font=("Menlo", 9),
            selectbackground="#21262d",
            highlightthickness=0,
            borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self.claude_log_box.yview)
        self.claude_log_box.configure(yscrollcommand=scrollbar.set)
        self.claude_log_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        actions = tk.Frame(self.claude_tab, bg=BG)
        actions.pack(fill="x", padx=6, pady=(8, 8))
        clear_btn = tk.Button(
            actions,
            text="CLEAR CLAUDE LIMITS & LOGS",
            command=lambda: self._clear_specific_tab("claude:"),
            bg="#21262d",
            fg=FG,
            font=("Menlo", 9),
            relief="flat",
        )
        clear_btn.pack(side="left")

        hint = tk.Label(
            actions,
            text="Wipes Claude locked statuses and clears tab history",
            bg=BG,
            fg="#6e7681",
            font=("Menlo", 9),
        )
        hint.pack(side="left", padx=12)

    def _build_claude_row(self, account):
        row = tk.Frame(
            self.claude_status_frame,
            bg=PANEL_BG,
            highlightbackground=ACCENT,
            highlightthickness=1,
        )
        row.pack(fill="x", pady=2)

        name = tk.Label(row, text=account, bg=PANEL_BG, fg=FG, font=FONT, width=28, anchor="w")
        name.pack(side="left", padx=8, pady=4)

        status = tk.Label(row, text="ONLINE", bg=PANEL_BG, fg=ACCENT, font=FONT_BOLD, width=10)
        status.pack(side="left", padx=8)

        reset = tk.Label(row, text="", bg=PANEL_BG, fg=FG, font=FONT, width=26, anchor="w")
        reset.pack(side="left", padx=8)

        clear_btn = tk.Button(
            row,
            text="MARK AVAILABLE",
            command=lambda a=account: self._mark_available(a),
            bg="#21262d",
            fg=FG,
            font=("Menlo", 9),
            relief="flat",
        )
        clear_btn.pack(side="right", padx=8)

        self.claude_account_widgets[account] = {"status": status, "reset": reset}

    def _build_gemini_tab(self):
        self.gemini_status_frame = tk.Frame(self.gemini_tab, bg=BG)
        self.gemini_status_frame.pack(fill="x", padx=6, pady=6)

        self.gemini_widgets = {}
        for account in GEMINI_ACCOUNTS:
            row = tk.Frame(
                self.gemini_status_frame,
                bg=PANEL_BG,
                highlightbackground=GEMINI_ACCENT,
                highlightthickness=1,
            )
            row.pack(fill="x", pady=2)

            name = tk.Label(row, text=account, bg=PANEL_BG, fg=FG, font=FONT, width=28, anchor="w")
            name.pack(side="left", padx=8, pady=4)

            status = tk.Label(row, text="ONLINE", bg=PANEL_BG, fg=ACCENT, font=FONT_BOLD, width=10)
            status.pack(side="left", padx=8)

            reset = tk.Label(row, text="", bg=PANEL_BG, fg=FG, font=FONT, width=32, anchor="w")
            reset.pack(side="left", padx=8)

            clear_btn = tk.Button(
                row,
                text="MARK AVAILABLE",
                command=lambda a=account: self._mark_gemini_available(a),
                bg="#21262d",
                fg=FG,
                font=("Menlo", 8),
                relief="flat",
            )
            clear_btn.pack(side="right", padx=4)

            req_btn = tk.Button(
                row,
                text="+ REQ",
                command=lambda a=account: gemini_trackers[a].add_request(1000),
                bg="#21262d",
                fg=GEMINI_ACCENT,
                font=("Menlo", 8),
                relief="flat",
            )
            req_btn.pack(side="right", padx=4)

            self.gemini_widgets[account] = {"status": status, "reset": reset}

        gemini_info = tk.Label(
            self.gemini_tab,
            text="Limits: 2 RPM | 32,000 TPM | 50 RPD (Free Tier) + Screen Detection Active",
            bg=BG,
            fg="#6e7681",
            font=("Menlo", 9),
        )
        gemini_info.pack(anchor="w", padx=6, pady=4)

        log_label = tk.Label(self.gemini_tab, text="GEMINI EVENT LOG", bg=BG, fg=GEMINI_ACCENT, font=FONT_BOLD)
        log_label.pack(anchor="w", padx=6, pady=(8, 2))

        log_frame = tk.Frame(self.gemini_tab, bg=BG)
        log_frame.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        self.gemini_log_box = tk.Listbox(
            log_frame,
            bg=PANEL_BG,
            fg=FG,
            font=("Menlo", 9),
            selectbackground="#21262d",
            highlightthickness=0,
            borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self.gemini_log_box.yview)
        self.gemini_log_box.configure(yscrollcommand=scrollbar.set)
        self.gemini_log_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        actions = tk.Frame(self.gemini_tab, bg=BG)
        actions.pack(fill="x", padx=6, pady=(8, 8))
        clear_btn = tk.Button(
            actions,
            text="CLEAR GEMINI LIMITS & LOGS",
            command=lambda: self._clear_specific_tab("gemini:"),
            bg="#21262d",
            fg=FG,
            font=("Menlo", 9),
            relief="flat",
        )
        clear_btn.pack(side="left")

        hint = tk.Label(
            actions,
            text="Wipes Gemini locked statuses and clears tab history",
            bg=BG,
            fg="#6e7681",
            font=("Menlo", 9),
        )
        hint.pack(side="left", padx=12)

    def _clear_specific_tab(self, prefix):
        """Clears state limits and file logs exclusively for the requested platform prefix."""
        storage.clear_prefix(prefix)
        if prefix == "gemini:":
            try:
                for tracker in gemini_trackers.values():
                    tracker.request_timestamps.clear()
                    tracker.token_history.clear()
            except NameError:
                pass
        self._refresh_log()

    def _mark_available(self, account):
        storage.mark_account_available(account)
        self._refresh_claude()

    def _mark_gemini_available(self, account):
        storage.mark_account_available(account)
        if account in gemini_trackers:
            gemini_trackers[account].request_timestamps.clear()
            gemini_trackers[account].token_history.clear()
        self._refresh_gemini()

    def _refresh_claude(self):
        state = storage.read_state()
        accounts = state.get("accounts", {})

        for account, widgets in self.claude_account_widgets.items():

            info = accounts.get(f"claude:{account}") or accounts.get(account)
            if not info or info.get("status") != "limited":
                widgets["status"].configure(text="ONLINE", fg=ACCENT)
                widgets["reset"].configure(text="")
                continue

            widgets["status"].configure(text="LOCKED", fg=WARN)
            reset_iso = info.get("reset_time")
            if reset_iso:
                try:
                    reset_dt = datetime.fromisoformat(reset_iso)
                    label = f"free at {reset_dt.strftime('%I:%M %p').lstrip('0')}"
                except ValueError:
                    label = info.get("reset_time_raw") or "unknown reset time"
            else:
                label = info.get("reset_time_raw") or "unknown reset time"
            widgets["reset"].configure(text=label)

        self._refresh_log()
        self.after(REFRESH_MS, self._refresh_claude)

    def _refresh_gemini(self):
        state = storage.read_state()
        accounts_state = state.get("accounts", {})

        for account, tracker in gemini_trackers.items():
            status, free_time, reason = tracker.get_status()
            ui = self.gemini_widgets[account]
            info = accounts_state.get(f"gemini:{account}") or accounts_state.get(account) or {}

            # Ensure we only fallback search if the key actually belongs to the gemini namespace
            if not info or info.get("status") != "limited":
                for k, v in accounts_state.items():
                    if k.lower().startswith("gemini:") and account.lower() in k.lower():
                        info = v
                        break

            if info.get("status") == "limited" or info.get("status") == "LOCKED" or info.get("reset_time") or info.get("reset_time_raw"):
                ui["status"].configure(text="LOCKED", fg=WARN)
                reset_iso = info.get("reset_time")
                if reset_iso:
                    try:
                        reset_dt = datetime.fromisoformat(reset_iso)
                        label = f"free at {reset_dt.strftime('%I:%M %p').lstrip('0')} (Pro Limit)"
                    except ValueError:
                        label = info.get("reset_time_raw") or "Pro limit (Switched to Flash)"
                else:
                    label = info.get("reset_time_raw") or "Pro limit (Switched to Flash)"
                ui["reset"].configure(text=label)
            elif status == "LOCKED":
                ui["status"].configure(text="LOCKED", fg=WARN)
                unlock_str = datetime.fromtimestamp(free_time).strftime('%I:%M:%S %p').lstrip('0')
                ui["reset"].configure(text=f"free at {unlock_str} ({reason})")
            else:
                ui["status"].configure(text="ONLINE", fg=ACCENT)
                ui["reset"].configure(text="")

        self.after(1000, self._refresh_gemini)

    def _refresh_log(self):
        events = storage.read_events(limit=200)
        self.claude_log_box.delete(0, "end")
        self.gemini_log_box.delete(0, "end")

        for event in reversed(events):
            ts = event.get("detected_at", "")[:19].replace("T", " ")
            acc = event.get("account", "unknown")
            reset = event.get("reset_time_raw") or event.get("reset_time") or "?"

            log_line = f"{ts}  [{acc}]  reset~ {reset}"

            # Route the log strictly to the matching listbox UI
            if "gemini:" in acc.lower():
                self.gemini_log_box.insert("end", log_line)
            else:
                self.claude_log_box.insert("end", log_line)

    def _reassign_selected(self):
        # NOTE: If implementing in the UI later, this needs to grab from the active tab's listbox.
        # Kept safely intact for your existing backend storage hooks.
        pass

    def _do_reassign(self, detected_at, account, picker):
        storage.reassign_event(detected_at, account)
        picker.destroy()
        self._refresh_claude()


def main():
    app = Dashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
