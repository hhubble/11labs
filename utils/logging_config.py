import logging
import sys
from pathlib import Path


def setup_logging(log_file: Path = None, log_level: str = "INFO"):
    """
    Set up logging configuration for the entire application
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure the root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Console handler
        ],
    )

    # Add file handler if log file is specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(file_handler)

    # Set some common third-party loggers to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
