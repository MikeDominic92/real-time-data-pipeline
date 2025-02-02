"""Metrics collector for the Real-Time Data Pipeline."""

import time
from typing import Dict, Optional

from google.cloud import monitoring_v3


class MetricsCollector:
    """Collect and report metrics to Cloud Monitoring."""

    def __init__(self, project_id: str, metric_prefix: str = "custom.googleapis.com/rtdp") -> None:
        """Initialize metrics collector.

        Args:
            project_id: GCP project ID
            metric_prefix: Prefix for custom metrics
        """
        self.project_id = project_id
        self.metric_prefix = metric_prefix
        self.client = monitoring_v3.MetricServiceClient()
        self.project_path = f"projects/{project_id}"

    def create_time_series(
        self,
        metric_type: str,
        value: float,
        metric_kind: str,
        value_type: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Create a new time series in Cloud Monitoring.

        Args:
            metric_type: Type of metric to create
            value: Metric value
            metric_kind: Kind of metric (GAUGE, DELTA, CUMULATIVE)
            value_type: Type of value (INT64, DOUBLE, BOOL)
            labels: Optional metric labels
        """
        series = monitoring_v3.TimeSeries()
        series.metric.type = f"{self.metric_prefix}/{metric_type}"

        if labels:
            series.metric.labels.update(labels)

        # Add resource labels
        series.resource.type = "generic_task"
        series.resource.labels["project_id"] = self.project_id
        series.resource.labels["location"] = "global"
        series.resource.labels["namespace"] = "rtdp"
        series.resource.labels["job"] = "pipeline"

        # Create the data point
        point = series.points.add()

        if value_type == "INT64":
            point.value.int64_value = int(value)
        elif value_type == "DOUBLE":
            point.value.double_value = float(value)
        elif value_type == "BOOL":
            point.value.bool_value = bool(value)

        now = time.time()
        point.interval.end_time.seconds = int(now)
        point.interval.end_time.nanos = int((now - int(now)) * 10**9)

        self.client.create_time_series(request={"name": self.project_path, "time_series": [series]})

    def record_counter(
        self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a counter metric.

        Args:
            name: Metric name
            value: Counter value
            labels: Optional metric labels
        """
        self.create_time_series(
            metric_type=f"counter/{name}",
            value=value,
            metric_kind="CUMULATIVE",
            value_type="INT64",
            labels=labels,
        )

    def record_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a gauge metric.

        Args:
            name: Metric name
            value: Gauge value
            labels: Optional metric labels
        """
        self.create_time_series(
            metric_type=f"gauge/{name}",
            value=value,
            metric_kind="GAUGE",
            value_type="DOUBLE",
            labels=labels,
        )

    def record_latency(
        self, name: str, latency: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a latency metric.

        Args:
            name: Metric name
            latency: Latency value in seconds
            labels: Optional metric labels
        """
        self.create_time_series(
            metric_type=f"latency/{name}",
            value=latency,
            metric_kind="GAUGE",
            value_type="DOUBLE",
            labels=labels,
        )

    def record_batch_size(
        self, name: str, size: int, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a batch size metric.

        Args:
            name: Metric name
            size: Batch size
            labels: Optional metric labels
        """
        self.create_time_series(
            metric_type=f"batch_size/{name}",
            value=size,
            metric_kind="GAUGE",
            value_type="INT64",
            labels=labels,
        )

    def record_error(self, name: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Record an error metric.

        Args:
            name: Error metric name
            labels: Optional metric labels
        """
        self.record_counter(name=f"errors/{name}", value=1, labels=labels)

    def record_success(self, name: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a success metric.

        Args:
            name: Success metric name
            labels: Optional metric labels
        """
        self.record_counter(name=f"successes/{name}", value=1, labels=labels)
