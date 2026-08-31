import logging
import sys
from typing import Any, Dict, Optional
from app.utils.config import get_settings


class ExecutionFormatter(logging.Formatter):
    """Custom formatter to format log lines with contextual execution fields."""

    def format(self, record: logging.LogRecord) -> str:
        base_msg = super().format(record)
        context_parts = []
        for key in ("execution_id", "step_id", "agent", "attempt", "status", "reason", "error_code"):
            val = getattr(record, key, None)
            if val is not None:
                context_parts.append(f"{key}={val}")

        if context_parts:
            return f"{base_msg} {' '.join(context_parts)}"
        return base_msg


def setup_logging() -> logging.Logger:
    settings = get_settings()
    logger = logging.getLogger("ai_agent_platform")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        formatter = ExecutionFormatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()


def get_logger() -> logging.Logger:
    return logger


def log_execution_event(
    level: str,
    event: str,
    execution_id: Optional[str] = None,
    step_id: Optional[str] = None,
    agent: Optional[str] = None,
    attempt: Optional[int] = None,
    status: Optional[str] = None,
    reason: Optional[str] = None,
    error_code: Optional[str] = None,
    extra_details: Optional[Dict[str, Any]] = None,
) -> None:
    extra = {
        "execution_id": execution_id,
        "step_id": step_id,
        "agent": agent,
        "attempt": attempt,
        "status": status,
        "reason": reason,
        "error_code": error_code,
    }
    if extra_details:
        extra.update(extra_details)

    level_name = level.lower()
    if level_name == "warn":
        level_name = "warning"
    log_func = getattr(logger, level_name, logger.info)
    log_func(event, extra=extra)
