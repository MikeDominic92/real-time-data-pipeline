"""Monitoring service for the Real-Time Data Pipeline."""

import os
import threading
import time
from typing import Any, Dict, Optional

import psutil
import yaml

from rtdp.monitoring.alerts import AlertManager
from rtdp.monitoring.logger import PipelineLogger
from rtdp.monitoring.metrics import MetricsCollector


class MonitoringService:
    """Central monitoring service for the Real-Time Data Pipeline."""

    def __init__(
        self, project_id: str, config_path: str, service_name: str = "rtdp"
    ) -> None:
        """Initialize the monitoring service.

        Args:
            project_id: GCP project ID
            config_path: Path to monitoring configuration file
            service_name: Name of the service
        """
        self.project_id = project_id
        self.service_name = service_name
        self.config = self._load_config(config_path)

        # Initialize components
        self._setup_logger()
        self._setup_metrics()
        self._setup_alerts()

        # Start system metrics collection
        self._start_system_metrics_collection()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load monitoring configuration.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _setup_logger(self) -> None:
        """Set up logging component."""
        log_config = self.config["logging"]

        # Create logs directory if it doesn't exist
        if log_config.get("log_file"):
            os.makedirs(os.path.dirname(log_config["log_file"]), exist_ok=True)

        self.logger = PipelineLogger(
            name=self.service_name,
            project_id=self.project_id,
            level=log_config.get("level", "INFO"),
            use_cloud_logging=log_config.get("use_cloud_logging", True),
            log_file=log_config.get("log_file"),
        )

    def _setup_metrics(self) -> None:
        """Set up metrics collection."""
        metrics_config = self.config["metrics"]
        self.metrics = MetricsCollector(
            project_id=self.project_id,
            metric_prefix=metrics_config.get("prefix", "custom.googleapis.com/rtdp"),
        )

    def _setup_alerts(self) -> None:
        """Set up alerting system."""
        alerts_config = self.config["alerts"]
        notification_channels = [
            channel["name"] for channel in self.config.get("notification_channels", [])
        ]

        self.alerts = AlertManager(
            project_id=self.project_id, notification_channels=notification_channels
        )

        # Create alert policies
        self._create_alert_policies(alerts_config)

    def _create_alert_policies(self, alerts_config: Dict[str, Any]) -> None:
        """Create alert policies from configuration.

        Args:
            alerts_config: Alert configuration dictionary
        """
        # Latency alerts
        if "processing_latency" in alerts_config:
            self.alerts.create_latency_alert(
                metric_type="processing_latency",
                threshold_seconds=alerts_config["processing_latency"][
                    "threshold_seconds"
                ],
                duration_seconds=alerts_config["processing_latency"][
                    "duration_seconds"
                ],
            )

        # Error rate alerts
        if "error_rate" in alerts_config:
            self.alerts.create_error_rate_alert(
                metric_type="error_rate",
                threshold_rate=alerts_config["error_rate"]["threshold_rate"],
                duration_seconds=alerts_config["error_rate"]["duration_seconds"],
            )

        # Throughput alerts
        if "low_throughput" in alerts_config:
            self.alerts.create_throughput_alert(
                metric_type="messages_processed",
                min_throughput=alerts_config["low_throughput"]["min_messages"],
                duration_seconds=alerts_config["low_throughput"]["duration_seconds"],
            )

    def _collect_system_metrics(self) -> None:
        """Collect and record system metrics."""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics.record_gauge(
                    name="system/cpu_usage", value=cpu_percent, labels={"type": "cpu"}
                )

                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics.record_gauge(
                    name="system/memory_usage",
                    value=memory.percent,
                    labels={"type": "memory"},
                )

                # Disk usage
                disk = psutil.disk_usage("/")
                self.metrics.record_gauge(
                    name="system/disk_usage",
                    value=disk.percent,
                    labels={"type": "disk"},
                )

                time.sleep(60)  # Collect every minute
            except Exception as e:
                self.logger.error("Error collecting system metrics", error=str(e))

    def _start_system_metrics_collection(self) -> None:
        """Start system metrics collection in a background thread."""
        thread = threading.Thread(target=self._collect_system_metrics, daemon=True)
        thread.start()

    def record_message_received(self) -> None:
        """Record a message received metric."""
        self.metrics.record_counter("messages_received")
        self.logger.info("Message received")

    def record_message_processed(
        self, processing_time: float, success: bool = True
    ) -> None:
        """Record message processing metrics.

        Args:
            processing_time: Time taken to process the message
            success: Whether processing was successful
        """
        if success:
            self.metrics.record_counter("messages_processed")
            self.metrics.record_latency(
                name="processing_latency", latency=processing_time
            )
            self.logger.info(
                "Message processed successfully", processing_time=processing_time
            )
        else:
            self.metrics.record_counter("messages_failed")
            self.logger.error(
                "Message processing failed", processing_time=processing_time
            )

    def record_batch_processed(self, batch_size: int, processing_time: float) -> None:
        """Record batch processing metrics.

        Args:
            batch_size: Size of the processed batch
            processing_time: Time taken to process the batch
        """
        self.metrics.record_batch_size(name="batch_size", size=batch_size)
        self.metrics.record_latency(
            name="batch_processing_time", latency=processing_time
        )
        self.logger.info(
            "Batch processed", batch_size=batch_size, processing_time=processing_time
        )

    def record_error(self, error_type: str, error_message: str, **kwargs: Any) -> None:
        """Record an error.

        Args:
            error_type: Type of error
            error_message: Error message
            **kwargs: Additional error context
        """
        self.metrics.record_error(f"errors/{error_type}")
        self.logger.error(error_message, error_type=error_type, **kwargs)

    def record_pipeline_latency(self, start_time: float, end_time: float) -> None:
        """Record end-to-end pipeline latency.

        Args:
            start_time: Pipeline start time
            end_time: Pipeline end time
        """
        latency = end_time - start_time
        self.metrics.record_latency(name="end_to_end_latency", latency=latency)
        self.logger.info("Pipeline latency recorded", latency=latency)
