"""
Centralized logging module for the RoboticImaging pipeline.

All modules must use: from utils.logger import logger
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


class Logger:
    """
    Production-ready logger for the Computer Vision pipeline.
    
    Provides unified logging interface across all modules.
    Logs to both console and file with proper formatting.
    """

    def __init__(self, name: str = "RoboticImaging", log_file: str = None):
        """
        Initialize the logger.

        Args:
            name: Logger name (default: "RoboticImaging")
            log_file: Optional file path for logging. If None, uses logs/roboimaging.log
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Create logs directory if needed
        if log_file is None:
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "roboimaging.log"
        else:
            log_file = Path(log_file)
            log_file.parent.mkdir(exist_ok=True, parents=True)

        # Remove any existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def log(self, message: str) -> None:
        """Log an info-level message."""
        self.logger.info(message)

    def debug(self, message: str) -> None:
        """Log a debug-level message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log an info-level message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log a warning-level message."""
        self.logger.warning(message)

    def error(self, message: str, exc_info: Exception = None) -> None:
        """
        Log an error-level message.

        Args:
            message: Error message
            exc_info: Optional exception object for traceback
        """
        if exc_info:
            self.logger.error(message, exc_info=exc_info)
        else:
            self.logger.error(message)

    def critical(self, message: str) -> None:
        """Log a critical-level message."""
        self.logger.critical(message)


# Global logger instance - use throughout the application
logger = Logger()
