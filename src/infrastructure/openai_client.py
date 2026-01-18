"""Async wrapper around the OpenAI API used for editorial extraction."""

from openai import AsyncOpenAI
import openai
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings
from domain.exceptions import OpenAIAPIError
from domain.models import ProblemIdentifier


class AsyncOpenAIClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize the client, falling back to configured API key and model.
        Raises OpenAIAPIError if no API key is available.
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model

        if not self.api_key:
            raise OpenAIAPIError("OpenAI API key not configured")

        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.debug(f"Initialized async OpenAI client with model: {self.model}")

    async def close(self) -> None:
        await self.client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        reraise=True,
    )
    async def send_message(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float | None = None,
        system: str | None = None,
    ) -> str:
        """
        Send a chat completion request to OpenAI with automatic retries and
        convert API failures into OpenAIAPIError.
        """
        logger.debug(f"Sending message to OpenAI (model: {self.model})")
        logger.debug(f"Prompt length: {len(prompt)} chars")

        try:
            messages = []

            if system:
                messages.append({"role": "system", "content": system})

            messages.append({"role": "user", "content": prompt})

            params = {
                "model": self.model,
                "messages": messages,
                "max_completion_tokens": max_tokens,
            }

            if temperature is not None:
                params["temperature"] = temperature

            response = await self.client.chat.completions.create(**params)

            response_text = response.choices[0].message.content
            if response_text is None:
                logger.warning(
                    "Response content is None - reasoning model may need more max_tokens"
                )
                response_text = ""

            logger.debug(f"Received response ({len(response_text)} chars)")
            logger.debug(f"Usage: {response.usage}")

            return response_text

        except openai.RateLimitError:
            logger.warning("Rate limit hit, retrying...")
            raise  # Let tenacity retry

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIAPIError(f"OpenAI API error: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI API: {e}")
            raise OpenAIAPIError(f"Failed to call OpenAI API: {e}") from e

    async def find_editorial_link(
        self, contest_html: str, problem_id: str
    ) -> str | None:
        """
        Use OpenAI to extract an editorial URL for a given problem from contest page HTML.
        Returns None if no valid link is found.
        """
        from domain.openai.prompts import get_find_editorial_prompt

        logger.info(f"Using OpenAI to find editorial link for problem {problem_id}")

        prompt = get_find_editorial_prompt(contest_html, problem_id)

        try:
            response = await self.send_message(
                prompt=prompt,
                max_tokens=2000,
                system="You are a helpful assistant that extracts URLs from HTML content. "
                "Return only the URL, nothing else.",
            )

            response = response.strip()

            # Check if found
            if response == "NOT_FOUND" or not response.startswith("http"):
                logger.warning("OpenAI could not find editorial link")
                return None

            logger.info(f"Found editorial link: {response}")
            return response

        except OpenAIAPIError:
            raise
        except Exception as e:
            logger.error(f"Error in find_editorial_link: {e}")
            raise OpenAIAPIError(f"Failed to find editorial link: {e}") from e

    async def extract_solution(
        self,
        tutorial_content: str,
        problem_id: str,
        problem_title: str = "",
    ) -> dict:
        """
        Use OpenAI to extract and structure a problem solution from tutorial content.
        """
        from domain.openai.prompts import get_extract_solution_prompt

        logger.info(f"Using OpenAI to extract solution for problem {problem_id}")

        # Create a minimal identifier for the prompt
        contest_id = "unknown"
        identifier = ProblemIdentifier(contest_id=contest_id, problem=problem_id)

        prompt = get_extract_solution_prompt(
            tutorial_content, identifier, problem_title
        )

        try:
            response = await self.send_message(
                prompt=prompt,
                max_tokens=8000,
                system="You are an expert at analyzing competitive programming editorials. "
                "Extract and structure the solution information clearly and accurately.",
            )

            logger.info(f"Successfully extracted solution ({len(response)} chars)")

            return {
                "raw_response": response,
                "problem": problem_id,
            }

        except OpenAIAPIError:
            raise
        except Exception as e:
            logger.error(f"Error in extract_solution: {e}")
            raise OpenAIAPIError(f"Failed to extract solution: {e}") from e

    async def validate_editorial_content(
        self,
        content: str,
        problem_id: str,
    ) -> bool:
        """
        Use OpenAI to check whether content contains an editorial for the given problem.
        Returns True on API errors to avoid false negatives.
        """
        from domain.openai.prompts import get_validate_editorial_prompt

        logger.debug(f"Validating editorial content for problem {problem_id}")

        prompt = get_validate_editorial_prompt(content, problem_id)

        try:
            response = await self.send_message(
                prompt=prompt,
                max_tokens=1000,
            )

            response = response.strip().upper()
            is_valid = response in ["YES", "PARTIAL"]

            logger.debug(f"Validation result: {response} (valid={is_valid})")
            return is_valid

        except Exception as e:
            logger.warning(f"Error validating content: {e}")
            # If validation fails, assume content might be valid
            return True
