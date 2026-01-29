"""Metrics and results for benchmarking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from benchmarks.pricing import ModelPricing


@dataclass
class TestResult:
    """Result for a single test case."""

    contest_id: str
    expected_editorial: list[str]
    found_editorial: list[str]
    is_correct: bool
    latency_ms: float
    error: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class BenchmarkMetrics:
    """Aggregate metrics for a model benchmark."""

    model_name: str
    display_name: str
    timestamp: str
    total_tests: int
    successful_tests: int
    failed_tests: int
    accuracy: float  # Percentage of correct predictions
    avg_latency_ms: float
    median_latency_ms: float
    true_positives: int  # Found editorial when it exists
    false_positives: int  # Found editorial when it doesn't exist
    false_negatives: int  # Didn't find editorial when it exists
    true_negatives: int  # Correctly identified no editorial
    total_prompt_tokens: int = 0  # Total prompt tokens used
    total_completion_tokens: int = 0  # Total completion tokens used
    avg_tokens_per_test: float = 0.0  # Average tokens per test
    pricing: Optional[ModelPricing] = None  # Pricing information from OpenRouter
    estimated_cost: float = 0.0  # Estimated cost in USD based on token usage
    cost_per_correct_prediction: float = 0.0  # Cost per correct prediction in USD
    test_results: list[TestResult] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens on the fly."""
        return self.total_prompt_tokens + self.total_completion_tokens

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        pricing_dict = None
        if self.pricing:
            pricing_dict = {
                "prompt_price": self.pricing.prompt_price,
                "completion_price": self.pricing.completion_price,
                "currency": self.pricing.currency,
            }

        return {
            "model_name": self.model_name,
            "display_name": self.display_name,
            "timestamp": self.timestamp,
            "summary": {
                "total_tests": self.total_tests,
                "successful_tests": self.successful_tests,
                "failed_tests": self.failed_tests,
                "accuracy": round(self.accuracy, 2),
            },
            "performance": {
                "avg_latency_ms": round(self.avg_latency_ms, 2),
                "median_latency_ms": round(self.median_latency_ms, 2),
            },
            "classification": {
                "true_positives": self.true_positives,
                "false_positives": self.false_positives,
                "false_negatives": self.false_negatives,
                "true_negatives": self.true_negatives,
                "precision": round(self._calculate_precision(), 2),
                "recall": round(self._calculate_recall(), 2),
                "f1_score": round(self._calculate_f1(), 2),
            },
            "pricing": pricing_dict,
            "token_usage": {
                "total_prompt_tokens": self.total_prompt_tokens,
                "total_completion_tokens": self.total_completion_tokens,
                "total_tokens": self.total_tokens,
                "avg_tokens_per_test": round(self.avg_tokens_per_test, 2),
                "estimated_cost_usd": round(self.estimated_cost, 4),
                "cost_per_correct_prediction_usd": round(self.cost_per_correct_prediction, 4),
            },
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
                for r in self.test_results
            ],
        }

    def _calculate_precision(self) -> float:
        """Calculate precision: TP / (TP + FP)."""
        denominator = self.true_positives + self.false_positives
        if denominator == 0:
            return 0.0
        return (self.true_positives / denominator) * 100

    def _calculate_recall(self) -> float:
        """Calculate recall: TP / (TP + FN)."""
        denominator = self.true_positives + self.false_negatives
        if denominator == 0:
            return 0.0
        return (self.true_positives / denominator) * 100

    def _calculate_f1(self) -> float:
        """Calculate F1 score: 2 * (precision * recall) / (precision + recall)."""
        precision = self._calculate_precision()
        recall = self._calculate_recall()
        denominator = precision + recall
        if denominator == 0:
            return 0.0
        return 2 * (precision * recall) / denominator


def calculate_metrics(
    model_name: str, display_name: str, results: list[TestResult]
) -> BenchmarkMetrics:
    """
    Calculate aggregate metrics from test results.

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
