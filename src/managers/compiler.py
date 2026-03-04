# managers/compiler.py
class CompilerManager:
    def __init__(self, ui, terminal):
        self.ui = ui
        self.terminal = terminal

    def run_lexical_analysis(self):
        self.terminal.log("$_")
        # Lógica futura aquí