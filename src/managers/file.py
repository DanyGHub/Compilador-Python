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
    
    def save_file(self, content):
        """Guarda el contenido en el archivo actual."""
        if self.current_file:
            try:
                with open(self.current_file, "w") as f:
                    f.write(content)
            except Exception as e:
                print(f"Error al guardar el archivo: {e}")
    
    def save_as_file(self, content):
        """Guarda el contenido en un nuevo archivo."""
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent, "Save File", "", "All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(content)
                self.current_file = file_path
            except Exception as e:
                print(f"Error al guardar el archivo: {e}")

    def open_folder_dialog(self):
        """Abre el diálogo para seleccionar una carpeta."""
        folder_path = QFileDialog.getExistingDirectory(
            self.parent, "Select Project Folder", ""
        )
        return folder_path

    def read_file(self, file_path):
        """Lee el contenido de un archivo dado su path."""
        if file_path:
            try:
                with open(file_path, "r") as f:
                    return f.read()
            except Exception as e:
                print(f"Error al leer el archivo: {e}")
        return None