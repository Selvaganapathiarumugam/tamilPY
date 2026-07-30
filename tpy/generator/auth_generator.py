from __future__ import annotations

import re
import secrets
from pathlib import Path

from tpy.runtime.builder import Builder
from tpy.runtime.template_engine import TemplateEngine
from tpy.utils.file_manager import FileManager

AUTH_ROLE_BLOCK = """
model AuthRole {
  id: uuid primary
  name: string unique required
}
""".strip()

AUTH_USER_BLOCK = """
model User {
  id: uuid primary
  name: string required
  email: string unique required
  password: string required
  role_id: uuid references AuthRole
}
""".strip()


class AuthGenerator:
    """
    Generate JWT auth layers, default AuthRole/User schema, and seeds.
    """

    AUTH_FILES = {
        "app/security/jwt.py": "auth/security_jwt.py.j2",
        "app/middleware/auth.py": "auth/middleware_auth.py.j2",
        "app/schemas/auth.py": "auth/schemas_auth.py.j2",
        "app/services/auth.py": "auth/services_auth.py.j2",
        "app/controllers/auth.py": "auth/controllers_auth.py.j2",
        "app/routes/auth.py": "auth/routes_auth.py.j2",
        "database/seeds/auth_role_seed.py": "auth/seed_auth_role.py.j2",
    }

    def __init__(self, project_root: Path | str = ".") -> None:
        self.project_root = Path(project_root)
        self.template = TemplateEngine()

    def generate(self) -> int:
        """
        Enable auth for the project and regenerate CRUD from schema.

        Returns:
            Number of models after schema merge.
        """
        self.ensure_auth_schema()
        self.write_auth_files()
        self.ensure_package_inits()
        self.patch_env()
        self.patch_requirements()
        FileManager.write(self.project_root / ".tpy_auth", "enabled\n")

        ast = Builder(self.project_root).build()
        self.ensure_auth_router_included()
        self.refresh_admin_if_present(ast)
        return len(ast.models)

    def refresh_admin_if_present(self, ast) -> None:
        """Regenerate admin login/auth UI when admin/ already exists."""
        admin_dir = self.project_root / "admin"
        if not admin_dir.exists():
            return
        from tpy.generator.admin_generator import AdminGenerator

        api_base = "http://127.0.0.1:8000"
        config_path = admin_dir / "src" / "config.js"
        if config_path.exists():
            text = config_path.read_text(encoding="utf-8")
            match = re.search(
                r'API_BASE_URL\s*=\s*"([^"]+)"',
                text,
            )
            if match:
                api_base = match.group(1)
        AdminGenerator(self.project_root).generate(ast, api_base)

    def ensure_auth_schema(self) -> None:
        """Merge AuthRole + User auth fields into ``schema.tpy``."""
        schema_path = self.project_root / "schema.tpy"
        if not schema_path.exists():
            raise FileNotFoundError("schema.tpy not found.")

        text = schema_path.read_text(encoding="utf-8")

        if not re.search(r"\bmodel\s+AuthRole\b", text, re.IGNORECASE):
            text = self._insert_auth_role(text)

        if not re.search(r"\bmodel\s+User\b", text, re.IGNORECASE):
            text = text.rstrip() + "\n\n" + AUTH_USER_BLOCK + "\n"
        else:
            text = self._ensure_user_auth_fields(text)

        FileManager.write(schema_path, text)

    def _insert_auth_role(self, text: str) -> str:
        """Insert AuthRole before the first model (FK parent first)."""
        match = re.search(r"\bmodel\s+\w+", text, re.IGNORECASE)
        block = AUTH_ROLE_BLOCK + "\n\n"
        if match is None:
            return text.rstrip() + "\n\n" + AUTH_ROLE_BLOCK + "\n"
        return text[: match.start()] + block + text[match.start() :]

    def _ensure_user_auth_fields(self, text: str) -> str:
        """Add password/role_id to existing User model when missing."""
        match = re.search(
            r"(model\s+User\s*\{)(.*?)(\n\})",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match is None:
            return text.rstrip() + "\n\n" + AUTH_USER_BLOCK + "\n"

        body = match.group(2)
        additions = ""
        if not re.search(r"\bpassword\s*:", body, re.IGNORECASE):
            additions += "\n  password: string required"
        if not re.search(r"\brole_id\s*:", body, re.IGNORECASE):
            additions += "\n  role_id: uuid references AuthRole"
        if not additions:
            return text
        return (
            text[: match.start(2)]
            + body.rstrip()
            + additions
            + "\n"
            + text[match.start(3) :]
        )

    def write_auth_files(self) -> None:
        """Render and write auth application modules."""
        for relative, template_name in self.AUTH_FILES.items():
            output = self.project_root / relative
            FileManager.create_directory(output.parent)
            content = self.template.render(template_name, {})
            FileManager.write(output, content)

    def ensure_package_inits(self) -> None:
        """Ensure package markers for security and middleware."""
        for relative in ("app/security/__init__.py", "app/middleware/__init__.py"):
            path = self.project_root / relative
            if not path.exists():
                FileManager.write(path, "")

    def patch_env(self) -> None:
        """Append JWT settings to ``.env`` when missing."""
        env_path = self.project_root / ".env"
        existing = ""
        if env_path.exists():
            existing = env_path.read_text(encoding="utf-8")

        lines = []
        if "JWT_SECRET=" not in existing:
            lines.append(f"JWT_SECRET={secrets.token_urlsafe(32)}")
        if "JWT_ACCESS_EXPIRE_MINUTES=" not in existing:
            lines.append("JWT_ACCESS_EXPIRE_MINUTES=15")
        if "JWT_REFRESH_EXPIRE_DAYS=" not in existing:
            lines.append("JWT_REFRESH_EXPIRE_DAYS=7")

        if not lines:
            return

        suffix = "\n".join(lines) + "\n"
        if existing and not existing.endswith("\n"):
            existing += "\n"
        FileManager.write(
            env_path,
            existing + "\n# JWT auth (tpy auth)\n" + suffix,
        )

    def patch_requirements(self) -> None:
        """Ensure JWT packages are listed in project requirements."""
        req_path = self.project_root / "requirements.txt"
        existing = ""
        if req_path.exists():
            existing = req_path.read_text(encoding="utf-8")

        needed = ["PyJWT", "passlib[bcrypt]", "bcrypt<4.1"]
        additions = [
            package
            for package in needed
            if package.split("[")[0].lower() not in existing.lower()
        ]
        if not additions:
            return

        body = existing.rstrip() + "\n" + "\n".join(additions) + "\n"
        FileManager.write(req_path, body)

    def ensure_auth_router_included(self) -> None:
        """
        Ensure ``app/routes/__init__.py`` includes the auth router.

        RouteGenerator may already do this when ``.tpy_auth`` exists;
        this is a safety net after the first generate.
        """
        init_path = self.project_root / "app" / "routes" / "__init__.py"
        if not init_path.exists():
            return
        text = init_path.read_text(encoding="utf-8")
        if "app.routes.auth" in text:
            return

        lines = text.splitlines()
        insert_at = 0
        for index, line in enumerate(lines):
            if line.startswith("from app.routes."):
                insert_at = index + 1
        lines.insert(
            insert_at,
            "from app.routes.auth import router as auth_router",
        )

        if "api_router = APIRouter()" in text:
            out: list[str] = []
            for line in lines:
                out.append(line)
                if line.strip() == "api_router = APIRouter()":
                    out.append("api_router.include_router(auth_router)")
            FileManager.write(init_path, "\n".join(out) + "\n")
            return

        lines.append("api_router.include_router(auth_router)")
        FileManager.write(init_path, "\n".join(lines) + "\n")
