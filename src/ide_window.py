import os
import sys
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

from ui.ui_main import Ui_MainWindow
from managers.project import ProjectManager
from managers.editor import EditorManager
from managers.terminal import TerminalManager
from managers.compiler import CompilerManager
from managers.file import FileManager

class CompilerIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.editor = EditorManager(self.ui)
        self.project = ProjectManager(self.ui)
        self.terminal = TerminalManager(self.ui)
        self.compiler = CompilerManager(self.ui, self.terminal)
        self.file_manager = FileManager(self)
        
        self.setup_connections()
        self.setup_initial_state()
        self.load_stylesheet()
        self.connect_signals()
        self.connect_toolbar_actions()
        
    def setup_connections(self):
        # Conexión segura de botones de terminal
        if hasattr(self.ui, 'btnTerminal'):
            self.ui.btnTerminal.clicked.connect(self.terminal.toggle_panel)
        if hasattr(self.ui, 'btnTerminalView'):
            self.ui.btnTerminalView.clicked.connect(self.terminal.toggle_panel)

        # Acciones de Menú (Corregidas para evitar AttributeError)
        if hasattr(self.ui, 'actionLexical'):
            self.ui.actionLexical.triggered.connect(lambda: self.compiler.toggle_panel(0, "LÉXICO"))
        if hasattr(self.ui, 'actionSyntactic'):
            self.ui.actionSyntactic.triggered.connect(lambda: self.compiler.toggle_panel(1, "SINTÁCTICO"))
        
    def setup_initial_state(self):
        self.setWindowTitle("Compilador IDE")
        self.project.setup_explorer()
        self.editor.toggle_editor_view(False)
        self.project.toggle_sidebar(False)
        self.ui.rightAccessBar.setFixedWidth(70)
        self.ui.bottomTabWidget.setCurrentIndex(2) 
        self.terminal.log("IDE Iniciado correctamente...")
        self.ui.centerSplitter.setSizes([500, 200])
        self.ui.mainSplitter.setSizes([200, 500, 330, 70])
        
    def connect_signals(self):
        # Atajos
        self.ui.actionNew.setShortcut(QKeySequence("Ctrl+N"))
        self.ui.actionOpen.setShortcut(QKeySequence("Ctrl+O"))
        self.ui.actionOpen_Folder.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.ui.actionClose.setShortcut(QKeySequence("Ctrl+W"))
        self.ui.actionSave.setShortcut(QKeySequence("Ctrl+S"))
        self.ui.actionSaveAs.setShortcut(QKeySequence("Ctrl+Shift+S"))

        # Slots de Archivo
        self.ui.actionNew.triggered.connect(self.on_new_file)
        self.ui.actionOpen.triggered.connect(self.on_open_file)
        self.ui.actionClose.triggered.connect(self.on_close_file)
        self.ui.actionOpen_Folder.triggered.connect(self.on_open_folder)
        self.ui.actionSave.triggered.connect(self.on_save_file)
        self.ui.actionSaveAs.triggered.connect(self.on_save_as_file)
        self.ui.actionExit.triggered.connect(self.close)

        # Botones de acceso lateral
        self.ui.btnLexical.clicked.connect(lambda: self.compiler.toggle_panel(0, "LÉXICO"))
        self.ui.btnSyntactic.clicked.connect(lambda: self.compiler.toggle_panel(1, "SINTÁCTICO"))
        self.ui.btnSemantic.clicked.connect(lambda: self.compiler.toggle_panel(2, "SEMÁNTICO"))
        self.ui.btnIntermediate.clicked.connect(lambda: self.compiler.toggle_panel(3, "CÓDIGO INTERMEDIO"))
        self.ui.btnHash.clicked.connect(lambda: self.compiler.toggle_panel(4, "TABLA HASH"))
        
        self.ui.btnFolder.clicked.connect(self.toggle_project_sidebar)
        self.ui.treeViewExplorer.doubleClicked.connect(self.on_tree_file_double_clicked)

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
        
    # Busca esta función en ide_window.py
    def run_lexical_analysis(self):
        code = self.editor.get_current_code()
        if code:
            self.compiler.run_lexical_analysis(code)   
            self.terminal.log("Análisis Léxico finalizado.")
        else:
            self.terminal.log("No hay código para analizar.")
    
    def run_syntactic_analysis(self):
        code = self.editor.get_current_code()
        if code:
            # Forzamos la limpieza de la terminal de problemas 
            self.terminal.clear_problems()
            
            # 1. Siempre se requiere correr el léxico primero silenciosamente para actualizar los tokens
            self.compiler.run_lexical_analysis(code)
            
            # 2. Correr el Sintáctico y pintar el árbol
            self.compiler.run_syntactic_analysis()
            
            # Si hubo errores sintácticos, la pestaña Problems se habrá abierto automáticamente
            self.terminal.log("Análisis Sintáctico finalizado (revisa los problemas si aplica).")
        else:
            self.terminal.log("No hay código para analizar sintácticamente.")

    def connect_toolbar_actions(self):
        self.editor.btnNew.clicked.connect(self.ui.actionNew.trigger)
        self.editor.btnOpen.clicked.connect(self.ui.actionOpen.trigger)
        self.editor.btnOpenDir.clicked.connect(self.ui.actionOpen_Folder.trigger)
        self.editor.btnSave.clicked.connect(self.ui.actionSave.trigger)
        self.editor.btnSaveAs.clicked.connect(self.ui.actionSaveAs.trigger)
        
        # Conexiones para Análisis
        self.editor.btnLex.clicked.connect(self.run_lexical_analysis)
        self.editor.btnSin.clicked.connect(self.run_syntactic_analysis) # <--- Cambiado aquí
        
        # Si tienes la acción de menú conectada en setup_connections o connect_signals, haz que apunte también:
        if hasattr(self.ui, 'actionSyntactic'):
            self.ui.actionSyntactic.triggered.disconnect() # Desconecta el lambda anterior si existía
            self.ui.actionSyntactic.triggered.connect(self.run_syntactic_analysis)

        # Para el botón de la barra lateral "btnSyntactic" en connect_signals:
        if hasattr(self.ui, 'btnSyntactic'):
             self.ui.btnSyntactic.clicked.disconnect()
             self.ui.btnSyntactic.clicked.connect(self.run_syntactic_analysis)

    # --- Lógica de Archivos ---
    def on_new_file(self):
        self.editor.set_content("", "Untitled", None)
        self.editor.toggle_editor_view(True)

    def on_open_file(self):
        path, content = self.file_manager.open_file_dialog()
        if path and content is not None:
            self.editor.set_content(content, os.path.basename(path), path)
            self.editor.toggle_editor_view(True)

    def on_save_file(self):
        content = self.editor.get_current_code()
        path = self.editor.get_current_path()
        if path:
            self.file_manager.save_file(content, path)
        else:
            self.on_save_as_file()

    def on_save_as_file(self):
        content = self.editor.get_current_code()
        self.file_manager.save_as_file(content)
        if self.file_manager.current_file:
            path = self.file_manager.current_file
            self.editor.tabs.setTabToolTip(self.editor.tabs.currentIndex(), path)
            self.editor.set_name_tab(self.editor.tabs.currentIndex(), os.path.basename(path))

    def on_close_file(self):
        self.editor.close_tab(self.editor.tabs.currentIndex())

    def on_open_folder(self):
        path = self.file_manager.open_folder_dialog()
        if path:
            self.project.setup_explorer(path)
            self.project.toggle_sidebar(True)

    def on_tree_file_double_clicked(self, index):
        path = self.project.model.filePath(index)
        if not self.project.model.isDir(index):
            content = self.file_manager.read_file(path)
            if content is not None:
                self.editor.set_content(content, os.path.basename(path), path)
                self.editor.toggle_editor_view(True)

    def toggle_project_sidebar(self):
        self.project.toggle_sidebar(not self.ui.sideBarProject.isVisible())

    def load_stylesheet(self):
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(__file__)
        style_path = os.path.join(base_path, "resources", "style.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def closeEvent(self, event):
        event.accept()