"""Performance test runner for the Real-Time Data Pipeline."""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from google.cloud import bigquery, monitoring_v3

from rtdp.monitoring.metrics import MetricsCollector
from rtdp.perf.load_generator import LoadGenerator


@dataclass
class TestResult:
    """Results of a performance test."""

    test_name: str
    start_time: datetime
    end_time: datetime
    messages_sent: int
    messages_processed: int
    avg_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    errors: int
    throughput: float


class PerformanceTestRunner:
    """Run performance tests for the Real-Time Data Pipeline."""

    def __init__(self, project_id: str, topic_id: str, dataset_id: str, table_id: str) -> None:
        """Initialize test runner.

        Args:
            project_id: GCP project ID
            topic_id: Pub/Sub topic ID
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
        """
        self.project_id = project_id
        self.topic_id = topic_id
        self.dataset_id = dataset_id
        self.table_id = table_id

        # Initialize clients
        self.metrics = MetricsCollector(
            project_id=project_id, metric_prefix="custom.googleapis.com/rtdp/perf"
        )
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.bq_client = bigquery.Client(project=project_id)

        # Initialize load generator
        self.load_generator = LoadGenerator(
            project_id=project_id, topic_id=topic_id, metrics_collector=self.metrics
        )

    def _get_metric_stats(
        self,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        percentiles: Optional[List[float]] = None,
    ) -> Tuple[float, Dict[float, float]]:
        """Get metric statistics from Cloud Monitoring.

        Args:
            metric_type: Type of metric to query
            start_time: Start time
            end_time: End time
            percentiles: Optional percentiles to calculate

        Returns:
            Tuple of (average, percentiles dict)
        """
        project_name = f"projects/{self.project_id}"
        interval = monitoring_v3.TimeInterval(
            {
                "start_time": start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z",
            }
        )

        results = self.monitoring_client.list_time_series(
            request={
                "name": project_name,
                "filter": f'metric.type = "{metric_type}"',
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            }
        )

        values = []
        for result in results:
            for point in result.points:
                values.append(point.value.double_value)

        if not values:
            return 0.0, {p: 0.0 for p in (percentiles or [])}

        avg = sum(values) / len(values)
        percentile_values = {}

        if percentiles:
            sorted_values = sorted(values)
            for p in percentiles:
                index = int(len(sorted_values) * p)
                percentile_values[p] = sorted_values[index]

        return avg, percentile_values

    def _get_message_counts(
        self, start_time: datetime, end_time: datetime, batch_id: Optional[str] = None
    ) -> Tuple[int, int]:
        """Get message counts from BigQuery.

        Args:
            start_time: Start time
            end_time: End time
            batch_id: Optional batch ID to filter

        Returns:
            Tuple of (messages sent, messages processed)
        """
        query = f"""
        WITH sent AS (
            SELECT COUNT(*) as count
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            WHERE timestamp BETWEEN @start_time AND @end_time
            {"AND batch_id = @batch_id" if batch_id else ""}
        ),
        processed AS (
            SELECT COUNT(*) as count
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            WHERE processed_timestamp IS NOT NULL
            AND timestamp BETWEEN @start_time AND @end_time
            {"AND batch_id = @batch_id" if batch_id else ""}
        )
        SELECT sent.count as sent, processed.count as processed
        FROM sent, processed
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time),
                bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time),
            ]
        )

        if batch_id:
            job_config.query_parameters.append(
                bigquery.ScalarQueryParameter("batch_id", "STRING", batch_id)
            )

        results = self.bq_client.query(query, job_config=job_config).result()
        row = next(iter(results))
        return row.sent, row.processed

    def run_constant_load_test(self, messages_per_second: int, duration_seconds: int) -> TestResult:
        """Run constant load test.

        Args:
            messages_per_second: Number of messages per second
            duration_seconds: Test duration in seconds

        Returns:
            Test results
        """
        test_name = f"constant_load_{messages_per_second}mps"
        start_time = datetime.utcnow()

        try:
            self.load_generator.generate_constant_load(messages_per_second, duration_seconds)
        finally:
            self.load_generator.stop()
            self.load_generator.wait_for_completion()

        # Allow time for processing
        time.sleep(60)
        end_time = datetime.utcnow()

        # Get metrics
        avg_latency, percentiles = self._get_metric_stats(
            "custom.googleapis.com/rtdp/processing_latency",
            start_time,
            end_time,
            [0.5, 0.95, 0.99],
        )

        messages_sent, messages_processed = self._get_message_counts(start_time, end_time)

        errors = self._get_metric_stats("custom.googleapis.com/rtdp/errors", start_time, end_time)[
            0
        ]

        test_duration = (end_time - start_time).total_seconds()
        throughput = messages_processed / test_duration if test_duration > 0 else 0

        return TestResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            messages_sent=messages_sent,
            messages_processed=messages_processed,
            avg_latency=avg_latency,
            p50_latency=percentiles[0.5],
            p95_latency=percentiles[0.95],
            p99_latency=percentiles[0.99],
            errors=int(errors),
            throughput=throughput,
        )

    def run_increasing_load_test(
        self, initial_rate: int, final_rate: int, step_size: int, step_duration: int
    ) -> List[TestResult]:
        """Run increasing load test.

        Args:
            initial_rate: Initial messages per second
            final_rate: Final messages per second
            step_size: Rate increase per step
            step_duration: Duration of each step in seconds

        Returns:
            List of test results
        """
        results = []
        current_rate = initial_rate

        try:
            while current_rate <= final_rate:
                result = self.run_constant_load_test(current_rate, step_duration)
                results.append(result)
                current_rate += step_size
        finally:
            self.load_generator.stop()

        return results

    def run_burst_load_test(
        self, burst_size: int, burst_duration: int, rest_duration: int, num_bursts: int
    ) -> List[TestResult]:
        """Run burst load test.

        Args:
            burst_size: Messages per second during burst
            burst_duration: Duration of each burst in seconds
            rest_duration: Duration of rest between bursts
            num_bursts: Number of bursts to generate

        Returns:
            List of test results
        """
        results = []

        try:
            for i in range(num_bursts):
                result = self.run_constant_load_test(burst_size, burst_duration)
                results.append(result)

                if i < num_bursts - 1:
                    time.sleep(rest_duration)
        finally:
            self.load_generator.stop()

        return results

    def save_results(self, results: List[TestResult], output_file: str) -> None:
        """Save test results to file.

        Args:
            results: Test results to save
            output_file: Output file path
        """
        output = []
        for result in results:
            output.append(
                {
                    "test_name": result.test_name,
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat(),
                    "messages_sent": result.messages_sent,
                    "messages_processed": result.messages_processed,
                    "avg_latency": result.avg_latency,
                    "p50_latency": result.p50_latency,
                    "p95_latency": result.p95_latency,
                    "p99_latency": result.p99_latency,
                    "errors": result.errors,
                    "throughput": result.throughput,
                }
            )

        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
