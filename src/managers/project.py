# managers/project.py
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import QDir

class ProjectManager:
    def __init__(self, ui):
        self.ui = ui
        self.model = QFileSystemModel()
        self.current_path = None
        
    def setup_explorer(self, path=None):
        if not path:
            return
            
        self.current_path = path
            
        # 1. Configurar el modelo
        self.model.setRootPath(path)
        self.ui.treeViewExplorer.setModel(self.model)
        self.ui.treeViewExplorer.setRootIndex(self.model.index(path))
        
        # 2. Actualizar el título con el nombre del directorio
        # os.path.basename extrae el nombre de la carpeta de la ruta completa
        import os
        folder_name = os.path.basename(path)
        self.ui.lblProjectTitle.setText(folder_name.upper()) # Como en tu diseño
        
        # Ocultar columnas innecesarias
        for i in range(1, 4):
            self.ui.treeViewExplorer.setColumnHidden(i, True)

    def toggle_sidebar(self, visible: bool):
        """Muestra u oculta el panel lateral del proyecto."""
        self.ui.sideBarProject.setVisible(visible)