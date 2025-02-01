"""Configuration management utilities."""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import yaml
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
    schema: Optional[list[bigquery.SchemaField]] = None

    # Pipeline settings
    batch_size: int = 100
    streaming: bool = True

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
        return cls(
            project_id=os.getenv("GCP_PROJECT_ID", ""),
            region=os.getenv("GCP_REGION", "us-central1"),
            topic_id=os.getenv("PUBSUB_TOPIC_ID", ""),
            subscription_id=os.getenv("PUBSUB_SUBSCRIPTION_ID", ""),
            dataset_id=os.getenv("BIGQUERY_DATASET_ID", ""),
            table_id=os.getenv("BIGQUERY_TABLE_ID", ""),
            batch_size=int(os.getenv("PIPELINE_BATCH_SIZE", "100")),
            streaming=os.getenv("PIPELINE_STREAMING", "true").lower() == "true",
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
