from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class ResultEnvelope:
    ok: bool
    data: Any
    message: str
    error_code: str | None = None
    trace_id: str = ""

    def __post_init__(self) -> None:
        if not self.trace_id:
            self.trace_id = uuid4().hex

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
