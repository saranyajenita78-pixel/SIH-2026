"""
src/utils/logging_config.py
Shared logging configuration. All modules obtain their logger via get_logger().
"""

import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

_LOG_FILE = os.path.join(config.LOGS_DIR, "app.log")

_configured = False


def _configure_root():
    global _configured
    if _configured:
        return
    handlers = [
        logging.FileHandler(_LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=handlers,
    )
    _configured = True


def get_logger(name):
    _configure_root()
    return logging.getLogger(name)
