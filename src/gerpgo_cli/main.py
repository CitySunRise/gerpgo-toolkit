from __future__ import annotations

import typer

from gerpgo_cli import __version__
from gerpgo_cli.commands import openapi, profile, skill, web_auth
from gerpgo_cli.commands.capabilities import capabilities
from gerpgo_cli.commands.doctor import doctor
from gerpgo_sdk.common.logging import configure_logging

app = typer.Typer(
    name="gerpgo-cli",
    help="Cross-platform CLI for approved Gerpgo ERP interfaces.",
    no_args_is_help=True,
)
web_app = typer.Typer(help="Web authentication foundation; business Web APIs are not implemented.")
web_app.add_typer(web_auth.app, name="auth")

app.add_typer(profile.app, name="profile")
app.add_typer(openapi.app, name="openapi")
app.add_typer(web_app, name="web")
app.add_typer(skill.app, name="skill")
app.command("capabilities")(capabilities)
app.command("doctor")(doctor)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", help="Write diagnostic logs to stderr."),
) -> None:
    configure_logging(verbose)


@app.command("version")
def version() -> None:
    typer.echo(__version__)


if __name__ == "__main__":
    app()
