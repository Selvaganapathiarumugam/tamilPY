from tpy.exceptions import TpyParseError
from tpy.parser.ast import (
    DatabaseNode,
    EnumNode,
    FieldNode,
    ForeignKeyNode,
    ModelNode,
    ProgramNode,
)
from tpy.parser.tokens import TokenType


_FK_ACTIONS = {
    TokenType.CASCADE: "cascade",
    TokenType.SET_NULL: "set_null",
    TokenType.RESTRICT: "restrict",
    TokenType.NO_ACTION: "no_action",
}


class Parser:
    """Parse tokenized ``schema.tpy`` into a ``ProgramNode`` AST."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def parse(self):
        program = ProgramNode()

        while not self.match(TokenType.EOF):
            if self.match(TokenType.NEWLINE):
                self.advance()
                continue

            if self.match(TokenType.DATABASE):
                program.database = self.parse_database()
                continue

            if self.match(TokenType.ENUM):
                program.enums.append(self.parse_enum())
                continue

            if self.match(TokenType.MODEL):
                program.models.append(self.parse_model())
                continue

            self.error(
                f"Unexpected token {self.current().type.name}"
            )

        return program

    def parse_database(self):
        self.consume(TokenType.DATABASE)
        provider = self.consume_any(
            TokenType.POSTGRES,
            TokenType.MYSQL,
            TokenType.SQLITE,
            TokenType.MONGODB,
        )
        return DatabaseNode(provider.value)

    def parse_enum(self) -> EnumNode:
        self.consume(TokenType.ENUM)
        name = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.LBRACE)
        values: list[str] = []
        while not self.match(TokenType.RBRACE):
            if self.match(TokenType.NEWLINE):
                self.advance()
                continue
            values.append(self.consume(TokenType.IDENTIFIER).value)
            if self.match(TokenType.COMMA):
                self.advance()
        self.consume(TokenType.RBRACE)
        return EnumNode(name=name, values=values)

    def parse_model(self):
        self.consume(TokenType.MODEL)
        name = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.LBRACE)

        fields = []
        unique_together: list[list[str]] = []

        while not self.match(TokenType.RBRACE):
            if self.match(TokenType.NEWLINE):
                self.advance()
                continue

            if self.match(TokenType.UNIQUE) and self._next_is(TokenType.LPAREN):
                unique_together.append(self.parse_unique_together())
                continue

            fields.append(self.parse_field())

        self.consume(TokenType.RBRACE)
        return ModelNode(
            name=name,
            fields=fields,
            unique_together=unique_together,
        )

    def parse_unique_together(self) -> list[str]:
        self.consume(TokenType.UNIQUE)
        self.consume(TokenType.LPAREN)
        columns: list[str] = []
        while not self.match(TokenType.RPAREN):
            if self.match(TokenType.NEWLINE):
                self.advance()
                continue
            columns.append(self.consume(TokenType.IDENTIFIER).value)
            if self.match(TokenType.COMMA):
                self.advance()
        self.consume(TokenType.RPAREN)
        if not columns:
            self.error("unique(...) requires at least one column")
        return columns

    def parse_field(self):
        name = self.consume(TokenType.IDENTIFIER).value
        self.consume(TokenType.COLON)

        datatype, enum_values = self.parse_datatype()

        constraints = []
        default_value = None
        has_default = False
        reference = None

        while True:
            if self.match(
                TokenType.PRIMARY,
                TokenType.REQUIRED,
                TokenType.UNIQUE,
                TokenType.NULLABLE,
                TokenType.INDEX,
            ):
                # Avoid treating unique(...) as a field constraint.
                if (
                    self.match(TokenType.UNIQUE)
                    and self._next_is(TokenType.LPAREN)
                ):
                    break
                constraints.append(self.current().value.lower())
                self.advance()
                continue

            if self.match(TokenType.DEFAULT):
                self.advance()
                default_value = self.parse_default_value()
                has_default = True
                continue

            if self.match(TokenType.REFERENCES, TokenType.FOREIGN):
                self.advance()
                reference = self.parse_reference()
                continue

            break

        return FieldNode(
            name=name,
            datatype=datatype,
            constraints=constraints,
            default=default_value,
            has_default=has_default,
            reference=reference,
            enum_values=enum_values,
        )

    def parse_datatype(self) -> tuple[str, list[str]]:
        if self.match(TokenType.ENUM):
            self.advance()
            if self.match(TokenType.LPAREN):
                self.advance()
                values: list[str] = []
                while not self.match(TokenType.RPAREN):
                    if self.match(TokenType.NEWLINE):
                        self.advance()
                        continue
                    values.append(self.consume(TokenType.IDENTIFIER).value)
                    if self.match(TokenType.COMMA):
                        self.advance()
                self.consume(TokenType.RPAREN)
                return "enum", values
            name = self.consume(TokenType.IDENTIFIER).value
            return f"enum:{name}", []

        token = self.consume_any(
            TokenType.INT,
            TokenType.STRING_TYPE,
            TokenType.FLOAT,
            TokenType.BOOL,
            TokenType.UUID,
            TokenType.DATETIME,
            TokenType.IDENTIFIER,
        )
        return token.value, []

    def parse_default_value(self):
        token = self.current()

        if token.type == TokenType.NUMBER:
            self.advance()
            return int(token.value)

        if token.type == TokenType.STRING:
            self.advance()
            return token.value

        if token.type == TokenType.IDENTIFIER:
            self.advance()
            lowered = token.value.lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False
            if lowered in ("null", "none"):
                return None
            return token.value

        self.error(f"Expected a default value, got {token.type.name}")

    def parse_reference(self):
        model = self.consume(TokenType.IDENTIFIER).value
        column = "id"

        if self.match(TokenType.DOT):
            self.advance()
            column = self.consume(TokenType.IDENTIFIER).value

        on_delete = None
        on_update = None
        while self.match(TokenType.ON_DELETE, TokenType.ON_UPDATE):
            kind = self.current().type
            self.advance()
            action_token = self.consume_any(*_FK_ACTIONS.keys())
            action = _FK_ACTIONS[action_token.type]
            if kind == TokenType.ON_DELETE:
                on_delete = action
            else:
                on_update = action

        return ForeignKeyNode(
            model=model,
            table=model.lower(),
            column=column,
            on_delete=on_delete,
            on_update=on_update,
        )

    def _next_is(self, token_type: TokenType) -> bool:
        nxt = self.position + 1
        if nxt >= len(self.tokens):
            return False
        return self.tokens[nxt].type == token_type

    def current(self):
        return self.tokens[self.position]

    def match(self, *types):
        return self.current().type in types

    def advance(self):
        self.position += 1

    def consume(self, token_type):
        if not self.match(token_type):
            self.error(
                f"Expected {token_type.name}, got {self.current().type.name}"
            )
        token = self.current()
        self.advance()
        return token

    def consume_any(self, *types):
        if not self.match(*types):
            expected = ", ".join(t.name for t in types)
            self.error(
                f"Expected one of [{expected}], got {self.current().type.name}"
            )
        token = self.current()
        self.advance()
        return token

    def error(self, message):
        token = self.current()
        raise TpyParseError(
            f"{message} (line {token.line}, column {token.column})"
        )
