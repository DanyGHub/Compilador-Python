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
        # Conexión de botón de terminal
        if hasattr(self.ui, 'btnTerminalView'):
            self.ui.btnTerminalView.clicked.connect(self.terminal.toggle_panel)

        # Acciones de Menú de Compilación
        if hasattr(self.ui, 'actionLexical'):
            self.ui.actionLexical.triggered.connect(self.run_lexical_analysis)
        if hasattr(self.ui, 'actionSyntactic'):
            self.ui.actionSyntactic.triggered.connect(self.run_syntactic_analysis)
        if hasattr(self.ui, 'actionSemantic'):
            self.ui.actionSemantic.triggered.connect(self.run_semantic_analysis)
        if hasattr(self.ui, 'actionHash'):
            self.ui.actionHash.triggered.connect(self.run_hash_analysis)
        if hasattr(self.ui, 'actionIntermediateCode'):
            self.ui.actionIntermediateCode.triggered.connect(lambda: self.compiler.toggle_panel(3, "CÓDIGO INTERMEDIO"))
        
    def setup_initial_state(self):
        self.setWindowTitle("Compilador IDE")
        self.project.setup_explorer()
        self.on_new_file()
        self.project.toggle_sidebar(False)
        self.ui.rightAccessBar.setFixedWidth(70)
        self.ui.bottomTabWidget.setCurrentWidget(self.ui.tabTerminal)
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

        # Botones de acceso lateral (alternan vista entre Léxico, Sintáctico, Semántico, Código Intermedio y Tabla Hash)
        self.ui.btnLexical.clicked.connect(lambda: self.compiler.toggle_panel(0, "LÉXICO"))
        self.ui.btnSyntactic.clicked.connect(lambda: self.compiler.toggle_panel(1, "SINTÁCTICO"))
        self.ui.btnSemantic.clicked.connect(lambda: self.compiler.toggle_panel(2, "SEMÁNTICO"))
        self.ui.btnHash.clicked.connect(self.run_hash_analysis)
        self.ui.btnIntermediate.clicked.connect(lambda: self.compiler.toggle_panel(3, "CÓDIGO INTERMEDIO"))
        
        self.ui.btnFolder.clicked.connect(self.toggle_project_sidebar)
        self.ui.treeViewExplorer.doubleClicked.connect(self.on_tree_file_double_clicked)

    def load_stylesheet(self):
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(__file__)
        style_path = os.path.join(base_path, "resources", "style.qss")
        if os.path.exists(style_path):
            try:
                with open(style_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception as e:
                print(f"Error al leer el archivo de estilos: {e}")
        
    def run_lexical_analysis(self):
        code = self.editor.get_current_code()
        if code.strip():
            self.compiler.run_lexical_analysis(code, show_panel=True)
            self.terminal.log("Análisis Léxico finalizado.")
        else:
            self.compiler.lex_table.setRowCount(0)
            self.compiler.tokens_list = []
            self.terminal.clear_problems()
            self.terminal.log("No hay código para analizar.")
    
    def run_syntactic_analysis(self):
        code = self.editor.get_current_code()
        if code.strip():
            # Forzamos la limpieza de la terminal de problemas 
            self.terminal.clear_problems()
            
            # 1. Siempre se requiere correr el léxico primero silenciosamente para actualizar los tokens
            self.compiler.run_lexical_analysis(code, show_panel=False)
            
            # 2. Correr el Sintáctico y pintar el árbol
            self.compiler.run_syntactic_analysis(show_panel=True)
            
            # Si hubo errores sintácticos, la pestaña Problems se habrá abierto automáticamente
            self.terminal.log("Análisis Sintáctico finalizado (revisa los problemas si aplica).")
        else:
            self.compiler.sin_out.clear()
            self.terminal.clear_problems()
            self.terminal.log("No hay código para analizar sintácticamente.")

    def run_semantic_analysis(self):
        code = self.editor.get_current_code()
        if code.strip():
            self.terminal.clear_problems()

            # 1. Ejecutar Análisis Léxico (actualiza tabla léxica y tokens)
            self.compiler.run_lexical_analysis(code, show_panel=False)

            # 2. Ejecutar Análisis Sintáctico (construye el AST original en la pestaña SINTÁCTICO)
            self.compiler.run_syntactic_analysis(show_panel=False)

            # 3. Ejecutar Análisis Semántico (construye el AST anotado en SEMÁNTICO y llena la TABLA HASH)
            self.compiler.run_semantic_analysis(show_panel=True)

            self.terminal.log("Análisis Semántico y Tabla de Símbolos finalizados.")
        else:
            self.compiler.sem_out.clear()
            self.compiler.hash_out.setRowCount(0)
            self.terminal.clear_problems()
            self.terminal.log("No hay código para analizar semánticamente.")

    def run_hash_analysis(self):
        # Si la Tabla Hash ya está visible, alternar visibilidad (cerrar)
        if self.compiler.right_panel.isVisible() and self.compiler.result_stack.currentIndex() == 4:
            self.compiler.right_panel.setVisible(False)
            return

        code = self.editor.get_current_code()
        if code.strip():
            self.terminal.clear_problems()

            # 1. Ejecutar Léxico silenciosamente
            self.compiler.run_lexical_analysis(code, show_panel=False)

            # 2. Ejecutar Sintáctico silenciosamente
            self.compiler.run_syntactic_analysis(show_panel=False)

            # 3. Ejecutar Semántico para generar la Tabla de Símbolos a partir del AST anotado
            self.compiler.run_semantic_analysis(show_panel=False)

            # 4. Mostrar la pestaña de la Tabla Hash
            self.compiler.show_panel(4, "TABLA HASH")
            self.terminal.log("Tabla de Símbolos (Hash) generada a partir del Análisis Semántico.")
        else:
            self.compiler.hash_out.setRowCount(0)
            self.compiler.show_panel(4, "TABLA HASH")
            self.terminal.clear_problems()
            self.terminal.log("No hay código para generar la Tabla de Símbolos.")

    def connect_toolbar_actions(self):
        self.editor.btnNew.clicked.connect(self.ui.actionNew.trigger)
        self.editor.btnOpen.clicked.connect(self.ui.actionOpen.trigger)
        self.editor.btnOpenDir.clicked.connect(self.ui.actionOpen_Folder.trigger)
        self.editor.btnSave.clicked.connect(self.ui.actionSave.trigger)
        self.editor.btnSaveAs.clicked.connect(self.ui.actionSaveAs.trigger)
        
        # Conexiones para Análisis en la barra de herramientas
        self.editor.btnLex.clicked.connect(self.run_lexical_analysis)
        self.editor.btnSin.clicked.connect(self.run_syntactic_analysis)
        self.editor.btnSem.clicked.connect(self.run_semantic_analysis)
        if hasattr(self.editor, 'btnHash'):
            self.editor.btnHash.clicked.connect(self.run_hash_analysis)
        self.editor.btnInt.clicked.connect(lambda: self.compiler.toggle_panel(3, "CÓDIGO INTERMEDIO"))
        self.editor.btnCompile.clicked.connect(self.run_semantic_analysis)

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
        saved_path = self.file_manager.save_as_file(content)
        if saved_path:
            self.editor.tabs.setTabToolTip(self.editor.tabs.currentIndex(), saved_path)
            self.editor.set_name_tab(self.editor.tabs.currentIndex(), os.path.basename(saved_path))

    def on_close_file(self):
        self.editor.close_tab(self.editor.tabs.currentIndex())

    def on_open_folder(self):
        path = self.file_manager.open_folder_dialog()
        if path:
            self.project.setup_explorer(path)
            if self.compiler.right_panel.isVisible():
                self.compiler.right_panel.setVisible(False)
            self.project.toggle_sidebar(True)

    def on_tree_file_double_clicked(self, index):
        path = self.project.model.filePath(index)
        if not self.project.model.isDir(index):
            content = self.file_manager.read_file(path)
            if content is not None:
                self.editor.set_content(content, os.path.basename(path), path)
                self.editor.toggle_editor_view(True)

    def toggle_project_sidebar(self):
        if not self.project.current_path:
            self.on_open_folder()
        else:
            opening = not self.ui.sideBarProject.isVisible()
            if opening and self.compiler.right_panel.isVisible():
                self.compiler.right_panel.setVisible(False)
            self.project.toggle_sidebar(opening)

    def closeEvent(self, event):
        event.accept()