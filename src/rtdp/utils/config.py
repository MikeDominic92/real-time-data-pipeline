"""Configuration management utilities."""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import yaml
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import bigquery


@dataclass
class PipelineConfig:
    """Configuration for the data pipeline."""

    # GCP Project settings
    project_id: str
    region: str

    # Pub/Sub settings
    topic_id: str
    subscription_id: str

    # BigQuery settings
    dataset_id: str
    table_id: str
    batch_size: int = 100
    streaming: bool = True
    pipeline_options: Optional[PipelineOptions] = None
    schema: Optional[list[bigquery.SchemaField]] = None

    def __init__(
        self,
        project_id: str,
        region: str,
        topic_id: str,
        subscription_id: str,
        dataset_id: str,
        table_id: str,
        batch_size: int = 100,
        streaming: bool = True,
        pipeline_options: Optional[PipelineOptions] = None,
        schema: Optional[list[bigquery.SchemaField]] = None,
    ) -> None:
        """Initialize pipeline configuration.

        Args:
            project_id: GCP project ID.
            region: GCP region.
            topic_id: Pub/Sub topic ID.
            subscription_id: Pub/Sub subscription ID.
            dataset_id: BigQuery dataset ID.
            table_id: BigQuery table ID.
            batch_size: Number of messages to process in each batch.
            streaming: Whether to run in streaming mode.
            pipeline_options: Apache Beam pipeline options.
            schema: BigQuery table schema.
        """
        self.project_id = project_id
        self.region = region
        self.topic_id = topic_id
        self.subscription_id = subscription_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.batch_size = batch_size
        self.streaming = streaming
        self.pipeline_options = pipeline_options or PipelineOptions()
        if self.streaming:
            self.pipeline_options.view_as(PipelineOptions).streaming = True
        
        # Set up default schema if none provided
        if schema is None:
            self.schema = [
                bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("processing_timestamp", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("data", "RECORD", mode="REQUIRED", fields=[
                    bigquery.SchemaField("key1", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("key2", "STRING", mode="NULLABLE"),
                ]),
                bigquery.SchemaField("metadata", "RECORD", mode="REQUIRED", fields=[
                    bigquery.SchemaField("source", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("version", "STRING", mode="REQUIRED"),
                ]),
            ]
        else:
            self.schema = schema

    @property
    def subscription_path(self) -> str:
        """Get the full Pub/Sub subscription path.

        Returns:
            Full subscription path.
        """
        return f"projects/{self.project_id}/subscriptions/{self.subscription_id}"

    @property
    def topic_path(self) -> str:
        """Get the full Pub/Sub topic path.

        Returns:
            Full topic path.
        """
        return f"projects/{self.project_id}/topics/{self.topic_id}"

    @classmethod
    def from_yaml(cls, path: str) -> "PipelineConfig":
        """Create configuration from YAML file.

        Args:
            path: Path to YAML configuration file.

        Returns:
            PipelineConfig instance.
        """
        with open(path, "r") as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Create configuration from environment variables.

        Returns:
            PipelineConfig instance.
        """
        pipeline_options = PipelineOptions()
        if os.getenv("PIPELINE_STREAMING", "true").lower() == "true":
            pipeline_options.view_as(PipelineOptions).streaming = True

        return cls(
            project_id=os.getenv("GCP_PROJECT_ID", ""),
            region=os.getenv("GCP_REGION", "us-central1"),
            topic_id=os.getenv("PUBSUB_TOPIC_ID", ""),
            subscription_id=os.getenv("PUBSUB_SUBSCRIPTION_ID", ""),
            dataset_id=os.getenv("BIGQUERY_DATASET_ID", ""),
            table_id=os.getenv("BIGQUERY_TABLE_ID", ""),
            batch_size=int(os.getenv("PIPELINE_BATCH_SIZE", "100")),
            streaming=os.getenv("PIPELINE_STREAMING", "true").lower() == "true",
            pipeline_options=pipeline_options,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return {
            "project_id": self.project_id,
            "region": self.region,
            "topic_id": self.topic_id,
            "subscription_id": self.subscription_id,
            "dataset_id": self.dataset_id,
            "table_id": self.table_id,
            "batch_size": self.batch_size,
            "streaming": self.streaming,
        }
