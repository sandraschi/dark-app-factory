import logging
import os
import zipfile
from logging.handlers import RotatingFileHandler
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler


class DarkLogger:
    """
    A unified logging system for Dark App Factory.
    Combines Rich UI for console output and standard logging for file persistence.
    """

    _instance = None
    _console = Console()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DarkLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.logger = logging.getLogger("dark_factory")
        self.logger.setLevel(logging.DEBUG)

        # Ensure logs directory exists
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)

        self.log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(self.log_dir, exist_ok=True)

        # Define the base log file path for rotation
        self.log_file = os.path.join(self.log_dir, "factory.log")

        # File Handler (with rotation: 5MB per file, 5 backups)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler = RotatingFileHandler(
            self.log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(file_formatter)

        # Rich Console Handler (Interactive)
        rich_handler = RichHandler(
            console=self._console, rich_tracebacks=True, markup=True, show_path=False
        )
        rich_handler.setLevel(logging.INFO)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(rich_handler)

        self._initialized = True

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str, exc_info=False):
        self.logger.error(message, exc_info=exc_info)

    def debug(self, message: str):
        self.logger.debug(message)

    def success(self, message: str):
        self.logger.info(f"SUCCESS: {message}")

    def audit(self, message: str):
        """Specialized logging for Satisficer verdicts."""
        self.logger.info(f"VERDICT: {message}")

    def tail(self, n: int = 50) -> list:
        """Returns the last n lines of the log file."""
        if not os.path.exists(self.log_file):
            return []
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return lines[-n:]

    def export(self, output_path: str = None) -> str:
        """Exports all logs in the log directory to a zip file."""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.log_dir, f"dark_app_logs_{timestamp}.zip")

        with zipfile.ZipFile(output_path, "w", zipfile.Z_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.log_dir):
                for file in files:
                    if file.endswith(".log") or file.endswith(".txt"):
                        zipf.write(
                            os.path.join(root, file),
                            os.path.relpath(os.path.join(root, file), self.log_dir),
                        )

        return output_path


# Global logger instance
logger = DarkLogger()
