"""Script to run performance tests for the Real-Time Data Pipeline."""

import argparse
import json
import os
from datetime import datetime

from rtdp.perf.test_runner import PerformanceTestRunner


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Run performance tests for Real-Time Data Pipeline"
    )
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--topic-id", required=True, help="Pub/Sub topic ID")
    parser.add_argument("--dataset-id", required=True, help="BigQuery dataset ID")
    parser.add_argument("--table-id", required=True, help="BigQuery table ID")
    parser.add_argument(
        "--test-type",
        choices=["constant", "increasing", "burst"],
        required=True,
        help="Type of performance test to run",
    )
    parser.add_argument(
        "--output-dir", default="test_results", help="Directory to save test results"
    )

    # Test-specific arguments
    parser.add_argument(
        "--messages-per-second",
        type=int,
        help="Messages per second for constant load test",
    )
    parser.add_argument(
        "--duration-seconds",
        type=int,
        help="Duration in seconds for constant load test",
    )
    parser.add_argument(
        "--initial-rate", type=int, help="Initial rate for increasing load test"
    )
    parser.add_argument(
        "--final-rate", type=int, help="Final rate for increasing load test"
    )
    parser.add_argument(
        "--step-size", type=int, help="Step size for increasing load test"
    )
    parser.add_argument(
        "--step-duration", type=int, help="Step duration for increasing load test"
    )
    parser.add_argument(
        "--burst-size", type=int, help="Messages per second during burst"
    )
    parser.add_argument(
        "--burst-duration", type=int, help="Duration of each burst in seconds"
    )
    parser.add_argument(
        "--rest-duration", type=int, help="Duration of rest between bursts"
    )
    parser.add_argument("--num-bursts", type=int, help="Number of bursts")

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialize test runner
    runner = PerformanceTestRunner(
        project_id=args.project_id,
        topic_id=args.topic_id,
        dataset_id=args.dataset_id,
        table_id=args.table_id,
    )

    # Run tests based on type
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if args.test_type == "constant":
        if not (args.messages_per_second and args.duration_seconds):
            parser.error(
                "constant load test requires --messages-per-second and "
                "--duration-seconds"
            )

        print(
            f"Running constant load test: {args.messages_per_second} msg/s "
            f"for {args.duration_seconds}s"
        )

        results = [
            runner.run_constant_load_test(
                args.messages_per_second, args.duration_seconds
            )
        ]

        output_file = os.path.join(
            args.output_dir, f"constant_load_test_{timestamp}.json"
        )

    elif args.test_type == "increasing":
        if not (
            args.initial_rate
            and args.final_rate
            and args.step_size
            and args.step_duration
        ):
            parser.error(
                "increasing load test requires --initial-rate, --final-rate, "
                "--step-size, and --step-duration"
            )

        print(
            f"Running increasing load test: {args.initial_rate} to "
            f"{args.final_rate} msg/s"
        )

        results = runner.run_increasing_load_test(
            args.initial_rate, args.final_rate, args.step_size, args.step_duration
        )

        output_file = os.path.join(
            args.output_dir, f"increasing_load_test_{timestamp}.json"
        )

    else:  # burst
        if not (
            args.burst_size
            and args.burst_duration
            and args.rest_duration
            and args.num_bursts
        ):
            parser.error(
                "burst load test requires --burst-size, --burst-duration, "
                "--rest-duration, and --num-bursts"
            )

        print(
            f"Running burst load test: {args.burst_size} msg/s, "
            f"{args.num_bursts} bursts"
        )

        results = runner.run_burst_load_test(
            args.burst_size, args.burst_duration, args.rest_duration, args.num_bursts
        )

        output_file = os.path.join(args.output_dir, f"burst_load_test_{timestamp}.json")

    # Save results
    runner.save_results(results, output_file)
    print(f"Test results saved to {output_file}")

    # Print summary
    print("\nTest Summary:")
    for result in results:
        print(f"\nTest: {result.test_name}")
        print(f"Messages sent: {result.messages_sent}")
        print(f"Messages processed: {result.messages_processed}")
        print(f"Average latency: {result.avg_latency:.2f}s")
        print(f"P50 latency: {result.p50_latency:.2f}s")
        print(f"P95 latency: {result.p95_latency:.2f}s")
        print(f"P99 latency: {result.p99_latency:.2f}s")
        print(f"Errors: {result.errors}")
        print(f"Throughput: {result.throughput:.2f} msg/s")


if __name__ == "__main__":
    main()
