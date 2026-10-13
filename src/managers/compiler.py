import re
from PyQt6.QtWidgets import (QStackedWidget, QTextEdit, QVBoxLayout, QLabel, 
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from managers.semantic import SemanticAnalyzer

# ==========================================
# ESTRUCTURAS DEL ÁRBOL SINTÁCTICO (AST)
# ==========================================
class ASTNode:
    """Nodo genérico para el Árbol Sintáctico Abstracto (soporta anotaciones semánticas)."""
    def __init__(self, name, value="", line=None, col=None):
        self.name = name
        self.value = value
        self.line = line
        self.col = col
        self.children = []
        # Atributos para el Árbol Sintáctico Anotado (Fase 3: Análisis Semántico)
        self.dtype = None
        self.inherited_dtype = None
        self.val = None
        self.scope = None
        self.memloc = None
        self.conversion = None
        self.sem_error = None

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
        
        # Sincronización robusta: Añadimos ')' para evitar que errores en condiciones destruyan bloques if/while
        self.sync_tokens = {
            ';', '}', '{', 'end', 'then', 'else', ')',
            'if', 'while', 'do', 'until', 'for', 'switch', 'case', 'default', 'break',
            'int', 'float', 'real', 'bool', 'main', 'return', 'cin', 'cout'
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
                break
            self.pos += 1

    def _is_closing_while(self):
        """
        Lookahead (Visión anticipada): Determina si el token 'while' actual es el 
        cierre definitivo de un ciclo do-while o el comienzo de un ciclo while anidado.
        Busca la estructura de cierre: while(...) ;
        """
        if not self.peek() or self.peek()['lexeme'] != 'while':
            return False
            
        temp_pos = self.pos + 1
        if temp_pos < len(self.tokens) and self.tokens[temp_pos]['lexeme'] == '(':
            paren_count = 1
            temp_pos += 1
            while temp_pos < len(self.tokens) and paren_count > 0:
                t = self.tokens[temp_pos]['lexeme']
                if t == '(': paren_count += 1
                elif t == ')': paren_count -= 1
                temp_pos += 1
            
            # Si inmediatamente después de los paréntesis hay un punto y coma, es el cierre.
            if temp_pos < len(self.tokens) and self.tokens[temp_pos]['lexeme'] == ';':
                return True
        return False

    # --- REGLAS DE LA GRAMÁTICA ---
    def parse(self):
        first = self.peek()
        root = ASTNode("Programa", line=first['line'] if first else 1, col=1)
        while self.pos < len(self.tokens):
            stmt = self.parse_statement()
            if stmt and stmt.name != "Sentencia Vacía":
                root.add(stmt)
            elif not stmt:
                self.pos += 1 
        return root

    def parse_statement(self):
        token = self.peek()
        if not token: return None

        lexeme = token['lexeme']
        kind = token['kind']

        if lexeme == ';':
            t = self.consume()
            return ASTNode("Sentencia Vacía", line=t['line'], col=t.get('col'))
        elif lexeme == 'main':
            return self.parse_main()
        elif lexeme in ['int', 'float', 'real', 'bool']:
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
        elif lexeme == 'break':
            t = self.consume(expected_lexeme='break')
            self.expect(expected_lexeme=';')
            return ASTNode("Break", line=t['line'], col=t.get('col'))
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
        t = self.consume(expected_lexeme='main')
        node = ASTNode("Función Principal", "main", line=t['line'], col=t.get('col'))
        if self.peek() and self.peek()['lexeme'] == '(':
            self.consume(expected_lexeme='(')
            self.expect(expected_lexeme=')')
        
        if self.peek() and self.peek()['lexeme'] == '{':
            node.add(self.parse_block())
        else:
            while self.pos < len(self.tokens):
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía":
                    node.add(stmt)
        return node

    def parse_block(self):
        tok = self.peek()
        node = ASTNode("Bloque", line=tok['line'] if tok else None, col=tok.get('col') if tok else None)
        if self.consume(expected_lexeme='{'):
            while self.peek() and self.peek()['lexeme'] != '}':
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía": node.add(stmt)
            self.expect(expected_lexeme='}')
        return node

    def parse_declaration(self):
        tipo = self.consume()
        node = ASTNode("Declaración", line=tipo['line'], col=tipo.get('col'))
        node.add(ASTNode("Tipo", tipo['lexeme'], line=tipo['line'], col=tipo.get('col')))
        
        while True:
            ident = self.expect(expected_kind='Identificador')
            if ident:
                var_node = ASTNode("Variable", ident['lexeme'], line=ident['line'], col=ident.get('col'))
                if self.consume(expected_lexeme='='):
                    asig_node = ASTNode("Inicialización", line=ident['line'], col=ident.get('col'))
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
        first = self.peek()
        node = ASTNode("Instrucción(es)", line=first['line'] if first else None, col=first.get('col') if first else None)
        
        while True:
            if self.peek() and self.peek()['kind'] == 'Identificador':
                start_pos = self.pos
                ident = self.consume(expected_kind='Identificador')
                
                if self.consume(expected_lexeme='='):
                    asig_node = ASTNode("Asignación", ident['lexeme'], line=ident['line'], col=ident.get('col'))
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
        if_tok = self.consume(expected_lexeme='if')
        node = ASTNode("If", line=if_tok['line'], col=if_tok.get('col'))
        expr = self.parse_expression()
        if expr: node.add(expr)
        if self.peek() and self.peek()['lexeme'] == ')':
            bad = self.consume()
            self.terminal.log_problem("Sintáctico", f"Paréntesis de cierre ')' sin apertura en línea {bad['line']}")
        
        use_then_end = False
        if self.peek() and self.peek()['lexeme'] == 'then':
            self.consume()
            use_then_end = True
            
        true_body = ASTNode("Cuerpo True", line=if_tok['line'])
        
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
            else_tok = self.consume()
            false_body = ASTNode("Cuerpo False", line=else_tok['line'])
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
            if self.peek() and self.peek()['lexeme'] == ';': 
                self.consume()
                
        return node

    def parse_while(self):
        w_tok = self.consume(expected_lexeme='while')
        node = ASTNode("While", line=w_tok['line'], col=w_tok.get('col'))
        expr = self.parse_expression()
        if expr: node.add(expr)
        if self.peek() and self.peek()['lexeme'] == ')':
            bad = self.consume()
            self.terminal.log_problem("Sintáctico", f"Paréntesis de cierre ')' sin apertura en línea {bad['line']}")
        
        body = ASTNode("Cuerpo", line=w_tok['line'])
        if self.peek() and self.peek()['lexeme'] == '{':
            body.add(self.parse_block())
            if self.peek() and self.peek()['lexeme'] == ';':
                self.consume()
        else:
            while self.peek() and self.peek()['lexeme'] not in ['end', '}']:
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía":
                    body.add(stmt)
            self.expect(expected_lexeme='end')
            if self.peek() and self.peek()['lexeme'] == ';':
                self.consume()
        if body.children:
            node.add(body)
        return node

    def parse_do_while(self):
        do_tok = self.consume(expected_lexeme='do')
        node = ASTNode("Do-While", line=do_tok['line'], col=do_tok.get('col'))

        body = ASTNode("Cuerpo", line=do_tok['line'])
        if self.peek() and self.peek()['lexeme'] == '{':
            body.add(self.parse_block())
        else:
            # Tolerancia estilo Pascal Repeat-Until para sentencias múltiples sin llaves
            while self.pos < len(self.tokens):
                nxt = self.peek()
                if not nxt or nxt['lexeme'] in ['end', '}']:
                    break
                
                # 'until' siempre cierra el bloque do; 'while' lo cierra si es while(...);
                if nxt['lexeme'] == 'until':
                    break
                if nxt['lexeme'] == 'while' and self._is_closing_while():
                    break
                
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía": 
                    body.add(stmt)

        if body.children: 
            node.add(body)

        # Cierre del bloque Do (Soporta do-while o do-until)
        is_until = False
        if self.peek() and self.peek()['lexeme'] in ['while', 'until']:
            closer = self.consume()
            if closer['lexeme'] == 'until':
                node.name = "Do-Until"
                is_until = True
        else:
            self.expect(expected_lexeme='while')

        expr = self.parse_expression()
        if expr: node.add(expr)
        if self.peek() and self.peek()['lexeme'] == ')':
            bad = self.consume()
            self.terminal.log_problem("Sintáctico", f"Paréntesis de cierre ')' sin apertura en línea {bad['line']}")
        if is_until:
            if self.peek() and self.peek()['lexeme'] == ';':
                self.consume()
        else:
            self.expect(expected_lexeme=';')
        return node

    def parse_for(self):
        for_tok = self.consume(expected_lexeme='for')
        node = ASTNode("For", line=for_tok['line'], col=for_tok.get('col'))
        self.expect(expected_lexeme='(')
        
        init = self.parse_statement()
        if init and init.name != "Sentencia Vacía":
            node.add(ASTNode("Inicialización", line=init.line).add(init))
        
        cond = self.parse_expression()
        if cond:
            node.add(ASTNode("Condición", line=cond.line).add(cond))
        self.expect(expected_lexeme=';')
        
        inc = None
        if self.peek() and self.peek()['kind'] == 'Identificador':
            start_pos = self.pos
            ident = self.consume(expected_kind='Identificador')
            if self.consume(expected_lexeme='='):
                inc = ASTNode("Asignación", ident['lexeme'], line=ident['line'], col=ident.get('col'))
                expr = self.parse_expression()
                if expr: inc.add(expr)
            else:
                self.pos = start_pos
                inc = self.parse_expression()
        elif self.peek() and self.peek()['lexeme'] != ')':
            inc = self.parse_expression()
        if inc:
            node.add(ASTNode("Incremento", line=inc.line).add(inc))
        self.expect(expected_lexeme=')')
        
        body = self.parse_statement()
        if body and body.name != "Sentencia Vacía":
            node.add(ASTNode("Cuerpo", line=body.line).add(body))
        return node

    def parse_switch(self):
        sw_tok = self.consume(expected_lexeme='switch')
        node = ASTNode("Switch", line=sw_tok['line'], col=sw_tok.get('col'))
        self.expect(expected_lexeme='(')
        expr = self.parse_expression()
        if expr: node.add(expr)
        self.expect(expected_lexeme=')')
        self.expect(expected_lexeme='{')
        
        while self.peek() and self.peek()['lexeme'] in ['case', 'default']:
            if self.peek()['lexeme'] == 'case':
                c_tok = self.consume(expected_lexeme='case')
                case_node = ASTNode("Case", line=c_tok['line'], col=c_tok.get('col'))
                val = self.consume() 
                if val: case_node.value = val['lexeme']
                self.expect(expected_lexeme=':')
            else:
                d_tok = self.consume(expected_lexeme='default')
                case_node = ASTNode("Default", line=d_tok['line'], col=d_tok.get('col'))
                self.expect(expected_lexeme=':')
            
            statements = ASTNode("Instrucciones", line=case_node.line)
            while self.peek() and self.peek()['lexeme'] not in ['case', 'default', '}']:
                stmt = self.parse_statement()
                if stmt and stmt.name != "Sentencia Vacía": statements.add(stmt)
            if statements.children: case_node.add(statements)
            node.add(case_node)
            
        self.expect(expected_lexeme='}')
        return node

    def parse_io(self):
        token = self.consume()
        node = ASTNode("Entrada" if token['lexeme'] == 'cin' else "Salida", line=token['line'], col=token.get('col'))
        is_cin = (token['lexeme'] == 'cin')
        
        if is_cin:
            if self.peek() and self.peek()['lexeme'] == '>>':
                self.consume()
            else:
                self.terminal.log_problem("Sintáctico", f"Se esperaba '>>' después de 'cin' en línea {token['line']}")
        else:
            if self.peek() and self.peek()['lexeme'] == '<<':
                self.consume()
            else:
                self.terminal.log_problem("Sintáctico", f"Se esperaba '<<' después de 'cout' en línea {token['line']}")

        # Soporte para cin/cout en cascada: cout << a << b << "Hola";
        while True:
            expr = self.parse_expression()
            if expr: node.add(expr)
            
            if is_cin and self.peek() and self.peek()['lexeme'] == '>>':
                self.consume()
            elif not is_cin and self.peek() and self.peek()['lexeme'] == '<<':
                self.consume()
            else:
                break

        self.expect(expected_lexeme=';')
        return node

    def parse_return(self):
        ret_tok = self.consume(expected_lexeme='return')
        node = ASTNode("Return", line=ret_tok['line'], col=ret_tok.get('col'))
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
            new_node = ASTNode("Op Lógico", op['lexeme'], line=op['line'], col=op.get('col'))
            if node: new_node.add(node)
            
            right = self.parse_relational()
            if right: 
                new_node.add(right)
            else:
                self.terminal.log_problem("Sintáctico", f"Falta operando derecho para '{op['lexeme']}' en línea {op['line']}")
            node = new_node
        return node

    def parse_relational(self):
        node = self.parse_algebraic()
        while self.peek() and self.peek()['lexeme'] in ['<', '>', '<=', '>=', '==', '!=']:
            op = self.consume()
            new_node = ASTNode("Op Relacional", op['lexeme'], line=op['line'], col=op.get('col'))
            if node: new_node.add(node)
            right = self.parse_algebraic()
            if right:
                new_node.add(right)
            else:
                self.terminal.log_problem("Sintáctico", f"Falta operando derecho para '{op['lexeme']}' en línea {op['line']}")
            node = new_node
        return node

    def parse_algebraic(self):
        node = self.parse_term()
        while self.peek() and self.peek()['lexeme'] in ['+', '-']:
            op = self.consume()
            new_node = ASTNode("Op Aritmético", op['lexeme'], line=op['line'], col=op.get('col'))
            if node: new_node.add(node)
            right = self.parse_term()
            if right:
                new_node.add(right)
            else:
                self.terminal.log_problem("Sintáctico", f"Falta operando derecho para '{op['lexeme']}' en línea {op['line']}")
            node = new_node
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek() and self.peek()['lexeme'] in ['*', '/', '%', '^']:
            op = self.consume()
            new_node = ASTNode("Op Multiplicativo", op['lexeme'], line=op['line'], col=op.get('col'))
            if node: new_node.add(node)
            right = self.parse_factor()
            if right:
                new_node.add(right)
            else:
                self.terminal.log_problem("Sintáctico", f"Falta operando derecho para '{op['lexeme']}' en línea {op['line']}")
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
            return ASTNode("Número", t['lexeme'], line=t['line'], col=t.get('col'))
        elif token['lexeme'] in ['true', 'false']:
            t = self.consume()
            return ASTNode("Booleano", t['lexeme'], line=t['line'], col=t.get('col'))
        elif token['kind'] == 'Cadena':
            t = self.consume()
            return ASTNode("Cadena de Texto", t['lexeme'], line=t['line'], col=t.get('col'))
        elif token['kind'] == 'Identificador':
            t = self.consume()
            ident_node = ASTNode("Identificador", t['lexeme'], line=t['line'], col=t.get('col'))
            
            # Sufijos (a++, c--) -> Expandido en el AST como: a = a + 1 / c = c - 1
            next_token = self.peek()
            if next_token and next_token['lexeme'] in ['++', '--']:
                op = self.consume()
                op_sign = '+' if op['lexeme'] == '++' else '-'
                asig_node = ASTNode("Asignación", t['lexeme'], line=t['line'], col=t.get('col'))
                arith_node = ASTNode("Op Aritmético", op_sign, line=op['line'], col=op.get('col'))
                arith_node.add(ident_node)
                arith_node.add(ASTNode("Número", "1", line=op['line'], col=op.get('col')))
                asig_node.add(arith_node)
                return asig_node
            
            return ident_node
        elif token['lexeme'] == '!':
            op = self.consume()
            node = ASTNode("Negación Lógica", "!", line=op['line'], col=op.get('col'))
            node.add(self.parse_factor())
            return node
        elif token['lexeme'] in ['-', '+']:
            op = self.consume()
            factor = self.parse_factor()
            node = ASTNode("Op Unario", op['lexeme'], line=op['line'], col=op.get('col'))
            if factor:
                node.add(factor)
            else:
                self.terminal.log_problem("Sintáctico", f"Falta operando para '{op['lexeme']}' unario en línea {op['line']}")
            return node
        elif token['lexeme'] in ['++', '--']:
            # Prefijos (++a, --c) -> Expandido en el AST como: a = a + 1 / c = c - 1
            op = self.consume()
            ident = self.expect(expected_kind='Identificador')
            op_sign = '+' if op['lexeme'] == '++' else '-'
            if ident:
                asig_node = ASTNode("Asignación", ident['lexeme'], line=ident['line'], col=ident.get('col'))
                arith_node = ASTNode("Op Aritmético", op_sign, line=op['line'], col=op.get('col'))
                arith_node.add(ASTNode("Identificador", ident['lexeme'], line=ident['line'], col=ident.get('col')))
                arith_node.add(ASTNode("Número", "1", line=op['line'], col=op.get('col')))
                asig_node.add(arith_node)
                return asig_node
            return ASTNode("Error", op['lexeme'], line=op['line'], col=op.get('col'))
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
        self.last_ast_root = None
        self.last_annotated_ast = None
        self.last_symbol_table = None
        
        self.type_colors = {
            "Palabra Reservada": "#C586C0",
            "Delimitador": "#D4D4D4",
            "Asignación": "#D4D4D4",
            "Op. Flujo": "#D4D4D4",
            "Op. Algebraico": "#D4D4D4",
            "Op. Relacional": "#D4D4D4",
            "Op. Lógico": "#D4D4D4",
            "Símbolo": "#D4D4D4",
            "Identificador": "#9CDCFE",
            "Cadena": "#CE9178",
            "Número Entero": "#B5CEA8",
            "Número Real": "#B5CEA8",
            "Error": "#F44747"
        }
        
        self.right_panel = QFrame()
        self.right_panel.setObjectName("rightAnalysisPanel")
        self.right_panel.setMinimumWidth(300)
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
        self.lex_table.setColumnCount(4)
        self.lex_table.setHorizontalHeaderLabels(["Token", "Tipo", "Línea", "Columna"])
        self.lex_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.lex_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 1. Salida Sintáctica (Árbol AST Original)
        self.sin_out = self._create_tree_widget()
        
        # 2. Salida Semántica (Árbol Sintáctico con Anotaciones Semánticas)
        self.sem_out = self._create_tree_widget()
        
        # 3. Código Intermedio
        self.int_out = self._create_terminal()
        
        # 4. Tabla de Símbolos (Tabla Hash)
        self.hash_out = QTableWidget()
        self.hash_out.setColumnCount(7)
        self.hash_out.setHorizontalHeaderLabels([
            "Hash", "Identificador", "Tipo", "Ámbito", "Memoria", "Valor", "Líneas"
        ])
        self.hash_out.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        hash_header = self.hash_out.horizontalHeader()
        hash_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hash_header.setStretchLastSection(True)
        
        self.result_stack.addWidget(self.lex_table)
        self.result_stack.addWidget(self.sin_out)
        self.result_stack.addWidget(self.sem_out)
        self.result_stack.addWidget(self.int_out)
        self.result_stack.addWidget(self.hash_out)
        
        layout.addWidget(self.result_stack)
        self.ui.mainSplitter.insertWidget(2, self.right_panel)
        self.right_panel.setVisible(False)

    def _create_tree_widget(self):
        tree = QTreeWidget()
        tree.setColumnCount(1)
        tree.setHeaderHidden(True)
        tree.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tree.header().setStretchLastSection(False)
        tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tree.setStyleSheet("""
            QTreeWidget { background-color: #1e1e1e; color: #d4d4d4; border: none; font-family: 'Segoe UI'; font-size: 11pt; }
            QTreeWidget::item:selected { background-color: #37373d; }
        """)
        return tree

    def _create_terminal(self):
        t = QTextEdit()
        t.setReadOnly(True)
        t.setFont(QFont("Consolas", 10))
        t.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border: none;")
        return t

    def _adjust_panel_width(self, index):
        """Ajusta la proporción del splitter para mostrar el árbol o la tabla sin expandir la ventana fuera de pantalla."""
        total_w = self.ui.mainSplitter.width()
        if total_w <= 100:
            total_w = 1000
        sidebar_w = self.ui.sideBarProject.width() if self.ui.sideBarProject.isVisible() else 0
        access_w = 70
        available_w = max(500, total_w - sidebar_w - access_w)
        max_allowed_w = max(350, min(int(available_w * 0.65), available_w - 250))

        if index in [1, 2]:
            target_tree = self.sin_out if index == 1 else self.sem_out
            target_tree.ensurePolished()
            target_tree.doItemsLayout()
            target_tree.resizeColumnToContents(0)
            col_w = target_tree.sizeHintForColumn(0)
            needed_w = max(380, col_w + 45)
            panel_w = min(needed_w, max_allowed_w)
        elif index == 4:
            self.hash_out.ensurePolished()
            self.hash_out.resizeColumnsToContents()
            cols_w = sum(self.hash_out.columnWidth(c) for c in range(self.hash_out.columnCount()))
            needed_w = max(460, cols_w + 45)
            panel_w = min(needed_w, max_allowed_w)
        else:
            panel_w = min(400, max_allowed_w)

        editor_w = max(250, available_w - panel_w)
        self.ui.mainSplitter.setSizes([sidebar_w, editor_w, panel_w, access_w])

    def show_panel(self, index, title):
        """Muestra el panel derecho en la pestaña solicitada y oculta el directorio si estaba abierto."""
        if hasattr(self.ui, 'sideBarProject') and self.ui.sideBarProject.isVisible():
            self.ui.sideBarProject.setVisible(False)
        self.header.setText(title)
        self.result_stack.setCurrentIndex(index)
        if not self.right_panel.isVisible():
            self.right_panel.setVisible(True)
        self._adjust_panel_width(index)

    def toggle_panel(self, index, title):
        if self.right_panel.isVisible() and self.result_stack.currentIndex() == index:
            self.right_panel.setVisible(False)
        else:
            self.show_panel(index, title)

    def add_to_table(self, token, kind, line, col=1):
        self.tokens_list.append({"lexeme": token, "kind": kind, "line": line, "col": col})
        row = self.lex_table.rowCount()
        self.lex_table.insertRow(row)
        
        col_token = QTableWidgetItem(token)
        col_kind = QTableWidgetItem(kind)
        col_line = QTableWidgetItem(str(line))
        col_col = QTableWidgetItem(str(col))
        
        for item in [col_token, col_kind, col_line, col_col]:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        color_hex = self.type_colors.get(kind, "#D4D4D4")
        col_kind.setForeground(QColor(color_hex))
        
        self.lex_table.setItem(row, 0, col_token)
        self.lex_table.setItem(row, 1, col_kind)
        self.lex_table.setItem(row, 2, col_line)
        self.lex_table.setItem(row, 3, col_col)

    def get_token_kind(self, token):
        keywords = {"if", "else", "end", "do", "while", "until", "switch", "case", "default", "break",
                    "int", "float", "real", "bool", "true", "false", "main", "cin", "cout", "return", "then", "for"}
        
        if token in keywords: return "Palabra Reservada"
        if token == ";": return "Delimitador"
        if token == "=": return "Asignación"
        if token in {"<<", ">>"}: return "Op. Flujo"
        if token in {"+", "-", "*", "/", "%", "^", "++", "--"}: return "Op. Algebraico"
        if token in {"<", ">", "<=", ">=", "==", "!="}: return "Op. Relacional"
        if token in {"&&", "||", "!"}: return "Op. Lógico"
        if token in {"(", ")", "{", "}", ",", ":"}: return "Símbolo"
        
        if re.fullmatch(r'"[^"]*"', token): return "Cadena"
        if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', token): return "Identificador"
        if re.fullmatch(r'\d+', token): return "Número Entero"
        if re.fullmatch(r'\d+\.\d+', token): return "Número Real"
        return "Error"

    def run_lexical_analysis(self, code, show_panel=True):
        self.lex_table.setRowCount(0)
        self.tokens_list = []
        self.terminal.clear_problems()
        if show_panel:
            self.show_panel(0, "LÉXICO")
        
        i = 0
        n = len(code)
        line_num = 1
        line_start = 0
        symbols = "+-*/%^=<>!&|(){},;:"
        
        while i < n:
            ch = code[i]
            col_num = i - line_start + 1
            
            # 1. Ignorar espacios y saltos de línea
            if ch.isspace():
                if ch == '\n':
                    line_num += 1
                    line_start = i + 1
                i += 1
                continue

            # 2. Ignorar Comentarios
            if ch == '/' and i+1 < n:
                if code[i+1] == '/':
                    i += 2
                    while i < n and code[i] != '\n': i += 1
                    continue
                if code[i+1] == '*':
                    start_line = line_num
                    i += 2
                    closed = False
                    while i+1 < n:
                        if code[i] == '*' and code[i+1] == '/':
                            closed = True
                            i += 2
                            break
                        if code[i] == '\n':
                            line_num += 1
                            line_start = i + 1
                        i += 1
                    if not closed:
                        if i < n and code[i] == '\n':
                            line_num += 1
                            line_start = i + 1
                        i = n
                        self.terminal.log_problem("Léxico", f"Comentario multilínea sin cerrar iniciado en línea {start_line}")
                    continue
            
            # 3. Soporte para Cadenas de Texto ("Texto")
            if ch == '"':
                start = i
                start_line = line_num
                start_col = col_num
                i += 1
                while i < n and code[i] != '"':
                    if code[i] == '\n':
                        line_num += 1
                        line_start = i + 1
                    i += 1
                if i < n:
                    i += 1
                    lexeme = code[start:i]
                    self.add_to_table(lexeme, "Cadena", start_line, start_col)
                else:
                    lexeme = code[start:i]
                    self.add_to_table(lexeme, "Error", start_line, start_col)
                    self.terminal.log_problem("Léxico", f"Cadena sin cerrar en línea {start_line}")
                continue

            # 4. Operadores Compuestos y de flujo (adyacentes sin espacios intermedios)
            first_chars = {'=', '+', '-', '<', '>', '!', '&', '|'}
            if ch in first_chars and i + 1 < n:
                valid_seconds = {
                    '=': ['='],
                    '+': ['+'],
                    '-': ['-'],
                    '<': ['=', '<'],
                    '>': ['=', '>'],
                    '!': ['='],
                    '&': ['&'],
                    '|': ['|']
                }
                nxt_ch = code[i + 1]
                if nxt_ch in valid_seconds[ch]:
                    lexeme = ch + nxt_ch
                    self.add_to_table(lexeme, self.get_token_kind(lexeme), line_num, col_num)
                    i += 2
                    continue

            # 5. Identificadores y palabras reservadas
            if ch.isalpha() or ch == '_':
                start = i
                while i < n and (code[i].isalnum() or code[i] == '_'):
                    i += 1
                lexeme = code[start:i]
                self.add_to_table(lexeme, self.get_token_kind(lexeme), line_num, col_num)
                continue

            # 6. Números Enteros y Reales
            if ch.isdigit():
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
                        # Verificar si hay puntos adicionales inválidos (ej. 34.34.34)
                        if i < n and code[i] == '.':
                            while i < n and (code[i].isdigit() or code[i] == '.'):
                                lexeme += code[i]
                                i += 1
                            self.add_to_table(lexeme, "Error", line_num, col_num)
                            self.terminal.log_problem("Léxico", f"Token inválido: '{lexeme}' en línea {line_num}")
                        else:
                            self.add_to_table(lexeme, "Número Real", line_num, col_num)
                    else:
                        lexeme += "."
                        i += 1
                        self.add_to_table(lexeme, "Error", line_num, col_num)
                        self.terminal.log_problem("Léxico", f"Token inválido: '{lexeme}' en línea {line_num}")
                else:
                    self.add_to_table(lexeme, "Número Entero", line_num, col_num)
                continue

            # 7. Símbolos de un solo caracter
            if ch in symbols:
                self.add_to_table(ch, self.get_token_kind(ch), line_num, col_num)
                i += 1
                continue

            if ch == '.':
                self.add_to_table(".", "Error", line_num, col_num)
                self.terminal.log_problem("Léxico", f"Carácter no válido: '.' en línea {line_num}")
                i += 1
                continue

            self.add_to_table(ch, "Error", line_num, col_num)
            self.terminal.log_problem("Léxico", f"Carácter no válido: '{ch}' en línea {line_num}")
            i += 1

        self.lex_table.viewport().update()

    def run_syntactic_analysis(self, show_panel=True):
        self.sin_out.clear()
        self.last_ast_root = None
        
        if not self.tokens_list:
            QTreeWidgetItem(self.sin_out, ["No hay código válido para analizar."])
            if show_panel:
                self.show_panel(1, "SINTÁCTICO")
            return None

        parser = Parser(self.tokens_list, self.terminal)
        ast_root = parser.parse()
        self.last_ast_root = ast_root

        def populate_tree(parent_widget, node):
            display_text = node.name
            if node.value:
                display_text += f": {node.value}"
            
            item = QTreeWidgetItem(parent_widget, [display_text])
            
            if node.name in ["Programa", "Bloque", "Cuerpo", "Cuerpo True", "Cuerpo False", "Instrucciones"]:
                item.setForeground(0, QColor("#DCDCAA"))
            elif node.name in ["If", "While", "Do-While", "Do-Until", "For", "Switch", "Case", "Default", "Break", "Función Principal"]:
                item.setForeground(0, QColor("#C586C0"))
            elif node.name == "Declaración":
                item.setForeground(0, QColor("#569CD6"))
            elif node.name in ["Entrada", "Salida", "Cadena de Texto"]:
                item.setForeground(0, QColor("#CE9178"))
            elif node.name == "Error":
                item.setForeground(0, QColor("#F44747"))
                
            for child in node.children:
                populate_tree(item, child)
            
            item.setExpanded(True)

        populate_tree(self.sin_out.invisibleRootItem(), ast_root)
        if show_panel:
            self.show_panel(1, "SINTÁCTICO")
        return ast_root

    def _format_annotated_label(self, node):
        """Construye la etiqueta del nodo con sus anotaciones semánticas (atributos heredados/sintetizados)."""
        text = node.name
        if node.value != "" and node.value is not None:
            text += f": {node.value}"

        annotations = []
        if node.name == "Declaración" and node.dtype:
            annotations.append(f"dtype heredado: {node.dtype}")
        elif node.name == "Variable":
            if node.inherited_dtype:
                annotations.append(f"dtype: {node.inherited_dtype}")
            if node.memloc is not None:
                annotations.append(f"mem: {node.memloc}")
            if node.scope:
                annotations.append(f"ámbito: {node.scope}")
            if node.val is not None:
                annotations.append(f"val: {node.val}")
        else:
            if node.dtype and node.dtype not in ["void"]:
                annotations.append(f"tipo: {node.dtype}")
            if node.memloc is not None:
                annotations.append(f"mem: {node.memloc}")
            if node.val is not None:
                val_str = "true" if node.val is True else ("false" if node.val is False else str(node.val))
                annotations.append(f"val: {val_str}")
            if node.conversion:
                annotations.append(f"conv: {node.conversion}")
            if node.name in ["Programa", "Función Principal"] and node.scope:
                annotations.append(f"ámbito: {node.scope}")

        if node.sem_error:
            annotations.append(f"ERROR: {node.sem_error}")

        if annotations:
            text += f"  [{', '.join(annotations)}]"
        return text

    def _populate_symbol_table_widget(self, symtab):
        self.hash_out.setRowCount(0)
        if not symtab:
            return

        for entry in symtab.get_all_entries():
            row = self.hash_out.rowCount()
            self.hash_out.insertRow(row)

            val_str = "-" if entry.value is None else str(entry.value)
            lines_str = ", ".join(str(line) for line in entry.lines)

            cells = [
                QTableWidgetItem(str(entry.hash_index)),
                QTableWidgetItem(entry.name),
                QTableWidgetItem(entry.dtype),
                QTableWidgetItem(entry.scope),
                QTableWidgetItem(str(entry.memloc)),
                QTableWidgetItem(val_str),
                QTableWidgetItem(lines_str)
            ]

            type_color = "#569CD6" if entry.dtype == "int" else ("#4EC9B0" if entry.dtype == "float" else "#C586C0")
            cells[1].setForeground(QColor("#9CDCFE"))
            cells[2].setForeground(QColor(type_color))
            cells[5].setForeground(QColor("#B5CEA8"))

            for idx, item in enumerate(cells):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if idx != 6 else (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
                self.hash_out.setItem(row, idx, item)

        self.hash_out.viewport().update()

    def run_semantic_analysis(self, show_panel=True):
        self.sem_out.clear()
        self.hash_out.setRowCount(0)

        if not self.last_ast_root:
            QTreeWidgetItem(self.sem_out, ["No hay Árbol Sintáctico disponible para analizar semánticamente."])
            if show_panel:
                self.show_panel(2, "SEMÁNTICO")
            return None, None

        analyzer = SemanticAnalyzer(self.last_ast_root, self.terminal)
        annotated_ast, symtab = analyzer.analyze()
        self.last_annotated_ast = annotated_ast
        self.last_symbol_table = symtab

        def populate_annotated_tree(parent_widget, node):
            display_text = self._format_annotated_label(node)
            item = QTreeWidgetItem(parent_widget, [display_text])

            if node.sem_error or node.dtype == "error":
                item.setForeground(0, QColor("#F44747"))
            elif node.conversion:
                item.setForeground(0, QColor("#4EC9B0"))
            elif node.name in ["Programa", "Bloque", "Cuerpo", "Cuerpo True", "Cuerpo False", "Instrucciones"]:
                item.setForeground(0, QColor("#DCDCAA"))
            elif node.name in ["If", "While", "Do-While", "Do-Until", "For", "Switch", "Case", "Default", "Break", "Función Principal"]:
                item.setForeground(0, QColor("#C586C0"))
            elif node.name in ["Declaración", "Variable", "Tipo"]:
                item.setForeground(0, QColor("#569CD6"))
            elif node.name in ["Asignación", "Inicialización"]:
                item.setForeground(0, QColor("#9CDCFE"))
            elif node.name in ["Entrada", "Salida", "Cadena de Texto"]:
                item.setForeground(0, QColor("#CE9178"))
            elif node.dtype in ["int", "float", "bool"]:
                item.setForeground(0, QColor("#B5CEA8"))

            for child in node.children:
                populate_annotated_tree(item, child)

            item.setExpanded(True)

        populate_annotated_tree(self.sem_out.invisibleRootItem(), annotated_ast)
        self._populate_symbol_table_widget(symtab)

        if show_panel:
            self.show_panel(2, "SEMÁNTICO")
        return annotated_ast, symtab