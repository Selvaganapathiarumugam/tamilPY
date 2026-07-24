from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # =========================
    # Special
    # =========================
    EOF = auto()
    NEWLINE = auto()

    # =========================
    # Identifiers & Literals
    # =========================
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # =========================
    # Keywords
    # =========================
    DATABASE = auto()
    MODEL = auto()

    # Database Providers
    POSTGRES = auto()
    MYSQL = auto()
    SQLITE = auto()
    MONGODB = auto()

    # =========================
    # Data Types
    # =========================
    INT = auto()
    STRING_TYPE = auto()
    FLOAT = auto()
    BOOL = auto()
    UUID = auto()
    DATETIME = auto()

    # =========================
    # Constraints
    # =========================
    PRIMARY = auto()
    REQUIRED = auto()
    UNIQUE = auto()
    NULLABLE = auto()
    DEFAULT = auto()

    # =========================
    # Symbols
    # =========================
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACKET = auto()    # [
    RBRACKET = auto()    # ]
    COLON = auto()       # :
    COMMA = auto()       # ,
    DOT = auto()         # .
    EQUAL = auto()       # =
    QUESTION = auto()    # ?


@dataclass(slots=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.type.name}({self.value}) [{self.line}:{self.column}]"

    def __repr__(self) -> str:
        return self.__str__()


KEYWORDS = {
    # Schema
    "database": TokenType.DATABASE,
    "model": TokenType.MODEL,

    # Providers
    "postgres": TokenType.POSTGRES,
    "mysql": TokenType.MYSQL,
    "sqlite": TokenType.SQLITE,
    "mongodb": TokenType.MONGODB,

    # Types
    "int": TokenType.INT,
    "string": TokenType.STRING_TYPE,
    "float": TokenType.FLOAT,
    "bool": TokenType.BOOL,
    "uuid": TokenType.UUID,
    "datetime": TokenType.DATETIME,

    # Constraints
    "primary": TokenType.PRIMARY,
    "required": TokenType.REQUIRED,
    "unique": TokenType.UNIQUE,
    "nullable": TokenType.NULLABLE,
    "default": TokenType.DEFAULT,
}