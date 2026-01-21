# LLM-Based Editorial Detection

## Overview

The Codeforces Editorial Finder can use Large Language Models (LLMs) to intelligently identify editorial/tutorial links on contest pages. This improves accuracy compared to simple regex-based detection, especially for:

- Multilingual contests (Russian/English)
- Non-standard editorial naming
- Complex page structures

## How It Works

### Architecture

1. **Link Extraction**: Parse contest page and extract relevant links
2. **LLM Analysis**: Send links to LLM with context about what editorials look like
3. **Fallback**: If LLM fails or is disabled, use regex-based detection

### Benefits

- **Intelligent**: Understands context and patterns beyond simple keyword matching
- **Multilingual**: Handles Russian terms like "Разбор задач"
- **Flexible**: Works with any OpenRouter-compatible model
- **Safe**: Automatic fallback to regex if LLM unavailable

## Configuration

### Prerequisites

1. Get an API key from [OpenRouter](https://openrouter.ai/)
2. Choose a model (default: `anthropic/claude-3.5-haiku`)

### Environment Variables

Add to your `.env` file:

```bash
# Required: Your OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional: Model to use (default: anthropic/claude-3.5-haiku)
OPENROUTER_MODEL=anthropic/claude-3.5-haiku

# Optional: OpenRouter API URL (default: https://openrouter.ai/api/v1)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Optional: Enable/disable LLM detection (default: true)
LLM_ENABLED=true
```

### Supported Models

Any OpenRouter model that supports chat completions:

- **Recommended**: `anthropic/claude-3.5-haiku` (fast, cheap, accurate)
- **Budget**: `openai/gpt-3.5-turbo`
- **Premium**: `anthropic/claude-3.5-sonnet`, `openai/gpt-4-turbo`

### Cost Considerations

LLM calls are made only once per contest (when parsing editorial URL). Typical costs:

- **Claude 3.5 Haiku**: ~$0.0001 per request
- **GPT-3.5 Turbo**: ~$0.0002 per request
- **Claude 3.5 Sonnet**: ~$0.001 per request

## Usage

### With LLM Enabled

```bash
# Set your API key
export OPENROUTER_API_KEY="sk-or-v1-..."

# Start the service
docker compose up -d

# Make request - LLM will be used
curl -X POST http://localhost:9000/contest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://codeforces.com/contest/2191"}'
```

### Without LLM (Fallback)

```bash
# Don't set API key, or disable LLM
export LLM_ENABLED=false

# Start the service
docker compose up -d

# Make request - regex fallback will be used
curl -X POST http://localhost:9000/contest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://codeforces.com/contest/2191"}'
```

## Implementation Details

### Clean Architecture

The implementation follows clean architecture principles:

```
┌─────────────────────────────────────────┐
│          API Layer (Litestar)           │
│    ContestController (/contest)         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         Service Layer                    │
│    ContestService (orchestration)       │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Infrastructure Layer                │
│  ┌─────────────────────────────────┐    │
│  │   ContestPageParser             │    │
│  │   ├─ LLMEditorialFinder ✨      │    │
│  │   └─ Regex fallback             │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │   OpenRouterClient              │    │
│  │   (httpx-based HTTP client)     │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### Key Components

1. **`OpenRouterClient`** (`infrastructure/llm_client.py`)
   - Generic client for OpenRouter API
   - Supports any OpenRouter model
   - Error handling and timeouts

2. **`LLMEditorialFinder`** (`infrastructure/parsers/llm_editorial_finder.py`)
   - Extracts links from contest page
   - Formats prompt for LLM
   - Parses JSON response

3. **`ContestPageParser`** (`infrastructure/parsers/contest_page_parser.py`)
   - Orchestrates LLM + fallback
   - Graceful degradation
   - Maintains backward compatibility

### Prompt Engineering

The LLM receives:

**System Prompt**: Instructions on how to identify editorials

**User Prompt**:
```
Contest ID: 2191

Available links:
1. [Tutorial] - https://codeforces.com/blog/entry/150256
2. [Standings] - https://codeforces.com/contest/2191/standings
...

Which link is the editorial/tutorial? Respond with JSON only.
```

**Expected Response**:
```json
{"url": "https://codeforces.com/blog/entry/150256"}
```

## Monitoring

### Logs

Check logs for LLM usage:

```bash
docker logs codeforces-editorial-finder-api-1 | grep -i llm
```

Typical log messages:
- `Attempting LLM-based editorial detection` - LLM enabled
- `LLM found editorial URL: ...` - Success
- `LLM did not find editorial, falling back to regex` - Fallback
- `LLM client not available, skipping` - No API key

### Debugging

Enable debug logging:

```bash
LOG_LEVEL=DEBUG docker compose up -d
```

## Testing

### Unit Tests

```bash
# Test LLM client
pytest tests/infrastructure/test_llm_client.py

# Test editorial finder
pytest tests/infrastructure/parsers/test_llm_editorial_finder.py
```

### Integration Tests

```bash
# Test with real API (requires API key)
OPENROUTER_API_KEY="..." pytest tests/integration/test_contest_llm.py
```

## Troubleshooting

### LLM Not Being Used

1. Check API key is set: `echo $OPENROUTER_API_KEY`
2. Check LLM is enabled: `echo $LLM_ENABLED`
3. Check logs for errors

### API Errors

- **401 Unauthorized**: Invalid API key
- **429 Rate Limit**: Too many requests
- **Timeout**: Model taking too long (default: 30s)

### Fallback Always Used

This is normal behavior if:
- No API key provided
- LLM disabled in config
- API request fails
- LLM returns no result

## Future Improvements

Potential enhancements:

1. **Caching**: Cache LLM responses per contest
2. **Batch Processing**: Process multiple contests in parallel
3. **Model Selection**: Auto-select model based on cost/accuracy
4. **Confidence Scores**: Return confidence level with URL
5. **A/B Testing**: Compare LLM vs regex accuracy

## Contributing

When contributing LLM features:

1. Maintain backward compatibility (fallback)
2. Add appropriate error handling
3. Update tests
4. Document configuration changes
5. Consider cost implications

## License

Same as main project (MIT)
