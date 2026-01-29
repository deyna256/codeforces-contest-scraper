"""LLM client for OpenRouter API."""

from dataclasses import dataclass
from typing import Optional

import httpx
from loguru import logger


class LLMError(Exception):
    """LLM API error."""

    pass


@dataclass
class TokenUsage:
    """Token usage information from LLM response."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class LLMResponse:
    """LLM response with content and token usage."""

    content: str
    usage: Optional[TokenUsage] = None


class OpenRouterClient:
    """Client for OpenRouter API to interact with various LLM models."""

    def __init__(
        self,
        api_key: str,
        model: str = "anthropic/claude-3.5-haiku",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: float = 30.0,
    ):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key
            model: Model identifier (e.g., "anthropic/claude-3.5-haiku")
            base_url: OpenRouter API base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate completion using OpenRouter API.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Temperature for generation (0.0 = deterministic)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text completion (for backward compatibility)

        Raises:
            LLMError: If API request fails
        """
        response = await self.complete_with_usage(prompt, system_prompt, temperature, max_tokens)
        return response.content

    async def complete_with_usage(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> LLMResponse:
        """
        Generate completion using OpenRouter API with token usage information.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Temperature for generation (0.0 = deterministic)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with content and token usage

        Raises:
            LLMError: If API request fails
        """
        url = f"{self.base_url}/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/codeforces-editorial-finder",  # Optional
            "X-Title": "Codeforces Editorial Finder",  # Optional
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    error_text = response.text
                    raise LLMError(
                        f"OpenRouter API returned status {response.status_code}: {error_text}"
                    )

                data = response.json()

                # Extract completion from response
                if "choices" not in data or len(data["choices"]) == 0:
                    raise LLMError("No choices in OpenRouter API response")

                content = data["choices"][0].get("message", {}).get("content", "")
                if not content:
                    raise LLMError("Empty content in OpenRouter API response")

                # Extract token usage information if available
                usage_data = data.get("usage", {})
                usage = None
                if usage_data:
                    usage = TokenUsage(
                        prompt_tokens=usage_data.get("prompt_tokens", 0),
                        completion_tokens=usage_data.get("completion_tokens", 0),
                        total_tokens=usage_data.get("total_tokens", 0),
                    )
                else:
                    # Debug: log when usage is missing
                    logger.warning(
                        f"OpenRouter API response for model {self.model} is missing 'usage' field. "
                        f"Response keys: {list(data.keys())}"
                    )

                return LLMResponse(content=content.strip(), usage=usage)

        except httpx.TimeoutException as e:
            raise LLMError(f"OpenRouter API timeout: {e}")
        except httpx.RequestError as e:
            raise LLMError(f"OpenRouter API request error: {e}")
        except Exception as e:
            raise LLMError(f"Unexpected error: {e}")
