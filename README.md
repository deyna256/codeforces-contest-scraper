# Codeforces Editorial Finder

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CLI tool for extracting editorials/tutorials for Codeforces problems using OpenAI API.

## Features

- Automatic editorial search for Codeforces problems
- AI-powered parsing (GPT-4o) - adapts to website structure changes
- JavaScript rendering for dynamic content (handles lazy-loaded editorials)
- Supports HTML and PDF formats
- Extracts specific problem solutions from general editorials
- Markdown-formatted output with caching

## Installation

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/deyna256/codeforces-editorial-finder.git
cd codeforces-editorial-finder
uv sync

# Install Playwright browsers (required for JavaScript rendering)
uv run playwright install chromium
```

## Configuration

Create a `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-xxxxx

# Optional
OPENAI_MODEL=gpt-4o              # Default: gpt-4o
CACHE_DIR=~/.cache/codeforces-editorial
CACHE_TTL_HOURS=168              # 7 days
HTTP_JS_WAIT=5000                # JS content wait time (ms)
LOG_LEVEL=INFO
```

## Usage

```bash
# Basic usage
codeforces-editorial https://codeforces.com/contest/1234/problem/A

# Save to file
codeforces-editorial <url> -o solution.md

# Ignore cache
codeforces-editorial <url> --no-cache

# Clear cache before running
codeforces-editorial <url> --clear-cache

# Verbose output
codeforces-editorial <url> -v
```

### Supported URL formats

```
https://codeforces.com/contest/1234/problem/A
https://codeforces.com/problemset/problem/1234/A
https://codeforces.com/gym/102345/problem/A
https://codeforces.ru/contest/1234/problem/A
```

## Development

```bash
# Install with dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Linting and formatting
just lint      # Check code
just lint-fix  # Fix issues
just format    # Format code

# Type checking
just typecheck

# Build package
just build
```

## Architecture

```
src/codeforces_editorial/
├── parsers/           # URL, problem pages, tutorials
├── fetchers/          # HTTP client, editorial finder
├── openai/            # OpenAI API integration
├── extractors/        # Solution extraction
├── orchestrator.py    # Main workflow coordinator
├── cache.py           # Result caching
└── config.py          # Settings management
```

## Error Handling

- `URLParseError` - Invalid URL format
- `ProblemNotFoundError` - Problem not found (404)
- `EditorialNotFoundError` - Editorial not found
- `OpenAIAPIError` - API error
- `NetworkError` - Network/HTTP error
- `CacheError` - Cache operation error

## License

MIT - see LICENSE file

## Author

[deyna256](https://github.com/deyna256)
