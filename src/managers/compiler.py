import re
from PyQt6.QtWidgets import (QStackedWidget, QTextEdit, QVBoxLayout, 
                             QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

class CompilerManager:
    def __init__(self, ui, terminal):
        self.ui = ui
        self.terminal = terminal
        
        # Panel lateral de resultados
        self.right_panel = QFrame()
        self.right_panel.setObjectName("rightAnalysisPanel")
        self.right_panel.setFixedWidth(330)
        
        layout = QVBoxLayout(self.right_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = QLabel("ANÁLISIS")
        self.header.setObjectName("analysisHeader")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header.setFixedHeight(35)
        layout.addWidget(self.header)

        self.result_stack = QStackedWidget()
        
        # Tabla Léxica
        self.lex_table = QTableWidget()
        self.lex_table.setColumnCount(3)
        self.lex_table.setHorizontalHeaderLabels(["Token", "Tipo", "Línea"])
        
        header = self.lex_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed) 
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.lex_table.setColumnWidth(0, 100)
        self.lex_table.setColumnWidth(1, 120)
        self.lex_table.setColumnWidth(2, 100)
        
        # Áreas de texto para otras fases
        self.sin_out = self._create_terminal()
        self.sem_out = self._create_terminal()
        self.int_out = self._create_terminal()
        self.hash_out = self._create_terminal()
        
        self.result_stack.addWidget(self.lex_table) # 0
        self.result_stack.addWidget(self.sin_out)    # 1
        self.result_stack.addWidget(self.sem_out)    # 2
        self.result_stack.addWidget(self.int_out)    # 3
        self.result_stack.addWidget(self.hash_out)   # 4
        
        layout.addWidget(self.result_stack)
        self.ui.mainSplitter.insertWidget(2, self.right_panel)
        self.right_panel.setVisible(False)

    def _create_terminal(self):
        t = QTextEdit()
        t.setReadOnly(True)
        t.setFont(QFont("Consolas", 10))
        return t

    def toggle_panel(self, index, title):
        if self.right_panel.isVisible() and self.result_stack.currentIndex() == index:
            self.right_panel.setVisible(False)
        else:
            self.header.setText(title)
            self.result_stack.setCurrentIndex(index)
            self.right_panel.setVisible(True)

    def run_lexical_analysis(self, code):
        self.lex_table.setRowCount(0)
        lines = code.split('\n')
        
        # Patrón de error unificado (sincronizado con el highlighter)
        error_pattern = r'^(\d+(\.\d+){2,}|\d+\.(?!\d)|(?<!\d)\.\d+|[^\s\w\+\-\*/%\^=<>!&\|\(\)\{\},;])$'

        for i, line in enumerate(lines):
            tokens = self.tokenize_line(line) 
            
            for value, kind in tokens:
                # Prioridad de detección de error léxico
                if re.match(error_pattern, value):
                    kind = "Error"
                
                row = self.lex_table.rowCount()
                self.lex_table.insertRow(row)
                
                item_value = QTableWidgetItem(value)
                item_kind = QTableWidgetItem(kind)
                item_line = QTableWidgetItem(str(i + 1))
                
                center = Qt.AlignmentFlag.AlignCenter
                item_value.setTextAlignment(center)
                item_kind.setTextAlignment(center)
                item_line.setTextAlignment(center)
                
                if kind == "Error":
                    item_kind.setForeground(QColor("#F44747"))
                    item_kind.setFont(QFont("Segoe UI", weight=QFont.Weight.Bold))
                elif kind == "Palabra Reservada":
                    item_kind.setForeground(QColor("#C586C0"))

                self.lex_table.setItem(row, 0, item_value)
                self.lex_table.setItem(row, 1, item_kind)
                self.lex_table.setItem(row, 2, item_line)
                
    def tokenize_line(self, line):
        # El pattern debe capturar tokens compuestos antes que simples (ej: == antes que =)
        pattern = r'\d+(\.\d+)+|\d+\.|\.\d+|//.*|/\*.*?\*/|[a-zA-Z_][a-zA-Z0-9_]*|\d+(\.\d+)?|==|<=|>=|!=|&&|\|\||\+\+|\-\-|[\+\-\*/%\^=<>!&\|\(\)\{\},;]|\S'
        matches = re.finditer(pattern, line)
        return [(m.group(), self.get_token_kind(m.group())) for m in matches]

    def get_token_kind(self, token):
        """Diccionario y lógica de categorización de tokens."""
        
        # 1. Definición de diccionarios y conjuntos
        keywords = {
            "if", "else", "end", "do", "while", "switch", "case",
            "int", "float", "main", "cin", "cout", "return", "then"
        }
        
        ops_algebraicos = {"+", "-", "*", "/", "%", "^", "++", "--"}
        ops_relacionales = {"<", ">", "<=", ">=", "==", "!="}
        ops_logicos = {"&&", "||", "!"}
        simbolos = {"(", ")", "{", "}", ",", ";"}

        # 2. Lógica de clasificación
        if token in keywords:
            return "Palabra Reservada"
        
        if token == "=":
            return "Asignación"
            
        if token in ops_algebraicos:
            return "Op. Algebraico"
            
        if token in ops_relacionales:
            return "Op. Relacional"
            
        if token in ops_logicos:
            return "Op. Lógico"
            
        if token in simbolos:
            return "Símbolo"
            
        # Números (Entero o Real)
        if re.match(r'^\d+$', token):
            return "Número"
        if re.match(r'^\d+\.\d+$', token):
            return "Número Real"
            
        # Identificadores
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', token):
            return "Identificador"
            
        # Comentarios (si el tokenizador los pasa)
        if token.startswith("//") or token.startswith("/*"):
            return "Comentario"
            
        return "Error"