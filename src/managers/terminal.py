from PyQt6.QtWidgets import QTextEdit

class TerminalManager:
    def __init__(self, ui):
        self.ui = ui

    def log(self, text):
        """Escribe en la terminal de salida principal."""
        if hasattr(self.ui, 'terminalOutput'):
            self.ui.terminalOutput.append(f"$ {text}")

    def clear_problems(self):
        """Limpia el contenido de la pestaña Problems."""
        if hasattr(self.ui, 'listProblems'):
            self.ui.listProblems.clear()

    def log_problem(self, phase, message):
        """Escribe errores en la pestaña Problems con el formato solicitado."""
        if hasattr(self.ui, 'listProblems'):
            out = self.ui.listProblems
            header = f"==== {phase.upper()} ===="
            
            # Agregamos el encabezado de la fase si aún no existe en la lista actual
            existing_items = [out.item(i).text() for i in range(out.count())]
            if header not in existing_items:
                out.addItem(header)
            
            out.addItem(f"Error, {message}")
            # Cambia a la pestaña de Problems (índice 0)
            self.ui.bottomTabWidget.setCurrentIndex(0)

    def toggle_panel(self, checked=None):
        """Alterna la visibilidad de la terminal inferior."""
        is_visible = self.ui.bottomTabWidget.isVisible()
        self.ui.bottomTabWidget.setVisible(not is_visible)