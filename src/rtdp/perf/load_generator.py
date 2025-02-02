"""Load generator for performance testing."""

import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, Optional

from google.cloud import pubsub_v1

from rtdp.monitoring.metrics import MetricsCollector


class LoadGenerator:
    """Generate test load for the pipeline."""

    def __init__(
        self,
        project_id: str,
        topic_id: str,
        metrics_collector: Optional[MetricsCollector] = None,
    ) -> None:
        """Initialize load generator.

        Args:
            project_id: GCP project ID
            topic_id: Pub/Sub topic ID
            metrics_collector: Optional metrics collector
        """
        self.project_id = project_id
        self.topic_id = topic_id
        self.metrics = metrics_collector
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_id)
        self._stop_event = threading.Event()

    def _generate_message(self, index: int) -> Dict[str, Any]:
        """Generate a test message.

        Args:
            index: Message index

        Returns:
            Generated message
        """
        return {
            "event_id": f"perf-test-{int(time.time())}-{index}",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "value": random.random(),
                "category": random.choice(["A", "B", "C", "D"]),
                "priority": random.randint(1, 5),
                "tags": [f"tag_{random.randint(1, 10)}" for _ in range(random.randint(1, 5))],
            },
            "metadata": {
                "source": "perf_test",
                "version": "1.0",
                "test_type": "load_test",
            },
        }

    def _publish_message(self, message: Dict[str, Any], batch_id: Optional[str] = None) -> None:
        """Publish a message to Pub/Sub.

        Args:
            message: Message to publish
            batch_id: Optional batch ID
        """
        try:
            start_time = time.time()
            data = json.dumps(message).encode("utf-8")

            attributes = {"source": "perf_test", "test_type": "load_test"}
            if batch_id:
                attributes["batch_id"] = batch_id

            future = self.publisher.publish(self.topic_path, data=data, **attributes)
            future.result()  # Wait for message to be published

            if self.metrics:
                latency = time.time() - start_time
                self.metrics.record_latency(name="publish_latency", latency=latency)
                self.metrics.record_counter("messages_published")

        except Exception as e:
            if self.metrics:
                self.metrics.record_error("publish_error")
            raise e

    def generate_constant_load(self, messages_per_second: int, duration_seconds: int) -> None:
        """Generate constant load.

        Args:
            messages_per_second: Number of messages per second
            duration_seconds: Test duration in seconds
        """
        print(f"Generating constant load: {messages_per_second} msg/s for {duration_seconds}s")

        start_time = time.time()
        message_count = 0

        with ThreadPoolExecutor(max_workers=10) as executor:
            while time.time() - start_time < duration_seconds and not self._stop_event.is_set():
                batch_start = time.time()
                batch_id = f"batch-{int(batch_start)}"

                # Submit batch of messages
                futures = []
                for i in range(messages_per_second):
                    message = self._generate_message(message_count + i)
                    futures.append(executor.submit(self._publish_message, message, batch_id))

                # Wait for batch to complete
                for future in futures:
                    future.result()

                message_count += len(futures)

                # Sleep if needed to maintain rate
                elapsed = time.time() - batch_start
                if elapsed < 1:
                    time.sleep(1 - elapsed)

        print(f"Generated {message_count} messages")

    def generate_increasing_load(
        self, initial_rate: int, final_rate: int, step_size: int, step_duration: int
    ) -> None:
        """Generate increasing load.

        Args:
            initial_rate: Initial messages per second
            final_rate: Final messages per second
            step_size: Rate increase per step
            step_duration: Duration of each step in seconds
        """
        print(
            f"Generating increasing load: {initial_rate} to {final_rate} "
            f"msg/s, step size {step_size}, step duration {step_duration}s"
        )

        current_rate = initial_rate
        while current_rate <= final_rate and not self._stop_event.is_set():
            print(f"Testing rate: {current_rate} msg/s")
            self.generate_constant_load(current_rate, step_duration)
            current_rate += step_size

    def generate_burst_load(
        self, burst_size: int, burst_duration: int, rest_duration: int, num_bursts: int
    ) -> None:
        """Generate burst load.

        Args:
            burst_size: Messages per second during burst
            burst_duration: Duration of each burst in seconds
            rest_duration: Duration of rest between bursts
            num_bursts: Number of bursts to generate
        """
        print(
            f"Generating burst load: {burst_size} msg/s for {burst_duration}s, "
            f"{num_bursts} bursts with {rest_duration}s rest"
        )

        for i in range(num_bursts):
            if self._stop_event.is_set():
                break

            print(f"Burst {i + 1}/{num_bursts}")
            self.generate_constant_load(burst_size, burst_duration)

            if i < num_bursts - 1:  # Don't sleep after last burst
                time.sleep(rest_duration)

    def stop(self) -> None:
        """Stop load generation."""
        self._stop_event.set()

    def wait_for_completion(self) -> None:
        """Wait for all messages to be published."""
        self.publisher.stop()
