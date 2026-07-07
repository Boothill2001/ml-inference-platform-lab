import logging
import sys

from loguru import logger

from app.core.config import get_settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def configure_logging() -> None:
    settings = get_settings()
    logger.remove()
    serialize = settings.log_format.lower() == "json"
    logger.add(sys.stdout, level=settings.log_level.upper(), serialize=serialize)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

