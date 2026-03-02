import os
from PyQt6.QtWidgets import QFileDialog

class FileManager:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.current_file = None

    def open_file_dialog(self):
        """Abre el diálogo de archivos y retorna la ruta y contenido."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent, "Open File", "", "All Files (*)"
        )
        if file_path:
            self.current_file = file_path
            try:
                with open(file_path, "r") as f:
                    return file_path, f.read()
            except Exception as e:
                print(f"Error al leer el archivo: {e}")
        return None, None