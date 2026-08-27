from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any, TypeVar

import typer

from gerpgo_sdk.common.errors import GerpgoError
from gerpgo_sdk.common.redaction import redact
from gerpgo_sdk.common.response import ResultEnvelope

T = TypeVar("T")


def emit_success(data: Any, *, message: str = "success", output_format: str = "json") -> None:
    envelope = ResultEnvelope(ok=True, data=redact(data), message=message)
    if output_format == "json":
        typer.echo(_json_text(envelope.to_dict()))
        return
    if output_format == "table":
        typer.echo(_table(envelope.data))
        return
    raise typer.BadParameter("--format must be json or table")


def execute_safely(
    operation: Callable[[], T],
    *,
    message: str = "success",
    output_format: str = "json",
) -> T:
    try:
        result = operation()
    except GerpgoError as exc:
        envelope = ResultEnvelope(
            ok=False,
            data=redact(exc.details),
            message=exc.message,
            error_code=exc.code.value,
            trace_id=exc.trace_id or "",
        )
        typer.echo(_json_text(envelope.to_dict()), err=False)
        raise typer.Exit(code=2) from exc
    except (OSError, ValueError) as exc:
        envelope = ResultEnvelope(
            ok=False,
            data={},
            message=str(redact(str(exc))),
            error_code="GERPGO_VALIDATION_ERROR",
        )
        typer.echo(_json_text(envelope.to_dict()), err=False)
        raise typer.Exit(code=2) from exc
    emit_success(result, message=message, output_format=output_format)
    return result


def warn(message: str) -> None:
    print(message, file=sys.stderr)


def _json_text(data: Any, *, encoding: str | None = None) -> str:
    """Keep Unicode readable when possible and valid on legacy Windows consoles."""
    text = json.dumps(data, ensure_ascii=False, indent=2)
    target_encoding = encoding or getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(target_encoding)
    except (LookupError, UnicodeEncodeError):
        return json.dumps(data, ensure_ascii=True, indent=2)
    return text


def _table(data: Any) -> str:
    rows: list[dict[str, Any]]
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        rows = data
    elif isinstance(data, dict) and isinstance(data.get("rows"), list):
        rows = [item for item in data["rows"] if isinstance(item, dict)]
    elif isinstance(data, dict):
        rows = [{"field": key, "value": value} for key, value in data.items()]
    else:
        return str(data)
    if not rows:
        return "(no rows)"
    columns = list(dict.fromkeys(key for row in rows for key in row))[:12]
    rendered = [[_cell(row.get(column)) for column in columns] for row in rows]
    widths = [
        min(48, max(len(column), *(len(row[index]) for row in rendered)))
        for index, column in enumerate(columns)
    ]
    header = " | ".join(
        column[: widths[index]].ljust(widths[index]) for index, column in enumerate(columns)
    )
    separator = "-+-".join("-" * width for width in widths)
    body = [
        " | ".join(value[: widths[index]].ljust(widths[index]) for index, value in enumerate(row))
        for row in rendered
    ]
    return "\n".join([header, separator, *body])


def _cell(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)
