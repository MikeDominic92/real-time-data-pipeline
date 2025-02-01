"""Test configuration and fixtures for the Real-Time Data Pipeline."""

import json
import os
from typing import Any, Dict, Generator

import pytest
from google.cloud import bigquery, pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message

from rtdp.utils.config import PipelineConfig


@pytest.fixture
def sample_message_data() -> Dict[str, Any]:
    """Sample message data for testing."""
    return {
        "event_id": "test-event-123",
        "timestamp": "2025-02-01T18:47:36-05:00",
        "data": {
            "key1": "value1",
            "key2": "value2"
        },
        "metadata": {
            "source": "test-source",
            "version": "1.0"
        }
    }


@pytest.fixture
def mock_pubsub_message(sample_message_data: Dict[str, Any]) -> Message:
    """Create a mock Pub/Sub message."""
    class MockPubSubMessage:
        def __init__(self, data: Dict[str, Any]):
            self.data = json.dumps(data).encode("utf-8")
            self.attributes = {}
            self.message_id = "test-message-id"
            self.publish_time = None
            self._ack_status = False

        def ack(self) -> None:
            """Acknowledge the message."""
            self._ack_status = True

    return MockPubSubMessage(sample_message_data)


@pytest.fixture
def test_config() -> PipelineConfig:
    """Test configuration."""
    return PipelineConfig(
        project_id="test-project",
        region="us-central1",
        topic_id="test-topic",
        subscription_id="test-subscription",
        dataset_id="test_dataset",
        table_id="test_table",
        batch_size=10,
        streaming=True
    )


@pytest.fixture
def mock_publisher_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock the Pub/Sub publisher client."""
    class MockPublisherClient:
        def __init__(self) -> None:
            self.published_messages: list = []

        def topic_path(self, project_id: str, topic_id: str) -> str:
            """Create a topic path."""
            return f"projects/{project_id}/topics/{topic_id}"

        def publish(
            self,
            topic: str,
            data: bytes,
            **kwargs: Any
        ) -> None:
            """Mock publish method."""
            self.published_messages.append({
                "topic": topic,
                "data": data,
                "attributes": kwargs
            })
            return "message-id"

    monkeypatch.setattr(pubsub_v1, "PublisherClient", MockPublisherClient)


@pytest.fixture
def mock_bigquery_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock the BigQuery client."""
    class MockBigQueryClient:
        def __init__(self) -> None:
            self.inserted_rows: list = []
            self.queries: list = []

        def get_table(self, table_ref: str) -> Any:
            """Mock get_table method."""
            return None

        def insert_rows_json(
            self,
            table: Any,
            json_rows: list
        ) -> list:
            """Mock insert_rows_json method."""
            self.inserted_rows.extend(json_rows)
            return []

        def query(self, query: str) -> Any:
            """Mock query method."""
            self.queries.append(query)
            return MockQueryJob()

    class MockQueryJob:
        def result(self) -> list:
            """Mock result method."""
            return []

    monkeypatch.setattr(bigquery, "Client", MockBigQueryClient)


@pytest.fixture
def temp_env_vars(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Set temporary environment variables for testing."""
    env_vars = {
        "GCP_PROJECT_ID": "test-project",
        "GCP_REGION": "us-central1",
        "PUBSUB_TOPIC_ID": "test-topic",
        "PUBSUB_SUBSCRIPTION_ID": "test-subscription",
        "BIGQUERY_DATASET_ID": "test_dataset",
        "BIGQUERY_TABLE_ID": "test_table",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    yield

    for key in env_vars:
        monkeypatch.delenv(key, raising=False)
