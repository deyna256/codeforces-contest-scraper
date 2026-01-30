"""Base benchmark runner with common logic."""

import asyncio
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from loguru import logger

from benchmarks.config import BENCHMARK_SETTINGS, ModelConfig
from benchmarks.reporting.base_metrics import BenchmarkMetrics
from infrastructure.http_client import AsyncHTTPClient

TestCaseType = TypeVar("TestCaseType")
TestResultType = TypeVar("TestResultType")


class BaseBenchmarkRunner(ABC, Generic[TestCaseType, TestResultType]):
    """Base class for all benchmark types with common execution logic."""

    def __init__(
        self,
        api_key: str,
        test_cases: list[TestCaseType],
    ):
        """
        Initialize benchmark runner.

        Args:
            api_key: OpenRouter API key
            test_cases: List of test cases to run
        """
        self.api_key = api_key
        self.test_cases = test_cases
        self.http_client = AsyncHTTPClient(timeout=30)

    @abstractmethod
    async def test_single_case(
        self,
        model_config: ModelConfig,
        test_case: TestCaseType,
    ) -> TestResultType:
        """
        Test a single case - must be implemented by subclasses.

        Args:
            model_config: Model configuration
            test_case: Test case data

        Returns:
            Test result
        """
        pass

    @abstractmethod
    def calculate_metrics(
        self,
        model_name: str,
        display_name: str,
        results: list[TestResultType],
    ) -> BenchmarkMetrics:
        """
        Calculate metrics from test results - must be implemented by subclasses.

        Args:
            model_name: Model name
            display_name: Display name
            results: List of test results

        Returns:
            Benchmark metrics
        """
        pass

    async def benchmark_model(self, model_config: ModelConfig) -> BenchmarkMetrics:
        """
        Run benchmark for a single model with parallel processing.

        Args:
            model_config: Model configuration

        Returns:
            Benchmark metrics
        """
        logger.info(f"Starting benchmark for {model_config['display_name']}")

        results: list[TestResultType] = []

        # Process test cases in parallel batches
        parallel_requests = BENCHMARK_SETTINGS["parallel_requests"]
        for i in range(0, len(self.test_cases), parallel_requests):
            batch = self.test_cases[i : i + parallel_requests]

            tasks = [self.test_single_case(model_config, tc) for tc in batch]

            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Log progress
            logger.info(f"Processed {len(results)}/{len(self.test_cases)} test cases")

        # Calculate metrics
        metrics = self.calculate_metrics(
            model_config["name"],
            model_config["display_name"],
            results,
        )

        return metrics

    async def run_all_benchmarks(
        self,
        models_to_run: list[ModelConfig],
    ) -> list[BenchmarkMetrics]:
        """
        Run benchmarks for all configured models.

        Args:
            models_to_run: List of model configurations to benchmark

        Returns:
            List of metrics for each model
        """
        all_metrics: list[BenchmarkMetrics] = []

        for model_config in models_to_run:
            try:
                metrics = await self.benchmark_model(model_config)
                all_metrics.append(metrics)
            except Exception as e:
                logger.error(f"Failed to benchmark {model_config['display_name']}: {e}")

        return all_metrics
