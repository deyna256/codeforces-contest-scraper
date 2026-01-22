# API Endpoints

## API Documentation

The API documentation is available via Swagger UI and ReDoc:

- **Swagger UI**: http://localhost:9000/schema/swagger
- **ReDoc**: http://localhost:9000/schema/redoc
- **OpenAPI JSON**: http://localhost:9000/schema/openapi.json

⚠️ **Note**: The documentation is at `/schema/swagger`, not `/docs`!

## Available Endpoints

### 1. Get Contest Information

Fetch complete contest information including all problems with their statements, ratings, tags, and editorial URL.

**Endpoint**: `POST /contest`

**Request**:
```json
{
  "url": "https://codeforces.com/contest/2191"
}
```

**Response**:
```json
{
  "contest_id": "2191",
  "title": "Codeforces Round 1073 (Div. 2)",
  "editorials": ["https://codeforces.com/blog/entry/150256"],
  "problems": [
    {
      "contest_id": "2191",
      "id": "A",
      "title": "Array Coloring",
      "statement": "You have $$$n$$$ cards arranged in a row...",
      "rating": null,
      "tags": ["constructive algorithms"],
      "time_limit": "1 second",
      "memory_limit": "256 megabytes"
    },
    {
      "contest_id": "2191",
      "id": "B",
      "title": "MEX Reordering",
      "statement": "You are given an integer array...",
      "rating": 1200,
      "tags": ["constructive algorithms", "sortings"],
      "time_limit": "1 second",
      "memory_limit": "256 megabytes"
    }
  ]
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:9000/contest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://codeforces.com/contest/2191"}'
```

**Error Responses**:

- **400 Bad Request** (Gym Contest):
```json
{
  "status_code": 400,
  "detail": "Gym contests are not supported: gym/102134",
  "error_type": "GymContestError"
}
```

- **404 Not Found** (Contest doesn't exist):
```json
{
  "status_code": 404,
  "detail": "Contest 99999 not found",
  "error_type": "ContestNotFoundError"
}
```

---

### 2. Get Problem Information

Fetch information about a single problem.

**Endpoint**: `POST /problems`

**Request**:
```json
{
  "url": "https://codeforces.com/problemset/problem/2190/B2"
}
```

**Response**:
```json
{
  "contest_id": "2190",
  "id": "B2",
  "statement": "Doremy's Drying Plan (Hard Version)",
  "description": "This is the hard version...",
  "time_limit": "4 seconds",
  "memory_limit": "512 megabytes",
  "rating": 2300,
  "tags": ["data structures", "greedy"],
  "url": "https://codeforces.com/problemset/problem/2190/B2"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:9000/problems \
  -H "Content-Type: application/json" \
  -d '{"url": "https://codeforces.com/problemset/problem/2190/B2"}'
```

---

### 3. Clear Cache

Clear the Redis cache.

**Endpoint**: `DELETE /cache`

**Response**:
```json
{
  "status": "Cache cleared successfully"
}
```

**cURL Example**:
```bash
curl -X DELETE http://localhost:9000/cache
```

---

## Response Fields

### Contest Response

| Field | Type | Description |
|-------|------|-------------|
| `contest_id` | string | Contest ID (e.g., "2191") |
| `title` | string | Contest title |
| `editorials` | array[string] | Array of editorial/tutorial URLs (empty if none) |
| `problems` | array | List of problems in the contest |

### Problem in Contest

| Field | Type | Description |
|-------|------|-------------|
| `contest_id` | string | Contest ID |
| `id` | string | Problem ID (e.g., "A", "B2") |
| `title` | string | Problem title |
| `statement` | string \| null | Full problem statement |
| `rating` | integer \| null | Problem difficulty rating |
| `tags` | array[string] | Problem tags/categories |
| `time_limit` | string \| null | Time limit (e.g., "1 second") |
| `memory_limit` | string \| null | Memory limit (e.g., "256 megabytes") |

### Problem Response (Single)

| Field | Type | Description |
|-------|------|-------------|
| `contest_id` | string | Contest ID |
| `id` | string | Problem ID |
| `statement` | string | Problem name/title |
| `description` | string \| null | Full problem description |
| `time_limit` | string \| null | Time limit |
| `memory_limit` | string \| null | Memory limit |
| `rating` | integer \| null | Difficulty rating |
| `tags` | array[string] | Problem tags |
| `url` | string | Original problem URL |

---

## Features

### Contest Endpoint Features

- ✅ Fetches all problems in a contest in parallel
- ✅ Includes full problem statements
- ✅ Includes time/memory limits
- ✅ Includes ratings and tags (if available)
- ✅ Finds editorial URL (with optional LLM support)
- ✅ Rejects gym contests
- ✅ Handles contests without ratings (new contests)
- ✅ Graceful degradation (continues if some problems fail)

### LLM-Enhanced Editorial Detection

The API can use LLMs (via OpenRouter) to intelligently find editorial links. See [LLM_EDITORIAL_DETECTION.md](./LLM_EDITORIAL_DETECTION.md) for details.

To enable:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
LLM_ENABLED=true
```

---

## Rate Limiting

When Redis is available, the API applies rate limiting:
- **Limit**: 10 requests per minute per IP
- **Header**: Check `X-RateLimit-*` headers in responses

---

## Error Handling

All errors follow this format:
```json
{
  "status_code": 400,
  "detail": "Error description",
  "error_type": "ErrorClassName"
}
```

Common error types:
- `URLParsingError` (400) - Invalid Codeforces URL
- `GymContestError` (400) - Gym contests not supported
- `ContestNotFoundError` (404) - Contest doesn't exist
- `ProblemNotFoundError` (404) - Problem doesn't exist
- `ParsingError` (422) - Failed to parse page
- `NetworkError` (500) - Network/API error

---

## Health Check

Check if the service is running:
```bash
curl http://localhost:9000/schema/openapi.json
```

If you get a valid JSON response, the service is up!

---

## Examples

### Python

```python
import requests

# Get contest
response = requests.post(
    "http://localhost:9000/contest",
    json={"url": "https://codeforces.com/contest/2191"}
)
contest = response.json()

print(f"Contest: {contest['title']}")
print(f"Problems: {len(contest['problems'])}")
print(f"Editorials: {contest['editorials']}")
```

### JavaScript

```javascript
// Get contest
const response = await fetch('http://localhost:9000/contest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://codeforces.com/contest/2191'
  })
});

const contest = await response.json();
console.log(`Contest: ${contest.title}`);
console.log(`Problems: ${contest.problems.length}`);
```

### Bash

```bash
# Get contest and extract problem titles
curl -s -X POST http://localhost:9000/contest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://codeforces.com/contest/2191"}' \
  | jq -r '.problems[] | "\(.id): \(.title)"'
```

---

## Development

Start the service:
```bash
docker compose up -d
```

View logs:
```bash
docker logs -f codeforces-editorial-finder-api-1
```

Stop the service:
```bash
docker compose down
```

---

## Additional Resources

- [LLM Editorial Detection](./LLM_EDITORIAL_DETECTION.md)
- [Main README](../README.md)
- [OpenAPI Schema](http://localhost:9000/schema/openapi.json)
