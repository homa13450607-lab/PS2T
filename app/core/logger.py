import logging
from app.core.config import settings

def _make_logger(name: str, filename: str):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(getattr(logging, str(settings.get("logging", "level", "INFO")).upper(), logging.INFO))
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = logging.FileHandler(settings.logs_dir / filename, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console)
    return logger

app_logger = _make_logger("ps2t.app", "app.log")
error_logger = _make_logger("ps2t.error", "error.log")
jobs_logger = _make_logger("ps2t.jobs", "jobs.log")
