"""
Enterprise Logging Configuration Module.
Configures root logger, handlers, log levels, and stdout outputs.
"""

import sys
import logging
from typing import Optional


def configure_logger(name: str = "hrlense", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns the central framework logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Check for pytest flags (-v, -s) or LOG_LEVEL env
        argv_str = " ".join(sys.argv).lower()
        if "-v" in argv_str or "-s" in argv_str or "debug" in argv_str:
            console_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
