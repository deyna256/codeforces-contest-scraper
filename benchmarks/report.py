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
        pricing_dict = None
        if metrics.pricing:
            pricing_dict = {
                "prompt_price": metrics.pricing.prompt_price,
                "completion_price": metrics.pricing.completion_price,
                "currency": metrics.pricing.currency,
            }

        summary = {
            "model_name": metrics.model_name,
            "display_name": metrics.display_name,
            "accuracy": round(metrics.accuracy, 2),
            "successful_tests": metrics.successful_tests,
            "failed_tests": metrics.failed_tests,
            "avg_latency_ms": round(metrics.avg_latency_ms, 2),
            "avg_tokens_per_test": round(metrics.avg_tokens_per_test, 2),
            "total_tokens": metrics.total_tokens,
            "total_prompt_tokens": metrics.total_prompt_tokens,
            "total_completion_tokens": metrics.total_completion_tokens,
            "estimated_cost_usd": round(metrics.estimated_cost, 4),
            "cost_per_correct_prediction_usd": round(metrics.cost_per_correct_prediction, 4),
            "precision": round(metrics._calculate_precision(), 2),
            "recall": round(metrics._calculate_recall(), 2),
            "f1_score": round(metrics._calculate_f1(), 2),
            "pricing": pricing_dict,
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
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "total_tokens": r.total_tokens,
                    "error": r.error,
                }
                for r in metrics.test_results
            ]
        }

    # Sort summary by accuracy descending, then by cost per correct prediction ascending
    def sort_key(item):
        accuracy = item["accuracy"]
        # Use a very high cost (1e9) if cost is not available to push those items down
        cost = item.get("cost_per_correct_prediction_usd", 1e9)
        return (-accuracy, cost)

    report_data["summary"].sort(key=sort_key)

    # Save report
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)

    return report_path, report_data


def generate_html_report(all_metrics: list[BenchmarkMetrics], output_dir: Path) -> Path:
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

    # Sort by accuracy descending, then by cost per correct prediction ascending
    def sort_key(metrics: BenchmarkMetrics):
        accuracy = metrics.accuracy
        cost = (
            metrics.cost_per_correct_prediction if metrics.cost_per_correct_prediction > 0 else 1e9
        )
        return (-accuracy, cost)

    sorted_metrics = sorted(all_metrics, key=sort_key)

    print("\n" + "=" * 150)
    print("BENCHMARK COMPARISON (Sorted: Accuracy → Price)")
    print("=" * 150)
    print(
        f"{'Rank':<6} {'Model':<30} {'Accuracy':>10} {'Avg Latency':>13} {'Avg Tokens':>12} {'Total Tokens':>14} {'Est. Cost':>12} {'F1 Score':>10}"
    )
    print("-" * 150)

    for rank, metrics in enumerate(sorted_metrics, 1):
        cost_str = f"${metrics.estimated_cost:.4f}" if metrics.estimated_cost > 0 else "N/A"

        print(
            f"{rank:<6} {metrics.display_name:<30} "
            f"{metrics.accuracy:>9.1f}% {metrics.avg_latency_ms:>11.0f}ms "
            f"{metrics.avg_tokens_per_test:>11.0f} {metrics.total_tokens:>13,} "
            f"{cost_str:>12} {metrics._calculate_f1():>9.1f}%"
        )

    print("=" * 150)
    print()
