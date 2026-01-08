"""OpenAI API client wrapper."""

from typing import Optional

import openai
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from codeforces_editorial.config import get_settings
from codeforces_editorial.utils.exceptions import OpenAIAPIError


class OpenAIClient:
    """Wrapper for OpenAI API with error handling and retry logic."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (uses settings if None)
            model: Model to use (uses settings if None)
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model

        if not self.api_key:
            raise OpenAIAPIError("OpenAI API key not configured")

        openai.api_key = self.api_key
        logger.debug(f"Initialized OpenAI client with model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        reraise=True,
    )
    def send_message(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        system: Optional[str] = None,
    ) -> str:
        """
        Send message to OpenAI and get response.

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            system: Optional system prompt

        Returns:
            OpenAI's response text

        Raises:
            OpenAIAPIError: If API call fails
        """
        logger.debug(f"Sending message to OpenAI (model: {self.model})")
        logger.debug(f"Prompt length: {len(prompt)} chars")

        try:
            messages = []

            if system:
                messages.append({"role": "system", "content": system})

            messages.append({"role": "user", "content": prompt})

            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            response_text = response.choices[0].message.content
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

    def find_editorial_link(self, contest_html: str, problem_id: str) -> Optional[str]:
        """
        Use OpenAI to find editorial link in contest page HTML.

        Args:
            contest_html: HTML content of contest page
            problem_id: Problem ID

        Returns:
            Editorial URL if found, None otherwise

        Raises:
            OpenAIAPIError: If API call fails
        """
        from codeforces_editorial.openai.prompts import get_find_editorial_prompt

        logger.info(f"Using OpenAI to find editorial link for problem {problem_id}")

        prompt = get_find_editorial_prompt(contest_html, problem_id)

        try:
            response = self.send_message(
                prompt=prompt,
                max_tokens=500,
                temperature=0.0,
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

    def extract_solution(
        self,
        tutorial_content: str,
        problem_id: str,
        problem_title: str = "",
    ) -> dict:
        """
        Use OpenAI to extract solution from tutorial content.

        Args:
            tutorial_content: Tutorial content (HTML or text)
            problem_id: Problem ID
            problem_title: Optional problem title

        Returns:
            Dictionary with extracted solution components

        Raises:
            OpenAIAPIError: If API call fails
        """
        from codeforces_editorial.openai.prompts import get_extract_solution_prompt
        from codeforces_editorial.models import ProblemIdentifier

        logger.info(f"Using OpenAI to extract solution for problem {problem_id}")

        # Create a minimal identifier for the prompt
        contest_id = "unknown"
        pid = problem_id
        identifier = ProblemIdentifier(contest_id=contest_id, problem_id=pid)

        prompt = get_extract_solution_prompt(tutorial_content, identifier, problem_title)

        try:
            response = self.send_message(
                prompt=prompt,
                max_tokens=8000,
                temperature=0.0,
                system="You are an expert at analyzing competitive programming editorials. "
                "Extract and structure the solution information clearly and accurately.",
            )

            logger.info(f"Successfully extracted solution ({len(response)} chars)")

            return {
                "raw_response": response,
                "problem_id": problem_id,
            }

        except OpenAIAPIError:
            raise
        except Exception as e:
            logger.error(f"Error in extract_solution: {e}")
            raise OpenAIAPIError(f"Failed to extract solution: {e}") from e

    def validate_editorial_content(
        self,
        content: str,
        problem_id: str,
    ) -> bool:
        """
        Validate if content contains editorial for specific problem.

        Args:
            content: Content to validate
            problem_id: Problem ID

        Returns:
            True if content contains editorial for the problem

        Raises:
            OpenAIAPIError: If API call fails
        """
        from codeforces_editorial.openai.prompts import get_validate_editorial_prompt

        logger.debug(f"Validating editorial content for problem {problem_id}")

        prompt = get_validate_editorial_prompt(content, problem_id)

        try:
            response = self.send_message(
                prompt=prompt,
                max_tokens=10,
                temperature=0.0,
            )

            response = response.strip().upper()
            is_valid = response in ["YES", "PARTIAL"]

            logger.debug(f"Validation result: {response} (valid={is_valid})")
            return is_valid

        except Exception as e:
            logger.warning(f"Error validating content: {e}")
            # If validation fails, assume content might be valid
            return True


def create_openai_client() -> OpenAIClient:
    """Create and return a new OpenAI client instance."""
    return OpenAIClient()
