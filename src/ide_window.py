import os
import sys
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

# Importación de la interfaz generada
from ui.ui_main import Ui_MainWindow

# Importación de Managers
from managers.project import ProjectManager
from managers.editor import EditorManager
from managers.terminal import TerminalManager
from managers.compiler import CompilerManager
from managers.file import FileManager

class CompilerIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Configuración de la UI base
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # 2. Instanciar los Managers
        self.editor = EditorManager(self.ui)
        self.project = ProjectManager(self.ui)
        self.terminal = TerminalManager(self.ui)
        self.compiler = CompilerManager(self.ui, self.terminal)
        self.file_manager = FileManager(self)

        # 3. Preparar el ambiente (Estado inicial)
        self.setup_initial_state()
        
        # 4. Cargar Estilos (.qss)
        self.load_stylesheet()
        
        # 5. Conectar señales y slots (Eventos)
        self.connect_signals()
        
        # Nota: Eliminamos el punto 6 para que respete el estado False inicial

    def setup_initial_state(self):
        """Define qué se ve y qué no al abrir el IDE por primera vez."""
        self.setWindowTitle("Compilador IDE")
        self.project.setup_explorer()
        
        # Estados de visibilidad iniciales
        self.editor.toggle_editor_view(False)
        self.project.toggle_sidebar(False)
        self.ui.actionClose.setEnabled(False)
        self.ui.actionSave.setEnabled(False)
        self.ui.actionSaveAs.setEnabled(False)
        
        # Configuración de terminal
        self.ui.bottomTabWidget.setCurrentIndex(2) 
        self.terminal.log("IDE Iniciado correctamente...")
        
        # Tamaños por defecto de splitters
        self.ui.centerSplitter.setSizes([500, 200])
        self.ui.mainSplitter.setSizes([200, 900])

    def connect_signals(self):
        """Conecta los clics de botones y menús."""
        # Atajos de teclado
        self.ui.actionNew.setShortcut(QKeySequence("Ctrl+N"))
        self.ui.actionOpen.setShortcut(QKeySequence("Ctrl+O"))
        self.ui.actionClose.setShortcut(QKeySequence("Ctrl+W"))
        self.ui.actionSave.setShortcut(QKeySequence("Ctrl+S"))
        self.ui.actionSaveAs.setShortcut(QKeySequence("Ctrl+Shift+S"))

        self.ui.actionNew.triggered.connect(self.on_new_file)
        self.ui.actionOpen.triggered.connect(self.on_open_file)
        self.ui.actionClose.triggered.connect(self.on_close_file)
        self.ui.actionSave.triggered.connect(self.on_save_file)
        self.ui.actionSaveAs.triggered.connect(self.on_save_as_file)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.btnLexical.clicked.connect(self.compiler.run_lexical_analysis)
        
        # Toggle de Terminal
        self.ui.btnTerminalView.clicked.connect(
            lambda: self.terminal.toggle_panel(not self.ui.bottomTabWidget.isVisible())
        )
        
        # Toggle de Carpeta
        self.ui.btnFolder.clicked.connect(self.toggle_project_sidebar)

    def load_stylesheet(self):
        # Verificar si estamos en el ejecutable empaquetado por PyInstaller
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
            
        style_path = os.path.join(base_path, "resources", "style.qss")
        if os.path.exists(style_path):
            try:
                with open(style_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception as e:
                print(f"Error al leer el archivo de estilos: {e}")

    def closeEvent(self, event):
        print("Cerrando el IDE...")
        event.accept()
    
    def toggle_project_sidebar(self):
        """Lógica para alternar la visibilidad de la barra de proyecto."""
        is_visible = self.ui.sideBarProject.isVisible()
        self.project.toggle_sidebar(not is_visible)

    def on_new_file(self):
        self.editor.set_content("", "Untitled", None)
        self.editor.toggle_editor_view(True)

    def on_open_file(self):
        """Maneja la apertura de archivos, verifica éxito y actualiza el editor."""
        path, content = self.file_manager.open_file_dialog()
        
        # Si path y content no son None, la lectura fue correcta
        if path and content is not None:
            filename = os.path.basename(path)
            self.editor.set_content(content, filename, path)
            self.editor.toggle_editor_view(True)

    def on_close_file(self):
        self.editor.close_tab(self.editor.tabs.currentIndex())

    def on_save_file(self):
        """Obtiene el código del editor y lo guarda."""
        content = self.editor.get_current_code()
        path = self.editor.get_current_path()
        
        if path:    # Si el archivo ya tiene una ruta definida, se guarda normal
            self.file_manager.current_file = path
            self.file_manager.save_file(content)
        else:       # Si no, se guarda como
            self.file_manager.current_file = None
            self.file_manager.save_as_file(content)
            path = self.file_manager.current_file # Recuperamos la nueva ruta
            
            # Si se guardó (path tiene valor), actualizamos la memoria de la pestaña (tooltip)
            if path:
                self.editor.tabs.setTabToolTip(self.editor.tabs.currentIndex(), path)

        if path:
            self.editor.set_name_tab(self.editor.tabs.currentIndex(), os.path.basename(path))

    def on_save_as_file(self):
        """Obtiene el código del editor y lo guarda como."""
        content = self.editor.get_current_code()
        self.file_manager.save_as_file(content)
        path = self.file_manager.current_file
        if path:
            self.editor.tabs.setTabToolTip(self.editor.tabs.currentIndex(), path)
            self.editor.set_name_tab(self.editor.tabs.currentIndex(), os.path.basename(path))