import copy

# ==========================================
# ESTRUCTURAS DE LA TABLA DE SÍMBOLOS (HASH)
# Basadas en el modelo de TINY con encadenamiento separado
# ==========================================
class LineListRec:
    """Nodo de lista enlazada para registrar las líneas donde aparece un identificador."""
    def __init__(self, lineno):
        self.lineno = lineno
        self.next = None


class BucketListRec:
    """Registro de la Tabla Hash (Bucket) con encadenamiento separado para colisiones."""
    def __init__(self, name, dtype, scope, memloc, lineno, hash_index, value=None):
        self.name = name
        self.dtype = dtype          # 'int', 'float', 'bool'
        self.scope = scope          # 'main', 'global', etc.
        self.memloc = memloc        # Localidad/desplazamiento de memoria único (0, 1, 2...)
        self.value = value          # Valor determinado en compilación (o None si es dinámico)
        self.hash_index = hash_index
        self.lines_head = LineListRec(lineno)
        self.lines = [lineno]       # Lista auxiliar para visualización directa
        self.next = None            # Puntero al siguiente Bucket en caso de colisión

    def add_line(self, lineno):
        if lineno is None or lineno == "EOF":
            return
        # Agregar al final de la lista enlazada LineListRec (permite registrar múltiples apariciones en la misma línea)
        curr = self.lines_head
        while curr.next is not None:
            curr = curr.next
        curr.next = LineListRec(lineno)
        self.lines.append(lineno)


class SymbolTable:
    """
    Tabla de Símbolos implementada como Tabla Hash con encadenamiento separado.
    Utiliza SIZE = 211 y SHIFT = 4 conforme al diseño de referencia de TINY,
    extendida para tipos explícitos (int, float, bool), ámbitos y valores.
    """
    SIZE = 211
    SHIFT = 4

    def __init__(self):
        self.table = [None] * self.SIZE
        self.location = 0
        self.entries_in_order = []

    def hash_fn(self, key: str) -> int:
        temp = 0
        for ch in key:
            temp = ((temp << self.SHIFT) + ord(ch)) % self.SIZE
        return temp

    def st_lookup(self, name: str, scope: str = None, current_scope_only: bool = False):
        """
        Busca un identificador en la tabla hash.
        Si current_scope_only es True, solo verifica el ámbito indicado (para detectar duplicados).
        Si es False, busca primero en el ámbito actual y luego en el ámbito 'main'/'global'.
        """
        h = self.hash_fn(name)
        bucket = self.table[h]
        fallback = None

        while bucket is not None:
            if bucket.name == name:
                if scope is None or bucket.scope == scope:
                    return bucket
                if not current_scope_only:
                    fallback = bucket
            bucket = bucket.next

        return fallback

    def st_insert(self, name: str, dtype: str, lineno: int, scope: str = "main", value=None):
        """
        Inserta un nuevo identificador declarado en la tabla de símbolos.
        Retorna (bucket, True) si se insertó con éxito, o (bucket_existente, False) si está duplicado.
        """
        existing = self.st_lookup(name, scope=scope, current_scope_only=True)
        if existing is not None:
            return existing, False

        h = self.hash_fn(name)
        new_bucket = BucketListRec(
            name=name,
            dtype=dtype,
            scope=scope,
            memloc=self.location,
            lineno=lineno,
            hash_index=h,
            value=value
        )
        self.location += 1

        # Encadenamiento separado al final de la lista del bucket
        if self.table[h] is None:
            self.table[h] = new_bucket
        else:
            curr = self.table[h]
            while curr.next is not None:
                curr = curr.next
            curr.next = new_bucket

        self.entries_in_order.append(new_bucket)
        return new_bucket, True

    def st_add_reference(self, name: str, lineno: int, scope: str = "main"):
        """
        Registra el uso de un identificador ya declarado agregando la línea a su LineList.
        Retorna el bucket si existe, o None si la variable no ha sido declarada.
        """
        bucket = self.st_lookup(name, scope=scope, current_scope_only=False)
        if bucket is not None:
            bucket.add_line(lineno)
            return bucket
        return None

    def st_update_value(self, name: str, value, scope: str = "main"):
        bucket = self.st_lookup(name, scope=scope, current_scope_only=False)
        if bucket is not None:
            bucket.value = value

    def get_all_entries(self):
        return self.entries_in_order

    def snapshot_values(self):
        return {(b.name, b.scope): b.value for b in self.entries_in_order}

    def restore_values(self, snapshot: dict):
        for b in self.entries_in_order:
            if (b.name, b.scope) in snapshot:
                b.value = snapshot[(b.name, b.scope)]


# ==========================================
# ANALIZADOR SEMÁNTICO
# ==========================================
class SemanticAnalyzer:
    """
    Ejecuta el análisis semántico sobre una copia del AST generado en el análisis sintáctico:
    - Propaga atributos heredados (ej. dtype en declaraciones y ámbito).
    - Construye y consulta la Tabla de Símbolos (Tabla Hash).
    - Calcula y propaga atributos sintetizados (dtype y val en expresiones).
    - Aplica reglas de compatibilidad y conversión implícita de tipos (int -> float).
    - Genera el Árbol Sintáctico con Anotaciones Semánticas y reporta errores semánticos.
    """
    TYPE_MAP = {
        "int": "int",
        "float": "float",
        "real": "float",
        "bool": "bool"
    }

    def __init__(self, ast_root, terminal):
        # Construimos una copia profunda del AST original para anotarlo sin alterar el AST sintáctico
        self.annotated_ast = copy.deepcopy(ast_root) if ast_root else None
        self.symbol_table = SymbolTable()
        self.terminal = terminal
        self.errors = []
        self.current_scope = "global"
        self.in_branch_or_loop = 0

    def log_error(self, node, rule_type, description):
        line = getattr(node, "line", None)
        col = getattr(node, "col", None)
        loc_str = f"línea {line}" if line else "ubicación desconocida"
        if col:
            loc_str += f", col {col}"
        msg = f"[{rule_type}] {description} ({loc_str})"
        self.errors.append(msg)
        if node is not None:
            node.sem_error = description
            if not getattr(node, "dtype", None):
                node.dtype = "error"
        self.terminal.log_problem("Semántico", msg)

    def analyze(self):
        if not self.annotated_ast:
            return None, self.symbol_table

        self._analyze_node(self.annotated_ast)
        return self.annotated_ast, self.symbol_table

    def _format_val(self, val, dtype=None):
        if val is None:
            return None
        if isinstance(val, bool):
            return "true" if val else "false"
        if dtype == "float" or isinstance(val, float):
            return round(float(val), 4)
        return val

    def _analyze_node(self, node):
        if node is None:
            return

        name = node.name

        # 1. Programa y Función Principal (Manejo de ámbito)
        if name == "Programa":
            node.scope = "global"
            for child in node.children:
                self._analyze_node(child)
            return

        if name == "Función Principal":
            prev_scope = self.current_scope
            self.current_scope = node.value if node.value else "main"
            node.scope = self.current_scope
            for child in node.children:
                self._analyze_node(child)
            self.current_scope = prev_scope
            return

        if name in ["Bloque", "Cuerpo", "Cuerpo True", "Cuerpo False", "Instrucciones", "Instrucción(es)"]:
            node.scope = self.current_scope
            for child in node.children:
                self._analyze_node(child)
            return

        # 2. Declaración de Variables (Atributo heredado dtype -> Variables -> Tabla de Símbolos)
        if name == "Declaración":
            self._handle_declaration(node)
            return

        # 3. Asignación
        if name == "Asignación":
            self._handle_assignment(node)
            return

        # 4. Estructuras de Control Condicionales y Repetitivas
        if name == "If":
            self._handle_if(node)
            return

        if name in ["While", "Do-While", "Do-Until"]:
            self._handle_loop(node)
            return

        if name == "For":
            self._handle_for(node)
            return

        if name == "Switch":
            self._handle_switch(node)
            return

        # 5. Entrada / Salida / Return / Break
        if name == "Entrada":
            self._handle_input(node)
            return

        if name == "Salida":
            self._handle_output(node)
            return

        if name == "Return":
            if node.children:
                expr = node.children[0]
                self._analyze_expression(expr)
                node.dtype = expr.dtype
                node.val = expr.val
            else:
                node.dtype = "void"
            return

        if name == "Break":
            node.dtype = "void"
            return

        # 6. Si es cualquier nodo de expresión suelto
        self._analyze_expression(node)

    # ------------------------------------------
    # REGLAS DE DECLARACIÓN Y TABLA DE SÍMBOLOS
    # ------------------------------------------
    def _handle_declaration(self, node):
        if not node.children:
            return

        tipo_node = node.children[0]
        raw_type = tipo_node.value
        inherited_dtype = self.TYPE_MAP.get(raw_type, raw_type)

        # Anotamos el tipo y lo propagamos como atributo heredado
        tipo_node.dtype = inherited_dtype
        node.dtype = inherited_dtype
        node.scope = self.current_scope

        for var_node in node.children[1:]:
            if var_node.name != "Variable":
                continue

            var_name = var_node.value
            # Atributo heredado desde la declaración hacia cada identificador
            var_node.inherited_dtype = inherited_dtype
            var_node.dtype = inherited_dtype
            var_node.scope = self.current_scope

            init_val = None
            if var_node.children:
                init_node = var_node.children[0]  # Nodo "Inicialización"
                if init_node.children:
                    expr = init_node.children[0]
                    self._analyze_expression(expr)
                    init_node.dtype = expr.dtype
                    init_node.val = expr.val

                    # Verificar compatibilidad de tipo en la inicialización
                    if expr.dtype and expr.dtype != "error":
                        if inherited_dtype == expr.dtype:
                            init_val = expr.val
                        elif inherited_dtype == "float" and expr.dtype == "int":
                            expr.conversion = "int -> float"
                            init_node.conversion = "int -> float"
                            init_val = float(expr.val) if expr.val is not None else None
                        elif inherited_dtype == "int" and expr.dtype == "float":
                            self.log_error(
                                var_node,
                                "Conversión no válida",
                                f"No se puede inicializar la variable '{var_name}' ('int') con un valor de tipo 'float'"
                            )
                        else:
                            self.log_error(
                                var_node,
                                "Incompatibilidad de tipos",
                                f"No se puede inicializar '{var_name}' ('{inherited_dtype}') con una expresión de tipo '{expr.dtype}'"
                            )

            # Insertar en la Tabla de Símbolos
            bucket, ok = self.symbol_table.st_insert(
                name=var_name,
                dtype=inherited_dtype,
                lineno=var_node.line,
                scope=self.current_scope,
                value=self._format_val(init_val, inherited_dtype)
            )
            if not ok:
                self.log_error(
                    var_node,
                    "Duplicidad de identificador",
                    f"El identificador '{var_name}' ya fue declarado previamente en el ámbito '{self.current_scope}' (línea {bucket.lines[0]})"
                )
            else:
                var_node.memloc = bucket.memloc
                var_node.val = self._format_val(init_val, inherited_dtype)

    # ------------------------------------------
    # REGLAS DE ASIGNACIÓN
    # ------------------------------------------
    def _handle_assignment(self, node):
        var_name = node.value
        node.scope = self.current_scope

        # Evaluar primero la expresión del lado derecho (post-orden)
        expr = node.children[0] if node.children else None
        if expr:
            self._analyze_expression(expr)

        # Buscar variable destino en la tabla de símbolos
        bucket = self.symbol_table.st_add_reference(var_name, node.line, self.current_scope)
        if bucket is None:
            self.log_error(
                node,
                "Variable no declarada",
                f"La variable '{var_name}' no ha sido declarada antes de su asignación"
            )
            return

        target_type = bucket.dtype
        node.dtype = target_type
        node.memloc = bucket.memloc

        if not expr or not expr.dtype or expr.dtype == "error":
            return

        expr_type = expr.dtype

        # Verificación de compatibilidad y conversión de tipos en asignación
        if target_type == expr_type:
            new_val = self._format_val(expr.val, target_type)
            node.val = new_val
            self.symbol_table.st_update_value(var_name, new_val, self.current_scope)
        elif target_type == "float" and expr_type == "int":
            # Promoción implícita permitida: int -> float
            expr.conversion = "int -> float"
            node.conversion = "int -> float"
            new_val = self._format_val(float(expr.val), "float") if expr.val is not None else None
            node.val = new_val
            self.symbol_table.st_update_value(var_name, new_val, self.current_scope)
        elif target_type == "int" and expr_type == "float":
            self.log_error(
                node,
                "Conversión no válida",
                f"Incompatibilidad en asignación a '{var_name}': no se puede convertir 'float' a 'int'"
            )
        else:
            self.log_error(
                node,
                "Incompatibilidad de tipos",
                f"No se puede asignar una expresión de tipo '{expr_type}' a la variable '{var_name}' de tipo '{target_type}'"
            )

    # ------------------------------------------
    # REGLAS DE ESTRUCTURAS DE CONTROL
    # ------------------------------------------
    def _check_boolean_condition(self, construct_Node, cond_node, construct_name):
        if cond_node is None:
            return
        self._analyze_expression(cond_node)
        if cond_node.dtype and cond_node.dtype != "error" and cond_node.dtype != "bool":
            self.log_error(
                cond_node,
                "Condición no booleana",
                f"La condición en '{construct_name}' requiere una expresión de tipo 'bool', pero se obtuvo '{cond_node.dtype}'"
            )

    def _handle_if(self, node):
        node.scope = self.current_scope
        if not node.children:
            return

        cond = None
        true_branch = None
        false_branch = None
        for child in node.children:
            if child.name == "Cuerpo True":
                true_branch = child
            elif child.name == "Cuerpo False":
                false_branch = child
            elif cond is None:
                cond = child

        if cond is not None:
            self._check_boolean_condition(node, cond, "if")
        node.dtype = "void"

        pre_snap = self.symbol_table.snapshot_values()

        self.in_branch_or_loop += 1
        if true_branch:
            self._analyze_node(true_branch)
        true_snap = self.symbol_table.snapshot_values()

        if false_branch:
            self.symbol_table.restore_values(pre_snap)
            self._analyze_node(false_branch)
            false_snap = self.symbol_table.snapshot_values()
        else:
            false_snap = pre_snap
        self.in_branch_or_loop -= 1

        # Si la condición es constante booleana conocida, conservamos los valores de la rama activa
        if cond is not None and cond.val is True:
            self.symbol_table.restore_values(true_snap)
        elif cond is not None and cond.val is False:
            self.symbol_table.restore_values(false_snap)

    def _handle_loop(self, node):
        node.scope = self.current_scope
        node.dtype = "void"
        if not node.children:
            return

        cond = None
        bodies = []
        for child in node.children:
            if child.name == "Cuerpo":
                bodies.append(child)
            elif cond is None:
                cond = child

        if node.name == "While":
            if cond is not None:
                self._check_boolean_condition(node, cond, "while")
            pre_snap = self.symbol_table.snapshot_values()
            self.in_branch_or_loop += 1
            for b in bodies:
                self._analyze_node(b)
            self.in_branch_or_loop -= 1
            if cond is not None and cond.val is False:
                self.symbol_table.restore_values(pre_snap)
        else:
            # Do-While / Do-Until: el cuerpo está primero y la condición al final
            self.in_branch_or_loop += 1
            for b in bodies:
                self._analyze_node(b)
            self.in_branch_or_loop -= 1

            if cond is not None:
                self._check_boolean_condition(node, cond, node.name.lower())

    def _handle_for(self, node):
        node.scope = self.current_scope
        node.dtype = "void"
        self.in_branch_or_loop += 1
        for child in node.children:
            if child.name == "Inicialización" and child.children:
                self._analyze_node(child.children[0])
                child.dtype = child.children[0].dtype
            elif child.name == "Condición" and child.children:
                cond = child.children[0]
                self._check_boolean_condition(node, cond, "for")
                child.dtype = cond.dtype
                child.val = cond.val
            elif child.name == "Incremento" and child.children:
                self._analyze_node(child.children[0])
                child.dtype = child.children[0].dtype
            else:
                self._analyze_node(child)
        self.in_branch_or_loop -= 1

    def _handle_switch(self, node):
        node.scope = self.current_scope
        node.dtype = "void"
        if not node.children:
            return

        expr = node.children[0]
        self._analyze_expression(expr)
        if expr.dtype and expr.dtype not in ["int", "error"]:
            self.log_error(
                expr,
                "Tipo inválido en switch",
                f"La expresión de selección en 'switch' debe ser de tipo 'int', pero se obtuvo '{expr.dtype}'"
            )

        self.in_branch_or_loop += 1
        for case_node in node.children[1:]:
            if case_node.name == "Case":
                if case_node.value and '.' in str(case_node.value):
                    self.log_error(
                        case_node,
                        "Incompatibilidad en case",
                        f"El valor del 'case' ('{case_node.value}') debe ser una constante entera ('int')"
                    )
                else:
                    case_node.dtype = "int"
            for stmt_group in case_node.children:
                self._analyze_node(stmt_group)
        self.in_branch_or_loop -= 1

    # ------------------------------------------
    # REGLAS DE ENTRADA Y SALIDA
    # ------------------------------------------
    def _handle_input(self, node):
        node.scope = self.current_scope
        node.dtype = "void"
        for child in node.children:
            if child.name == "Identificador":
                var_name = child.value
                bucket = self.symbol_table.st_add_reference(var_name, child.line, self.current_scope)
                if bucket is None:
                    self.log_error(
                        child,
                        "Variable no declarada",
                        f"La variable '{var_name}' en 'cin' no ha sido declarada"
                    )
                else:
                    child.dtype = bucket.dtype
                    child.memloc = bucket.memloc
                    child.scope = bucket.scope
                    # Al leerse por entrada estándar, su valor solo se conocerá en tiempo de ejecución
                    self.symbol_table.st_update_value(var_name, None, self.current_scope)
            else:
                self.log_error(
                    child,
                    "Operando inválido en cin",
                    "La sentencia de entrada 'cin' requiere una variable como destino"
                )

    def _handle_output(self, node):
        node.scope = self.current_scope
        node.dtype = "void"
        for child in node.children:
            self._analyze_expression(child)

    # ------------------------------------------
    # REGLAS DE EXPRESIONES (ATRIBUTOS SINTETIZADOS)
    # ------------------------------------------
    def _analyze_expression(self, node):
        if node is None:
            return

        name = node.name

        # 1. Hojas: Números, Booleanos, Cadenas, Identificadores
        if name == "Número":
            lex = str(node.value)
            if '.' in lex:
                node.dtype = "float"
                try:
                    node.val = float(lex)
                except ValueError:
                    node.val = None
            else:
                node.dtype = "int"
                try:
                    node.val = int(lex)
                except ValueError:
                    node.val = None
            return

        if name == "Booleano":
            node.dtype = "bool"
            node.val = (str(node.value).lower() == "true")
            return

        if name == "Cadena de Texto":
            node.dtype = "string"
            node.val = node.value
            return

        if name == "Identificador":
            var_name = node.value
            bucket = self.symbol_table.st_add_reference(var_name, node.line, self.current_scope)
            if bucket is None:
                self.log_error(
                    node,
                    "Variable no declarada",
                    f"La variable '{var_name}' no ha sido declarada"
                )
            else:
                node.dtype = bucket.dtype
                node.memloc = bucket.memloc
                node.scope = bucket.scope
                node.val = bucket.value
            return

        # Si una expresión es una asignación embebida (como a++ -> a = a + 1)
        if name == "Asignación":
            self._handle_assignment(node)
            return

        # 2. Operadores Unarios (-, +, !)
        if name == "Op Unario":
            op = node.value
            child = node.children[0] if node.children else None
            self._analyze_expression(child)
            if not child or not child.dtype or child.dtype == "error":
                node.dtype = "error"
                return
            if child.dtype not in ["int", "float"]:
                self.log_error(
                    node,
                    "Uso indebido de operador",
                    f"El operador unario '{op}' requiere un operando numérico ('int' o 'float'), pero se obtuvo '{child.dtype}'"
                )
                return
            node.dtype = child.dtype
            if child.val is not None:
                node.val = -child.val if op == '-' else +child.val
            return

        if name == "Negación Lógica":
            child = node.children[0] if node.children else None
            self._analyze_expression(child)
            if not child or not child.dtype or child.dtype == "error":
                node.dtype = "error"
                return
            if child.dtype != "bool":
                self.log_error(
                    node,
                    "Uso indebido de operador",
                    f"El operador lógico '!' requiere un operando de tipo 'bool', pero se obtuvo '{child.dtype}'"
                )
                return
            node.dtype = "bool"
            if isinstance(child.val, bool):
                node.val = not child.val
            return

        # 3. Operadores Binarios Aritméticos, Multiplicativos, Relacionales y Lógicos
        if name in ["Op Aritmético", "Op Multiplicativo", "Op Relacional", "Op Lógico"]:
            op = node.value
            left = node.children[0] if len(node.children) > 0 else None
            right = node.children[1] if len(node.children) > 1 else None

            self._analyze_expression(left)
            self._analyze_expression(right)

            if not left or not right or left.dtype == "error" or right.dtype == "error" or not left.dtype or not right.dtype:
                node.dtype = "error"
                return

            lt, rt = left.dtype, right.dtype

            # --- A. Operadores Aritméticos y Multiplicativos (+, -, *, /, %, ^) ---
            if name in ["Op Aritmético", "Op Multiplicativo"]:
                if lt not in ["int", "float"] or rt not in ["int", "float"]:
                    self.log_error(
                        node,
                        "Uso indebido de operador",
                        f"El operador aritmético '{op}' requiere operandos numéricos ('int' o 'float'), pero se encontró '{lt}' y '{rt}'"
                    )
                    return

                if op == "%" and (lt == "float" or rt == "float"):
                    self.log_error(
                        node,
                        "Uso indebido de operador",
                        "El operador módulo '%' solo se permite entre operandos enteros ('int')"
                    )
                    return

                # Regla de promoción de tipos: int + float -> float
                if lt == "float" or rt == "float":
                    node.dtype = "float"
                    if lt == "int":
                        left.conversion = "int -> float"
                    if rt == "int":
                        right.conversion = "int -> float"
                else:
                    node.dtype = "int"

                # Evaluación de valor constante (si ambos operandos tienen valor numérico conocido)
                if isinstance(left.val, (int, float)) and isinstance(right.val, (int, float)):
                    try:
                        if op == "+":
                            res = left.val + right.val
                        elif op == "-":
                            res = left.val - right.val
                        elif op == "*":
                            res = left.val * right.val
                        elif op == "/":
                            if right.val == 0:
                                self.log_error(node, "Error aritmético", "División entre cero detectada")
                                res = None
                            elif node.dtype == "int":
                                res = int(left.val / right.val)
                            else:
                                res = float(left.val) / float(right.val)
                        elif op == "%":
                            if right.val == 0:
                                self.log_error(node, "Error aritmético", "Módulo entre cero detectado")
                                res = None
                            else:
                                res = int(left.val) % int(right.val)
                        elif op == "^":
                            res = left.val ** right.val
                        else:
                            res = None
                        node.val = self._format_val(res, node.dtype)
                    except Exception:
                        node.val = None
                return

            # --- B. Operadores Relacionales (<, >, <=, >=, ==, !=) ---
            if name == "Op Relacional":
                if op in ["<", ">", "<=", ">="]:
                    if lt not in ["int", "float"] or rt not in ["int", "float"]:
                        self.log_error(
                            node,
                            "Uso indebido de operador",
                            f"El operador relacional '{op}' requiere operandos numéricos, pero se encontró '{lt}' y '{rt}'"
                        )
                        return
                    if lt != rt:
                        if lt == "int" and rt == "float":
                            left.conversion = "int -> float"
                        elif lt == "float" and rt == "int":
                            right.conversion = "int -> float"
                else:
                    # '==' o '!='
                    both_numeric = (lt in ["int", "float"] and rt in ["int", "float"])
                    same_type = (lt == rt)
                    if not (both_numeric or same_type):
                        self.log_error(
                            node,
                            "Incompatibilidad de tipos",
                            f"No se pueden comparar operandos incompatibles de tipo '{lt}' y '{rt}' con '{op}'"
                        )
                        return
                    if both_numeric and lt != rt:
                        if lt == "int" and rt == "float":
                            left.conversion = "int -> float"
                        elif lt == "float" and rt == "int":
                            right.conversion = "int -> float"

                node.dtype = "bool"
                if left.val is not None and right.val is not None:
                    try:
                        if op == "<": node.val = (left.val < right.val)
                        elif op == ">": node.val = (left.val > right.val)
                        elif op == "<=": node.val = (left.val <= right.val)
                        elif op == ">=": node.val = (left.val >= right.val)
                        elif op == "==": node.val = (left.val == right.val)
                        elif op == "!=": node.val = (left.val != right.val)
                    except Exception:
                        node.val = None
                return

            # --- C. Operadores Lógicos (&&, ||) ---
            if name == "Op Lógico":
                if lt != "bool" or rt != "bool":
                    self.log_error(
                        node,
                        "Uso indebido de operador",
                        f"El operador lógico '{op}' requiere operandos de tipo 'bool', pero se encontró '{lt}' y '{rt}'"
                    )
                    return

                node.dtype = "bool"
                if isinstance(left.val, bool) and isinstance(right.val, bool):
                    if op == "&&":
                        node.val = (left.val and right.val)
                    elif op == "||":
                        node.val = (left.val or right.val)
                return
