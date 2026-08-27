from __future__ import annotations

from pathlib import Path

import typer

from gerpgo_cli.output import execute_safely
from gerpgo_cli.skill_manager import SkillManager

app = typer.Typer(help="Install or atomically update the bundled gerpgo-erp Skill.")


def _manager(target_root: Path | None) -> SkillManager:
    return SkillManager(target_root=target_root)


@app.command("install")
def install(
    target_root: Path | None = typer.Option(None, help="Override the Codex skills directory."),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    execute_safely(
        lambda: _manager(target_root).install(),
        message="skill installed",
        output_format=output_format,
    )


@app.command("update")
def update(
    target_root: Path | None = typer.Option(None, help="Override the Codex skills directory."),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    execute_safely(
        lambda: _manager(target_root).update(),
        message="skill updated",
        output_format=output_format,
    )


@app.command("status")
def status(
    target_root: Path | None = typer.Option(None, help="Override the Codex skills directory."),
    output_format: str = typer.Option("json", "--format"),
) -> None:
    execute_safely(
        lambda: _manager(target_root).status(),
        message="skill status",
        output_format=output_format,
    )
