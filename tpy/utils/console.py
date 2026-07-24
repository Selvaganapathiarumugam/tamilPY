import typer


class Console:

    @staticmethod
    def info(message: str):
        typer.secho(message, fg=typer.colors.CYAN)

    @staticmethod
    def success(message: str):
        typer.secho(message, fg=typer.colors.GREEN)

    @staticmethod
    def warning(message: str):
        typer.secho(message, fg=typer.colors.YELLOW)

    @staticmethod
    def error(message: str):
        typer.secho(message, fg=typer.colors.RED)