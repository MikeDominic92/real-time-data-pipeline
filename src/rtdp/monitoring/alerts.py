"""Alert management for the Real-Time Data Pipeline."""

import json
from typing import Any, Dict, List, Optional, Union

from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import AlertPolicy, NotificationChannel
from google.protobuf.duration_pb2 import Duration


class AlertManager:
    """Manage alerts for the Real-Time Data Pipeline."""

    def __init__(
        self,
        project_id: str,
        notification_channels: Optional[List[str]] = None
    ) -> None:
        """Initialize alert manager.
        
        Args:
            project_id: GCP project ID
            notification_channels: List of notification channel names
        """
        self.project_id = project_id
        self.client = monitoring_v3.AlertPolicyServiceClient()
        self.project_name = f"projects/{project_id}"
        self.notification_channels = notification_channels or []

    def create_alert_policy(
        self,
        display_name: str,
        filter_str: str,
        duration: int,
        alignment_period: int,
        threshold_value: Union[int, float],
        comparison: str,
        description: str = "",
        documentation: Optional[Dict[str, str]] = None
    ) -> AlertPolicy:
        """Create a new alert policy.
        
        Args:
            display_name: Alert policy display name
            filter_str: Metric filter string
            duration: Duration in seconds
            alignment_period: Alignment period in seconds
            threshold_value: Threshold value
            comparison: Comparison type
            description: Optional alert description
            documentation: Optional documentation
            
        Returns:
            Created alert policy
        """
        duration_pb = Duration()
        duration_pb.seconds = duration

        alignment_pb = Duration()
        alignment_pb.seconds = alignment_period

        # Create condition
        condition = monitoring_v3.AlertPolicy.Condition(
            display_name=f"Condition for {display_name}",
            condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                filter=filter_str,
                duration=duration_pb,
                comparison=getattr(
                    monitoring_v3.AlertPolicy.Condition.ComparisonType,
                    comparison
                ),
                threshold_value=threshold_value,
                aggregations=[
                    monitoring_v3.Aggregation(
                        alignment_period=alignment_pb,
                        per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
                    )
                ],
            ),
        )

        # Create alert policy
        alert_policy = monitoring_v3.AlertPolicy(
            display_name=display_name,
            conditions=[condition],
            combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.AND,
            notification_channels=self.notification_channels,
            documentation=monitoring_v3.AlertPolicy.Documentation(
                content=description,
                mime_type="text/markdown",
            ) if description else None,
        )

        if documentation:
            alert_policy.documentation.content = json.dumps(documentation)

        return self.client.create_alert_policy(
            request={
                "name": self.project_name,
                "alert_policy": alert_policy,
            }
        )

    def create_latency_alert(
        self,
        metric_type: str,
        threshold_seconds: float,
        duration_seconds: int = 300,
        alignment_period_seconds: int = 60
    ) -> AlertPolicy:
        """Create a latency alert policy.
        
        Args:
            metric_type: Type of latency metric
            threshold_seconds: Latency threshold in seconds
            duration_seconds: Duration for condition evaluation
            alignment_period_seconds: Alignment period in seconds
            
        Returns:
            Created alert policy
        """
        return self.create_alert_policy(
            display_name=f"High Latency Alert - {metric_type}",
            filter_str=(
                f'metric.type="custom.googleapis.com/rtdp/latency/{metric_type}" '
                'AND resource.type="generic_task"'
            ),
            duration=duration_seconds,
            alignment_period=alignment_period_seconds,
            threshold_value=threshold_seconds,
            comparison="COMPARISON_GT",
            description=(
                f"Alert when {metric_type} latency exceeds {threshold_seconds} "
                f"seconds for {duration_seconds} seconds"
            ),
            documentation={
                "impact": "High latency may indicate processing bottlenecks",
                "recommended_actions": [
                    "Check system resources",
                    "Verify upstream dependencies",
                    "Scale processing resources if needed"
                ]
            }
        )

    def create_error_rate_alert(
        self,
        metric_type: str,
        threshold_rate: float,
        duration_seconds: int = 300,
        alignment_period_seconds: int = 60
    ) -> AlertPolicy:
        """Create an error rate alert policy.
        
        Args:
            metric_type: Type of error metric
            threshold_rate: Error rate threshold (0-1)
            duration_seconds: Duration for condition evaluation
            alignment_period_seconds: Alignment period in seconds
            
        Returns:
            Created alert policy
        """
        return self.create_alert_policy(
            display_name=f"High Error Rate Alert - {metric_type}",
            filter_str=(
                f'metric.type="custom.googleapis.com/rtdp/errors/{metric_type}" '
                'AND resource.type="generic_task"'
            ),
            duration=duration_seconds,
            alignment_period=alignment_period_seconds,
            threshold_value=threshold_rate,
            comparison="COMPARISON_GT",
            description=(
                f"Alert when {metric_type} error rate exceeds {threshold_rate} "
                f"for {duration_seconds} seconds"
            ),
            documentation={
                "impact": "High error rate may indicate system issues",
                "recommended_actions": [
                    "Check error logs",
                    "Verify system configuration",
                    "Check data quality"
                ]
            }
        )

    def create_throughput_alert(
        self,
        metric_type: str,
        min_throughput: int,
        duration_seconds: int = 300,
        alignment_period_seconds: int = 60
    ) -> AlertPolicy:
        """Create a throughput alert policy.
        
        Args:
            metric_type: Type of throughput metric
            min_throughput: Minimum expected throughput
            duration_seconds: Duration for condition evaluation
            alignment_period_seconds: Alignment period in seconds
            
        Returns:
            Created alert policy
        """
        return self.create_alert_policy(
            display_name=f"Low Throughput Alert - {metric_type}",
            filter_str=(
                f'metric.type="custom.googleapis.com/rtdp/counter/{metric_type}" '
                'AND resource.type="generic_task"'
            ),
            duration=duration_seconds,
            alignment_period=alignment_period_seconds,
            threshold_value=min_throughput,
            comparison="COMPARISON_LT",
            description=(
                f"Alert when {metric_type} throughput falls below "
                f"{min_throughput} for {duration_seconds} seconds"
            ),
            documentation={
                "impact": "Low throughput may indicate processing issues",
                "recommended_actions": [
                    "Check input data flow",
                    "Verify processing capacity",
                    "Check for bottlenecks"
                ]
            }
        )

    def delete_alert_policy(self, policy_name: str) -> None:
        """Delete an alert policy.
        
        Args:
            policy_name: Name of the alert policy to delete
        """
        self.client.delete_alert_policy(name=policy_name)

    def list_alert_policies(self) -> List[AlertPolicy]:
        """List all alert policies.
        
        Returns:
            List of alert policies
        """
        return list(self.client.list_alert_policies(name=self.project_name))

    def update_alert_policy(
        self,
        policy_name: str,
        alert_policy: AlertPolicy
    ) -> AlertPolicy:
        """Update an alert policy.
        
        Args:
            policy_name: Name of the alert policy to update
            alert_policy: Updated alert policy
            
        Returns:
            Updated alert policy
        """
        return self.client.update_alert_policy(
            alert_policy=alert_policy
        )
