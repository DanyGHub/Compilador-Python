from PyQt6.QtWidgets import (QTabWidget, QVBoxLayout, QHBoxLayout, 
                             QPlainTextEdit, QWidget, QTextEdit, QLabel, 
                             QFrame, QPushButton, QSpacerItem, QSizePolicy)
from PyQt6.QtGui import QFont, QTextCursor, QTextFormat, QColor, QTextCharFormat
from PyQt6.QtCore import Qt

class EditorManager:
    def __init__(self, ui):
        self.ui = ui
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.tabs.tabCloseRequested.connect(self.close_tab)

        # 1. Configurar layout del editorContainer si no existe
        if not self.ui.editorContainer.layout():
            layout = QVBoxLayout(self.ui.editorContainer)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.ui.editorContainer.setLayout(layout)

        # 2. CREAR E INYECTAR LA TOOLBAR (Persistente)
        self.setup_toolbar()

        # 3. Mover componentes existentes al flujo correcto
        self.ui.editorContainer.layout().insertWidget(0, self.toolbarFrame)
        self.ui.editorContainer.layout().addWidget(self.ui.editorHeader)
        self.ui.editorContainer.layout().addWidget(self.tabs)

        # Ocultar elementos base de Qt Designer
        self.ui.mainCodeEditor.hide()
        self.ui.lineNumberArea.hide()
        self.ui.editorHeader.setVisible(False)

    def setup_toolbar(self):
        """Genera la barra de herramientas programáticamente."""
        self.toolbarFrame = QFrame()
        self.toolbarFrame.setObjectName("toolbarFrame")
        self.toolbarFrame.setFixedHeight(40)
        
        layout = QHBoxLayout(self.toolbarFrame)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        # Botones de File
        self.btnNew = QPushButton("📄")
        self.btnOpen = QPushButton("📂")
        self.btnOpenDir = QPushButton("📁") # Nuevo botón
        self.btnSave = QPushButton("💾")
        self.btnSaveAs = QPushButton("📑")
        
        # Tooltips
        self.btnNew.setToolTip("New File (Ctrl+N)")
        self.btnOpen.setToolTip("Open File (Ctrl+O)")
        self.btnOpenDir.setToolTip("Open Directory (Ctrl+Shift+O)")
        self.btnSave.setToolTip("Save (Ctrl+S)")
        self.btnSaveAs.setToolTip("Save As... (Ctrl+Shift+S)")

        # Separador
        sep = QFrame()
        sep.setObjectName("toolbarSeparator")
        sep.setFixedWidth(1)
        sep.setStyleSheet("background-color: #555;") # Asegurar visibilidad
        layout.addWidget(sep)

        # Botones de Compile
        self.btnLex = QPushButton("LEX")
        self.btnSin = QPushButton("SIN")
        self.btnSem = QPushButton("SEM")
        self.btnInt = QPushButton("INT")
        self.btnCompile = QPushButton("⚙️")
        
        self.btnLex.setToolTip("Lexical Analysis")
        self.btnSin.setToolTip("Syntactic Analysis")
        self.btnSem.setToolTip("Semantic Analysis")
        self.btnInt.setToolTip("Intermediate Code")
        self.btnCompile.setToolTip("Compile")
        
        # Añadir al layout
        for btn in [self.btnNew, self.btnOpen, self.btnOpenDir, self.btnSave, self.btnSaveAs]:
            btn.setFixedSize(28, 28)
            layout.addWidget(btn)
        
        layout.addWidget(sep)
        
        for btn in [self.btnLex, self.btnSin, self.btnSem, self.btnInt, self.btnCompile]:
            btn.setFixedSize(38, 28)
            layout.addWidget(btn)

        layout.addStretch()

    def set_content(self, text, filename="Untitled", path=None):
        self.toggle_editor_view(True)
        tab_widget = QWidget()
        tab_widget.setObjectName("tabContainer")
        tab_main_layout = QVBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(0, 0, 0, 0)
        tab_main_layout.setSpacing(0)

        editor_layout = QHBoxLayout()
        editor_layout.setSpacing(0)

        # Numeración y Editor
        line_numbers = QPlainTextEdit()
        line_numbers.setProperty("lineNumbers", "true") 
        line_numbers.setFixedWidth(50)
        line_numbers.setReadOnly(True)
        line_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        code_editor = QPlainTextEdit()
        code_editor.setProperty("codeEditor", "true") 
        code_editor.setObjectName("mainEditor")
        code_editor.setPlainText(text)
        code_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Barra de estado inferior (Línea/Columna)
        status_bar = QLabel(" Línea 1, Columna 1")
        status_bar.setObjectName("editorStatusBar")
        status_bar.setFixedHeight(25)
        status_bar.setStyleSheet("background-color: #353535; color: white; padding-left: 10px; border-top: 1px solid #000;")

        def update_ui_editor():
            line_count = code_editor.document().blockCount()
            line_numbers.setPlainText("\n".join(str(i + 1) for i in range(line_count)))
            cursor = code_editor.textCursor()
            status_bar.setText(f" Línea {cursor.blockNumber() + 1}, Columna {cursor.columnNumber() + 1}")
            
            # Resaltado de línea
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor("#2c2c2c"))
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = cursor
            sel.cursor.clearSelection()
            
            # Negrita en número
            sel_num = QTextEdit.ExtraSelection()
            sel_num.format.setFontWeight(QFont.Weight.Bold)
            sel_num.format.setForeground(QColor("#ffffff"))
            sel_num.cursor = QTextCursor(line_numbers.document().findBlockByNumber(cursor.blockNumber()))
            
            code_editor.setExtraSelections([sel])
            line_numbers.setExtraSelections([sel_num])
            line_numbers.verticalScrollBar().setValue(code_editor.verticalScrollBar().value())

        code_editor.cursorPositionChanged.connect(update_ui_editor)
        code_editor.verticalScrollBar().valueChanged.connect(lambda v: line_numbers.verticalScrollBar().setValue(v))

        editor_layout.addWidget(line_numbers)
        editor_layout.addWidget(code_editor)
        tab_main_layout.addLayout(editor_layout)
        tab_main_layout.addWidget(status_bar)

        update_ui_editor()
        index = self.tabs.addTab(tab_widget, filename)
        self.tabs.setCurrentIndex(index)
        if path: self.tabs.setTabToolTip(index, path)

    def toggle_editor_view(self, visible: bool):
        """Maneja la visibilidad y habilita/deshabilita acciones de guardado."""
        self.tabs.setVisible(visible)
        
        # Solo mostramos el header si hay un archivo abierto y es deseado
        # Por ahora lo mantenemos oculto para evitar la barra estática doble
        self.ui.editorHeader.setVisible(False) 
        
        # Actualizar estado de botones
        self.btnSave.setEnabled(visible)
        self.btnSaveAs.setEnabled(visible)
        
        # Habilitar/Deshabilitar acciones del MENÚ (File > Save)
        # Accedemos a través de self.ui que pasaste al constructor
        self.ui.actionSave.setEnabled(visible)
        self.ui.actionSaveAs.setEnabled(visible)
        self.ui.actionClose.setEnabled(visible)

    def close_tab(self, index):
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.toggle_editor_view(False)
    
    def get_current_code(self):
        """Retorna el texto del editor que está visible actualmente."""
        current_widget = self.tabs.currentWidget()
        if current_widget:
            # Buscamos el mainEditor dentro del widget de la pestaña
            editor = current_widget.findChild(QPlainTextEdit, "mainEditor")
            return editor.toPlainText() if editor else ""
        return ""

    def get_current_path(self):
        """Retorna la ruta guardada en el ToolTip de la pestaña actual."""
        return self.tabs.tabToolTip(self.tabs.currentIndex())

    def set_name_tab(self, index, name):
        """Cambia el texto visible de la pestaña."""
        self.tabs.setTabText(index, name)