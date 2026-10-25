import logging
import sys
from pathlib import Path
from app.core.config import settings

def setup_logger(name: str, log_filename: str, level=logging.INFO) -> logging.Logger:
    logs_dir = settings.get_path("logs_dir")
    log_file = logs_dir / log_filename

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(console_handler)

    return logger

app_logger = setup_logger("app", "app.log")
error_logger = setup_logger("error", "error.log", level=logging.ERROR)
jobs_logger = setup_logger("jobs", "jobs.log")