import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "backend.log"


def configure_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    if not any(getattr(handler, "_backend_console_handler", False) for handler in root_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler._backend_console_handler = True
        root_logger.addHandler(console_handler)

    if not any(getattr(handler, "_backend_file_handler", False) for handler in root_logger.handlers):
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=5 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler._backend_file_handler = True
            root_logger.addHandler(file_handler)
        except OSError as exc:
            root_logger.warning("File logging disabled: %s", exc)
