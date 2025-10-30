import logging
import os

from asgi_correlation_id import CorrelationIdFilter

env = os.getenv("DJANGO_ENV", "dev")


def obfuscated(email: str, obfuscated_length: int) -> str:
    """Obfuscate the email by replacing characters with asterisks."""
    first, last = email.split("@")
    return (
        first[:obfuscated_length]
        + ("*" * (len(first) - obfuscated_length))
        + "@"
        + last
    )


class EmailObfuscationFilter(logging.Filter):
    """Filter to obfuscate email addresses in log records."""

    def __init__(self, name: str = "", obfuscated_length: int = 2) -> None:
        super().__init__(name)
        self.obfuscated_length = obfuscated_length

    def filter(self, record: logging.LogRecord) -> bool:
        """Obfuscates the email in the log record if it exists."""
        if "email" in record.__dict__:
            record.email = obfuscated(record.email, self.obfuscated_length)
        return True


def get_logging_config() -> None:
    """Get the logging configuration dictionary."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": CorrelationIdFilter,
                "uuid_length": 8 if env == "dev" else 32,
                "default_value": "-",
            },
            "email_obfuscation": {
                "()": EmailObfuscationFilter,
                "obfuscated_length": 2 if env == "dev" else 0,
            },
        },
        "formatters": {
            "console": {
                "class": "logging.Formatter",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
                "format": "(%(correlation_id)s) %(name)s:%(lineno)d - %(message)s",
            },
            "file": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
                "format": "%(asctime)s.%(msecs)03d %(levelname)-8s %(correlation_id)s %(name)s:%(lineno)d - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "class": "rich.logging.RichHandler",
                "level": "DEBUG",
                "formatter": "console",
                "filters": ["correlation_id", "email_obfuscation"],
            },
            "rotating_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "file",
                "filename": "myrabbai.log",
                "maxBytes": 1024 * 1024,  # 1MB
                "backupCount": 2,
                "encoding": "utf8",
                "filters": ["correlation_id"],
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default", "rotating_file"], "level": "INFO"},
            "django": {
                "handlers": ["default", "rotating_file"],
                "level": "INFO",
                "propagate": False,
            },
            "django.request": {
                "handlers": ["default"],
                "level": "DEBUG",
                "propagate": False,
            },
            "django.db.backends": {
                "handlers": ["default", "rotating_file"],
                "level": "INFO",
                "propagate": False,
            },
            "backend": {
                "handlers": ["default"],
                "level": "DEBUG" if env == "dev" else "INFO",
                "propagate": False,
            },
            "authentication": {},
        },
    }
