import re
from PyQt6.QtWidgets import (QStackedWidget, QTextEdit, QVBoxLayout, 
                             QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

class CompilerManager:
    def __init__(self, ui, terminal):
        self.ui = ui
        self.terminal = terminal
        
        # Mapa de colores para la tabla (mismos que en highlighter)
        self.type_colors = {
            "Palabra Reservada": "#C586C0",
            "Delimitador": "#D4D4D4",
            "Asignación": "#D4D4D4",
            "Op. Algebraico": "#D4D4D4",
            "Op. Relacional": "#D4D4D4",
            "Op. Lógico": "#D4D4D4",
            "Símbolo": "#D4D4D4",
            "Identificador": "#9CDCFE",
            "Número Entero": "#CE9178",
            "Número Real": "#CE9178",
            "Error": "#F44747"
        }
        
        # Panel lateral de resultados
        self.right_panel = QFrame()
        self.right_panel.setObjectName("rightAnalysisPanel")
        self.right_panel.setFixedWidth(400)
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
        self.lex_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.lex_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Salidas adicionales
        self.sin_out = self._create_terminal()
        self.sem_out = self._create_terminal()
        self.int_out = self._create_terminal()
        self.hash_out = self._create_terminal()
        
        self.result_stack.addWidget(self.lex_table)  # 0
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
        t.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border: none;")
        return t

    def toggle_panel(self, index, title):
        if self.right_panel.isVisible() and self.result_stack.currentIndex() == index:
            self.right_panel.setVisible(False)
        else:
            self.header.setText(title)
            self.result_stack.setCurrentIndex(index)
            self.right_panel.setVisible(True)
            self.ui.mainSplitter.setSizes([200, 400, 330, 70])

    def add_to_table(self, token, kind, line):
        row = self.lex_table.rowCount()
        self.lex_table.insertRow(row)
        
        col_token = QTableWidgetItem(token)
        col_kind = QTableWidgetItem(kind)
        col_line = QTableWidgetItem(str(line))
        
        # Centrar texto
        for item in [col_token, col_kind, col_line]:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Aplicar color al tipo según el diccionario
        color_hex = self.type_colors.get(kind, "#D4D4D4")  # gris por defecto
        col_kind.setForeground(QColor(color_hex))
        
        self.lex_table.setItem(row, 0, col_token)
        self.lex_table.setItem(row, 1, col_kind)
        self.lex_table.setItem(row, 2, col_line)

    def run_lexical_analysis(self, code):
        """Analizador léxico carácter por carácter con eliminación de espacios y saltos."""
        self.lex_table.setRowCount(0)
        self.terminal.clear_problems()
        self.toggle_panel(0, "LÉXICO")
        
        i = 0
        n = len(code)
        line_num = 1
        symbols = "+-*/%^=<>!&|(){},;"
        
        while i < n:
            ch = code[i]

            # 1. Ignorar espacios, tabs, saltos (excepto para contar líneas)
            if ch.isspace():
                if ch == '\n':
                    line_num += 1
                i += 1
                continue

            # 2. Comentarios de línea //
            if ch == '/' and i+1 < n and code[i+1] == '/':
                i += 2
                while i < n and code[i] != '\n':
                    i += 1
                continue

            # 3. Comentarios multilínea /* ... */
            if ch == '/' and i+1 < n and code[i+1] == '*':
                i += 2
                while i+1 < n and not (code[i] == '*' and code[i+1] == '/'):
                    if code[i] == '\n':
                        line_num += 1
                    i += 1
                i += 2  # saltar */
                continue

            # 4. Operadores compuestos con posible espacio/salto entre ellos
            compound_ops = {
                '=': '=', '+': '+', '-': '-', '<': '=', '>': '=', '!': '=', '&': '&', '|': '|'
            }
            if ch in compound_ops:
                second = compound_ops[ch]
                j = i + 1
                temp_line = line_num
                # Saltar espacios en blanco entre los dos caracteres
                while j < n and code[j].isspace():
                    if code[j] == '\n':
                        temp_line += 1
                    j += 1
                if j < n and code[j] == second:
                    lexeme = ch + second
                    self.add_to_table(lexeme, self.get_token_kind(lexeme), line_num)
                    i = j + 1
                    line_num = temp_line
                    continue

            # 5. Identificadores y palabras reservadas
            if ch.isalpha() or ch == '_':
                start = i
                while i < n and (code[i].isalnum() or code[i] == '_'):
                    i += 1
                lexeme = code[start:i]
                kind = self.get_token_kind(lexeme)
                self.add_to_table(lexeme, kind, line_num)
                continue

            # 6. Números (enteros o reales) y errores como "34.algo"
            if ch.isdigit():
                start = i
                dot_count = 0
                error_flag = False
                while i < n and not code[i].isspace() and code[i] not in symbols:
                    if code[i] == '.':
                        dot_count += 1
                    elif code[i].isalpha():
                        error_flag = True
                    i += 1
                lexeme = code[start:i]
                if error_flag or dot_count > 1 or lexeme.endswith('.'):
                    # Error léxico -> no se agrega a tabla, solo a terminal
                    self.terminal.log_problem("Léxico", f"Token inválido: '{lexeme}' en línea {line_num}")
                else:
                    kind = self.get_token_kind(lexeme)
                    self.add_to_table(lexeme, kind, line_num)
                continue

            # 7. Símbolos simples
            if ch in symbols:
                kind = self.get_token_kind(ch)
                self.add_to_table(ch, kind, line_num)
                i += 1
                continue

            # 8. Punto aislado (operador miembro, ej. en algunos lenguajes)
            if ch == '.':
                self.add_to_table('.', 'Símbolo', line_num)  # o "Operador"
                i += 1
                continue

            # 9. Carácter no reconocido
            self.terminal.log_problem("Léxico", f"Carácter no válido: '{ch}' en línea {line_num}")
            i += 1

        # Forzar refresco visual de la tabla
        self.lex_table.viewport().update()

    def get_token_kind(self, token):
        keywords = {"if", "else", "end", "do", "while", "switch", "case",
                    "int", "float", "main", "cin", "cout", "return", "then", "for"}
        ops_arit = {"+", "-", "*", "/", "%", "^", "++", "--"}
        ops_rel = {"<", ">", "<=", ">=", "==", "!="}
        ops_log = {"&&", "||", "!"}
        simbolos = {"(", ")", "{", "}", ","}
        
        if token in keywords:
            return "Palabra Reservada"
        if token == ";":
            return "Delimitador"
        if token == "=":
            return "Asignación"
        if token in ops_arit:
            return "Op. Algebraico"
        if token in ops_rel:
            return "Op. Relacional"
        if token in ops_log:
            return "Op. Lógico"
        if token in simbolos:
            return "Símbolo"
        if token == ".":
            return "Símbolo"   # O "Operador"
        if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', token):
            return "Identificador"
        if re.fullmatch(r'\d+', token):
            return "Número Entero"
        if re.fullmatch(r'\d+\.\d+', token):
            return "Número Real"
        return "Error"