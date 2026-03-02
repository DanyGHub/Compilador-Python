import os
from PyQt6.QtWidgets import QFileDialog

class FileManager:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.current_file = None

    def open_file_dialog(self):
        """Abre el diálogo de archivos y retorna la ruta y contenido."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent, "Abrir archivo", "", "Archivos de texto (*.txt);;Todos (*)"
        )
        if file_path:
            self.current_file = file_path
            with open(file_path, "r", encoding="utf-8") as f:
                return file_path, f.read()
        return None, None