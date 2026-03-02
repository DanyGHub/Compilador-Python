# managers/editor.py
from PyQt6.QtWidgets import (QTabWidget, QVBoxLayout, QHBoxLayout, 
                             QPlainTextEdit, QWidget, QTextEdit, QLabel)
from PyQt6.QtGui import QFont, QTextCursor, QTextFormat, QColor, QTextCharFormat
from PyQt6.QtCore import Qt

class EditorManager:
    def __init__(self, ui):
        self.ui = ui
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.tabs.tabCloseRequested.connect(self.close_tab)

        if not self.ui.editorSubContainer.layout():
            layout = QVBoxLayout(self.ui.editorSubContainer)
            layout.setContentsMargins(0, 0, 0, 0)
            self.ui.editorSubContainer.setLayout(layout)
        
        self.ui.editorSubContainer.layout().addWidget(self.tabs)

        self.ui.mainCodeEditor.hide()
        self.ui.lineNumberArea.hide()
        self.ui.editorHeader.hide()

    def set_content(self, text, filename="Untitled"):
        # 1. Contenedor principal de la pestaña (Vertical para incluir la barra de estado abajo)
        tab_widget = QWidget()
        tab_widget.setObjectName("tabContainer")
        tab_main_layout = QVBoxLayout(tab_widget)
        tab_main_layout.setContentsMargins(0, 0, 0, 0)
        tab_main_layout.setSpacing(0)

        # 2. Contenedor para Números + Código (Horizontal)
        editor_layout = QHBoxLayout()
        editor_layout.setSpacing(0)

        # --- ÁREA DE NUMERACIÓN ---
        line_numbers = QPlainTextEdit()
        line_numbers.setProperty("lineNumbers", "true") 
        line_numbers.setFixedWidth(50)
        line_numbers.setFont(QFont("Courier New", 10))
        line_numbers.setReadOnly(True)
        line_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        line_numbers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # --- EDITOR DE CÓDIGO ---
        code_editor = QPlainTextEdit()
        code_editor.setProperty("codeEditor", "true") 
        code_editor.setPlainText(text)
        code_editor.setFont(QFont("Courier New", 10))
        code_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # --- BARRA DE ESTADO (Línea y Columna) ---
        status_bar = QLabel(" Línea 1, Columna 1")
        status_bar.setFixedHeight(25)
        status_bar.setStyleSheet("""
            background-color: #353535; 
            color: white; 
            font-family: 'Segoe UI'; 
            font-size: 11px;
            padding-left: 10px;
            border-top: 1px solid #000;
        """)

        def update_ui_editor():
            # Actualizar números de línea
            line_count = code_editor.document().blockCount()
            lines_text = "\n".join(str(i + 1) for i in range(line_count))
            line_numbers.blockSignals(True)
            line_numbers.setPlainText(lines_text)
            line_numbers.blockSignals(False)

            # Obtener posición del cursor
            cursor = code_editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            status_bar.setText(f" Línea {line}, Columna {col}")

            # Resaltados (ExtraSelections)
            selections_editor = []
            selections_numbers = []

            # Fondo línea editor
            sel_bg = QTextEdit.ExtraSelection()
            sel_bg.format.setBackground(QColor("#2c2c2c"))
            sel_bg.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel_bg.cursor = cursor
            sel_bg.cursor.clearSelection()
            selections_editor.append(sel_bg)

            # Negrita en numeración
            sel_num = QTextEdit.ExtraSelection()
            sel_num.format.setFontWeight(QFont.Weight.Bold)
            sel_num.format.setForeground(QColor("#ffffff"))
            num_cursor = QTextCursor(line_numbers.document().findBlockByNumber(line - 1))
            sel_num.cursor = num_cursor
            selections_numbers.append(sel_num)

            code_editor.setExtraSelections(selections_editor)
            line_numbers.setExtraSelections(selections_numbers)

            # Sincronizar scroll
            line_numbers.verticalScrollBar().setValue(code_editor.verticalScrollBar().value())

        # Conexiones
        code_editor.textChanged.connect(update_ui_editor)
        code_editor.cursorPositionChanged.connect(update_ui_editor)
        code_editor.verticalScrollBar().valueChanged.connect(
            lambda v: line_numbers.verticalScrollBar().setValue(v)
        )

        # Armar la interfaz
        editor_layout.addWidget(line_numbers)
        editor_layout.addWidget(code_editor)
        
        tab_main_layout.addLayout(editor_layout)
        tab_main_layout.addWidget(status_bar) # Añadimos la barra abajo

        # Inicialización
        update_ui_editor()

        index = self.tabs.addTab(tab_widget, filename)
        self.tabs.setCurrentIndex(index)
        
        tab_widget.style().unpolish(tab_widget)
        tab_widget.style().polish(tab_widget)

    def toggle_editor_view(self, visible: bool):
        self.ui.editorSubContainer.setVisible(visible)

    def close_tab(self, index):
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.toggle_editor_view(False)