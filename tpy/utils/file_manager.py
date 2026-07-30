import shutil
from pathlib import Path


class FileManager:

    @staticmethod
    def create_directory(path: Path):
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def write(path: Path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def read(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def exists(path: Path) -> bool:
        return path.exists()

    @staticmethod
    def copy(source: Path, destination: Path):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)