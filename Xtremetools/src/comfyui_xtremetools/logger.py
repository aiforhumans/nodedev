"""Centralized logging utilities for Xtremetools."""
from __future__ import annotations

import logging
import os
from typing import Final

# Copilot: keep docstrings synchronized with logging helpers.

_LOGGER_INITIALIZED: Final[dict[str, bool]] = {"configured": False}


def _configure_root_logger() -> None:
    if _LOGGER_INITIALIZED["configured"]:
        return

    level_name = os.getenv("XTREMETOOLS_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    _LOGGER_INITIALIZED["configured"] = True


def get_logger(name: str = "xtremetools") -> logging.Logger:
    """Return a namespaced logger configured with timestamps + levels."""

    _configure_root_logger()
    return logging.getLogger(name)


__all__ = ["get_logger"]
