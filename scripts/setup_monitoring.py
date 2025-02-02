"""Script to set up monitoring infrastructure for the Real-Time Data Pipeline."""

import argparse
import os
from typing import Any, Dict

import yaml
from google.cloud import monitoring_v3, secretmanager_v1

from rtdp.monitoring.alerts import AlertManager
from rtdp.monitoring.service import MonitoringService


def setup_notification_channels(project_id: str, channels_config: list) -> list:
    """Set up notification channels.

    Args:
        project_id: GCP project ID
        channels_config: Notification channel configuration

    Returns:
        List of created notification channel names
    """
    client = monitoring_v3.NotificationChannelServiceClient()
    project_name = f"projects/{project_id}"
    channels = []

    for channel in channels_config:
        if channel["type"] == "email":
            notification_channel = monitoring_v3.NotificationChannel(
                type_="email",
                display_name=channel["name"],
                labels={"email_address": channel["email_address"]},
            )
        elif channel["type"] == "slack":
            # Store Slack webhook URL in Secret Manager
            secret_id = f"slack_webhook_{channel['name'].lower().replace(' ', '_')}"
            store_secret(project_id, secret_id, channel["webhook_url"])

            notification_channel = monitoring_v3.NotificationChannel(
                type_="slack",
                display_name=channel["name"],
                labels={
                    "channel_name": channel["name"],
                    "auth_token": f"projects/{project_id}/secrets/{secret_id}",
                },
            )

        result = client.create_notification_channel(
            request={"name": project_name, "notification_channel": notification_channel}
        )
        channels.append(result.name)

    return channels


def store_secret(project_id: str, secret_id: str, secret_value: str) -> None:
    """Store a secret in Secret Manager.

    Args:
        project_id: GCP project ID
        secret_id: Secret ID
        secret_value: Secret value
    """
    client = secretmanager_v1.SecretManagerServiceClient()
    parent = f"projects/{project_id}"

    # Create secret
    secret = client.create_secret(
        request={
            "parent": parent,
            "secret_id": secret_id,
            "secret": {"replication": {"automatic": {}}},
        }
    )

    # Add secret version
    client.add_secret_version(
        request={
            "parent": secret.name,
            "payload": {"data": secret_value.encode("UTF-8")},
        }
    )


def setup_export_config(project_id: str, export_config: Dict[str, Any]) -> None:
    """Set up monitoring data export.

    Args:
        project_id: GCP project ID
        export_config: Export configuration
    """
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"

    # BigQuery export
    if "bigquery" in export_config:
        bq_config = export_config["bigquery"]
        sink_name = f"{project_name}/metricSinks/bq-export"

        sink = monitoring_v3.MetricDescriptor(
            name=sink_name,
            type_="bigquery.googleapis.com/sink",
            labels={
                "dataset_id": bq_config["dataset_id"],
                "table_id": bq_config["table_id"],
            },
        )

        client.create_metric_descriptor(name=project_name, metric_descriptor=sink)

    # Cloud Storage export
    if "storage" in export_config:
        storage_config = export_config["storage"]
        sink_name = f"{project_name}/metricSinks/storage-export"

        sink = monitoring_v3.MetricDescriptor(
            name=sink_name,
            type_="storage.googleapis.com/sink",
            labels={"bucket_name": storage_config["bucket_name"]},
        )

        client.create_metric_descriptor(name=project_name, metric_descriptor=sink)


def main() -> None:
    """Main function to set up monitoring infrastructure."""
    parser = argparse.ArgumentParser(description="Set up monitoring infrastructure")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument(
        "--config",
        default="config/monitoring_config.yaml",
        help="Path to monitoring configuration file",
    )
    args = parser.parse_args()

    # Load configuration
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    # Set up notification channels
    channels = setup_notification_channels(
        args.project_id, config.get("notification_channels", [])
    )

    # Initialize monitoring service
    monitoring_service = MonitoringService(
        project_id=args.project_id, config_path=args.config, service_name="rtdp"
    )

    # Set up export configuration
    if "export" in config:
        setup_export_config(args.project_id, config["export"])

    print("Monitoring infrastructure setup completed successfully!")
    print(f"Created {len(channels)} notification channels")


if __name__ == "__main__":
    main()
