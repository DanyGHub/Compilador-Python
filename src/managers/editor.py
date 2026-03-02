# managers/editor.py
from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QPlainTextEdit
from PyQt6.QtGui import QFont

class EditorManager:
    def __init__(self, ui):
        self.ui = ui
        # sistema de pestañas dinámico
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.tabs.tabCloseRequested.connect(self.close_tab)

        # Inyeccion del QTabWidget en el contenedor existente (editorSubContainer)
        # Si el contenedor no tiene layout, le asignamos uno vertical
        if not self.ui.editorSubContainer.layout():
            layout = QVBoxLayout(self.ui.editorSubContainer)
            layout.setContentsMargins(0, 0, 0, 0)
            self.ui.editorSubContainer.setLayout(layout)
        
        self.ui.editorSubContainer.layout().addWidget(self.tabs)

        # Quitando los elementos de ejemplo
        self.ui.mainCodeEditor.hide()
        self.ui.editorHeader.hide()

    def toggle_editor_view(self, visible: bool):
        """Muestra u oculta el contenedor principal del editor"""
        self.ui.editorSubContainer.setVisible(visible)
        
    def set_content(self, text, filename="Untitled"):
        # Creando un nuevo editor para la nueva pestaña
        new_editor = QPlainTextEdit()
        new_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        new_editor.setPlainText(text)
        new_editor.setFont(QFont("Courier New", 10))
        index = self.tabs.addTab(new_editor, filename)
        self.tabs.setCurrentIndex(index)

    def close_tab(self, index):
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.toggle_editor_view(False)