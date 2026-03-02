import os
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt

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
        
        # Configuración de terminal
        self.ui.bottomTabWidget.setCurrentIndex(2) 
        self.terminal.log("IDE Iniciado correctamente...")
        
        # Tamaños por defecto de splitters
        self.ui.centerSplitter.setSizes([500, 200])
        self.ui.mainSplitter.setSizes([200, 900])

    def connect_signals(self):
        """Conecta los clics de botones y menús."""
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.btnLexical.clicked.connect(self.compiler.run_lexical_analysis)
        
        # Toggle de Terminal
        self.ui.btnTerminalView.clicked.connect(
            lambda: self.terminal.toggle_panel(not self.ui.bottomTabWidget.isVisible())
        )
        
        # Toggle de Carpeta
        self.ui.btnFolder.clicked.connect(self.toggle_project_sidebar)

    def load_stylesheet(self):
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