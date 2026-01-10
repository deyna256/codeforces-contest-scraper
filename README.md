# Codeforces Editorial Finder

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![LiteStar](https://img.shields.io/badge/LiteStar-2.0+-orange.svg)](https://litestar.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

HTTP API for extracting editorials/tutorials for Codeforces problems using OpenAI API.

## Features

- **Async-first architecture** built with LiteStar
- **AI-powered editorial extraction** using GPT-4o
- **Automatic editorial search** across contest pages and blog posts
- **JavaScript rendering** for dynamic content (lazy-loaded editorials)
- **Supports HTML and PDF** tutorial formats
- **Redis caching** with configurable TTL
- **Rate limiting** (10 requests per minute)
- **Clean architecture** with clear separation of concerns

## Quick Start with Docker

```bash
# Clone repository
git clone https://github.com/deyna256/codeforces-editorial-finder.git
cd codeforces-editorial-finder

# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=sk-xxxxx" > .env

# Start services (API + Redis)
docker-compose up
```

The API will be available at `http://localhost:8000`

## API Usage

### Endpoint

**POST** `/editorial`

### Request

```json
{
  "url": "https://codeforces.com/contest/1234/problem/A"
}
```

### Response

```json
{
  "problem": {
    "contest_id": "1234",
    "problem_id": "A",
    "title": "Problem Title",
    "url": "https://codeforces.com/contest/1234/problem/A",
    "contest_name": "Codeforces Round #...",
    "tags": ["math", "greedy"],
    "time_limit": "2 seconds",
    "memory_limit": "256 megabytes"
  },
  "editorial": {
    "problem_id": "A",
    "solution_text": "Full editorial text...",
    "approach": "Greedy algorithm",
    "algorithm": "Two pointers",
    "time_complexity": "O(n)",
    "space_complexity": "O(1)",
    "code_snippets": [
      {
        "language": "python",
        "code": "# Solution code...",
        "description": "Python solution"
      }
    ],
    "hints": ["Try sorting first", "Consider edge cases"],
    "notes": "Additional notes...",
    "source_url": "https://codeforces.com/blog/entry/...",
    "extracted_at": "2025-01-10T12:00:00",
    "ai_model": "gpt-4o"
  }
}
```

### Examples

#### Using curl

```bash
curl -X POST http://localhost:8000/editorial \
  -H "Content-Type: application/json" \
  -d '{"url": "https://codeforces.com/contest/1/problem/A"}'
```

#### Using Python

```python
import httpx
import asyncio

async def get_editorial(problem_url: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/editorial",
            json={"url": problem_url}
        )
        return response.json()

# Example usage
result = asyncio.run(get_editorial("https://codeforces.com/contest/1/problem/A"))
print(result["editorial"]["solution_text"])
```

#### Using httpx CLI

```bash
httpx POST http://localhost:8000/editorial url=https://codeforces.com/contest/1/problem/A
```

### Supported URL Formats

```
https://codeforces.com/contest/1234/problem/A
https://codeforces.com/problemset/problem/1234/A
https://codeforces.com/gym/102345/problem/A
https://codeforces.ru/contest/1234/problem/A
```

### Error Responses

| Status Code | Error Type | Description |
|------------|------------|-------------|
| 400 | URLParsingError | Invalid URL format |
| 404 | EditorialNotFoundError | Editorial not found |
| 422 | ExtractionError / ParsingError | Failed to extract or parse editorial |
| 429 | RateLimitExceeded | Too many requests (limit: 10/minute) |
| 503 | OpenAIAPIError | OpenAI API unavailable |

### Response Headers

Rate limiting information is included in response headers:

```
RateLimit-Limit: 10
RateLimit-Remaining: 8
RateLimit-Reset: 1673456789
```

## Configuration

Environment variables (create a `.env` file):

```bash
# Required
OPENAI_API_KEY=sk-xxxxx

# Optional
OPENAI_MODEL=gpt-4o                    # Default: gpt-4o
REDIS_URL=redis://localhost:6379/0     # Default: redis://localhost:6379/0
CACHE_TTL_HOURS=168                    # Default: 168 (7 days)
HTTP_TIMEOUT=30                        # Default: 30 seconds
HTTP_RETRIES=3                         # Default: 3
HTTP_JS_WAIT=5000                      # Default: 5000ms
LOG_LEVEL=INFO                         # Default: INFO
```

## Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────┐
│   Presentation Layer (HTTP API)         │  ← LiteStar routes, schemas
├─────────────────────────────────────────┤
│   Application Layer (Use Cases)         │  ← Orchestrator, cache logic
├─────────────────────────────────────────┤
│   Domain Layer (Business Logic)         │  ← Parsers, extractors, models
├─────────────────────────────────────────┤
│   Infrastructure Layer (External APIs)  │  ← HTTP, OpenAI, Redis clients
└─────────────────────────────────────────┘
```

### Project Structure

```
src/
├── presentation/           # HTTP API layer
│   ├── app.py             # LiteStar application
│   ├── routes.py          # Route handlers
│   ├── schemas.py         # Request/response models
│   ├── dependencies.py    # Dependency injection
│   └── exceptions.py      # Exception handlers
│
├── application/           # Application layer
│   └── orchestrator.py    # Async editorial extraction workflow
│
├── domain/                # Domain layer
│   ├── models.py          # Core domain models
│   ├── exceptions.py      # Domain exceptions
│   ├── parsers/           # URL, problem page, tutorial parsers
│   ├── extractors/        # Editorial extraction logic
│   └── fetchers/          # Tutorial finder
│
├── infrastructure/        # Infrastructure layer
│   ├── http_client.py     # Async HTTP client (httpx + Playwright)
│   ├── openai_client.py   # Async OpenAI client
│   └── cache_redis.py     # Async Redis cache
│
└── config.py              # Pydantic settings
```

## Development

### Local Setup

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install dependencies
git clone https://github.com/deyna256/codeforces-editorial-finder.git
cd codeforces-editorial-finder
uv sync --group dev

# Install Playwright browsers
uv run playwright install chromium

# Start Redis (required)
docker run -d -p 6379:6379 redis:7-alpine

# Create .env file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run development server
uv run uvicorn src.presentation.app:app --reload --port 8000
```

### Testing

```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/url_parser_test.py
```

### Code Quality

```bash
# Linting and formatting (if using just)
just lint      # Check code
just lint-fix  # Fix issues
just format    # Format code

# Or using ruff directly
uv run ruff check src/
uv run ruff format src/
```

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Using Docker directly

```bash
# Build image
docker build -t codeforces-editorial-finder .

# Run with Redis
docker run -d --name redis redis:7-alpine
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-xxxxx \
  -e REDIS_URL=redis://redis:6379/0 \
  --link redis \
  codeforces-editorial-finder
```

## How It Works

1. **Parse URL** → Extract problem identifier (contest ID, problem ID)
2. **Check Cache** → Return cached result if available
3. **Fetch Problem Data** → Parse problem page for metadata
4. **Find Tutorial** → Search for editorial using AI and pattern matching
5. **Parse Tutorial** → Extract content from HTML or PDF
6. **Extract Editorial** → Use AI to extract specific problem solution
7. **Cache Result** → Store in Redis with TTL

## Performance

- **Response caching**: 1 hour (LiteStar built-in)
- **Editorial caching**: 7 days (Redis)
- **Rate limiting**: 10 requests per minute per client
- **Typical response time**: 5-15 seconds (uncached)
- **Cached response time**: <100ms

## License

MIT - see LICENSE file

## Author

[deyna256](https://github.com/deyna256)
