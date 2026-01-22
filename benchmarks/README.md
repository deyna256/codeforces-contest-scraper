# LLM Model Benchmarking

Comprehensive benchmarking system for testing LLM models on the editorial finding task.

## Overview

Test different LLM models to find the best one for editorial detection:
- Compare multiple models on standardized test cases
- Get accuracy, latency, precision, recall, and F1 scores
- View results in interactive HTML reports or JSON format
- Multiple runs per test to handle model variability

## Quick Start

### 1. Add Test Data

Edit `test_data.py` with verified contest editorial URLs:

```python
{
    "contest_id": "2185",
    "expected_editorial": "https://codeforces.com/blog/entry/150288",
    "description": "Codeforces Round 1074 (Div. 4)",
    "difficulty": "easy",
}
```

**Finding editorials:**
1. Visit https://codeforces.com/contests → Past Contests
2. Click on a contest
3. Find "Tutorial" link in sidebar
4. Copy contest ID and editorial URL

**Recommended:** 20-50 test cases for reliable results.

### 2. Configure Models

Edit `config.py`:

```python
MODELS_TO_BENCHMARK = [
    {
        "name": "anthropic/claude-3.5-haiku",
        "display_name": "Claude 3.5 Haiku",
        "timeout": 30.0,
        "max_tokens": 100,
    },
]

BENCHMARK_SETTINGS = {
    "runs_per_test": 3,  # Multiple runs for averaging
    "parallel_requests": 3,
}
```

### 3. Run Benchmarks

Ensure `.env` has `OPENROUTER_API_KEY`:

```bash
# Test all configured models
just benchmark-all

# Test specific model
just benchmark "claude-3.5-haiku"
```

### 4. View Results

```bash
# Open HTML report in browser
just benchmark-results

# View JSON data
just benchmark-results-json
```

## Features

### 🎯 Multiple Runs with Averaging

Each test case runs **3 times by default** to handle LLM variability:
- **Latency**: Average across all runs
- **Correctness**: Majority vote (>50%)
- **Result**: Most common found_editorial

Example:
```
Contest 2185, 3 runs:
├─ Run 1: ✅ found editorial, 1200ms
├─ Run 2: ✅ found editorial, 1100ms
└─ Run 3: ❌ not found, 900ms

→ Final result:
   is_correct: true (2/3)
   avg_latency: 1067ms
```

### 📊 Interactive HTML Reports

Beautiful, sortable HTML reports with:
- Model comparison table (click headers to sort)
- Detailed metrics for each model
- Per-test results with visual indicators
- Responsive design for mobile/desktop

![HTML Report Preview]

**Features:**
- Color-coded accuracy (green/yellow/red)
- Sortable columns
- Test-by-test breakdown
- No dependencies - just open in browser

### 📄 JSON Reports

Machine-readable JSON format:
```json
{
  "benchmark_info": {
    "timestamp": "20260122_202500",
    "total_models": 2,
    "test_cases": 4
  },
  "summary": [
    {
      "model_name": "anthropic/claude-3.5-haiku",
      "accuracy": 85.71,
      "avg_latency_ms": 1234.56,
      "precision": 87.5,
      "recall": 87.5,
      "f1_score": 87.5
    }
  ],
  "detailed_results": {...}
}
```

### 📈 Comprehensive Metrics

- **Accuracy**: % of correctly identified editorials
- **Latency**: Average response time (ms)
- **Precision**: TP / (TP + FP)
- **Recall**: TP / (TP + FN)
- **F1 Score**: Harmonic mean of precision/recall

**Quality thresholds:**
- ✅ Good: ≥80%
- ⚠️ Medium: 70-79%
- ❌ Poor: <70%

## Project Structure

```
benchmarks/
├── config.py           # Model and settings configuration
├── test_data.py        # Ground truth test cases
├── metrics.py          # Metrics calculation
├── report.py           # Report generation orchestration
├── html_report.py      # HTML report generator
├── run_benchmark.py    # Main benchmark script
├── README.md           # This file
└── results/            # Generated reports
    ├── benchmark_comparison_*.json
    └── benchmark_report_*.html
```

## Configuration

### Model Settings

```python
# config.py
MODELS_TO_BENCHMARK = [
    {
        "name": "anthropic/claude-3.5-haiku",  # OpenRouter model ID
        "display_name": "Claude 3.5 Haiku",    # Human-readable name
        "timeout": 30.0,                        # Request timeout (seconds)
        "max_tokens": 100,                      # Max tokens to generate
    },
]
```

### Benchmark Settings

```python
BENCHMARK_SETTINGS = {
    "runs_per_test": 3,        # Runs per test case (for averaging)
    "parallel_requests": 3,     # Parallel contest processing
    "retry_on_failure": True,   # Retry failed requests
    "retry_attempts": 2,        # Number of retries
    "save_html_cache": True,    # Cache HTML pages
}
```

**Tips:**
- Increase `runs_per_test` (5-10) for more reliable results
- Reduce `parallel_requests` if hitting rate limits
- Enable `save_html_cache` to avoid re-fetching pages

## Commands

```bash
# Run benchmarks
just benchmark-all                  # All models
just benchmark "claude"             # Models matching "claude"
just benchmark "claude-3.5-haiku"  # Specific model

# View results
just benchmark-results              # Open HTML in browser
just benchmark-results-json         # Show JSON output

# Development
just typecheck                      # Type checking
just lint                           # Code linting
```

## Understanding Results

### Console Output

```
====================================================================================================
BENCHMARK COMPARISON
====================================================================================================
Rank   Model                                 Accuracy     Avg Latency     F1 Score
----------------------------------------------------------------------------------------------------
1      Claude 3.5 Haiku                         85.7%          1234ms        87.5%
2      GPT-4o Mini                              82.1%           987ms        84.2%
====================================================================================================
```

### HTML Report

Open `benchmark_report_*.html` in browser:
- **Top section**: Model comparison table (sortable)
- **Bottom section**: Detailed results per model
  - Metrics overview
  - Test-by-test results
  - Visual indicators (✓/✗/⚠)

### JSON Report

Programmatic access to all data:
- `benchmark_info`: Metadata
- `summary`: Model comparison data
- `detailed_results`: Per-test results for each model

## Cost Estimation

Approximate costs (30 test cases, 3 runs each = 90 total API calls):

| Model | Cost per Run | Total (90 calls) |
|-------|--------------|------------------|
| Claude 3.5 Haiku | ~$0.001 | ~$0.15 |
| GPT-4o Mini | ~$0.002 | ~$0.20 |
| DeepSeek v3 | ~$0.0005 | ~$0.08 |
| Gemini Flash (free) | $0 | Free |

**Cost factors:**
- Number of test cases
- Runs per test
- Number of links per page (affects token count)

**Tip:** Start with 5 test cases and `runs_per_test: 1` to validate setup.

## Best Practices

1. **Verify Ground Truth**: Manually check each editorial URL
2. **Diverse Test Cases**: Include Div 1/2/3/4, recent and old contests
3. **Edge Cases**: Contests without editorials, multiple tutorials
4. **Sufficient Size**: 20+ test cases minimum
5. **Multiple Runs**: Use 3-5 runs per test for reliable results
6. **Regular Re-benchmarks**: Re-run when updating prompts or testing new models

## Troubleshooting

### "OPENROUTER_API_KEY not set"
```bash
# Add to .env
OPENROUTER_API_KEY=sk-or-v1-...
```

### Rate Limiting
Reduce `parallel_requests` in `config.py`:
```python
BENCHMARK_SETTINGS = {
    "parallel_requests": 1,  # Slower but no rate limits
}
```

### Timeout Errors
Increase timeout in model config:
```python
{
    "timeout": 60.0,  # 60 seconds
}
```

### Low Accuracy
- Verify test data is correct
- Try different models
- Check LLM prompt in `src/infrastructure/parsers/llm_editorial_finder.py`

### HTML Report Won't Open
```bash
# Linux
xdg-open benchmarks/results/benchmark_report_*.html

# macOS
open benchmarks/results/benchmark_report_*.html

# Windows
start benchmarks/results/benchmark_report_*.html
```

## Choosing the Best Model

Consider:
1. **Accuracy** (most important) - aim for >80%
2. **F1 Score** (balanced) - combines precision and recall
3. **Latency** (UX) - lower is better, <2000ms is good
4. **Cost** (operations) - balance against accuracy gain

**Example decision:**
- Claude Haiku: 85% accuracy, 1200ms, $0.15 → ✅ **Best choice**
- GPT-4o Mini: 82% accuracy, 900ms, $0.20 → ✅ Good alternative
- Gemini Flash: 75% accuracy, 1500ms, Free → ⚠️ Budget option

## Next Steps

1. ✅ Add 20-50 verified contests to `test_data.py`
2. ✅ Configure models in `config.py`
3. ✅ Run: `just benchmark "claude-3.5-haiku"`
4. ✅ Open HTML report: `just benchmark-results`
5. ✅ Run all models: `just benchmark-all`
6. ✅ Analyze and choose best model
7. ✅ Update production config with winner
8. ✅ Set up monthly re-benchmarking

## Resources

- **OpenRouter Docs**: https://openrouter.ai/docs
- **Model Pricing**: https://openrouter.ai/models
- **Codeforces Contests**: https://codeforces.com/contests
