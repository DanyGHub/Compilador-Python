import re
from PyQt6.QtWidgets import (QStackedWidget, QTextEdit, QVBoxLayout, QLabel, 
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# ==========================================
# ESTRUCTURAS DEL ÁRBOL SINTÁCTICO (AST)
# ==========================================
class ASTNode:
    """Nodo genérico para el Árbol Sintáctico Abstracto."""
    def __init__(self, name, value=""):
        self.name = name
        self.value = value
        self.children = []

    def add(self, child):
        if child is not None:
            self.children.append(child)
        return self

# ==========================================
# ANALIZADOR SINTÁCTICO (DESCENSO RECURSIVO)
# ==========================================
class Parser:
    def __init__(self, tokens, terminal):
        self.tokens = [t for t in tokens if t['kind'] != 'Error']
        self.pos = 0
        self.terminal = terminal
        
        # Tokens de sincronización (Estilo Yacc/Bison) para evitar saltar bloques enteros
        self.sync_tokens = {
            ';', '}', '{', 'end', 'then', 'else', 
            'if', 'while', 'do', 'for', 'switch', 
            'int', 'float', 'real', 'main', 'return', 'cin', 'cout'
        }

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_lexeme=None, expected_kind=None):
        token = self.peek()
        if not token:
            return None
        
        match_lexeme = (expected_lexeme is None or token['lexeme'] == expected_lexeme)
        match_kind = (expected_kind is None or token['kind'] == expected_kind)
        
        if match_lexeme and match_kind:
            self.pos += 1
            return token
        return None

    def expect(self, expected_lexeme=None, expected_kind=None):
        token = self.consume(expected_lexeme, expected_kind)
        if token:
            return token
        
        curr = self.peek()
        line = curr['line'] if curr else "EOF"
        found = curr['lexeme'] if curr else "Fin de archivo"
        expected = expected_lexeme if expected_lexeme else expected_kind
        
        self.terminal.log_problem("Sintáctico", f"Se esperaba '{expected}' pero se encontró '{found}' en línea {line}")
        self.recover()
        return None

    def recover(self):
        """Panic Mode: Avanza hasta encontrar un punto seguro (sync token)."""
        while self.pos < len(self.tokens):
            token = self.peek()
            if token['lexeme'] in self.sync_tokens:
                break # Se detiene EXACTAMENTE en el sync token, sin consumirlo
            self.pos += 1

    # --- REGLAS DE LA GRAMÁTICA ---
    def parse(self):
        root = ASTNode("Programa")
        while self.pos < len(self.tokens):
            stmt = self.parse_statement()
            if stmt and stmt.name != "Sentencia Vacía":
                root.add(stmt)
            elif not stmt:
                # Si falló completamente y recover() no ayudó, forzamos el avance
                self.pos += 1 
        return root

    def parse_statement(self):
        token = self.peek()
        if not token: return None

        lexeme = token['lexeme']
        kind = token['kind']

        if lexeme == ';':
            self.consume()
            return ASTNode("Sentencia Vacía")
        elif lexeme == 'main':
            return self.parse_main()
        elif lexeme in ['int', 'float', 'real']:
            return self.parse_declaration()
        elif lexeme == 'if':
            return self.parse_if()
        elif lexeme == 'while':
            return self.parse_while()
        elif lexeme == 'do':
            return self.parse_do_while()
        elif lexeme == 'for':
            return self.parse_for()
        elif lexeme == 'switch':
            return self.parse_switch()
        elif lexeme in ['cin', 'cout']:
            return self.parse_io()
        elif lexeme == 'return':
            return self.parse_return()
        elif lexeme == '{':
            return self.parse_block()
        elif kind == 'Identificador' or lexeme in ['++', '--']:
            return self.parse_assignment_or_expr()
        else:
            self.terminal.log_problem("Sintáctico", f"Sentencia no válida iniciando con '{lexeme}' en línea {token['line']}")
            self.pos += 1 
            self.recover()
            return None

    def parse_main(self):
        node = ASTNode("Función Principal", "main")
        self.consume(expected_lexeme='main')
        
        if self.peek() and self.peek()['lexeme'] == '{':
            node.add(self.parse_block())
        else:
            while self.pos < len(self.tokens):
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía":
                    node.add(stmt)
        return node

    def parse_block(self):
        node = ASTNode("Bloque")
        if self.consume(expected_lexeme='{'):
            while self.peek() and self.peek()['lexeme'] != '}':
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía": node.add(stmt)
            self.expect(expected_lexeme='}')
        return node

    def parse_declaration(self):
        node = ASTNode("Declaración")
        tipo = self.consume() 
        node.add(ASTNode("Tipo", tipo['lexeme']))
        
        while True:
            ident = self.expect(expected_kind='Identificador')
            if ident:
                var_node = ASTNode("Variable", ident['lexeme'])
                if self.consume(expected_lexeme='='):
                    asig_node = ASTNode("Inicialización")
                    expr = self.parse_expression()
                    if expr: asig_node.add(expr)
                    var_node.add(asig_node)
                node.add(var_node)
            
            if self.peek() and self.peek()['lexeme'] == ',':
                self.consume(expected_lexeme=',')
            else:
                break
                
        self.expect(expected_lexeme=';')
        return node

    def parse_assignment_or_expr(self):
        node = ASTNode("Instrucción(es)")
        
        while True:
            if self.peek() and self.peek()['kind'] == 'Identificador':
                start_pos = self.pos
                ident = self.consume(expected_kind='Identificador')
                
                if self.consume(expected_lexeme='='):
                    asig_node = ASTNode("Asignación", ident['lexeme'])
                    expr = self.parse_expression()
                    if expr: asig_node.add(expr)
                    node.add(asig_node)
                else:
                    self.pos = start_pos
                    expr = self.parse_expression()
                    if expr: node.add(expr)
            else:
                expr = self.parse_expression()
                if expr: node.add(expr)
                
            if self.peek() and self.peek()['lexeme'] == ',':
                self.consume(expected_lexeme=',')
            else:
                break
                
        self.expect(expected_lexeme=';')
        if len(node.children) == 1:
            return node.children[0]
        return node

    def parse_if(self):
        node = ASTNode("If")
        self.consume(expected_lexeme='if')
        self.expect(expected_lexeme='(')
        expr = self.parse_expression()
        if expr: node.add(expr)
        self.expect(expected_lexeme=')')
        
        use_then_end = False
        if self.peek() and self.peek()['lexeme'] == 'then':
            self.consume()
            use_then_end = True
            
        true_body = ASTNode("Cuerpo True")
        
        if use_then_end:
            while self.peek() and self.peek()['lexeme'] not in ['else', 'end', '}']:
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía": true_body.add(stmt)
        else:
            stmt = self.parse_statement()
            if stmt and stmt.name != "Sentencia Vacía": true_body.add(stmt)
                
        if true_body.children:
            node.add(true_body)
            
        if self.peek() and self.peek()['lexeme'] == 'else':
            self.consume()
            false_body = ASTNode("Cuerpo False")
            if use_then_end:
                while self.peek() and self.peek()['lexeme'] not in ['end', '}']:
                    stmt = self.parse_statement()
                    if stmt and stmt.name != "Sentencia Vacía": false_body.add(stmt)
            else:
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía": false_body.add(stmt)
                    
            if false_body.children:
                node.add(false_body)
                
        if use_then_end:
            self.expect(expected_lexeme='end')
            if self.peek() and self.peek()['lexeme'] == ';': # Opcional punto y coma tras end
                self.consume()
                
        return node

    def parse_while(self):
        node = ASTNode("While")
        self.consume(expected_lexeme='while')
        self.expect(expected_lexeme='(')
        expr = self.parse_expression()
        if expr: node.add(expr)
        self.expect(expected_lexeme=')')
        
        body = self.parse_statement()
        if body and body.name != "Sentencia Vacía": 
            node.add(ASTNode("Cuerpo").add(body))
        return node

    def parse_do_while(self):
        node = ASTNode("Do-While")
        self.consume(expected_lexeme='do')
        
        body = ASTNode("Cuerpo")
        if self.peek() and self.peek()['lexeme'] == '{':
            body.add(self.parse_block())
        else:
            while self.peek() and self.peek()['lexeme'] != 'while':
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía": body.add(stmt)
                    
        if body.children: node.add(body)
            
        self.expect(expected_lexeme='while')
        self.expect(expected_lexeme='(')
        expr = self.parse_expression()
        if expr: node.add(expr)
        self.expect(expected_lexeme=')')
        self.expect(expected_lexeme=';')
        return node

    def parse_for(self):
        node = ASTNode("For")
        self.consume(expected_lexeme='for')
        self.expect(expected_lexeme='(')
        
        init = self.parse_statement()
        if init and init.name != "Sentencia Vacía": node.add(ASTNode("Inicialización").add(init))
        
        cond = self.parse_expression()
        if cond: node.add(ASTNode("Condición").add(cond))
        self.expect(expected_lexeme=';')
        
        inc = self.parse_expression()
        if inc: node.add(ASTNode("Incremento").add(inc))
        self.expect(expected_lexeme=')')
        
        body = self.parse_statement()
        if body and body.name != "Sentencia Vacía": node.add(ASTNode("Cuerpo").add(body))
        return node

    def parse_switch(self):
        node = ASTNode("Switch")
        self.consume(expected_lexeme='switch')
        self.expect(expected_lexeme='(')
        expr = self.parse_expression()
        if expr: node.add(expr)
        self.expect(expected_lexeme=')')
        self.expect(expected_lexeme='{')
        
        while self.peek() and self.peek()['lexeme'] == 'case':
            case_node = ASTNode("Case")
            self.consume(expected_lexeme='case')
            val = self.consume() 
            if val: case_node.value = val['lexeme']
            self.expect(expected_lexeme=':')
            
            statements = ASTNode("Instrucciones")
            while self.peek() and self.peek()['lexeme'] not in ['case', '}']:
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía": statements.add(stmt)
            if statements.children: case_node.add(statements)
            node.add(case_node)
            
        self.expect(expected_lexeme='}')
        return node

    def parse_io(self):
        token = self.consume()
        node = ASTNode("Entrada" if token['lexeme'] == 'cin' else "Salida")
        if token['lexeme'] == 'cin':
            self.expect(expected_lexeme='>')
            self.expect(expected_lexeme='>')
        else:
            self.expect(expected_lexeme='<')
            self.expect(expected_lexeme='<')
            
        expr = self.parse_expression()
        if expr: node.add(expr)
        self.expect(expected_lexeme=';')
        return node

    def parse_return(self):
        node = ASTNode("Return")
        self.consume(expected_lexeme='return')
        expr = self.parse_expression()
        if expr: node.add(expr)
        self.expect(expected_lexeme=';')
        return node

    # --- EXPRESIONES Y PRECEDENCIA ---
    def parse_expression(self):
        return self.parse_logical()

    def parse_logical(self):
        node = self.parse_relational()
        while self.peek() and self.peek()['lexeme'] in ['&&', '||']:
            op = self.consume()
            new_node = ASTNode("Op Lógico", op['lexeme'])
            if node: new_node.add(node)
            
            right = self.parse_relational()
            if right: 
                new_node.add(right)
            else:
                self.terminal.log_problem("Sintáctico", f"Falta operando derecho para '{op['lexeme']}'")
            node = new_node
        return node

    def parse_relational(self):
        node = self.parse_algebraic()
        while self.peek() and self.peek()['lexeme'] in ['<', '>', '<=', '>=', '==', '!=']:
            op = self.consume()
            new_node = ASTNode("Op Relacional", op['lexeme'])
            if node: new_node.add(node)
            right = self.parse_algebraic()
            if right: new_node.add(right)
            node = new_node
        return node

    def parse_algebraic(self):
        node = self.parse_term()
        while self.peek() and self.peek()['lexeme'] in ['+', '-']:
            op = self.consume()
            new_node = ASTNode("Op Aritmético", op['lexeme'])
            if node: new_node.add(node)
            right = self.parse_term()
            if right: new_node.add(right)
            node = new_node
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek() and self.peek()['lexeme'] in ['*', '/', '%', '^']:
            op = self.consume()
            new_node = ASTNode("Op Multiplicativo", op['lexeme'])
            if node: new_node.add(node)
            right = self.parse_factor()
            if right: new_node.add(right)
            node = new_node
        return node

    def parse_factor(self):
        token = self.peek()
        if not token: return None
        
        if self.consume(expected_lexeme='('):
            node = self.parse_expression()
            self.expect(expected_lexeme=')')
            return node
        elif token['kind'] in ['Número Entero', 'Número Real']:
            t = self.consume()
            return ASTNode("Número", t['lexeme'])
        elif token['kind'] == 'Identificador':
            t = self.consume()
            return ASTNode("Identificador", t['lexeme'])
        elif token['lexeme'] == '!':
            self.consume()
            node = ASTNode("Negación Lógica", "!")
            node.add(self.parse_factor())
            return node
        elif token['lexeme'] in ['++', '--']:
            op = self.consume()
            ident = self.expect(expected_kind='Identificador')
            node = ASTNode("Operador Unario", op['lexeme'])
            if ident: node.add(ASTNode("Identificador", ident['lexeme']))
            return node
        else:
            self.terminal.log_problem("Sintáctico", f"Expresión inválida en '{token['lexeme']}' (línea {token['line']})")
            self.recover()
            return None


# ==========================================
# GESTOR DEL COMPILADOR UI
# ==========================================
class CompilerManager:
    def __init__(self, ui, terminal):
        self.ui = ui
        self.terminal = terminal
        self.tokens_list = []
        
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
        
        # 0. Tabla Léxica
        self.lex_table = QTableWidget()
        self.lex_table.setColumnCount(3)
        self.lex_table.setHorizontalHeaderLabels(["Token", "Tipo", "Línea"])
        self.lex_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.lex_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 1. Salida Sintáctica (Árbol AST)
        self.sin_out = QTreeWidget()
        self.sin_out.setColumnCount(1)
        self.sin_out.setHeaderLabels(["Árbol Sintáctico Abstracto (AST)"])
        self.sin_out.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.sin_out.header().setStretchLastSection(False)
        self.sin_out.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.sin_out.setStyleSheet("""
            QTreeWidget { background-color: #1e1e1e; color: #d4d4d4; border: none; font-family: 'Segoe UI'; font-size: 11pt; }
            QTreeWidget::item:selected { background-color: #37373d; }
            QHeaderView::section { background-color: #252526; color: #d4d4d4; padding: 4px; border: 1px solid #3e3e42; }
        """)
        
        self.sem_out = self._create_terminal()
        self.int_out = self._create_terminal()
        self.hash_out = self._create_terminal()
        
        self.result_stack.addWidget(self.lex_table)
        self.result_stack.addWidget(self.sin_out)
        self.result_stack.addWidget(self.sem_out)
        self.result_stack.addWidget(self.int_out)
        self.result_stack.addWidget(self.hash_out)
        
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
        self.tokens_list.append({"lexeme": token, "kind": kind, "line": line})
        row = self.lex_table.rowCount()
        self.lex_table.insertRow(row)
        
        col_token = QTableWidgetItem(token)
        col_kind = QTableWidgetItem(kind)
        col_line = QTableWidgetItem(str(line))
        
        for item in [col_token, col_kind, col_line]:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        color_hex = self.type_colors.get(kind, "#D4D4D4")
        col_kind.setForeground(QColor(color_hex))
        
        self.lex_table.setItem(row, 0, col_token)
        self.lex_table.setItem(row, 1, col_kind)
        self.lex_table.setItem(row, 2, col_line)

    def get_token_kind(self, token):
        keywords = {"if", "else", "end", "do", "while", "switch", "case",
                    "int", "float", "real", "main", "cin", "cout", "return", "then", "for"}
        
        if token in keywords: return "Palabra Reservada"
        if token == ";": return "Delimitador"
        if token == "=": return "Asignación"
        if token in {"+", "-", "*", "/", "%", "^", "++", "--"}: return "Op. Algebraico"
        if token in {"<", ">", "<=", ">=", "==", "!="}: return "Op. Relacional"
        if token in {"&&", "||", "!"}: return "Op. Lógico"
        if token in {"(", ")", "{", "}", ","}: return "Símbolo"
        
        if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', token): return "Identificador"
        if re.fullmatch(r'\d+', token): return "Número Entero"
        if re.fullmatch(r'\d+\.\d+', token): return "Número Real"
        return "Error"

    def run_lexical_analysis(self, code):
        self.lex_table.setRowCount(0)
        self.tokens_list = []
        self.terminal.clear_problems()
        self.toggle_panel(0, "LÉXICO")
        
        i = 0
        n = len(code)
        line_num = 1
        symbols = "+-*/%^=<>!&|(){},;"
        
        while i < n:
            ch = code[i]
            if ch.isspace():
                if ch == '\n': line_num += 1
                i += 1
                continue

            if ch == '/' and i+1 < n:
                if code[i+1] == '/':
                    i += 2
                    while i < n and code[i] != '\n': i += 1
                    continue
                if code[i+1] == '*':
                    i += 2
                    while i+1 < n and not (code[i] == '*' and code[i+1] == '/'):
                        if code[i] == '\n': line_num += 1
                        i += 1
                    i += 2
                    continue

            compound_ops = {'=': '=', '+': '+', '-': '-', '<': '=', '>': '=', '!': '=', '&': '&', '|': '|'}
            if ch in compound_ops:
                second = compound_ops[ch]
                j = i + 1
                temp_line = line_num
                while j < n and code[j].isspace():
                    if code[j] == '\n': temp_line += 1
                    j += 1
                if j < n and code[j] == second:
                    lexeme = ch + second
                    self.add_to_table(lexeme, self.get_token_kind(lexeme), line_num)
                    i, line_num = j + 1, temp_line
                    continue

            if ch.isalpha() or ch == '_':
                start = i
                while i < n and (code[i].isalnum() or code[i] == '_'):
                    i += 1
                lexeme = code[start:i]
                self.add_to_table(lexeme, self.get_token_kind(lexeme), line_num)
                continue

            if ch.isdigit():
                start = i
                lexeme = ""
                while i < n and code[i].isdigit():
                    lexeme += code[i]
                    i += 1
                
                if i < n and code[i] == '.':
                    if i + 1 < n and code[i+1].isdigit():
                        lexeme += "."
                        i += 1
                        while i < n and code[i].isdigit():
                            lexeme += code[i]
                            i += 1
                        self.add_to_table(lexeme, "Número Real", line_num)
                    else:
                        lexeme += "."
                        i += 1
                        self.add_to_table(lexeme, "Error", line_num)
                        self.terminal.log_problem("Léxico", f"Token inválido: '{lexeme}' en línea {line_num}")
                else:
                    self.add_to_table(lexeme, "Número Entero", line_num)
                continue

            if ch in symbols:
                self.add_to_table(ch, self.get_token_kind(ch), line_num)
                i += 1
                continue

            if ch == '.':
                self.add_to_table(".", "Error", line_num)
                self.terminal.log_problem("Léxico", f"Carácter no válido: '.' en línea {line_num}")
                i += 1
                continue

            self.add_to_table(ch, "Error", line_num)
            self.terminal.log_problem("Léxico", f"Carácter no válido: '{ch}' en línea {line_num}")
            i += 1

        self.lex_table.viewport().update()

    def run_syntactic_analysis(self):
        self.sin_out.clear()
        
        if not self.tokens_list:
            QTreeWidgetItem(self.sin_out, ["No hay código válido para analizar."])
            return

        parser = Parser(self.tokens_list, self.terminal)
        ast_root = parser.parse()

        def populate_tree(parent_widget, node):
            display_text = node.name
            if node.value:
                display_text += f": {node.value}"
            
            item = QTreeWidgetItem(parent_widget, [display_text])
            
            if node.name in ["Programa", "Bloque", "Cuerpo", "Cuerpo True", "Cuerpo False"]:
                item.setForeground(0, QColor("#DCDCAA"))
            elif node.name in ["If", "While", "Do-While", "For", "Switch", "Case", "Función Principal"]:
                item.setForeground(0, QColor("#C586C0"))
            elif node.name == "Declaración":
                item.setForeground(0, QColor("#569CD6"))
            elif node.name == "Error":
                item.setForeground(0, QColor("#F44747"))
                
            for child in node.children:
                populate_tree(item, child)
            
            item.setExpanded(True)

        populate_tree(self.sin_out.invisibleRootItem(), ast_root)
        self.toggle_panel(1, "SINTÁCTICO")