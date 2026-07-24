from tpy.parser.ast import (
    DatabaseNode,
    FieldNode,
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

        while True:

            if self.match(
                TokenType.PRIMARY,
                TokenType.REQUIRED,
                TokenType.UNIQUE,
                TokenType.NULLABLE,
            ):
                constraints.append(
                    self.current().value
                )
                self.advance()
                continue

            break

        return FieldNode(
            name=name,
            datatype=datatype,
            constraints=constraints,
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