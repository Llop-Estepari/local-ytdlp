"""Local file logging."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .config import Settings


def setup_logging(settings: Settings) -> logging.Logger:
    logger = logging.getLogger("local_ytdlp")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    try:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            settings.log_dir / "app.log",
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        logger.warning("No se pudo crear el archivo de log local.")

    return logger
