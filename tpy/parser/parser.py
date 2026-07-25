from tpy.parser.ast import (
    DatabaseNode,
    FieldNode,
    ForeignKeyNode,
    ModelNode,
    ProgramNode,
)
from tpy.parser.tokens import TokenType


class Parser:

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

            if self.match(TokenType.MODEL):
                program.models.append(
                    self.parse_model()
                )
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

    def parse_model(self):

        self.consume(TokenType.MODEL)

        name = self.consume(
            TokenType.IDENTIFIER
        ).value

        self.consume(TokenType.LBRACE)

        fields = []

        while not self.match(TokenType.RBRACE):

            if self.match(TokenType.NEWLINE):
                self.advance()
                continue

            fields.append(
                self.parse_field()
            )

        self.consume(TokenType.RBRACE)

        return ModelNode(
            name=name,
            fields=fields,
        )

    def parse_field(self):

        name = self.consume(
            TokenType.IDENTIFIER
        ).value

        self.consume(TokenType.COLON)

        datatype = self.consume_any(
            TokenType.INT,
            TokenType.STRING_TYPE,
            TokenType.FLOAT,
            TokenType.BOOL,
            TokenType.UUID,
            TokenType.DATETIME,
        ).value

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
                constraints.append(
                    self.current().value.lower()
                )
                self.advance()
                continue

            if self.match(TokenType.DEFAULT):
                self.advance()
                default_value = self.parse_default_value()
                has_default = True
                continue

            if self.match(
                TokenType.REFERENCES,
                TokenType.FOREIGN,
            ):
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
        )

    def parse_default_value(self):
        """
        Parse a literal default value.

        Accepts a number, quoted string, or the bare words
        ``true`` / ``false`` / ``null``.
        """
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

        self.error(
            f"Expected a default value, got {token.type.name}"
        )

    def parse_reference(self):
        """
        Parse a foreign-key target: ``<Model>`` or ``<Model>.<column>``.
        """
        model = self.consume(TokenType.IDENTIFIER).value
        column = "id"

        if self.match(TokenType.DOT):
            self.advance()
            column = self.consume(TokenType.IDENTIFIER).value

        return ForeignKeyNode(
            model=model,
            table=model.lower(),
            column=column,
        )

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
            expected = ", ".join(
                t.name for t in types
            )
            self.error(
                f"Expected one of [{expected}], got {self.current().type.name}"
            )

        token = self.current()

        self.advance()

        return token

    def error(self, message):
        token = self.current()

        raise SyntaxError(
            f"{message} "
            f"(line {token.line}, column {token.column})"
        )