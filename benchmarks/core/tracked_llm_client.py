"""Tracked LLM client for benchmark usage measurement."""

from typing import Optional

from loguru import logger

from infrastructure.llm_client import OpenRouterClient, TokenUsage


class TrackedLLMClient(OpenRouterClient):
    """LLM client wrapper that tracks token usage."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_usage: Optional[TokenUsage] = None

    async def complete(self, *args, **kwargs) -> str:
        """Override complete to track token usage."""
        response = await self.complete_with_usage(*args, **kwargs)
        self.last_usage = response.usage

        # Debug logging
        if response.usage:
            logger.debug(
                f"Token usage for {self.model}: "
                f"prompt={response.usage.prompt_tokens}, "
                f"completion={response.usage.completion_tokens}, "
                f"total={response.usage.total_tokens}"
            )
        else:
            logger.warning(f"No token usage data returned from {self.model}")

        return response.content

    def get_last_usage(self) -> TokenUsage:
        """Get token usage from last request."""
        if self.last_usage is None:
            logger.warning("get_last_usage called but last_usage is None - returning zeros")
            return TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        return self.last_usage
