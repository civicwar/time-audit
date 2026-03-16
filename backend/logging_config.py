import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.settings import BASE_DIR


LOG_DIR = Path(os.getenv("TIME_AUDIT_LOG_DIR", BASE_DIR / "logs"))
APP_LOG_FILE = Path(os.getenv("TIME_AUDIT_LOG_FILE", LOG_DIR / "time-audit.log"))
APP_LOG_LEVEL = os.getenv("TIME_AUDIT_LOG_LEVEL", "INFO").upper()
APP_LOG_MAX_BYTES = int(os.getenv("TIME_AUDIT_LOG_MAX_BYTES", str(5 * 1024 * 1024)))
APP_LOG_BACKUP_COUNT = int(os.getenv("TIME_AUDIT_LOG_BACKUP_COUNT", "5"))


def _has_file_handler(logger: logging.Logger) -> bool:
    target_path = APP_LOG_FILE.resolve()
    for handler in logger.handlers:
        base_filename = getattr(handler, "baseFilename", None)
        if not base_filename:
            continue
        try:
            if Path(base_filename).resolve() == target_path:
                return True
        except OSError:
            continue
    return False


def configure_application_logging() -> Path:
    APP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, APP_LOG_LEVEL, logging.INFO))

    if not _has_file_handler(root_logger):
        file_handler = RotatingFileHandler(
            APP_LOG_FILE,
            maxBytes=APP_LOG_MAX_BYTES,
            backupCount=APP_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, APP_LOG_LEVEL, logging.INFO))
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        root_logger.addHandler(file_handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logger = logging.getLogger(logger_name)
        logger.propagate = True

    return APP_LOG_FILE