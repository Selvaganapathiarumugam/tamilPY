from pathlib import Path

from tpy.exceptions import TpyParseError
from tpy.parser.tokens import Token, TokenType, KEYWORDS


class Lexer:

    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        tokens = []

        while self.position < len(self.source):
            ch = self.current()

            # whitespace
            if ch in (" ", "\t", "\r"):
                self.advance()
                continue

            # newline
            if ch == "\n":
                tokens.append(
                    Token(
                        TokenType.NEWLINE,
                        "\\n",
                        self.line,
                        self.column,
                    )
                )
                self.advance_line()
                continue

            # line comments
            if ch == "#":
                while (
                    self.position < len(self.source)
                    and self.current() != "\n"
                ):
                    self.advance()
                continue

            # identifier / keyword
            if ch.isalpha() or ch == "_":
                tokens.append(self.read_identifier())
                continue

            # number
            if ch.isdigit():
                tokens.append(self.read_number())
                continue

            # string
            if ch in ('"', "'"):
                tokens.append(self.read_string())
                continue

            # symbols
            symbol = self.read_symbol()

            if symbol:
                tokens.append(symbol)
                continue

            raise TpyParseError(
                f"Unexpected character '{ch}' "
                f"at line {self.line}, column {self.column}"
            )

        tokens.append(
            Token(
                TokenType.EOF,
                "",
                self.line,
                self.column,
            )
        )

        return tokens

    def current(self):
        return self.source[self.position]

    def advance(self):
        self.position += 1
        self.column += 1

    def advance_line(self):
        self.position += 1
        self.line += 1
        self.column = 1

    def read_identifier(self):

        start = self.column
        value = ""

        while (
            self.position < len(self.source)
            and (
                self.current().isalnum()
                or self.current() == "_"
            )
        ):
            value += self.current()
            self.advance()

        token_type = KEYWORDS.get(
            value.lower(),
            TokenType.IDENTIFIER,
        )

        return Token(
            token_type,
            value,
            self.line,
            start,
        )

    def read_number(self):

        start = self.column
        value = ""

        while (
            self.position < len(self.source)
            and self.current().isdigit()
        ):
            value += self.current()
            self.advance()

        return Token(
            TokenType.NUMBER,
            value,
            self.line,
            start,
        )

    def read_string(self):

        quote = self.current()
        start = self.column

        self.advance()

        value = ""

        while (
            self.position < len(self.source)
            and self.current() != quote
        ):
            value += self.current()
            self.advance()

        if self.position >= len(self.source):
            raise TpyParseError("Unterminated string literal")

        self.advance()

        return Token(
            TokenType.STRING,
            value,
            self.line,
            start,
        )

    def read_symbol(self):

        mapping = {
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ":": TokenType.COLON,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
            "=": TokenType.EQUAL,
            "?": TokenType.QUESTION,
        }

        token_type = mapping.get(self.current())

        if token_type is None:
            return None

        token = Token(
            token_type,
            self.current(),
            self.line,
            self.column,
        )

        self.advance()

        return token

    @classmethod
    def from_file(cls, path: str | Path):

        content = Path(path).read_text(
            encoding="utf-8"
        )

        return cls(content)