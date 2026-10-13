from PyQt6.QtWidgets import (QTabWidget, QVBoxLayout, QHBoxLayout, 
                             QPlainTextEdit, QWidget, QTextEdit, QLabel, 
                             QFrame, QPushButton)
from PyQt6.QtGui import QFont, QTextCursor, QTextFormat, QColor
from PyQt6.QtCore import Qt
from managers.highlighter import CustomHighlighter

class EditorManager:
    def __init__(self, ui):
        self.ui = ui
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.tabs.tabCloseRequested.connect(self.close_tab)

        if not self.ui.editorContainer.layout():
            layout = QVBoxLayout(self.ui.editorContainer)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.ui.editorContainer.setLayout(layout)

        self.ui.editorContainer.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setup_toolbar()
        self.ui.editorContainer.layout().insertWidget(0, self.toolbarFrame)
        self.ui.editorContainer.layout().addWidget(self.tabs)

    def setup_toolbar(self):
        self.toolbarFrame = QFrame()
        self.toolbarFrame.setObjectName("toolbarFrame")
        self.toolbarFrame.setFixedHeight(40)
        
        layout = QHBoxLayout(self.toolbarFrame)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        self.btnNew = QPushButton("📄")
        self.btnOpen = QPushButton("📂")
        self.btnOpenDir = QPushButton("📁")
        self.btnSave = QPushButton("💾")
        self.btnSaveAs = QPushButton("📑")

        self.btnNew.setToolTip("New File (Ctrl+N)")
        self.btnOpen.setToolTip("Open File (Ctrl+O)")
        self.btnOpenDir.setToolTip("Open Directory (Ctrl+Shift+O)")
        self.btnSave.setToolTip("Save (Ctrl+S)")
        self.btnSaveAs.setToolTip("Save As... (Ctrl+Shift+S)")
        
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background-color: #555;")

        self.btnLex = QPushButton("LEX")
        self.btnSin = QPushButton("SIN")
        self.btnSem = QPushButton("SEM")
        self.btnHash = QPushButton("HASH")
        self.btnInt = QPushButton("INT")
        self.btnCompile = QPushButton("⚙️")

        self.btnLex.setToolTip("Lexical Analysis")
        self.btnSin.setToolTip("Syntactic Analysis")
        self.btnSem.setToolTip("Semantic Analysis")
        self.btnHash.setToolTip("Tabla Hash / Tabla de Símbolos")
        self.btnInt.setToolTip("Intermediate Code")
        self.btnCompile.setToolTip("Compile")
        
        for btn in [self.btnNew, self.btnOpen, self.btnOpenDir, self.btnSave, self.btnSaveAs]:
            btn.setFixedSize(28, 28)
            layout.addWidget(btn)
        
        layout.addWidget(sep)
        
        for btn in [self.btnLex, self.btnSin, self.btnSem, self.btnHash, self.btnInt, self.btnCompile]:
            btn.setFixedSize(38, 28)
            layout.addWidget(btn)

        layout.addStretch()

    def set_content(self, text, filename="Untitled", path=None):
        tab_widget = QWidget()
        tab_widget.setObjectName("tabContainer")
        tab_main_layout = QVBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(0, 0, 0, 0)
        tab_main_layout.setSpacing(0)

        editor_layout = QHBoxLayout()
        line_numbers = QPlainTextEdit()
        line_numbers.setProperty("lineNumbers", True)
        line_numbers.setFixedWidth(50)
        line_numbers.setReadOnly(True)
        line_numbers.setFont(QFont("Courier New", 10))
        line_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        code_editor = QPlainTextEdit()
        code_editor.setObjectName("mainEditor")
        code_editor.setProperty("codeEditor", True)
        code_editor.setStyleSheet("background-color: #353535; color: #d4d4d4;")
        code_editor.highlighter = CustomHighlighter(code_editor.document())
        code_editor.setPlainText(text)
        code_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        code_editor.setFont(QFont("Courier New", 10))

        status_bar = QLabel(" Línea 1, Columna 1")
        status_bar.setFixedHeight(25)
        status_bar.setObjectName("editorStatusBar")

        # managers/editor.py

        def update_ui_editor():
            line_count = code_editor.document().blockCount()
            line_numbers.setPlainText("\n".join(str(i + 1) for i in range(line_count)))
            cursor = code_editor.textCursor()
            status_bar.setText(f" Línea {cursor.blockNumber() + 1}, Columna {cursor.columnNumber() + 1}")
            
            # --- MODIFICAR ESTA SECCIÓN ---
            sel = QTextEdit.ExtraSelection()
            
            # Usamos un gris muy claro (puedes probar #F0F0F0 o #E8E8E8)
            line_highlight_color = QColor("#464646") 
            
            sel.format.setBackground(line_highlight_color)
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = cursor
            sel.cursor.clearSelection()
            # ------------------------------
            
            # Negrita en el número de línea (opcional: cambia a un color oscuro para que se vea)
            sel_num = QTextEdit.ExtraSelection()
            sel_num.format.setFontWeight(QFont.Weight.Bold)
            sel_num.format.setForeground(QColor("#000000")) # Texto negro para el número
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

        index = self.tabs.addTab(tab_widget, filename)
        self.tabs.setCurrentIndex(index)
        if path: self.tabs.setTabToolTip(index, path)
        update_ui_editor()

    def toggle_editor_view(self, visible: bool):
        self.tabs.setVisible(visible)
        self.btnSave.setEnabled(visible)
        self.btnSaveAs.setEnabled(visible)
        self.ui.actionSave.setEnabled(visible)
        self.ui.actionSaveAs.setEnabled(visible)
        self.ui.actionClose.setEnabled(visible)

    def close_tab(self, index):
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.toggle_editor_view(False)

    def get_current_code(self):
        current_widget = self.tabs.currentWidget()
        if current_widget:
            editor = current_widget.findChild(QPlainTextEdit, "mainEditor")
            return editor.toPlainText() if editor else ""
        return ""

    def get_current_path(self):
        return self.tabs.tabToolTip(self.tabs.currentIndex())

    def set_name_tab(self, index, name):
        self.tabs.setTabText(index, name)