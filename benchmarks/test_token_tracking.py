#!/usr/bin/env python3
"""Quick test script to verify token tracking and cost calculation."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# ruff: noqa: E402
from dotenv import load_dotenv
from loguru import logger

from infrastructure.llm_client import OpenRouterClient
from benchmarks.pricing import PricingManager

# Setup logging
logger.remove()
logger.add(sys.stderr, level="DEBUG")


async def test_token_tracking():
    """Test token tracking and cost calculation."""
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        return

    # Test 1: Check if LLM client returns token usage
    logger.info("=" * 60)
    logger.info("TEST 1: Token usage from API")
    logger.info("=" * 60)

    client = OpenRouterClient(
        api_key=api_key, model="anthropic/claude-3.5-haiku", timeout=30.0
    )

    response = await client.complete_with_usage(
        prompt="Say hello in exactly 3 words.", temperature=0.0, max_tokens=10
    )

    logger.info(f"Response content: {response.content}")
    if response.usage:
        logger.info("✅ Token usage received:")
        logger.info(f"   Prompt tokens: {response.usage.prompt_tokens}")
        logger.info(f"   Completion tokens: {response.usage.completion_tokens}")
        logger.info(f"   Total tokens: {response.usage.total_tokens}")
    else:
        logger.error("❌ No token usage in response!")

    # Test 2: Check if pricing manager loads data
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST 2: Pricing data")
    logger.info("=" * 60)

    pricing_manager = PricingManager()
    await pricing_manager.load_or_fetch_pricing(force_refresh=False)

    model_name = "anthropic/claude-3.5-haiku"
    pricing = pricing_manager.get_pricing_for_model(model_name)

    if pricing:
        logger.info(f"✅ Pricing found for {model_name}:")
        logger.info(f"   Prompt price: ${pricing.prompt_price}/1M tokens")
        logger.info(f"   Completion price: ${pricing.completion_price}/1M tokens")
        logger.info(f"   Avg price: ${pricing.avg_price_per_token:.10f}/token")
    else:
        logger.error(f"❌ No pricing data for {model_name}")

    # Test 3: Calculate cost
    if response.usage and pricing:
        logger.info("")
        logger.info("=" * 60)
        logger.info("TEST 3: Cost calculation")
        logger.info("=" * 60)

        # OpenRouter pricing is per token, not per million
        prompt_cost = response.usage.prompt_tokens * pricing.prompt_price
        completion_cost = response.usage.completion_tokens * pricing.completion_price
        total_cost = prompt_cost + completion_cost

        # Convert to per-million format for display
        prompt_price_per_m = pricing.prompt_price * 1_000_000
        completion_price_per_m = pricing.completion_price * 1_000_000

        logger.info("✅ Cost calculation:")
        logger.info(
            f"   Prompt: {response.usage.prompt_tokens} tokens × ${prompt_price_per_m:.2f}/1M = ${prompt_cost:.8f}"
        )
        logger.info(
            f"   Completion: {response.usage.completion_tokens} tokens × ${completion_price_per_m:.2f}/1M = ${completion_cost:.8f}"
        )
        logger.info(f"   Total: ${total_cost:.8f}")

        if total_cost > 0:
            logger.info("✅ Cost is greater than zero - working correctly!")
        else:
            logger.warning(
                "⚠️  Cost is zero - either tokens are zero or pricing is zero"
            )

    await pricing_manager.close()

    logger.info("")
    logger.info("=" * 60)
    logger.info("Test complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_token_tracking())
