"""LLM client for OpenRouter API."""

from typing import Optional

import httpx
from loguru import logger


class LLMError(Exception):
    """LLM API error."""

    pass


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
            Generated text completion

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

        logger.debug(f"Calling OpenRouter API with model {self.model}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(
                        f"OpenRouter API error: status={response.status_code}, response={error_text}"
                    )
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

                logger.debug(f"OpenRouter API response: {content[:100]}...")
                return content.strip()

        except httpx.TimeoutException as e:
            logger.error(f"OpenRouter API timeout: {e}")
            raise LLMError(f"OpenRouter API timeout: {e}")
        except httpx.RequestError as e:
            logger.error(f"OpenRouter API request error: {e}")
            raise LLMError(f"OpenRouter API request error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling OpenRouter API: {e}")
            raise LLMError(f"Unexpected error: {e}")
