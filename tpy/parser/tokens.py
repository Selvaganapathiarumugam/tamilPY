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
    ENUM = auto()

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
    INDEX = auto()
    REFERENCES = auto()
    FOREIGN = auto()
    ON_DELETE = auto()
    ON_UPDATE = auto()
    CASCADE = auto()
    SET_NULL = auto()
    RESTRICT = auto()
    NO_ACTION = auto()

    # =========================
    # Symbols
    # =========================
    LBRACE = auto()
    RBRACE = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    EQUAL = auto()
    QUESTION = auto()


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
    "database": TokenType.DATABASE,
    "model": TokenType.MODEL,
    "enum": TokenType.ENUM,
    "postgres": TokenType.POSTGRES,
    "mysql": TokenType.MYSQL,
    "sqlite": TokenType.SQLITE,
    "mongodb": TokenType.MONGODB,
    "int": TokenType.INT,
    "string": TokenType.STRING_TYPE,
    "float": TokenType.FLOAT,
    "bool": TokenType.BOOL,
    "uuid": TokenType.UUID,
    "datetime": TokenType.DATETIME,
    "primary": TokenType.PRIMARY,
    "required": TokenType.REQUIRED,
    "unique": TokenType.UNIQUE,
    "nullable": TokenType.NULLABLE,
    "default": TokenType.DEFAULT,
    "index": TokenType.INDEX,
    "references": TokenType.REFERENCES,
    "foreign": TokenType.FOREIGN,
    "on_delete": TokenType.ON_DELETE,
    "on_update": TokenType.ON_UPDATE,
    "cascade": TokenType.CASCADE,
    "set_null": TokenType.SET_NULL,
    "restrict": TokenType.RESTRICT,
    "no_action": TokenType.NO_ACTION,
}
