from __future__ import annotations

import logging
import sys

from .redaction import redact_text


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact_text(super().format(record))


def configure_logging(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("gerpgo")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG if verbose else logging.WARNING)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(RedactingFormatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
