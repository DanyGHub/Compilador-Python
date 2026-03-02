# managers/terminal.py
class TerminalManager:
    def __init__(self, ui):
        self.ui = ui

    def log(self, text):
        self.ui.terminalOutput.append(f"$ {text}")

    def toggle_panel(self, visible: bool):
        self.ui.bottomTabWidget.setVisible(visible)