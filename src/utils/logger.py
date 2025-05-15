import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).resolve().parents[2] / "logs"
os.makedirs(logs_dir, exist_ok=True)


def get_logger(name: str):
    """Get a logger with the specified name."""
    logger = logging.getLogger(name)
    return logger


def setup_logging():
    """Setup logging configuration with daily rotation."""
    log_file = os.path.join(logs_dir, "app.log")

    # Create a rotating file handler that rotates daily
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,  # Keep logs for 30 days
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


# 忽略 Tortoise ORM 相关日志
logging.getLogger("tortoise").setLevel(logging.WARNING)
logging.getLogger("tortoise.models").setLevel(logging.WARNING)
logging.getLogger("tortoise.db_client").setLevel(logging.WARNING)
logging.getLogger("tortoise.backends").setLevel(logging.WARNING)
logging.getLogger("tortoise.transactions").setLevel(logging.WARNING)


# Initialize logging when the module is imported
setup_logging()
# logger = logging.getLogger(__name__)
