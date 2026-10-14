"""Logging configuration for retail analytics pipeline."""

from __future__ import annotations

import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure a unified, readable console logger.

    Parameters
    ----------
    level : int, default logging.INFO
        Logging verbosity level.

    Returns
    -------
    logging.Logger
        Configured root pipeline logger.
    """
    logger = logging.getLogger("retail_analytics")
    logger.setLevel(level)

    # Avoid adding duplicate handlers if reconfigured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_logger() -> logging.Logger:
    """Retrieve the retail analytics logger."""
    return logging.getLogger("retail_analytics")

