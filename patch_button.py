import os

path = os.path.expanduser("~/Downloads/ai_limit_tracker/gui.py")
with open(path, "r") as f:
    code = f.read()

# 1. Move the action bar to the main window so it is visible on both tabs
code = code.replace("actions = tk.Frame(self.claude_tab, bg=BG)", "actions = tk.Frame(self, bg=BG)")

# 2. Update the button text, command, and hint label
code = code.replace('text="REASSIGN SELECTED ENTRY"', 'text="CLEAR ALL"')
code = code.replace('command=self._reassign_selected', 'command=self._clear_all_active_tab')
code = code.replace('text="unknown-account entries can be tagged manually here"', 'text="Clears all account limits for the currently active tab"')

# 3. Inject the logic to clear accounts based on the active tab
new_func = """    def _clear_all_active_tab(self):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            for account in self.claude_account_widgets:
                self._mark_available(account)
        elif current_tab == 1:
            for account in gemini_trackers:
                self._mark_gemini_available(account)

    def _mark_available"""

code = code.replace("    def _mark_available", new_func)

with open(path, "w") as f:
    f.write(code)
