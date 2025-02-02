"""Apache Beam pipeline for processing streaming data."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Iterator, Optional, Tuple

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions


class ParseJsonDoFn(beam.DoFn):
    """Parse JSON messages from Pub/Sub."""

    def process(
        self,
        element: bytes,
        timestamp: beam.DoFn.TimestampParam = beam.DoFn.TimestampParam,
    ) -> Iterator[Dict[str, Any]]:
        """Process each Pub/Sub message.

        Args:
            element: Raw message data from Pub/Sub.
            timestamp: Message timestamp.

        Yields:
            Parsed JSON message data.
        """
        try:
            # Decode and parse JSON message
            message: Dict[str, Any] = json.loads(element.decode("utf-8"))

            # Add processing timestamp
            message["processing_timestamp"] = timestamp.to_utc_datetime().isoformat()

            yield message
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON message: {e}")
        except Exception as e:
            logging.error(f"Error processing message: {e}")


class ValidateMessageDoFn(beam.DoFn):
    """Validate message format and content."""

    REQUIRED_FIELDS = {"event_id", "timestamp", "data", "metadata"}

    def process(self, element: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Process and validate each message.

        Args:
            element: Message to validate.

        Yields:
            Validated message if it passes all checks.
        """
        try:
            # Check required fields
            if not all(field in element for field in self.REQUIRED_FIELDS):
                logging.error(
                    f"Message missing required fields. Required: {self.REQUIRED_FIELDS}, "
                    f"Got: {set(element.keys())}"
                )
                return

            # Validate timestamp format
            try:
                datetime.fromisoformat(element["timestamp"])
            except (ValueError, TypeError) as e:
                logging.error(f"Invalid timestamp format: {e}")
                return

            # Validate metadata
            metadata: Dict[str, Any] = element.get("metadata", {})
            if not isinstance(metadata, dict):
                logging.error("Metadata must be a dictionary")
                return

            if "source" not in metadata or "version" not in metadata:
                logging.error("Metadata missing required fields: source, version")
                return

            # Message passed all validations
            yield element

        except Exception as e:
            logging.error(f"Error validating message: {e}")


class DataPipeline:
    """Handles the creation and execution of the data processing pipeline."""

    def __init__(self, config: Any) -> None:
        """Initialize the pipeline configuration.

        Args:
            config: Pipeline configuration object.
        """
        self.config = config

    def apply_transforms(self, pcoll: beam.PCollection) -> beam.PCollection:
        """Apply pipeline transformations.

        Args:
            pcoll: Input PCollection.

        Returns:
            Transformed PCollection.
        """
        return (
            pcoll
            | "Parse JSON" >> beam.ParDo(ParseJsonDoFn())
            | "Validate Messages" >> beam.ParDo(ValidateMessageDoFn())
        )

    def build_pipeline(self) -> beam.Pipeline:
        """Build the data processing pipeline.

        Returns:
            An Apache Beam Pipeline object.
        """
        pipeline: beam.Pipeline = beam.Pipeline(options=self.config.pipeline_options)

        # Read from Pub/Sub
        messages: beam.PCollection = (
            pipeline
            | "Read from Pub/Sub"
            >> beam.io.ReadFromPubSub(subscription=self.config.subscription_path)
        )

        # Apply pipeline transformations
        transformed_messages: beam.PCollection = self.apply_transforms(messages)

        # Write to BigQuery
        table_spec: str = (
            f"{self.config.project_id}:{self.config.dataset_id}.{self.config.table_id}"
        )
        transformed_messages | "Write to BigQuery" >> beam.io.WriteToBigQuery(
            table_spec,
            schema=self.config.schema,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        )

        return pipeline
