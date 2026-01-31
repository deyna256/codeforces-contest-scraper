"""Base metrics and results for benchmarking."""

from dataclasses import dataclass, field
from typing import Any, Optional

from benchmarks.pricing import ModelPricing


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
    test_results: list[Any] = field(default_factory=list)

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
            "test_results": self._serialize_test_results(),
        }

    def _serialize_test_results(self) -> list[dict[str, Any]]:
        """Serialize test results - handles both Finder and Segmentation result types."""
        results = []
        for r in self.test_results:
            # Determine result type and extract appropriate fields
            if hasattr(r, "expected_editorial"):
                # FinderTestResult
                result_dict: dict[str, Any] = {
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
            elif hasattr(r, "expected_problems"):
                # SegmentationTestResult
                result_dict = {
                    "contest_id": r.contest_id,
                    "expected_problems": r.expected_problems,
                    "found_problems": r.found_problems,
                    "problem_accuracy": r.problem_accuracy,
                    "correct": r.is_correct,
                    "latency_ms": round(r.latency_ms, 2),
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                    "total_tokens": r.total_tokens,
                    "error": r.error,
                }
            else:
                # Fallback for unknown result types
                result_dict = {
                    "contest_id": getattr(r, "contest_id", None),
                    "correct": getattr(r, "is_correct", None),
                    "latency_ms": round(getattr(r, "latency_ms", 0), 2),
                    "error": getattr(r, "error", None),
                }
            results.append(result_dict)
        return results

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
