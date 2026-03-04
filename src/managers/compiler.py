# managers/compiler.py
from PyQt6.QtWidgets import QStackedWidget, QTextEdit, QVBoxLayout, QWidget, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class CompilerManager:
    def __init__(self, ui, terminal):
        self.ui = ui
        self.terminal = terminal
        
        # 1. Creamos el contenedor lateral
        self.right_panel = QFrame()
        self.right_panel.setObjectName("rightAnalysisPanel")
        self.right_panel.setFixedWidth(250)
        self.right_panel.setMaximumWidth(400)
        self.right_panel.setMinimumWidth(200)
        
        layout = QVBoxLayout(self.right_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 2. Encabezado del panel
        self.header = QLabel("ANÁLISIS")
        self.header.setObjectName("analysisHeader")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header.setFixedHeight(35)
        layout.addWidget(self.header)

        # 3. Stack de terminales
        self.result_stack = QStackedWidget()
        # ... (aquí creas tus terminales lex_out, sin_out, etc. como ya tenías)
        layout.addWidget(self.result_stack)

        # --- LA CORRECCIÓN CLAVE ---
        # Insertamos el panel en el mainSplitter (Horizontal) 
        # para que aparezca a la derecha del editor y a la izquierda de los botones.
        # El índice 2 lo coloca justo antes de la barra de acceso derecha (rightAccessBar)
        self.ui.mainSplitter.insertWidget(2, self.right_panel)
        
        # Ajustamos el estiramiento para que el editor sea el que mande en el espacio
        self.ui.mainSplitter.setStretchFactor(1, 1) 
        self.ui.mainSplitter.setStretchFactor(2, 1)
        
        self.ui.mainSplitter.setStretchFactor(3, 0)
        self.right_panel.setVisible(False)

    def _create_terminal(self):
        t = QTextEdit()
        t.setReadOnly(True)
        t.setObjectName("subTerminal")
        t.setFont(QFont("Consolas", 10))
        return t

    def toggle_panel(self, index, title):
        """Maneja la apertura/cierre y el cambio de título."""
        if self.right_panel.isVisible() and self.result_stack.currentIndex() == index:
            self.right_panel.setVisible(False)
        else:
            self.header.setText(title)
            self.result_stack.setCurrentIndex(index)
            self.right_panel.setVisible(True)