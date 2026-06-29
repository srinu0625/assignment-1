"""
=========================================================
Market Intelligence Monitor (MIM)
Logger
=========================================================
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from config import LOG_FOLDER

# -------------------------------------------------------
# Create logs folder if it doesn't exist
# -------------------------------------------------------
os.makedirs(LOG_FOLDER, exist_ok=True)

LOG_FILE = os.path.join(LOG_FOLDER, "market_monitor.log")

# -------------------------------------------------------
# Configure logger
# -------------------------------------------------------
logger = logging.getLogger("MarketMonitor")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers if imported multiple times
if not logger.handlers:

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=5,
        encoding="utf-8"
    )

    console_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# -------------------------------------------------------
# Helper functions
# -------------------------------------------------------
def info(message):
    logger.info(message)


def warning(message):
    logger.warning(message)


def error(message):
    logger.error(message)


def critical(message):
    logger.critical(message)


def debug(message):
    logger.debug(message)