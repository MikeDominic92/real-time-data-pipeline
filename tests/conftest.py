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
def mock_publisher_client(monkeypatch: pytest.MonkeyPatch) -> Generator[Any, None, None]:
    """Mock the Pub/Sub publisher client."""
    class MockPublisherClient:
        def __init__(self) -> None:
            self.published_messages = []

        def topic_path(self, project_id: str, topic_id: str) -> str:
            """Create a topic path."""
            return f"projects/{project_id}/topics/{topic_id}"

        def publish(
            self,
            topic: str,
            data: bytes,
            **kwargs: Any
        ) -> str:
            """Mock publish method."""
            self.published_messages.append({
                "topic": topic,
                "data": data,
                "attributes": kwargs
            })
            return "message-id"

    client = MockPublisherClient()
    monkeypatch.setattr(pubsub_v1, "PublisherClient", lambda: client)
    yield client


@pytest.fixture
def mock_bigquery_client(monkeypatch: pytest.MonkeyPatch) -> Generator[Any, None, None]:
    """Mock the BigQuery client."""
    class MockBigQueryClient:
        def __init__(self) -> None:
            self.inserted_rows = []
            self.queries = []

        def get_table(self, table_ref: str) -> Any:
            """Mock get_table method."""
            return None

        def insert_rows_json(
            self,
            table: str,
            json_rows: list,
            **kwargs: Any
        ) -> list:
            """Mock insert_rows_json method."""
            self.inserted_rows.extend(json_rows)
            return []

    client = MockBigQueryClient()
    monkeypatch.setattr(bigquery, "Client", lambda: client)
    yield client
