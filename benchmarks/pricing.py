"""Utilities for fetching and managing model pricing from OpenRouter."""

import json
from dataclasses import dataclass
from typing import Optional, Dict
from pathlib import Path

import httpx


@dataclass
class ModelPricing:
    """Pricing information for a model.

    Note: Prices are per token (e.g., $0.0000008 per token),
    not per million tokens. To display as "$/1M tokens", multiply by 1,000,000.
    """

    prompt_price: float  # Price per token for input (e.g., 0.0000008 = $0.80/1M)
    completion_price: float  # Price per token for output (e.g., 0.000004 = $4.00/1M)
    currency: str = "USD"  # Assuming USD as most common


class PricingManager:
    """Manages fetching and caching of model pricing data."""

    def __init__(self, cache_file: Path | None = None):
        """
        Initialize pricing manager.

        Args:
            cache_file: Path to cache pricing data. If None, uses default location.
        """
        self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        self.cache_file = (
            cache_file or Path(__file__).parent / "results" / "openrouter_pricing_cache.json"
        )
        self._pricing_cache: Dict[str, ModelPricing] = {}
        self._cache_loaded = False

    async def load_or_fetch_pricing(self, force_refresh: bool = False) -> Dict[str, ModelPricing]:
        """
        Load pricing data from cache or fetch from OpenRouter API.

        Args:
            force_refresh: If True, ignore cache and fetch fresh data

        Returns:
            Dictionary mapping model names to pricing info
        """
        if not force_refresh and self._load_from_cache():
            return self._pricing_cache

        # Fetch fresh data from OpenRouter
        await self._fetch_from_api()
        self._save_to_cache()

        return self._pricing_cache

    def get_pricing_for_model(self, model_name: str) -> Optional[ModelPricing]:
        """
        Get pricing information for a specific model.

        Args:
            model_name: Model identifier (e.g., 'anthropic/claude-3.5-haiku')

        Returns:
            ModelPricing if available, None otherwise
        """
        return self._pricing_cache.get(model_name)

    def _load_from_cache(self) -> bool:
        """Load pricing data from cache file."""
        if self._cache_loaded:
            return True

        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r") as f:
                    data = json.load(f)

                self._pricing_cache = {}
                for model_name, pricing_data in data.items():
                    self._pricing_cache[model_name] = ModelPricing(
                        prompt_price=float(pricing_data["prompt_price"]),
                        completion_price=float(pricing_data["completion_price"]),
                        currency=pricing_data.get("currency", "USD"),
                    )

                self._cache_loaded = True
                return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Failed to load pricing cache: {e}")

        return False

    async def _fetch_from_api(self) -> None:
        """Fetch pricing data from OpenRouter API."""
        url = "https://openrouter.ai/api/v1/models"
        response = await self.http_client.get(url)
        response.raise_for_status()
        response_data = response.json()

        self._pricing_cache = {}
        for model in response_data.get("data", []):
            model_id = model.get("id")
            pricing_data = model.get("pricing", {})

            if model_id and pricing_data:
                try:
                    # Convert string prices to float (they're in scientific notation sometimes)
                    prompt_price = float(pricing_data.get("prompt", "0"))
                    completion_price = float(pricing_data.get("completion", "0"))

                    self._pricing_cache[model_id] = ModelPricing(
                        prompt_price=prompt_price,
                        completion_price=completion_price,
                        currency="USD",  # OpenRouter uses USD
                    )
                except (ValueError, TypeError) as e:
                    print(f"Failed to parse pricing for {model_id}: {e}")
                    continue

    def _save_to_cache(self) -> None:
        """Save current pricing data to cache file."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            cache_data = {}
            for model_name, pricing in self._pricing_cache.items():
                cache_data[model_name] = {
                    "prompt_price": pricing.prompt_price,
                    "completion_price": pricing.completion_price,
                    "currency": pricing.currency,
                }

            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            print(f"Failed to save pricing cache: {e}")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.http_client.aclose()
