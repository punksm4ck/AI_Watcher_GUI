import os
import json
import customtkinter as ctk

STATE_FILE = os.path.expanduser("~/Downloads/ai_limit_tracker/current_state.json")

ACCOUNTS = [
    "tsannasardo@gmail.com",
    "tsannasardo2@gmail.com",
    "punksm4ck@gmail.com",
    "punksm4ck2@gmail.com",
    "ts7605689@gmail.com",
    "t420x710s@gmail.com",
    "tom@desklogix.app",
    "tom@visitlog.app",
    "tom1@visitlog.app"
]

class AILimitTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI LIMIT TRACKER // AEGIS-CLASS")
        self.geometry("820x680")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.configure(fg_color="#0b0e14")

        self.status_labels = {}
        self.log_textbox = None
        self.current_provider = "claude"

        self.build_ui()
        self.poll_state()

    def build_ui(self):
        title_label = ctk.CTkLabel(
            self, 
            text="[ AI LIMIT TRACKER - MULTI-ACCOUNT WATCH ]", 
            font=("Courier", 18, "bold"),
            text_color="#00f0ff"
        )
        title_label.pack(pady=(15, 10))

        self.tabview = ctk.CTkTabview(
            self, 
            fg_color="#121620",
            segmented_button_fg_color="#1a202c",
            segmented_button_selected_color="#00f0ff",
            segmented_button_selected_hover_color="#00d0df",
            command=self.on_tab_change
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=5)

        self.tab_claude = self.tabview.add("CLAUDE ACCOUNTS")
        self.tab_gemini = self.tabview.add("GEMINI PRO")

        self.build_account_list(self.tab_claude, "claude")
        self.build_account_list(self.tab_gemini, "gemini")

        log_title = ctk.CTkLabel(
            self, 
            text="EVENT LOG", 
            font=("Courier", 12, "bold"),
            text_color="#00f0ff"
        )
        log_title.pack(anchor="w", padx=25, pady=(5, 0))

        self.log_textbox = ctk.CTkTextbox(
            self, 
            height=120, 
            fg_color="#080a0f",
            text_color="#00ff88",
            font=("Courier", 11)
        )
        self.log_textbox.pack(fill="x", padx=20, pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(5, 15))

        self.clear_btn = ctk.CTkButton(
            btn_frame,
            text="CLEAR CLAUDE LIMITS & LOGS",
            fg_color="#1f2937",
            hover_color="#374151",
            text_color="#e5e7eb",
            command=self.clear_current_limits
        )
        self.clear_btn.pack(side="left")

        desc_label = ctk.CTkLabel(
            btn_frame,
            text="Wipes active locked statuses and clears history",
            font=("Helvetica", 11),
            text_color="#6b7280"
        )
        desc_label.pack(side="left", padx=15)

    def build_account_list(self, parent, provider):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        for email in ACCOUNTS:
            row = ctk.CTkFrame(scroll, fg_color="#181e2a", border_color="#2d3748", border_width=1, corner_radius=6)
            row.pack(fill="x", pady=3, padx=2)

            lbl_email = ctk.CTkLabel(row, text=email, font=("Courier", 13, "bold"), text_color="#ffffff", width=260, anchor="w")
            lbl_email.pack(side="left", padx=15, pady=8)

            key = f"{provider}:{email}"
            lbl_status = ctk.CTkLabel(row, text="ONLINE", font=("Courier", 12, "bold"), text_color="#00ff88", width=180, anchor="w")
            lbl_status.pack(side="left", padx=10)
            self.status_labels[key] = lbl_status

            btn_mark = ctk.CTkButton(
                row, 
                text="MARK AVAILABLE", 
                font=("Courier", 11, "bold"),
                fg_color="#242c3d", 
                hover_color="#323d54",
                text_color="#94a3b8",
                width=130,
                command=lambda k=key: self.mark_available(k)
            )
            btn_mark.pack(side="right", padx=15)

    def on_tab_change(self):
        selected = self.tabview.get()
        if "CLAUDE" in selected:
            self.current_provider = "claude"
            self.clear_btn.configure(text="CLEAR CLAUDE LIMITS & LOGS")
        else:
            self.current_provider = "gemini"
            self.clear_btn.configure(text="CLEAR GEMINI LIMITS & LOGS")

    def mark_available(self, key):
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                accs = data.get("accounts", {})
                if key in accs:
                    del accs[key]
                    data["accounts"] = accs
                    with open(STATE_FILE, "w") as f:
                        json.dump(data, f, indent=2)
        except Exception:
            pass
        self.poll_state()

    def clear_current_limits(self):
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                accs = data.get("accounts", {})
                new_accs = {k: v for k, v in accs.items() if not k.startswith(self.current_provider)}
                data["accounts"] = new_accs
                data["logs"] = []
                with open(STATE_FILE, "w") as f:
                    json.dump(data, f, indent=2)
        except Exception:
            pass
        self.poll_state()

    def poll_state(self):
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r") as f:
                    data = json.load(f)
                accs = data.get("accounts", {})
                logs = data.get("logs", [])

                for key, lbl in self.status_labels.items():
                    if key in accs and accs[key].get("status") == "limited":
                        raw_t = accs[key].get("reset_time_raw", "LOCKED")
                        lbl.configure(text=f"LOCKED  {raw_t}", text_color="#ff5555")
                    else:
                        lbl.configure(text="ONLINE", text_color="#00ff88")

                if self.log_textbox:
                    log_text = "\n".join(logs)
                    self.log_textbox.delete("1.0", "end")
                    self.log_textbox.insert("1.0", log_text)
                    self.log_textbox.see("end")
        except Exception:
            pass

        self.after(1000, self.poll_state)

if __name__ == "__main__":
    app = AILimitTrackerApp()
    app.mainloop()
