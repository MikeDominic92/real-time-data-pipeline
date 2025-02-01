"""Publisher module for handling Pub/Sub message publishing."""

import json
from typing import Any, Dict, Optional

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.publisher.futures import Future


class DataPublisher:
    """Handles publishing messages to Google Cloud Pub/Sub."""

    def __init__(
        self,
        project_id: str,
        topic_id: str,
        batch_settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the publisher client.

        Args:
            project_id: The GCP project ID.
            topic_id: The Pub/Sub topic ID.
            batch_settings: Optional batch settings for the publisher client.
        """
        self.project_id = project_id
        self.topic_id = topic_id
        self.publisher = pubsub_v1.PublisherClient(
            publisher_options=pubsub_v1.types.PublisherOptions(
                enable_message_ordering=True,
            ),
        )
        self.topic_path = self.publisher.topic_path(project_id, topic_id)

        # Apply batch settings if provided
        if batch_settings:
            self.publisher = pubsub_v1.PublisherClient(
                batch_settings=pubsub_v1.types.BatchSettings(**batch_settings),
            )

    def publish(
        self,
        data: Dict[str, Any],
        ordering_key: Optional[str] = None,
        **attributes: str,
    ) -> Future:
        """Publish a message to the Pub/Sub topic.

        Args:
            data: The message data to publish.
            ordering_key: Optional key for ordered message delivery.
            **attributes: Additional attributes to attach to the message.

        Returns:
            A Future object for tracking the message delivery.
        """
        # Convert data to JSON string
        message_data = json.dumps(data).encode("utf-8")

        # Publish the message
        future = self.publisher.publish(
            topic=self.topic_path,
            data=message_data,
            ordering_key=ordering_key,
            **attributes,
        )

        return future

    def close(self) -> None:
        """Close the publisher client."""
        self.publisher.stop()
