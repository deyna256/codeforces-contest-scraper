"""Main benchmark runner for testing LLM models on editorial finding."""

import asyncio
import os
import sys
import time
from collections import Counter
from pathlib import Path

# Add project root and src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# ruff: noqa: E402
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger

from benchmarks.config import BENCHMARK_SETTINGS, MODELS_TO_BENCHMARK, ModelConfig
from benchmarks.metrics import BenchmarkMetrics, TestResult, calculate_metrics
from benchmarks.report import (
    generate_comparison_report,
    generate_html_report,
    print_comparison_table,
)
from benchmarks.test_data import BENCHMARK_TEST_CASES
from infrastructure.http_client import AsyncHTTPClient
from infrastructure.llm_client import LLMError, OpenRouterClient
from infrastructure.parsers.llm_editorial_finder import LLMEditorialFinder


class BenchmarkRunner:
    """Runs benchmarks for editorial finder with different LLM models."""

    def __init__(self, api_key: str):
        """
        Initialize benchmark runner.

        Args:
            api_key: OpenRouter API key
        """
        self.api_key = api_key
        self.http_client = AsyncHTTPClient(timeout=30)
        self.html_cache: dict[str, str] = {}

    async def fetch_contest_page_html(self, contest_id: str) -> str:
        """
        Fetch contest page HTML with caching.

        Args:
            contest_id: Contest ID

        Returns:
            HTML content
        """
        if contest_id in self.html_cache:
            logger.debug(f"Using cached HTML for contest {contest_id}")
            return self.html_cache[contest_id]

        url = f"https://codeforces.com/contest/{contest_id}"
        logger.debug(f"Fetching HTML for contest {contest_id}")
        html = await self.http_client.get_text(url)

        if BENCHMARK_SETTINGS["save_html_cache"]:
            self.html_cache[contest_id] = html

        return html

    async def test_single_case_with_averaging(
        self, model_config: ModelConfig, contest_id: str, expected_editorial: str | None
    ) -> TestResult:
        """
        Test a single contest multiple times and average results.

        Args:
            model_config: Model configuration
            contest_id: Contest ID
            expected_editorial: Expected editorial URL or None

        Returns:
            Averaged test result
        """
        runs_per_test = BENCHMARK_SETTINGS["runs_per_test"]

        # Run test multiple times
        results = []
        for _ in range(runs_per_test):
            result = await self._test_single_run(
                model_config, contest_id, expected_editorial
            )
            results.append(result)

        # Average latency
        avg_latency = sum(r.latency_ms for r in results) / len(results)

        # Determine correctness by majority vote
        correct_count = sum(1 for r in results if r.is_correct)
        is_correct = correct_count > (runs_per_test / 2)

        # Find most common found_editorial result
        found_editorials_tuples = [tuple(r.found_editorial) for r in results]
        most_common = Counter(found_editorials_tuples).most_common(1)
        found_editorial = list(most_common[0][0]) if most_common else []

        # Collect errors if any
        errors = [r.error for r in results if r.error]
        error = errors[0] if errors else None

        return TestResult(
            contest_id=contest_id,
            expected_editorial=expected_editorial,
            found_editorial=found_editorial,
            is_correct=is_correct,
            latency_ms=avg_latency,
            error=error,
        )

    async def _test_single_run(
        self, model_config: ModelConfig, contest_id: str, expected_editorial: str | None
    ) -> TestResult:
        """
        Run a single test for a contest with a specific model.

        Args:
            model_config: Model configuration
            contest_id: Contest ID
            expected_editorial: Expected editorial URL or None

        Returns:
            Test result for this run
        """
        start_time = time.perf_counter()
        error = None
        found_editorial: list[str] = []

        try:
            # Initialize LLM client with specific model
            llm_client = OpenRouterClient(
                api_key=self.api_key,
                model=model_config["name"],
                timeout=model_config["timeout"],
            )

            # Create editorial finder
            finder = LLMEditorialFinder(llm_client=llm_client)

            # Fetch and parse HTML
            html = await self.fetch_contest_page_html(contest_id)
            soup = BeautifulSoup(html, "lxml")

            # Find editorial URLs
            found_editorial = await finder.find_editorial_url(soup, contest_id)

        except LLMError as e:
            error = f"LLM Error: {str(e)}"
            logger.warning(f"LLM error for contest {contest_id}: {e}")
        except Exception as e:
            error = f"Error: {str(e)}"
            logger.error(f"Unexpected error for contest {contest_id}: {e}")

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # Determine if result is correct
        is_correct = self._is_result_correct(expected_editorial, found_editorial)

        return TestResult(
            contest_id=contest_id,
            expected_editorial=expected_editorial,
            found_editorial=found_editorial,
            is_correct=is_correct,
            latency_ms=latency_ms,
            error=error,
        )

    def _is_result_correct(
        self, expected: str | None, found: list[str]
    ) -> bool:
        """
        Check if found editorial matches expected.

        Args:
            expected: Expected editorial URL or None
            found: Found editorial URLs

        Returns:
            True if correct
        """
        # Case 1: No editorial expected and none found
        if expected is None and len(found) == 0:
            return True

        # Case 2: Editorial expected but none found
        if expected is not None and len(found) == 0:
            return False

        # Case 3: No editorial expected but some found
        if expected is None and len(found) > 0:
            return False

        # Case 4: Editorial expected and found - check if it matches
        if expected is not None and len(found) > 0:
            # Normalize URLs for comparison (remove trailing slashes, etc.)
            expected_normalized = expected.rstrip("/").lower()
            for url in found:
                if url.rstrip("/").lower() == expected_normalized:
                    return True
            return False

        return False

    async def benchmark_model(self, model_config: ModelConfig) -> BenchmarkMetrics:
        """
        Run benchmark for a single model.

        Args:
            model_config: Model configuration

        Returns:
            Benchmark metrics
        """
        runs_per_test = BENCHMARK_SETTINGS["runs_per_test"]
        logger.info(
            f"Starting benchmark for {model_config['display_name']} "
            f"({runs_per_test} runs per test case)"
        )

        results: list[TestResult] = []

        # Process test cases in parallel batches
        parallel_requests = BENCHMARK_SETTINGS["parallel_requests"]
        for i in range(0, len(BENCHMARK_TEST_CASES), parallel_requests):
            batch = BENCHMARK_TEST_CASES[i : i + parallel_requests]

            tasks = [
                self.test_single_case_with_averaging(
                    model_config, tc["contest_id"], tc["expected_editorial"]
                )
                for tc in batch
            ]

            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Log progress
            logger.info(
                f"Processed {len(results)}/{len(BENCHMARK_TEST_CASES)} test cases"
            )

        # Calculate metrics
        metrics = calculate_metrics(
            model_config["name"], model_config["display_name"], results
        )

        return metrics

    async def run_all_benchmarks(self) -> list[BenchmarkMetrics]:
        """
        Run benchmarks for all configured models.

        Returns:
            List of metrics for each model
        """
        all_metrics: list[BenchmarkMetrics] = []

        for model_config in MODELS_TO_BENCHMARK:
            try:
                metrics = await self.benchmark_model(model_config)
                all_metrics.append(metrics)
            except Exception as e:
                logger.error(f"Failed to benchmark {model_config['display_name']}: {e}")

        return all_metrics


async def main():
    """Main entry point for benchmark script."""
    # Load environment variables from .env file
    load_dotenv()

    # Setup logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable not set")
        sys.exit(1)

    # Type checker doesn't understand sys.exit guarantees non-None
    assert api_key is not None

    # Parse command line arguments
    run_all = "--all" in sys.argv
    model_filter = None
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model_filter = sys.argv[idx + 1]

    # Initialize runner
    runner = BenchmarkRunner(api_key)

    # Determine which models to run
    models_to_run = MODELS_TO_BENCHMARK
    if model_filter and not run_all:
        models_to_run = [m for m in MODELS_TO_BENCHMARK if model_filter in m["name"]]
        if not models_to_run:
            logger.error(f"No models found matching: {model_filter}")
            sys.exit(1)

    logger.info(f"Running benchmarks for {len(models_to_run)} model(s)")
    logger.info(f"Test cases: {len(BENCHMARK_TEST_CASES)}")

    # Run benchmarks
    results_dir = Path(__file__).parent / "results"
    all_metrics: list[BenchmarkMetrics] = []

    for model_config in models_to_run:
        try:
            metrics = await runner.benchmark_model(model_config)
            all_metrics.append(metrics)

        except Exception as e:
            logger.error(f"Failed to benchmark {model_config['display_name']}: {e}")

    # Generate comparison reports if we have results
    if all_metrics:
        logger.info("Generating reports...")

        # Generate JSON comparison report
        json_report, _ = generate_comparison_report(all_metrics, results_dir)
        logger.info(f"Saved JSON report: {json_report}")

        # Generate HTML report
        html_report = generate_html_report(all_metrics, results_dir)
        logger.info(f"Saved HTML report: {html_report}")

        # Print comparison table
        if len(all_metrics) > 1:
            print_comparison_table(all_metrics)

        print(f"\n📄 View report in browser: file://{html_report.absolute()}")

    logger.info("Benchmark complete!")


if __name__ == "__main__":
    asyncio.run(main())
