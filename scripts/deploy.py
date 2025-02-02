"""Deployment script for the Real-Time Data Pipeline."""

import argparse
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

import yaml
from google.cloud.dataflow_v1beta3 import JobsV1Beta3Client
from google.cloud import storage


class PipelineDeployer:
    """Deploy the Real-Time Data Pipeline to GCP."""

    def __init__(
        self,
        project_id: str,
        environment: str,
        version: str,
        config_path: str = "config/deployment_config.yaml"
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
        self.config = self._load_config(config_path)[environment]
        
        # Initialize clients
        self.dataflow_client = JobsV1Beta3Client()
        self.storage_client = storage.Client(project=project_id)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load deployment configuration.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _upload_package(self) -> str:
        """Upload package to Cloud Storage.
        
        Returns:
            GCS path to uploaded package
        """
        bucket_name = f"{self.project_id}-dataflow-packages"
        bucket = self.storage_client.bucket(bucket_name)
        
        if not bucket.exists():
            bucket.create()

        blob_name = f"rtdp-{self.version}.tar.gz"
        blob = bucket.blob(blob_name)

        # Create package
        subprocess.run(
            ["python", "setup.py", "sdist", "--formats=gztar"],
            check=True
        )

        # Upload package
        dist_file = f"dist/rtdp-{self.version}.tar.gz"
        blob.upload_from_filename(dist_file)

        return f"gs://{bucket_name}/{blob_name}"

    def _launch_dataflow_job(
        self,
        package_path: str,
        job_name: str
    ) -> str:
        """Launch Dataflow job.
        
        Args:
            package_path: GCS path to package
            job_name: Name for the job
            
        Returns:
            Job ID
        """
        location_path = f"projects/{self.project_id}/locations/{self.config['region']}"
        
        job = {
            "name": job_name,
            "parameters": {
                "project": self.project_id,
                "region": self.config["region"],
                "temp_location": f"gs://{self.project_id}-dataflow-temp",
                "setup_file": "./setup.py",
                "requirements_file": "requirements.txt",
                "streaming": True,
                "runner": "DataflowRunner",
                "max_num_workers": self.config["max_workers"],
                "autoscaling_algorithm": "THROUGHPUT_BASED",
                "experiments": [
                    "use_runner_v2",
                    "enable_streaming_engine"
                ]
            },
            "environment": {
                "service_account_email": self.config["service_account"],
                "worker_zone": self.config["zone"],
                "temp_location": f"gs://{self.project_id}-dataflow-temp",
                "network": self.config["network"],
                "subnetwork": self.config["subnetwork"],
                "machine_type": self.config["machine_type"],
                "additional_experiments": [
                    "use_runner_v2",
                    "enable_streaming_engine"
                ],
                "enable_streaming_engine": True
            }
        }

        request = dataflow_v1beta3.LaunchTemplateRequest(
            project_id=self.project_id,
            gcs_path=package_path,
            location=self.config["region"],
            launch_parameters=job
        )

        response = self.dataflow_client.launch_template(request=request)
        return response.job.id

    def _wait_for_job(self, job_id: str, timeout: int = 300) -> None:
        """Wait for Dataflow job to be ready.
        
        Args:
            job_id: Job ID to wait for
            timeout: Timeout in seconds
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            job = self.dataflow_client.get_job(
                project_id=self.project_id,
                location=self.config["region"],
                job_id=job_id
            )
            
            if job.current_state == "JOB_STATE_RUNNING":
                return
            elif job.current_state in ["JOB_STATE_FAILED", "JOB_STATE_CANCELLED"]:
                raise Exception(f"Job failed with state: {job.current_state}")
            
            time.sleep(10)
        
        raise TimeoutError("Job did not reach running state within timeout")

    def deploy(self) -> None:
        """Deploy the pipeline."""
        print(f"Deploying to {self.environment}...")

        # Upload package
        package_path = self._upload_package()
        print(f"Uploaded package to {package_path}")

        # Launch job
        job_name = f"rtdp-{self.environment}-{self.version}"
        job_id = self._launch_dataflow_job(package_path, job_name)
        print(f"Launched Dataflow job {job_id}")

        # Wait for job to be ready
        self._wait_for_job(job_id)
        print("Deployment completed successfully!")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Deploy Real-Time Data Pipeline"
    )
    parser.add_argument(
        "--project-id",
        required=True,
        help="GCP project ID"
    )
    parser.add_argument(
        "--environment",
        choices=["staging", "production"],
        required=True,
        help="Deployment environment"
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Deployment version"
    )
    parser.add_argument(
        "--config",
        default="config/deployment_config.yaml",
        help="Path to deployment configuration"
    )
    args = parser.parse_args()

    deployer = PipelineDeployer(
        project_id=args.project_id,
        environment=args.environment,
        version=args.version,
        config_path=args.config
    )
    deployer.deploy()


if __name__ == "__main__":
    main()
