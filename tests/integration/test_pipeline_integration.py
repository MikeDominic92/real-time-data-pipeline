"""Integration tests for the Real-Time Data Pipeline."""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Generator

import pytest
from google.cloud import bigquery, pubsub_v1

from rtdp.processor.pipeline import DataPipeline
from rtdp.publisher.publisher import DataPublisher
from rtdp.storage.bigquery import BigQueryClient
from rtdp.utils.config import PipelineConfig


@pytest.fixture(scope="module")
def integration_config() -> Generator[PipelineConfig, None, None]:
    """Integration test configuration."""
    config = PipelineConfig(
        project_id="test-project-integration",
        region="us-central1",
        topic_id="test-topic-integration",
        subscription_id="test-subscription-integration",
        dataset_id="test_dataset_integration",
        table_id="test_table_integration",
        batch_size=10,
        streaming=True,
    )
    yield config


@pytest.fixture(scope="module")
def publisher_client(
    integration_config: PipelineConfig,
) -> Generator[DataPublisher, None, None]:
    """Create a publisher client for integration tests."""
    publisher = DataPublisher(
        project_id=integration_config.project_id, topic_id=integration_config.topic_id
    )
    yield publisher
    publisher.close()


@pytest.fixture(scope="module")
def bigquery_client(
    integration_config: PipelineConfig,
) -> Generator[BigQueryClient, None, None]:
    """Create a BigQuery client for integration tests."""
    client = BigQueryClient(
        project_id=integration_config.project_id,
        dataset_id=integration_config.dataset_id,
        table_id=integration_config.table_id,
    )
    yield client


def test_end_to_end_pipeline(
    integration_config: PipelineConfig,
    publisher_client: DataPublisher,
    bigquery_client: BigQueryClient,
    sample_message_data: Dict[str, Any],
) -> None:
    """Test the entire pipeline from publishing to storage."""
    # 1. Publish messages
    message_count = 5
    published_messages = []

    for i in range(message_count):
        message = dict(sample_message_data)
        message["event_id"] = f"test-event-{i}"
        message["timestamp"] = datetime.now().isoformat()

        future = publisher_client.publish(message)
        published_messages.append(message)

        # Wait for message to be published
        future.result()

    # 2. Wait for processing
    time.sleep(10)  # Allow time for messages to be processed

    # 3. Verify data in BigQuery
    query = f"""
    SELECT COUNT(*) as count
    FROM `{integration_config.project_id}.{integration_config.dataset_id}.{integration_config.table_id}`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 MINUTE)
    """
    results = bigquery_client.query(query)

    assert len(results) == 1
    assert results[0]["count"] >= message_count


def test_pipeline_error_recovery(
    integration_config: PipelineConfig,
    publisher_client: DataPublisher,
    bigquery_client: BigQueryClient,
) -> None:
    """Test pipeline recovery from errors."""
    # 1. Publish invalid message
    invalid_message = {"invalid": "data"}
    publisher_client.publish(invalid_message)

    # 2. Publish valid message
    valid_message = {
        "event_id": "recovery-test",
        "timestamp": datetime.now().isoformat(),
        "data": {"key": "value"},
        "metadata": {"source": "test"},
    }
    publisher_client.publish(valid_message)

    # 3. Wait for processing
    time.sleep(10)

    # 4. Verify only valid message was processed
    query = f"""
    SELECT *
    FROM `{integration_config.project_id}.{integration_config.dataset_id}.{integration_config.table_id}`
    WHERE event_id = 'recovery-test'
    """
    results = bigquery_client.query(query)

    assert len(results) == 1
    assert results[0]["event_id"] == "recovery-test"


def test_pipeline_performance(
    integration_config: PipelineConfig,
    publisher_client: DataPublisher,
    bigquery_client: BigQueryClient,
    sample_message_data: Dict[str, Any],
) -> None:
    """Test pipeline performance with batch processing."""
    # 1. Prepare batch of messages
    batch_size = 100
    messages = []

    for i in range(batch_size):
        message = dict(sample_message_data)
        message["event_id"] = f"perf-test-{i}"
        message["timestamp"] = datetime.now().isoformat()
        messages.append(message)

    # 2. Measure publishing time
    start_time = time.time()

    for message in messages:
        publisher_client.publish(message)

    publish_time = time.time() - start_time

    # 3. Wait for processing
    time.sleep(20)

    # 4. Verify processing time and completeness
    query = f"""
    SELECT COUNT(*) as count
    FROM `{integration_config.project_id}.{integration_config.dataset_id}.{integration_config.table_id}`
    WHERE event_id LIKE 'perf-test-%'
    AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 MINUTE)
    """
    results = bigquery_client.query(query)

    assert len(results) == 1
    assert results[0]["count"] >= batch_size
    assert publish_time < 10  # Publishing should take less than 10 seconds


def test_pipeline_data_consistency(
    integration_config: PipelineConfig,
    publisher_client: DataPublisher,
    bigquery_client: BigQueryClient,
    sample_message_data: Dict[str, Any],
) -> None:
    """Test data consistency across the pipeline."""
    # 1. Create message with specific test data
    test_data = dict(sample_message_data)
    test_data["event_id"] = "consistency-test"
    test_data["timestamp"] = datetime.now().isoformat()
    test_data["data"]["test_value"] = "unique_test_value"

    # 2. Publish message
    publisher_client.publish(test_data)

    # 3. Wait for processing
    time.sleep(10)

    # 4. Verify data consistency in BigQuery
    query = f"""
    SELECT *
    FROM `{integration_config.project_id}.{integration_config.dataset_id}.{integration_config.table_id}`
    WHERE event_id = 'consistency-test'
    """
    results = bigquery_client.query(query)

    assert len(results) == 1
    result = results[0]

    # Verify all fields are preserved
    assert result["event_id"] == test_data["event_id"]
    assert result["timestamp"] == test_data["timestamp"]
    assert json.loads(result["data"])["test_value"] == "unique_test_value"
