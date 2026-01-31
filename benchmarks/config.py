"""Benchmark configuration for LLM models."""

from typing import TypedDict


class ModelConfig(TypedDict):
    """Configuration for a single model."""

    name: str
    display_name: str
    timeout: float  # Timeout for finder tasks
    timeout_segmentation: float  # Longer timeout for segmentation tasks
    max_tokens: int
    max_tokens_segmentation: int  # Higher token limit for segmentation tasks


# Models to benchmark
# Add or remove models as needed
# TOP-6 models selected for faster benchmarking
MODELS_TO_BENCHMARK: list[ModelConfig] = [
    {
        "name": "anthropic/claude-3.5-haiku",
        "display_name": "Claude 3.5 Haiku",
        "timeout": 15.0,
        "timeout_segmentation": 60.0,
        "max_tokens": 100,
        "max_tokens_segmentation": 8000,
    },
    {
        "name": "deepseek/deepseek-v3.2",
        "display_name": "DeepSeek v3.2",
        "timeout": 15.0,
        "timeout_segmentation": 60.0,
        "max_tokens": 100,
        "max_tokens_segmentation": 6000,
    },
    {
        "name": "google/gemini-2.5-flash",
        "display_name": "Gemini 2.5 Flash",
        "timeout": 15.0,
        "timeout_segmentation": 60.0,
        "max_tokens": 100,
        "max_tokens_segmentation": 8000,
    },
    {
        "name": "openai/gpt-4o-mini",
        "display_name": "OpenAI GPT 4o-mini",
        "timeout": 15.0,
        "timeout_segmentation": 60.0,
        "max_tokens": 100,
        "max_tokens_segmentation": 6000,
    },
    {
        "name": "qwen/qwen-2.5-72b-instruct",
        "display_name": "Qwen 2.5 72B Instruct",
        "timeout": 15.0,
        "timeout_segmentation": 60.0,
        "max_tokens": 100,
        "max_tokens_segmentation": 6000,
    },
    {
        "name": "meta-llama/llama-3.1-8b-instruct",
        "display_name": "Meta: Llama 3.1 8B Instruct",
        "timeout": 20.0,
        "timeout_segmentation": 60.0,
        "max_tokens": 100,
        "max_tokens_segmentation": 4000,
    },
]

# Full list of available models (commented out for faster benchmarking)
# Uncomment and add to MODELS_TO_BENCHMARK as needed:
# {
#     "name": "openai/gpt-oss-120b",
#     "display_name": "OpenAI GPT OSS",
#     "timeout": 15.0,
#     "timeout_segmentation": 60.0,
#     "max_tokens": 100,
#     "max_tokens_segmentation": 6000,
# },
# {
#     "name": "x-ai/grok-4.1-fast",
#     "display_name": "xAI: Grok 4.1 Fast",
#     "timeout": 15.0,
#     "timeout_segmentation": 60.0,
#     "max_tokens": 100,
#     "max_tokens_segmentation": 6000,
# },
# {
#     "name": "google/gemini-2.0-flash-001",
#     "display_name": "Google Gemini 2.0 Flash",
#     "timeout": 15.0,
#     "timeout_segmentation": 60.0,
#     "max_tokens": 100,
#     "max_tokens_segmentation": 8000,
# },
# {
#     "name": "meta-llama/llama-3.1-8b-instruct",
#     "display_name": "Meta: Llama 3.1 8B Instruct",
#     "timeout": 20.0,
#     "timeout_segmentation": 60.0,
#     "max_tokens": 100,
#     "max_tokens_segmentation": 4000,
# },
# {
#     "name": "google/gemini-2.5-flash-lite",
#     "display_name": "Google: Gemini 2.5 Flash Lite",
#     "timeout": 15.0,
#     "timeout_segmentation": 60.0,
#     "max_tokens": 100,
#     "max_tokens_segmentation": 6000,
# },
# {
#     "name": "google/gemini-3-flash-preview",
#     "display_name": "Gemini 3 Flash-Preview",
#     "timeout": 15.0,
#     "timeout_segmentation": 60.0,
#     "max_tokens": 100,
#     "max_tokens_segmentation": 8000,
# },
# {
#     "name": "qwen/qwen-2.5-coder-32b-instruct",
#     "display_name": "Qwen 2.5 Coder 32B",
#     "timeout": 15.0,
#     "timeout_segmentation": 60.0,
#     "max_tokens": 100,
#     "max_tokens_segmentation": 6000,
# },
# {
#     "name": "mistralai/mistral-small-3.2-24b-instruct",
#     "display_name": "Mistral Small 3.2 24B",
#     "timeout": 15.0,
#     "timeout_segmentation": 60.0,
#     "max_tokens": 100,
#     "max_tokens_segmentation": 6000,
# },
# {
#     "name": "mistralai/devstral-2512",
#     "display_name": "Mistral Devstral 2512",
#     "timeout": 15.0,
#     "timeout_segmentation": 60.0,
#     "max_tokens": 100,
#     "max_tokens_segmentation": 6000,
# },

# Benchmark settings
BENCHMARK_SETTINGS = {
    "parallel_requests": 5,  # Number of contests to process in parallel
    "runs_per_test": 1,  # Number of runs per test case to average results
    "retry_on_failure": True,
    "retry_attempts": 2,
    "save_html_cache": True,  # Cache HTML to avoid re-fetching
}
