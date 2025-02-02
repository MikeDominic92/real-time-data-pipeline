"""Custom logger for the Real-Time Data Pipeline."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from google.cloud import logging as cloud_logging
from google.cloud.logging.handlers import CloudLoggingHandler
from google.cloud.logging_v2.handlers.transports.sync import SyncTransport


class PipelineLogger:
    """Custom logger for the Real-Time Data Pipeline.

    Supports both local logging and Cloud Logging with structured logs.
    """

    def __init__(
        self,
        name: str,
        project_id: str,
        level: str = "INFO",
        use_cloud_logging: bool = True,
        log_file: Optional[str] = None,
    ) -> None:
        """Initialize the logger.

        Args:
            name: Logger name
            project_id: GCP project ID
            level: Logging level (default: INFO)
            use_cloud_logging: Whether to use Cloud Logging (default: True)
            log_file: Optional path to local log file
        """
        self.name = name
        self.project_id = project_id
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.use_cloud_logging = use_cloud_logging

        # Clear any existing handlers
        self.logger.handlers = []

        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(console_handler)

        # Add file handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(file_handler)

        # Add Cloud Logging handler if enabled
        if use_cloud_logging:
            self._setup_cloud_logging()

    def _get_formatter(self) -> logging.Formatter:
        """Get log formatter."""
        return logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    def _setup_cloud_logging(self) -> None:
        """Set up Google Cloud Logging."""
        client = cloud_logging.Client(project=self.project_id)
        handler = CloudLoggingHandler(client, name=self.name, transport=SyncTransport)
        self.logger.addHandler(handler)

    def _format_structured_log(
        self, message: str, severity: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """Format structured log entry.

        Args:
            message: Log message
            severity: Log severity
            **kwargs: Additional log fields

        Returns:
            Structured log entry
        """
        log_entry = {
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "logger": self.name,
        }
        log_entry.update(kwargs)
        return log_entry

    def log(self, severity: str, message: str, **kwargs: Any) -> None:
        """Log a message with structured data.

        Args:
            severity: Log severity
            message: Log message
            **kwargs: Additional log fields
        """
        structured_log = self._format_structured_log(
            message=message, severity=severity, **kwargs
        )

        log_message = json.dumps(structured_log)
        getattr(self.logger, severity.lower())(log_message)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self.log("CRITICAL", message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception message with traceback."""
        exc_info = sys.exc_info()
        kwargs["exc_info"] = {
            "type": str(exc_info[0]),
            "value": str(exc_info[1]),
            "traceback": self._format_traceback(exc_info[2]),
        }
        self.log("ERROR", message, **kwargs)

    @staticmethod
    def _format_traceback(tb: Any) -> str:
        """Format traceback for structured logging."""
        import traceback

        return "".join(traceback.format_tb(tb))
