"""Main benchmark runner for testing LLM models."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add project root and src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# ruff: noqa: E402
from dotenv import load_dotenv
from loguru import logger

from benchmarks.config import MODELS_TO_BENCHMARK
from benchmarks.core.benchmark_types import BenchmarkType
from benchmarks.editorial_finder.runner import EditorialFinderRunner
from benchmarks.editorial_segmentation.runner import SegmentationRunner
from benchmarks.pricing import PricingManager
from benchmarks.reporting import (
    generate_comparison_report,
    generate_html_report,
    print_comparison_table,
)


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
    parser = argparse.ArgumentParser(description="Run LLM benchmarks")
    parser.add_argument("--all", action="store_true", help="Run all models")
    parser.add_argument("--model", type=str, help="Filter models by name")
    parser.add_argument(
        "--type",
        type=str,
        choices=["finder", "segmentation", "all"],
        default="all",
        help="Benchmark type to run (default: all)",
    )

    args = parser.parse_args()

    # Determine benchmark types to run
    benchmark_types = []
    if args.type in ["finder", "all"]:
        benchmark_types.append(BenchmarkType.EDITORIAL_FINDER)
    if args.type in ["segmentation", "all"]:
        benchmark_types.append(BenchmarkType.EDITORIAL_SEGMENTATION)

    # Determine which models to run
    models_to_run = MODELS_TO_BENCHMARK
    if args.model and not args.all:
        models_to_run = [m for m in MODELS_TO_BENCHMARK if args.model in m["name"]]
        if not models_to_run:
            logger.error(f"No models found matching: {args.model}")
            sys.exit(1)

    # Initialize pricing manager to fetch model pricing data
    pricing_manager = PricingManager()

    try:
        logger.info("Fetching pricing data from OpenRouter...")
        await pricing_manager.load_or_fetch_pricing(force_refresh=False)
    except Exception as e:
        logger.warning(
            f"Failed to fetch pricing data: {e}. Benchmarks will run without pricing info."
        )

    # Run benchmarks for each type
    for benchmark_type in benchmark_types:
        logger.info("=" * 80)
        logger.info(f"Running {benchmark_type.value} benchmark")
        logger.info("=" * 80)

        # Create appropriate runner
        if benchmark_type == BenchmarkType.EDITORIAL_FINDER:
            runner = EditorialFinderRunner(api_key)
            results_dir = Path(__file__).parent / "results" / "editorial_finder"
        else:
            runner = SegmentationRunner(api_key)
            results_dir = Path(__file__).parent / "results" / "editorial_segmentation"

        logger.info(f"Running benchmarks for {len(models_to_run)} model(s)")
        logger.info(f"Test cases: {len(runner.test_cases)}")

        # Run benchmarks for all models
        all_metrics = []
        for model_config in models_to_run:
            try:
                metrics = await runner.benchmark_model(model_config)

                # Attach pricing information if available
                pricing = pricing_manager.get_pricing_for_model(model_config["name"])
                metrics.pricing = pricing

                # Calculate estimated cost if pricing is available
                if pricing:
                    prompt_cost = metrics.total_prompt_tokens * pricing.prompt_price
                    completion_cost = metrics.total_completion_tokens * pricing.completion_price
                    metrics.estimated_cost = prompt_cost + completion_cost

                    # Calculate cost per correct prediction
                    correct_predictions = sum(
                        1 for r in metrics.test_results if r.is_correct and r.error is None
                    )
                    if correct_predictions > 0:
                        metrics.cost_per_correct_prediction = (
                            metrics.estimated_cost / correct_predictions
                        )

                    # Log with price converted to per-million format for readability
                    prompt_price_per_m = pricing.prompt_price * 1_000_000
                    completion_price_per_m = pricing.completion_price * 1_000_000
                    logger.info(
                        f"Cost calculation for {model_config['name']}: "
                        f"{metrics.total_prompt_tokens} prompt tokens × ${prompt_price_per_m:.2f}/1M = ${prompt_cost:.6f}, "
                        f"{metrics.total_completion_tokens} completion tokens × ${completion_price_per_m:.2f}/1M = ${completion_cost:.6f}, "
                        f"Total: ${metrics.estimated_cost:.6f}"
                    )
                else:
                    logger.warning(
                        f"No pricing data available for {model_config['name']}. "
                        f"Cost will be shown as N/A. Tokens: {metrics.total_tokens}"
                    )

                all_metrics.append(metrics)

            except Exception as e:
                logger.error(f"Failed to benchmark {model_config['display_name']}: {e}")

        # Generate comparison reports if we have results
        if all_metrics:
            logger.info("Generating reports...")

            # Generate JSON comparison report
            json_report, _ = generate_comparison_report(all_metrics, results_dir, benchmark_type)
            logger.info(f"Saved JSON report: {json_report}")

            # Generate HTML report
            html_report_path = results_dir / f"benchmark_report_{all_metrics[0].timestamp}.html"
            _, report_data = generate_comparison_report(all_metrics, results_dir, benchmark_type)
            html_report = generate_html_report(report_data, html_report_path)
            logger.info(f"Saved HTML report: {html_report}")

            # Print comparison table
            if len(all_metrics) > 1:
                print_comparison_table(all_metrics)

            print(f"\n📄 View report in browser: file://{html_report.absolute()}\n")

    # Clean up pricing manager
    await pricing_manager.close()

    logger.info("Benchmark complete!")


if __name__ == "__main__":
    asyncio.run(main())
