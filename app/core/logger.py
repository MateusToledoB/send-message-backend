import logging
import sys

from app.core.settings import settings

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
        return

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
