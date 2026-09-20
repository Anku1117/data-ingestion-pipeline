from __future__ import annotations

import logging
import sys
from typing import Any

from libraries.configuration.settings import get_settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json

        log_data: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        return json.dumps(log_data, default=str)


def setup_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if settings.is_production:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(logger_name).handlers.clear()
        logging.getLogger(logger_name).propagate = True

    logging.getLogger("uvicorn").setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
