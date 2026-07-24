import importlib
import pkgutil
import typer
import tpy.commands

app = typer.Typer()

for _, module_name, _ in pkgutil.iter_modules(tpy.commands.__path__):
    module = importlib.import_module(f"tpy.commands.{module_name}")
    if hasattr(module, "register"):
        module.register(app)

if __name__ == "__main__":
    app()