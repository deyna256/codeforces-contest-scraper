"""Generate JSON comparison reports for benchmark results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from benchmarks.core.benchmark_types import BenchmarkType
from benchmarks.reporting.base_metrics import BenchmarkMetrics


def generate_comparison_report(
    all_metrics: list[BenchmarkMetrics],
    output_dir: Path,
    benchmark_type: BenchmarkType,
) -> tuple[Path, dict[str, Any]]:
    """
    Generate a comprehensive comparison report for all models.

    Args:
        all_metrics: List of metrics for each model
        output_dir: Directory to save the report
        benchmark_type: Type of benchmark

    Returns:
        Tuple of (report_path, report_data)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"benchmark_comparison_{timestamp}.json"
    report_path = output_dir / report_filename

    # Prepare comparison data
    report_data: dict[str, Any] = {
        "benchmark_info": {
            "type": benchmark_type.value,
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

        # Add detailed results using the metrics' serialization method
        report_data["detailed_results"][metrics.model_name] = {
            "test_results": metrics._serialize_test_results()
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
