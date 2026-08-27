from __future__ import annotations

import os
import re
import shutil
from importlib import resources
from pathlib import Path
from uuid import uuid4

from gerpgo_sdk.common.errors import ConfigError, ValidationError

_VERSION_RE = re.compile(r'^\s*version:\s*["\']?([^"\'\s]+)', re.MULTILINE)


class SkillManager:
    def __init__(self, target_root: Path | None = None) -> None:
        codex_home = os.getenv("CODEX_HOME")
        self.target_root = target_root or (
            Path(codex_home) / "skills" if codex_home else Path.home() / ".codex" / "skills"
        )
        self.skill_name = "gerpgo-erp"

    @property
    def target(self) -> Path:
        return self.target_root / self.skill_name

    def install(self) -> dict[str, object]:
        if self.target.exists():
            raise ValidationError("Skill is already installed. Use 'gerpgo-cli skill update'.")
        self._replace_target()
        return self.status()

    def update(self) -> dict[str, object]:
        self._replace_target()
        return self.status()

    def status(self) -> dict[str, object]:
        source_version = self._version(self._source_skill_file())
        installed_version = (
            self._version(self.target / "SKILL.md") if self.target.exists() else None
        )
        return {
            "skill": self.skill_name,
            "installed": self.target.exists(),
            "path": self._display_path(self.target),
            "installed_version": installed_version,
            "bundled_version": source_version,
            "update_available": bool(
                installed_version and source_version and installed_version != source_version
            ),
        }

    def _replace_target(self) -> None:
        source = self._source_path()
        self.target_root.mkdir(parents=True, exist_ok=True)
        temp = self.target_root / f".{self.skill_name}.new-{uuid4().hex}"
        backup = self.target_root / f".{self.skill_name}.backup-{uuid4().hex}"
        shutil.copytree(source, temp)
        moved_existing = False
        try:
            if self.target.exists():
                os.replace(self.target, backup)
                moved_existing = True
            os.replace(temp, self.target)
        except OSError:
            if moved_existing and backup.exists() and not self.target.exists():
                os.replace(backup, self.target)
            raise
        finally:
            if temp.exists():
                shutil.rmtree(temp)
            if backup.exists() and self.target.exists():
                shutil.rmtree(backup)

    @staticmethod
    def _source_path() -> Path:
        packaged = resources.files("gerpgo_cli").joinpath("resources", "gerpgo-erp")
        try:
            packaged_path = Path(str(packaged))
            if packaged_path.is_dir():
                return packaged_path
        except TypeError:
            pass
        checkout = Path(__file__).resolve().parents[2] / "skills" / "gerpgo-erp"
        if checkout.is_dir():
            return checkout
        raise ConfigError("Bundled gerpgo-erp Skill could not be located.")

    def _source_skill_file(self) -> Path:
        return self._source_path() / "SKILL.md"

    @staticmethod
    def _display_path(path: Path) -> str:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(Path.home().resolve())
        except ValueError:
            return str(resolved)
        return str(Path("~") / relative)

    @staticmethod
    def _version(path: Path) -> str | None:
        if not path.exists():
            return None
        match = _VERSION_RE.search(path.read_text(encoding="utf-8"))
        return match.group(1) if match else None
