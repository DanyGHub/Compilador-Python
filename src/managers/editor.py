# managers/editor.py
class EditorManager:
    def __init__(self, ui):
        self.ui = ui

    def toggle_editor_view(self, visible: bool):
        """Muestra u oculta los componentes del editor (texto y números)"""
        self.ui.editorSubContainer.setVisible(visible)
        self.ui.editorHeader.setVisible(visible)
        
    def set_content(self, text, filename="Untitled"):
        self.ui.mainCodeEditor.setPlainText(text)
        self.ui.lblCurrentFileName.setText(f"{filename}   X")