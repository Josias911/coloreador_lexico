import re
from dataclasses import dataclass

@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int

class LexError(Exception):
    def __init__(self, message, line, col):
        super().__init__(message)
        self.line = line
        self.col = col

class Lexer:
    """
    Configurable lexer. Defaults to a PSeInt/Pseudocódigo-like language
    with Spanish keywords used in cursos de Algoritmos.
    """
    def __init__(self, code:str, *, custom_keywords=None):
        self.code = code
        self.pos = 0
        self.line = 1
        self.col = 1
        # Default keywords (can be overridden)
        default_keywords = [
            "Algoritmo","FinAlgoritmo","Definir","Como","Entero","Real","Caracter",
            "Leer","Escribir","Si","Entonces","Sino","FinSi","Segun","Hacer","Caso",
            "De","Otro","Modo","FinSegun","Mientras","Repetir","Hasta","Que","Para",
            "FinMientras","FinPara","Funcion","FinFuncion","Procedimiento","Verdadero","Falso"
        ]
        self.keywords = set(custom_keywords or default_keywords)

        # Regex parts
        self.ws_re = re.compile(r'[ \t]+')
        self.nl_re = re.compile(r'\r\n|\r|\n')
        self.comment_line_re = re.compile(r'//[^\n\r]*')
        self.comment_block_re = re.compile(r'/\*.*?\*/', re.DOTALL)

        # Strings: "..." or '...'
        self.string_re = re.compile(r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'')

        # Numbers: int or float (e.g., 123, 45.67, .5, 5.)
        self.number_re = re.compile(r'(?:(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)')

        # Grouping symbols
        self.group_re = re.compile(r'[\(\)\[\]\{\}]')

        # Operators and logical/comparison words
        self.op_re = re.compile(r'(>=|<=|==|!=|<>|:=|&&|\|\||\+|-|\*|/|=|>|<|\^|,|;|\band\b|\bor\b|\bnot\b)', re.IGNORECASE)

        # Identifiers (including accented letters and underscore)
        self.ident_re = re.compile(r'[A-Za-zÁÉÍÓÚáéíóúÑñ_][A-Za-zÁÉÍÓÚáéíóúÑñ_0-9]*')

    def _advance(self, text):
        # update line/col with text consumed
        for ch in text:
            if ch == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
        self.pos += len(text)

    def _match(self, regex):
        return regex.match(self.code, self.pos)

    def tokens(self):
        while self.pos < len(self.code):
            # newline
            m = self._match(self.nl_re)
            if m:
                self._advance(m.group(0))
                yield Token("NL", "\\n", self.line-1, 1)
                continue

            # whitespace
            m = self._match(self.ws_re)
            if m:
                self._advance(m.group(0))
                continue

            # comments
            m = self._match(self.comment_line_re)
            if m:
                tok = Token("COMMENT", m.group(0), self.line, self.col)
                self._advance(m.group(0))
                yield tok
                continue

            m = self._match(self.comment_block_re)
            if m:
                block = m.group(0)
                tok = Token("COMMENT", block, self.line, self.col)
                self._advance(block)
                yield tok
                continue
