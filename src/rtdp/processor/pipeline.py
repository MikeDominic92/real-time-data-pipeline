"""Apache Beam pipeline for processing streaming data."""

import json
import logging
from typing import Any, Dict, Iterator, Optional, Tuple

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions


class ParseJsonDoFn(beam.DoFn):
    """Parse JSON messages from Pub/Sub."""

    def process(self, element: bytes, timestamp=beam.DoFn.TimestampParam) -> Iterator[Dict[str, Any]]:
        """Process each Pub/Sub message.

        Args:
            element: Raw message data from Pub/Sub.
            timestamp: Message timestamp.

        Yields:
            Parsed JSON message data.
        """
        try:
            # Decode and parse JSON message
            message = json.loads(element.decode("utf-8"))
            
            # Add processing timestamp
            message["processing_timestamp"] = timestamp.to_utc_datetime().isoformat()
            
            yield message
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON message: {e}")
        except Exception as e:
            logging.error(f"Error processing message: {e}")


class DataPipeline:
    """Handles the creation and execution of the data processing pipeline."""

    def __init__(
        self,
        project_id: str,
        subscription_path: str,
        dataset_id: str,
        table_id: str,
        pipeline_options: Optional[PipelineOptions] = None,
    ) -> None:
        """Initialize the pipeline configuration.

        Args:
            project_id: The GCP project ID.
            subscription_path: The full path to the Pub/Sub subscription.
            dataset_id: The BigQuery dataset ID.
            table_id: The BigQuery table ID.
            pipeline_options: Optional Apache Beam pipeline options.
        """
        self.project_id = project_id
        self.subscription_path = subscription_path
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.pipeline_options = pipeline_options or PipelineOptions()

    def build_pipeline(self) -> beam.Pipeline:
        """Build the data processing pipeline.

        Returns:
            An Apache Beam Pipeline object.
        """
        pipeline = beam.Pipeline(options=self.pipeline_options)

        # Read from Pub/Sub
        messages = (
            pipeline
            | "Read from Pub/Sub" >> beam.io.ReadFromPubSub(
                subscription=self.subscription_path
            )
            | "Parse JSON" >> beam.ParDo(ParseJsonDoFn())
        )

        # Write to BigQuery
        table_spec = f"{self.project_id}:{self.dataset_id}.{self.table_id}"
        messages | "Write to BigQuery" >> beam.io.WriteToBigQuery(
            table_spec,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        )

        return pipeline
