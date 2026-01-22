"""Metrics and results for benchmarking."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from benchmarks.pricing import ModelPricing


@dataclass
class TestResult:
    """Result for a single test case."""

    contest_id: str
    expected_editorial: str | None
    found_editorial: list[str]
    is_correct: bool
    latency_ms: float
    error: str | None = None


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
    min_latency_ms: float
    max_latency_ms: float
    true_positives: int  # Found editorial when it exists
    false_positives: int  # Found editorial when it doesn't exist
    false_negatives: int  # Didn't find editorial when it exists
    true_negatives: int  # Correctly identified no editorial
    pricing: Optional[ModelPricing] = None  # Pricing information from OpenRouter
    test_results: list[TestResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        pricing_dict = None
        if self.pricing:
            pricing_dict = {
                "prompt_price": self.pricing.prompt_price,
                "completion_price": self.pricing.completion_price,
                "avg_price_per_token": round(self.pricing.avg_price_per_token, 10),
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
                "min_latency_ms": round(self.min_latency_ms, 2),
                "max_latency_ms": round(self.max_latency_ms, 2),
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
            "test_results": [
                {
                    "contest_id": r.contest_id,
                    "expected": r.expected_editorial,
                    "found": r.found_editorial,
                    "correct": r.is_correct,
                    "latency_ms": round(r.latency_ms, 2),
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

    def save(self, output_dir: Path) -> Path:
        """Save metrics to JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.model_name.replace('/', '_')}_{self.timestamp}.json"
        filepath = output_dir / filename
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        return filepath

    def print_summary(self) -> None:
        """Print formatted summary to console."""
        print(f"\n{'='*70}")
        print(f"Benchmark Results: {self.display_name}")
        print(f"{'='*70}")
        print(f"Model: {self.model_name}")
        print(f"Timestamp: {self.timestamp}")
        print()
        print(f"Tests: {self.successful_tests}/{self.total_tests} successful")
        print(f"Accuracy: {self.accuracy:.1f}%")
        print()
        print("Performance:")
        print(f"  Avg Latency: {self.avg_latency_ms:.0f}ms")
        print(f"  Median Latency: {self.median_latency_ms:.0f}ms")
        print(f"  Range: {self.min_latency_ms:.0f}ms - {self.max_latency_ms:.0f}ms")
        print()
        print("Classification Metrics:")
        print(f"  True Positives:  {self.true_positives}")
        print(f"  False Positives: {self.false_positives}")
        print(f"  False Negatives: {self.false_negatives}")
        print(f"  True Negatives:  {self.true_negatives}")
        print(f"  Precision: {self._calculate_precision():.1f}%")
        print(f"  Recall:    {self._calculate_recall():.1f}%")
        print(f"  F1 Score:  {self._calculate_f1():.1f}%")
        print(f"{'='*70}\n")


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
    min_latency = min(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0

    # Classification metrics
    tp = sum(
        1
        for r in results
        if r.expected_editorial is not None and len(r.found_editorial) > 0 and r.is_correct
    )
    fp = sum(
        1
        for r in results
        if r.expected_editorial is None and len(r.found_editorial) > 0 and not r.is_correct
    )
    fn = sum(
        1
        for r in results
        if r.expected_editorial is not None and len(r.found_editorial) == 0
    )
    tn = sum(
        1
        for r in results
        if r.expected_editorial is None and len(r.found_editorial) == 0 and r.is_correct
    )

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
        min_latency_ms=min_latency,
        max_latency_ms=max_latency,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        true_negatives=tn,
        test_results=results,
    )
