"""Unit tests for the publisher module."""

import json
from typing import Any, Dict

import pytest
from google.cloud import pubsub_v1

from rtdp.publisher.publisher import DataPublisher


def test_publisher_initialization(test_config: Any) -> None:
    """Test publisher initialization."""
    publisher = DataPublisher(
        project_id=test_config.project_id,
        topic_id=test_config.topic_id,
    )

    assert publisher.project_id == test_config.project_id
    assert publisher.topic_id == test_config.topic_id
    assert isinstance(publisher.publisher, pubsub_v1.PublisherClient)


def test_publish_message(
    mock_publisher_client: None,
    test_config: Any,
    sample_message_data: Dict[str, Any]
) -> None:
    """Test publishing a message."""
    publisher = DataPublisher(
        project_id=test_config.project_id,
        topic_id=test_config.topic_id,
    )

    # Publish a message
    future = publisher.publish(
        data=sample_message_data,
        ordering_key="test-key"
    )

    # Verify the message was published
    assert future == "message-id"
    published_message = publisher.publisher.published_messages[0]
    assert published_message["topic"] == publisher.topic_path
    assert json.loads(published_message["data"]) == sample_message_data
    assert published_message["attributes"]["ordering_key"] == "test-key"


def test_publish_message_with_attributes(
    mock_publisher_client: None,
    test_config: Any,
    sample_message_data: Dict[str, Any]
) -> None:
    """Test publishing a message with additional attributes."""
    publisher = DataPublisher(
        project_id=test_config.project_id,
        topic_id=test_config.topic_id,
    )

    # Additional attributes
    attributes = {
        "source": "test-source",
        "environment": "test"
    }

    # Publish a message with attributes
    future = publisher.publish(
        data=sample_message_data,
        ordering_key="test-key",
        **attributes
    )

    # Verify the message was published with attributes
    assert future == "message-id"
    published_message = publisher.publisher.published_messages[0]
    assert published_message["attributes"]["source"] == "test-source"
    assert published_message["attributes"]["environment"] == "test"


def test_publish_message_with_batch_settings(
    mock_publisher_client: None,
    test_config: Any,
    sample_message_data: Dict[str, Any]
) -> None:
    """Test publishing with batch settings."""
    batch_settings = {
        "max_bytes": 1024 * 1024,  # 1MB
        "max_latency": 1,  # 1 second
        "max_messages": 100,
    }

    publisher = DataPublisher(
        project_id=test_config.project_id,
        topic_id=test_config.topic_id,
        batch_settings=batch_settings,
    )

    # Publish a message
    future = publisher.publish(data=sample_message_data)
    assert future == "message-id"


def test_close_publisher(
    mock_publisher_client: None,
    test_config: Any
) -> None:
    """Test closing the publisher."""
    publisher = DataPublisher(
        project_id=test_config.project_id,
        topic_id=test_config.topic_id,
    )

    # Close should not raise any exceptions
    publisher.close()
