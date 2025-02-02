"""Deployment script for the Real-Time Data Pipeline."""

import argparse
import os
from pathlib import Path
from typing import Any, Dict

import apache_beam as beam
import yaml
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import storage


class PipelineDeployer:
    """Deploy the Real-Time Data Pipeline to GCP."""

    def __init__(
        self,
        project_id: str,
        environment: str,
        version: str,
        config_path: str = "config/deployment_config.yaml",
    ) -> None:
        """Initialize deployer.

        Args:
            project_id: GCP project ID
            environment: Deployment environment
            version: Deployment version
            config_path: Path to deployment configuration
        """
        self.project_id = project_id
        self.environment = environment
        self.version = version
        self.config = self._load_config(config_path)["environments"][environment]

        # Initialize clients
        self.pipeline_options = PipelineOptions(
            project=project_id,
            region=self.config.get("region", "us-central1"),
            runner="DataflowRunner",
        )
        self.storage_client = storage.Client(project=project_id)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load deployment configuration.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config

    def _upload_package(self) -> str:
        """Upload package to Cloud Storage.

        Returns:
            GCS path to uploaded package
        """
        bucket_name = f"{self.project_id}-dataflow-packages"
        bucket = self.storage_client.bucket(bucket_name)

        if not bucket.exists():
            bucket.create()

        # Find the first .tar.gz file in dist directory
        dist_files = [f for f in os.listdir("dist") if f.endswith(".tar.gz")]
        if not dist_files:
            raise FileNotFoundError(
                "No .tar.gz distribution package found in dist/ directory"
            )

        dist_file = os.path.join("dist", dist_files[0])
        blob_name = f"rtdp-{self.version}.tar.gz"
        blob = bucket.blob(blob_name)

        # Upload package
        blob.upload_from_filename(dist_file)

        return f"gs://{bucket_name}/{blob_name}"

    def _launch_dataflow_job(self, package_path: str, job_name: str) -> str:
        """Launch Dataflow job.

        Args:
            package_path: GCS path to package
            job_name: Name for the job

        Returns:
            Job ID
        """
        # Create pipeline options
        options = {
            "project": self.project_id,
            "region": self.config["region"],
            "temp_location": f"gs://{self.project_id}-dataflow-temp",
            "setup_file": "./setup.py",
            "requirements_file": "requirements.txt",
            "streaming": True,
            "runner": "DataflowRunner",
            "max_num_workers": self.config.get("max_workers", 10),
            "autoscaling_algorithm": "THROUGHPUT_BASED",
            "experiments": ["use_runner_v2", "enable_streaming_engine"],
        }

        # Create and launch pipeline
        pipeline = beam.Pipeline(options=PipelineOptions(**options))
        result = pipeline.run()
        return result.job_id()

    def deploy(self) -> None:
        """Deploy the pipeline."""
        print("Starting deployment...")

        # Upload package
        package_path = self._upload_package()
        print(f"Uploaded package to {package_path}")

        # Launch job
        job_name = f"rtdp-{self.environment}-{self.version}"
        job_id = self._launch_dataflow_job(package_path, job_name)
        print(f"Launched job with ID: {job_id}")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Deploy Real-Time Data Pipeline")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument(
        "--environment",
        choices=["staging", "production"],
        required=True,
        help="Deployment environment",
    )
    parser.add_argument("--version", required=True, help="Deployment version")
    parser.add_argument(
        "--config",
        default="config/deployment_config.yaml",
        help="Path to deployment configuration",
    )
    args = parser.parse_args()

    deployer = PipelineDeployer(
        project_id=args.project_id,
        environment=args.environment,
        version=args.version,
        config_path=args.config,
    )
    deployer.deploy()


if __name__ == "__main__":
    main()
