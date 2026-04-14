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
        COLOR_STRING     = "#CE9178"   # Naranja (para cadenas)
        COLOR_ERROR      = "#F44747"   # Rojo

        # --- Reglas en orden de prioridad (las últimas sobrescriben) ---
      
        # Números válidos (enteros y decimales)
        number_format = create_format(COLOR_NUMBER)
        self.highlighting_rules.append(
            (QRegularExpression(r'\b\d+(\.\d+)?\b'), number_format)
        )

        # Errores léxicos
        error_format = create_format(COLOR_ERROR, bold=True)
        invalid_patterns = [
            r'\d+\.[a-zA-Z_]+',       # Ejemplo: 34.algo
            r'\d+(\.\d+){2,}',        # Ejemplo: 34.34.34
            r'\d+\.(?!\d)',           # Ejemplo: 12.
            r'(?<!\d)\.\d+',          # Ejemplo: .45
            r'[^\s\w\+\-\*/%\^=<>!&\|\(\)\{\},;\.]' # Caracteres ilegales
        ]
        for pat in invalid_patterns:
            self.highlighting_rules.append((QRegularExpression(pat), error_format))

        # Cadenas y caracteres
        string_format = create_format(COLOR_STRING)
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.?'"), string_format))

        # Identificadores (incluye palabras reservadas, luego se sobrescriben)
        id_format = create_format(COLOR_IDENTIFIER)
        self.highlighting_rules.append(
            (QRegularExpression(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'), id_format)
        )

        # Palabras reservadas (sobrescriben identificadores)
        keyword_format = create_format(COLOR_KEYWORD, bold=True)
        keywords = [
            "if", "else", "end", "do", "while", "switch", "case",
            "int", "float", "main", "cin", "cout", "return","for"
        ]
        for word in keywords:
            pattern = QRegularExpression(fr'\b{word}\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Operadores compuestos
        operator_format = create_format(COLOR_OPERATOR)
        comp_ops = [r'<=', r'>=', r'!=', r'==', r'&&', r'\|\|', r'\+\+', r'\-\-']
        for op in comp_ops:
            self.highlighting_rules.append((QRegularExpression(op), operator_format))

        # Operadores simples y asignación (incluye el punto)
        simple_ops = [r'\+', r'\-', r'\*', r'/', r'%', r'\^', r'<', r'>', r'!', r'=', r'\.']
        for op in simple_ops:
            self.highlighting_rules.append((QRegularExpression(op), operator_format))

        # Símbolos
        symbol_format = create_format(COLOR_SYMBOL)
        symbols = [r'\(', r'\)', r'\{', r'\}', r',', r';']
        for sym in symbols:
            self.highlighting_rules.append((QRegularExpression(sym), symbol_format))

        # Comentarios de una línea
        comment_format = create_format(COLOR_COMMENT)
        self.highlighting_rules.append(
            (QRegularExpression(r'//[^\n]*'), comment_format)
        )

        # Comentarios multilínea (estado especial)
        self.multiLineCommentFormat = comment_format
        self.commentStartExpression = QRegularExpression(r'/\*')
        self.commentEndExpression = QRegularExpression(r'\*/')

    def highlightBlock(self, text):
        # --- NUEVO: Formato por defecto para todo el bloque (gris claro) ---
        default_fmt = QTextCharFormat()
        default_fmt.setForeground(QColor("#D4D4D4"))
        self.setFormat(0, len(text), default_fmt)

        # Aplicar reglas estándar (sobrescriben el formato por defecto)
        for pattern, fmt in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # Manejo de comentarios multilínea
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