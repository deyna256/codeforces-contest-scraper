"""Editorial finder benchmark runner."""

import asyncio
import time
from collections import Counter

from bs4 import BeautifulSoup
from loguru import logger

from benchmarks.config import BENCHMARK_SETTINGS, ModelConfig
from benchmarks.core.base_runner import BaseBenchmarkRunner
from benchmarks.core.tracked_llm_client import TrackedLLMClient
from benchmarks.editorial_finder.metrics import FinderTestResult, calculate_finder_metrics
from benchmarks.editorial_finder.test_data import FINDER_TEST_CASES, TestCase
from benchmarks.reporting.base_metrics import BenchmarkMetrics
from infrastructure.llm_client import LLMError
from infrastructure.parsers.llm_editorial_finder import LLMEditorialFinder


class EditorialFinderRunner(BaseBenchmarkRunner[TestCase, FinderTestResult]):
    """Benchmark runner for editorial finder with different LLM models."""

    def __init__(self, api_key: str):
        """
        Initialize editorial finder benchmark runner.

        Args:
            api_key: OpenRouter API key
        """
        super().__init__(api_key=api_key, test_cases=FINDER_TEST_CASES)
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

    async def test_single_case(
        self,
        model_config: ModelConfig,
        test_case: TestCase,
    ) -> FinderTestResult:
        """
        Test a single case with averaging over multiple runs.

        Args:
            model_config: Model configuration
            test_case: Test case data

        Returns:
            Averaged test result
        """
        contest_id = test_case["contest_id"]
        expected_editorial = test_case["expected_editorial"]
        runs_per_test = BENCHMARK_SETTINGS["runs_per_test"]

        # Run test multiple times
        results = []
        for _ in range(runs_per_test):
            result = await self._test_single_run(model_config, contest_id, expected_editorial)
            results.append(result)

        # Average latency
        avg_latency = sum(r.latency_ms for r in results) / len(results)

        # Average token usage
        avg_prompt_tokens = sum(r.prompt_tokens for r in results) / len(results)
        avg_completion_tokens = sum(r.completion_tokens for r in results) / len(results)
        avg_total_tokens = sum(r.total_tokens for r in results) / len(results)

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

        return FinderTestResult(
            contest_id=contest_id,
            expected_editorial=expected_editorial,
            found_editorial=found_editorial,
            is_correct=is_correct,
            latency_ms=avg_latency,
            error=error,
            prompt_tokens=int(avg_prompt_tokens),
            completion_tokens=int(avg_completion_tokens),
            total_tokens=int(avg_total_tokens),
        )

    async def _test_single_run(
        self,
        model_config: ModelConfig,
        contest_id: str,
        expected_editorial: list[str],
    ) -> FinderTestResult:
        """
        Run a single test for a contest with a specific model.

        Args:
            model_config: Model configuration
            contest_id: Contest ID
            expected_editorial: Expected editorial URLs (empty list if no editorial exists)

        Returns:
            Test result for this run
        """
        # Add delay for free models to avoid rate limiting (before timing starts)
        if ":free" in model_config["name"]:
            logger.debug(f"Adding 20-second delay for free model: {model_config['display_name']}")
            await asyncio.sleep(20)

        start_time = time.perf_counter()
        error = None
        found_editorial: list[str] = []
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        try:
            # Initialize tracked LLM client with specific model
            llm_client = TrackedLLMClient(
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

            # Get token usage from last LLM call
            usage = llm_client.get_last_usage()
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens

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

        return FinderTestResult(
            contest_id=contest_id,
            expected_editorial=expected_editorial,
            found_editorial=found_editorial,
            is_correct=is_correct,
            latency_ms=latency_ms,
            error=error,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    def _is_result_correct(self, expected: list[str], found: list[str]) -> bool:
        """
        Check if found editorial matches expected.

        Args:
            expected: Expected editorial URLs (empty list if no editorial exists)
            found: Found editorial URLs

        Returns:
            True if correct
        """
        # Case 1: No editorial expected and none found
        if len(expected) == 0 and len(found) == 0:
            return True

        # Case 2: Editorial expected but none found
        if len(expected) > 0 and len(found) == 0:
            return False

        # Case 3: No editorial expected but some found
        if len(expected) == 0 and len(found) > 0:
            return False

        # Case 4: Editorial expected and found - check if there's at least one match
        if len(expected) > 0 and len(found) > 0:
            # Normalize URLs for comparison (remove trailing slashes, etc.)
            expected_normalized = {url.rstrip("/").lower() for url in expected}
            found_normalized = {url.rstrip("/").lower() for url in found}

            # Check if there's any intersection
            return len(expected_normalized & found_normalized) > 0

        return False

    def calculate_metrics(
        self,
        model_name: str,
        display_name: str,
        results: list[FinderTestResult],
    ) -> BenchmarkMetrics:
        """
        Calculate metrics from editorial finder test results.

        Args:
            model_name: Model name
            display_name: Display name
            results: List of test results

        Returns:
            Benchmark metrics
        """
        return calculate_finder_metrics(model_name, display_name, results)
