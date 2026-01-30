"""Console output formatting for benchmark results."""

from benchmarks.reporting.base_metrics import BenchmarkMetrics


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
