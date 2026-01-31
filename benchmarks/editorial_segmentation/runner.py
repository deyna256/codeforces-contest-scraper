"""Editorial segmentation benchmark runner."""

import time

from loguru import logger

from benchmarks.config import ModelConfig
from benchmarks.core.base_runner import BaseBenchmarkRunner
from benchmarks.core.tracked_llm_client import TrackedLLMClient
from benchmarks.editorial_segmentation.metrics import (
    SegmentationTestResult,
    calculate_segmentation_metrics,
)
from benchmarks.editorial_segmentation.test_data import (
    SEGMENTATION_TEST_CASES,
    SegmentationTestCase,
)
from benchmarks.reporting.base_metrics import BenchmarkMetrics
from infrastructure.parsers.editorial_content_parser import EditorialContentParser


class SegmentationRunner(BaseBenchmarkRunner[SegmentationTestCase, SegmentationTestResult]):
    """Benchmark runner for editorial segmentation with different LLM models."""

    def __init__(self, api_key: str):
        """
        Initialize segmentation benchmark runner.

        Args:
            api_key: OpenRouter API key
        """
        super().__init__(api_key=api_key, test_cases=SEGMENTATION_TEST_CASES)

    async def test_single_case(
        self,
        model_config: ModelConfig,
        test_case: SegmentationTestCase,
    ) -> SegmentationTestResult:
        """
        Test editorial segmentation for a single contest.

        Args:
            model_config: Model configuration
            test_case: Test case data

        Returns:
            Segmentation test result
        """
        contest_id = test_case["contest_id"]
        editorial_urls = test_case["editorial_urls"]
        expected_problems = test_case["expected_problems"]

        # Format expected problems as list of strings
        expected_problems_list = [f"{cid}/{pid}" for cid, pid in expected_problems.keys()]

        # If no URLs - expected to return empty (correct result)
        if not editorial_urls:
            if not expected_problems:
                return SegmentationTestResult(
                    contest_id=contest_id,
                    expected_problems=[],
                    found_problems=[],
                    problem_accuracy={},
                    is_correct=True,
                    latency_ms=0.0,
                    error=None,
                )
            else:
                # No URLs but problems expected - incorrect
                return SegmentationTestResult(
                    contest_id=contest_id,
                    expected_problems=expected_problems_list,
                    found_problems=[],
                    problem_accuracy={key: False for key in expected_problems_list},
                    is_correct=False,
                    latency_ms=0.0,
                    error="No editorial URLs provided but problems expected",
                )

        start_time = time.perf_counter()

        try:
            # Initialize tracked LLM client with specific model
            # Use longer timeout for segmentation tasks
            llm_client = TrackedLLMClient(
                api_key=self.api_key,
                model=model_config["name"],
                timeout=model_config["timeout_segmentation"],
            )

            # Create editorial content parser
            parser = EditorialContentParser(
                http_client=self.http_client,
                llm_client=llm_client,
            )

            # Parse editorial content and segment by problem
            result = await parser.parse_editorial_content(
                contest_id=contest_id,
                editorial_urls=editorial_urls,
                expected_problems=list(expected_problems.keys()),
            )

            # Collect found problems
            found = {(e.contest_id, e.problem_id) for e in result.editorials}
            found_problems_list = [f"{cid}/{pid}" for cid, pid in found]

            # Calculate accuracy for each problem
            problem_accuracy = {}
            for (cid, pid), should_exist in expected_problems.items():
                key = f"{cid}/{pid}"
                is_found = (cid, pid) in found
                problem_accuracy[key] = is_found == should_exist

            # Overall correctness - all problems must be correct
            is_correct = all(problem_accuracy.values())

            # Get token usage
            usage = llm_client.get_last_usage()
            latency_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                f"Segmentation test for contest {contest_id}: "
                f"{'✓' if is_correct else '✗'} "
                f"({sum(problem_accuracy.values())}/{len(problem_accuracy)} problems correct)"
            )

            return SegmentationTestResult(
                contest_id=contest_id,
                expected_problems=expected_problems_list,
                found_problems=found_problems_list,
                problem_accuracy=problem_accuracy,
                is_correct=is_correct,
                latency_ms=latency_ms,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                error=None,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Error in segmentation test for contest {contest_id}: {e}")

            return SegmentationTestResult(
                contest_id=contest_id,
                expected_problems=expected_problems_list,
                found_problems=[],
                problem_accuracy={key: False for key in expected_problems_list},
                is_correct=False,
                latency_ms=latency_ms,
                error=str(e),
            )

    def calculate_metrics(
        self,
        model_name: str,
        display_name: str,
        results: list[SegmentationTestResult],
    ) -> BenchmarkMetrics:
        """
        Calculate metrics from segmentation test results.

        Args:
            model_name: Model name
            display_name: Display name
            results: List of test results

        Returns:
            Benchmark metrics
        """
        return calculate_segmentation_metrics(model_name, display_name, results)
