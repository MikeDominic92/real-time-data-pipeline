"""Smoke tests for the Real-Time Data Pipeline deployment."""

import argparse
import json
import time
from datetime import datetime
from typing import Any, Dict

from google.cloud import bigquery, pubsub_v1

from rtdp.utils.config import PipelineConfig


class SmokeTest:
    """Run smoke tests for the Real-Time Data Pipeline."""

    def __init__(
        self,
        project_id: str,
        environment: str,
        config_path: str = "config/deployment_config.yaml",
    ) -> None:
        """Initialize smoke test.

        Args:
            project_id: GCP project ID
            environment: Test environment
            config_path: Path to configuration
        """
        self.project_id = project_id
        self.environment = environment
        self.config = PipelineConfig.from_yaml(config_path)[environment]

        # Initialize clients
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.bq_client = bigquery.Client(project=project_id)

        self.topic_path = self.publisher.topic_path(project_id, self.config["topic_id"])

    def _generate_test_message(self) -> Dict[str, Any]:
        """Generate a test message.

        Returns:
            Test message dictionary
        """
        return {
            "event_id": f"smoke-test-{int(time.time())}",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"test_key": "test_value", "environment": self.environment},
            "metadata": {"source": "smoke_test", "version": "1.0"},
        }

    def _publish_message(self, message: Dict[str, Any]) -> str:
        """Publish a test message.

        Args:
            message: Message to publish

        Returns:
            Message ID
        """
        data = json.dumps(message).encode("utf-8")
        future = self.publisher.publish(self.topic_path, data=data, origin="smoke_test")
        return future.result()

    def _verify_bigquery(self, message: Dict[str, Any], timeout: int = 300) -> bool:
        """Verify message in BigQuery.

        Args:
            message: Published message
            timeout: Timeout in seconds

        Returns:
            True if verification successful
        """
        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.config['dataset_id']}.{self.config['table_id']}`
        WHERE event_id = '{message['event_id']}'
        """

        start_time = time.time()
        while time.time() - start_time < timeout:
            query_job = self.bq_client.query(query)
            results = list(query_job.result())

            if results:
                row = results[0]
                return (
                    row.event_id == message["event_id"]
                    and row.data["test_key"] == message["data"]["test_key"]
                )

            time.sleep(10)

        return False

    def run(self) -> None:
        """Run smoke tests."""
        print(f"Running smoke tests in {self.environment}...")

        # Generate and publish test message
        message = self._generate_test_message()
        message_id = self._publish_message(message)
        print(f"Published test message {message_id}")

        # Verify message in BigQuery
        print("Verifying message in BigQuery...")
        if self._verify_bigquery(message):
            print("Smoke tests passed successfully!")
        else:
            raise Exception("Smoke tests failed: Message not found in BigQuery")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Run smoke tests for Real-Time Data Pipeline")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument(
        "--environment",
        choices=["staging", "production"],
        required=True,
        help="Test environment",
    )
    parser.add_argument(
        "--config",
        default="config/deployment_config.yaml",
        help="Path to deployment configuration",
    )
    args = parser.parse_args()

    smoke_test = SmokeTest(
        project_id=args.project_id,
        environment=args.environment,
        config_path=args.config,
    )
    smoke_test.run()


if __name__ == "__main__":
    main()
