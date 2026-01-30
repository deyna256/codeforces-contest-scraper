"""Metrics and results for editorial segmentation benchmarks."""

from dataclasses import dataclass
from datetime import datetime

from benchmarks.reporting.base_metrics import BenchmarkMetrics


@dataclass
class SegmentationTestResult:
    """Result for a single editorial segmentation test case."""

    contest_id: str
    expected_problems: list[str]  # ["2185/A", "2185/B", ...]
    found_problems: list[str]  # What the LLM found
    problem_accuracy: dict[str, bool]  # {"2185/A": True, "2185/B": False}
    is_correct: bool  # All problems found correctly?
    latency_ms: float
    error: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def calculate_segmentation_metrics(
    model_name: str, display_name: str, results: list[SegmentationTestResult]
) -> BenchmarkMetrics:
    """
    Calculate aggregate metrics from editorial segmentation test results.

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

    # Classification metrics for segmentation
    # True positive: expected problem was found
    # False positive: found problem that shouldn't exist
    # False negative: didn't find problem that should exist
    # True negative: correctly identified problem that shouldn't exist
    tp = 0
    fp = 0
    fn = 0
    tn = 0

    for result in results:
        if result.error:
            continue

        for problem_key, was_correct in result.problem_accuracy.items():
            # Check if this problem was expected
            is_expected = problem_key in result.expected_problems
            is_found = problem_key in result.found_problems

            if is_expected and is_found and was_correct:
                tp += 1
            elif not is_expected and is_found:
                fp += 1
            elif is_expected and not is_found:
                fn += 1
            elif not is_expected and not is_found:
                tn += 1

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
