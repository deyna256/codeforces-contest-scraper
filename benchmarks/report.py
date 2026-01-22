"""Generate comparison reports for multiple model benchmarks."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from benchmarks.html_report import generate_html_report as generate_html_report_from_data
from benchmarks.metrics import BenchmarkMetrics


def generate_comparison_report(
    all_metrics: list[BenchmarkMetrics], output_dir: Path
) -> tuple[Path, dict[str, Any]]:
    """
    Generate a comprehensive comparison report for all models.

    Args:
        all_metrics: List of metrics for each model
        output_dir: Directory to save the report

    Returns:
        Path to the generated report file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"benchmark_comparison_{timestamp}.json"
    report_path = output_dir / report_filename

    # Prepare comparison data
    report_data: dict[str, Any] = {
        "benchmark_info": {
            "timestamp": timestamp,
            "total_models": len(all_metrics),
            "test_cases": all_metrics[0].total_tests if all_metrics else 0,
        },
        "summary": [],
        "detailed_results": {},
    }

    # Add summary for each model
    for metrics in all_metrics:
        summary = {
            "model_name": metrics.model_name,
            "display_name": metrics.display_name,
            "accuracy": round(metrics.accuracy, 2),
            "successful_tests": metrics.successful_tests,
            "failed_tests": metrics.failed_tests,
            "avg_latency_ms": round(metrics.avg_latency_ms, 2),
            "precision": round(metrics._calculate_precision(), 2),
            "recall": round(metrics._calculate_recall(), 2),
            "f1_score": round(metrics._calculate_f1(), 2),
        }
        report_data["summary"].append(summary)

        # Add detailed results
        report_data["detailed_results"][metrics.model_name] = {
            "test_results": [
                {
                    "contest_id": r.contest_id,
                    "expected": r.expected_editorial,
                    "found": r.found_editorial,
                    "correct": r.is_correct,
                    "latency_ms": round(r.latency_ms, 2),
                    "error": r.error,
                }
                for r in metrics.test_results
            ]
        }

    # Sort summary by accuracy descending
    report_data["summary"].sort(key=lambda x: x["accuracy"], reverse=True)

    # Save report
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)

    return report_path, report_data


def generate_html_report(
    all_metrics: list[BenchmarkMetrics], output_dir: Path
) -> Path:
    """
    Generate interactive HTML report for benchmark results.

    Args:
        all_metrics: List of metrics for each model
        output_dir: Directory to save the report

    Returns:
        Path to the generated HTML report file
    """
    # First generate JSON data
    _, report_data = generate_comparison_report(all_metrics, output_dir)

    # Generate HTML filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_filename = f"benchmark_report_{timestamp}.html"
    html_path = output_dir / html_filename

    # Generate HTML report
    return generate_html_report_from_data(report_data, html_path)


def print_comparison_table(all_metrics: list[BenchmarkMetrics]) -> None:
    """
    Print a formatted comparison table to console.

    Args:
        all_metrics: List of metrics for each model
    """
    if not all_metrics:
        return

    # Sort by accuracy
    sorted_metrics = sorted(all_metrics, key=lambda m: m.accuracy, reverse=True)

    print("\n" + "=" * 100)
    print("BENCHMARK COMPARISON")
    print("=" * 100)
    print(
        f"{'Rank':<6} {'Model':<35} {'Accuracy':>10} {'Avg Latency':>15} {'F1 Score':>12}"
    )
    print("-" * 100)

    for rank, metrics in enumerate(sorted_metrics, 1):
        print(
            f"{rank:<6} {metrics.display_name:<35} "
            f"{metrics.accuracy:>9.1f}% {metrics.avg_latency_ms:>13.0f}ms "
            f"{metrics._calculate_f1():>11.1f}%"
        )

    print("=" * 100)
    print()
