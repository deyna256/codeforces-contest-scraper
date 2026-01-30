"""Metrics and results for editorial finder benchmarks."""

from dataclasses import dataclass
from datetime import datetime

from benchmarks.reporting.base_metrics import BenchmarkMetrics


@dataclass
class FinderTestResult:
    """Result for a single editorial finder test case."""

    contest_id: str
    expected_editorial: list[str]
    found_editorial: list[str]
    is_correct: bool
    latency_ms: float
    error: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def calculate_finder_metrics(
    model_name: str, display_name: str, results: list[FinderTestResult]
) -> BenchmarkMetrics:
    """
    Calculate aggregate metrics from editorial finder test results.

    Args:
        model_name: Model identifier
        display_name: Human-readable model name
        results: List of test results

    Returns:
        Aggregated metrics
    """
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.error is None)
    failed_tests = total_tests - successful_tests

    # Only consider successful tests for accuracy
    correct = sum(1 for r in results if r.is_correct and r.error is None)
    accuracy = (correct / successful_tests * 100) if successful_tests > 0 else 0.0

    # Latency metrics (only for successful tests)
    latencies = [r.latency_ms for r in results if r.error is None]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    median_latency = sorted(latencies)[len(latencies) // 2] if latencies else 0.0

    # Classification metrics
    tp = sum(
        1
        for r in results
        if len(r.expected_editorial) > 0 and len(r.found_editorial) > 0 and r.is_correct
    )
    fp = sum(
        1
        for r in results
        if len(r.expected_editorial) == 0 and len(r.found_editorial) > 0 and not r.is_correct
    )
    fn = sum(1 for r in results if len(r.expected_editorial) > 0 and len(r.found_editorial) == 0)
    tn = sum(
        1
        for r in results
        if len(r.expected_editorial) == 0 and len(r.found_editorial) == 0 and r.is_correct
    )

    # Calculate token usage
    total_prompt_tokens = sum(r.prompt_tokens for r in results)
    total_completion_tokens = sum(r.completion_tokens for r in results)
    total_tokens_used = total_prompt_tokens + total_completion_tokens
    avg_tokens = total_tokens_used / total_tests if total_tests > 0 else 0.0

    return BenchmarkMetrics(
        model_name=model_name,
        display_name=display_name,
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
        total_tests=total_tests,
        successful_tests=successful_tests,
        failed_tests=failed_tests,
        accuracy=accuracy,
        avg_latency_ms=avg_latency,
        median_latency_ms=median_latency,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        true_negatives=tn,
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        avg_tokens_per_test=avg_tokens,
        test_results=results,
    )
