"""Script to analyze and visualize performance test results."""

import argparse
import json
from datetime import datetime
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


def load_results(file_path: str) -> List[Dict[str, Any]]:
    """Load test results from file.

    Args:
        file_path: Path to results file

    Returns:
        List of test results
    """
    with open(file_path, "r") as f:
        results = json.load(f)

    # Convert timestamp strings to datetime
    for result in results:
        result["start_time"] = datetime.fromisoformat(result["start_time"])
        result["end_time"] = datetime.fromisoformat(result["end_time"])

    return results


def plot_latency_distribution(results: List[Dict[str, Any]], output_file: str) -> None:
    """Plot latency distribution.

    Args:
        results: Test results
        output_file: Output file path
    """
    plt.figure(figsize=(12, 6))

    data = pd.DataFrame(
        [
            {"Test": result["test_name"], "Latency": latency, "Percentile": percentile}
            for result in results
            for latency, percentile in [
                (result["p50_latency"], "P50"),
                (result["p95_latency"], "P95"),
                (result["p99_latency"], "P99"),
            ]
        ]
    )

    sns.barplot(data=data, x="Test", y="Latency", hue="Percentile")

    plt.title("Latency Distribution by Test")
    plt.xlabel("Test")
    plt.ylabel("Latency (seconds)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_file}_latency_dist.png")
    plt.close()


def plot_throughput_vs_errors(results: List[Dict[str, Any]], output_file: str) -> None:
    """Plot throughput vs errors.

    Args:
        results: Test results
        output_file: Output file path
    """
    plt.figure(figsize=(10, 6))

    throughputs = [result["throughput"] for result in results]
    errors = [result["errors"] for result in results]
    labels = [result["test_name"] for result in results]

    plt.scatter(throughputs, errors)

    for i, label in enumerate(labels):
        plt.annotate(
            label,
            (throughputs[i], errors[i]),
            xytext=(5, 5),
            textcoords="offset points",
        )

    plt.title("Throughput vs Errors")
    plt.xlabel("Throughput (messages/second)")
    plt.ylabel("Number of Errors")
    plt.tight_layout()
    plt.savefig(f"{output_file}_throughput_errors.png")
    plt.close()


def plot_processing_efficiency(results: List[Dict[str, Any]], output_file: str) -> None:
    """Plot processing efficiency.

    Args:
        results: Test results
        output_file: Output file path
    """
    plt.figure(figsize=(10, 6))

    data = pd.DataFrame(
        [
            {"Test": result["test_name"], "Messages": count, "Type": msg_type}
            for result in results
            for count, msg_type in [
                (result["messages_sent"], "Sent"),
                (result["messages_processed"], "Processed"),
            ]
        ]
    )

    sns.barplot(data=data, x="Test", y="Messages", hue="Type")

    plt.title("Message Processing Efficiency")
    plt.xlabel("Test")
    plt.ylabel("Number of Messages")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_file}_processing_efficiency.png")
    plt.close()


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze test results.

    Args:
        results: Test results

    Returns:
        Analysis results
    """
    analysis = {
        "total_tests": len(results),
        "total_messages_sent": sum(r["messages_sent"] for r in results),
        "total_messages_processed": sum(r["messages_processed"] for r in results),
        "total_errors": sum(r["errors"] for r in results),
        "avg_throughput": np.mean([r["throughput"] for r in results]),
        "max_throughput": max(r["throughput"] for r in results),
        "avg_latency": np.mean([r["avg_latency"] for r in results]),
        "processing_efficiency": (
            sum(r["messages_processed"] for r in results)
            / sum(r["messages_sent"] for r in results)
            * 100
            if sum(r["messages_sent"] for r in results) > 0
            else 0
        ),
    }

    # Calculate throughput stability
    throughputs = [r["throughput"] for r in results]
    analysis["throughput_std"] = np.std(throughputs)
    analysis["throughput_cv"] = (
        analysis["throughput_std"] / analysis["avg_throughput"]
        if analysis["avg_throughput"] > 0
        else 0
    )

    # Identify performance bottlenecks
    latencies = [r["avg_latency"] for r in results]
    throughputs = [r["throughput"] for r in results]
    correlation = stats.pearsonr(throughputs, latencies)[0]

    analysis["bottleneck_indicators"] = {
        "latency_throughput_correlation": correlation,
        "high_error_tests": [r["test_name"] for r in results if r["errors"] > 0],
        "high_latency_tests": [
            r["test_name"]
            for r in results
            if r["avg_latency"] > np.mean(latencies) + np.std(latencies)
        ],
    }

    return analysis


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze performance test results")
    parser.add_argument("results_file", help="Path to test results file")
    parser.add_argument(
        "--output-prefix", default="perf_analysis", help="Prefix for output files"
    )
    args = parser.parse_args()

    # Load results
    results = load_results(args.results_file)

    # Generate plots
    plot_latency_distribution(results, args.output_prefix)
    plot_throughput_vs_errors(results, args.output_prefix)
    plot_processing_efficiency(results, args.output_prefix)

    # Analyze results
    analysis = analyze_results(results)

    # Save analysis
    with open(f"{args.output_prefix}_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Print summary
    print("\nPerformance Analysis Summary:")
    print(f"Total tests run: {analysis['total_tests']}")
    print(f"Total messages sent: {analysis['total_messages_sent']}")
    print(f"Total messages processed: {analysis['total_messages_processed']}")
    print(f"Total errors: {analysis['total_errors']}")
    print(f"Average throughput: {analysis['avg_throughput']:.2f} msg/s")
    print(f"Maximum throughput: {analysis['max_throughput']:.2f} msg/s")
    print(f"Average latency: {analysis['avg_latency']:.2f}s")
    print(f"Processing efficiency: {analysis['processing_efficiency']:.2f}%")
    print(f"Throughput stability (CV): {analysis['throughput_cv']:.2f}")

    if analysis["bottleneck_indicators"]["high_error_tests"]:
        print("\nTests with high errors:")
        for test in analysis["bottleneck_indicators"]["high_error_tests"]:
            print(f"- {test}")

    if analysis["bottleneck_indicators"]["high_latency_tests"]:
        print("\nTests with high latency:")
        for test in analysis["bottleneck_indicators"]["high_latency_tests"]:
            print(f"- {test}")


if __name__ == "__main__":
    main()
