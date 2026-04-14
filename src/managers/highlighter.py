from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

class CustomHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        def create_format(color, bold=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)
            return fmt

        # Colores Visual Studio Code Dark+
        COLOR_KEYWORD    = "#C586C0"   # Púrpura
        COLOR_NUMBER     = "#CE9178"   # Naranja
        COLOR_COMMENT    = "#6A9955"   # Verde
        COLOR_OPERATOR   = "#D4D4D4"   # Gris claro
        COLOR_SYMBOL     = "#D4D4D4"
        COLOR_IDENTIFIER = "#9CDCFE"   # Azul claro
        COLOR_STRING     = "#CE9178"   # Naranja
        COLOR_ERROR      = "#F44747"   # Rojo

        # 1. Identificadores (Base para palabras reservadas)
        id_format = create_format(COLOR_IDENTIFIER)
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'), id_format)
        )

        # 2. Palabras reservadas (Sobrescriben identificadores)
        keyword_format = create_format(COLOR_KEYWORD, bold=True)
        keywords = [
            "if", "else", "end", "do", "while", "switch", "case",
            "int", "float", "real", "main", "cin", "cout", "return", "then", "for"
        ]
        for word in keywords:
            pattern = QRegularExpression(fr'\b{word}\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # 3. Números válidos (Enteros y Reales bien formados)
        number_format = create_format(COLOR_NUMBER)
        # Real: dígito(s) + punto + dígito(s)
        self.highlighting_rules.append(
            (QRegularExpression(r'\b\d+\.\d+\b'), number_format)
        )
        # Entero: dígito(s) que no formen parte de un real
        self.highlighting_rules.append(
            (QRegularExpression(r'\b\d+\b'), number_format)
        )

        # 4. Operadores y Símbolos
        operator_format = create_format(COLOR_OPERATOR)
        # Compuestos
        comp_ops = [r'<=', r'>=', r'!=', r'==', r'&&', r'\|\|', r'\+\+', r'\-\-']
        for op in comp_ops:
            self.highlighting_rules.append((QRegularExpression(op), operator_format))
        # Simples
        simple_elements = [r'\+', r'\-', r'\*', r'/', r'%', r'\^', r'<', r'>', r'!', r'=', 
                           r'\(', r'\)', r'\{', r'\}', r',', r';']
        for el in simple_elements:
            self.highlighting_rules.append((QRegularExpression(el), operator_format))

        # 5. ERRORES LÉXICOS (Reglas de pintura para casos inválidos)
        error_format = create_format(COLOR_ERROR, bold=True)
        invalid_patterns = [
            # Caso 32.algo -> El número seguido de punto pero SIN dígitos después
            r'\d+\.(?!\d)', 
            # Caso .45 -> Punto seguido de números pero sin nada antes
            r'(?<!\d)\.\d+',
            # Caso 34.34.34 -> Un punto que aparece inmediatamente después de un número real
            r'(?<=\d\.\d)\.',
            # Caracteres ilegales (no permitidos en el lenguaje)
            r'[^\s\w\+\-\*/%\^=<>!&\|\(\)\{\},;\.]'
        ]
        for pat in invalid_patterns:
            self.highlighting_rules.append((QRegularExpression(pat), error_format))

        # 6. Cadenas y Comentarios
        string_format = create_format(COLOR_STRING)
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))
        
        comment_format = create_format(COLOR_COMMENT)
        self.highlighting_rules.append((QRegularExpression(r'//[^\n]*'), comment_format))

        self.multiLineCommentFormat = comment_format
        self.commentStartExpression = QRegularExpression(r'/\*')
        self.commentEndExpression = QRegularExpression(r'\*/')

    def highlightBlock(self, text):
        # Formato base
        default_fmt = QTextCharFormat()
        default_fmt.setForeground(QColor("#D4D4D4"))
        self.setFormat(0, len(text), default_fmt)

        # Aplicar reglas en orden
        for pattern, fmt in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # Lógica de comentarios multilínea
        self.setCurrentBlockState(0)
        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.match(text).capturedStart()

        while startIndex >= 0:
            match = self.commentEndExpression.match(text, startIndex)
            endIndex = match.capturedStart()
            commentLength = 0
            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + match.capturedLength()
            self.setFormat(startIndex, commentLength, self.multiLineCommentFormat)
            startIndex = self.commentStartExpression.match(text, startIndex + commentLength).capturedStart()