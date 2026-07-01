"""Logging configuration for the trading bot."""

import logging
import re
from pathlib import Path
from typing import Any

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"
LOGGER_NAME = "trading_bot"

_SENSITIVE_PATTERNS = (
    (re.compile(r"(api_key=)[^&\s]+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(api_secret=)[^&\s]+", re.IGNORECASE), r"\1***"),
    (re.compile(r'("apiKey"\s*:\s*")[^"]+(")', re.IGNORECASE), r"\1***\2"),
    (re.compile(r'("secretKey"\s*:\s*")[^"]+(")', re.IGNORECASE), r"\1***\2"),
)


def redact_secrets(message: str) -> str:
    """Remove API keys and secrets from log messages."""
    redacted = message
    for pattern, replacement in _SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure application logging and return the trading bot logger."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger


def log_request(logger: logging.Logger, request: dict[str, Any]) -> None:
    """Log an outgoing order request."""
    logger.info("Request: %s", redact_secrets(str(request)))


def log_response(logger: logging.Logger, response: dict[str, Any]) -> None:
    """Log an order response from Binance."""
    logger.info("Response: %s", redact_secrets(str(response)))


def log_error(logger: logging.Logger, message: str, exc: Exception | None = None) -> None:
    """Log an error with optional exception details."""
    safe_message = redact_secrets(message)
    if exc is not None:
        logger.error("%s | %s: %s", safe_message, type(exc).__name__, exc)
    else:
        logger.error("%s", safe_message)
