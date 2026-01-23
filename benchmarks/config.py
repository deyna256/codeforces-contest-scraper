"""Benchmark configuration for LLM models."""

from typing import TypedDict


class ModelConfig(TypedDict):
    """Configuration for a single model."""

    name: str
    display_name: str
    timeout: float
    max_tokens: int


# Models to benchmark
# Add or remove models as needed
MODELS_TO_BENCHMARK: list[ModelConfig] = [
    {
        "name": "anthropic/claude-3.5-haiku",
        "display_name": "Claude 3.5 Haiku",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "deepseek/deepseek-v3.2",
        "display_name": "DeepSeek v3.2",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "openai/gpt-oss-120b",
        "display_name": "OpenAI GPT OSS",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "x-ai/grok-4.1-fast",
        "display_name": "xAI: Grok 4.1 Fast",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "google/gemini-2.0-flash-001",
        "display_name": "Google Gemini 2.0 Flash",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "meta-llama/llama-3.1-8b-instruct",
        "display_name": "Meta: Llama 3.1 8B Instruct",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "google/gemini-2.5-flash-lite",
        "display_name": "Google: Gemini 2.5 Flash Lite",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "google/gemini-3-flash-preview",
        "display_name": "Gemini 3 Flash-Preview",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "google/gemini-2.5-flash",
        "display_name": "Gemini 2.5 Flash",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "openai/gpt-4o-mini",
        "display_name": "OpenAI GPT 4o-mini",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "openai/gpt-oss-20b:free",
        "display_name": "OpenAI GPT OSS 20b",
        "timeout": 30.0,
        "max_tokens": 100,
    },
    {
        "name": "meta-llama/llama-3.3-70b-instruct:free",
        "display_name": "Meta LLAMA-3.3 70B",
        "timeout": 30.0,
        "max_tokens": 100,
    },

]

# Benchmark settings
BENCHMARK_SETTINGS = {
    "parallel_requests": 5,  # Number of contests to process in parallel
    "runs_per_test": 1,  # Number of runs per test case to average results
    "retry_on_failure": True,
    "retry_attempts": 2,
    "save_html_cache": True,  # Cache HTML to avoid re-fetching
}
