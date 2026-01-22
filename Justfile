# List available commands
default:
    @just --list

# Build services
build:
    docker compose build

# Start services
up:
    docker compose up -d

# Stop services
down:
    docker compose down

# Restart services
restart:
    just down
    just up

# View logs
logs:
    docker compose logs -f

# Clean up
clean:
    docker compose down -v --rmi local
    rm -rf .pytest_cache .ruff_cache .venv build dist *.egg-info

# Run tests
test:
    uv run pytest

# Format code
format:
    uv run ruff format .

# Run linting
lint:
    uv run ruff check .

# Run linting with auto-fix
lintfix:
    uv run ruff check --fix .

# Run type checking
typecheck:
    uv run ty check

# Run LLM model benchmarks for all models
benchmark-all:
    uv run python benchmarks/run_benchmark.py --all

# Run LLM model benchmark for specific model (e.g., just benchmark claude)
benchmark model:
    uv run python benchmarks/run_benchmark.py --model {{model}}

# View latest benchmark results in browser
benchmark-results:
    @xdg-open $(ls -t benchmarks/results/benchmark_report_*.html | head -1) 2>/dev/null || open $(ls -t benchmarks/results/benchmark_report_*.html | head -1) 2>/dev/null || echo "Open this file in browser: $(ls -t benchmarks/results/benchmark_report_*.html | head -1)"

# View latest JSON benchmark results
benchmark-results-json:
    @cat $(ls -t benchmarks/results/benchmark_comparison_*.json | head -1)
