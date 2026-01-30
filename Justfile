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
    docker compose logs --tail=250

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

# Run LLM model benchmarks for all models (both finder and segmentation)
benchmark-all:
    uv run python benchmarks/run_benchmark.py --all

# Run LLM model benchmark for specific model (e.g., just benchmark claude)
benchmark model:
    uv run python benchmarks/run_benchmark.py --model {{model}}

# Run editorial finder benchmark for all models
benchmark-finder-all:
    uv run python benchmarks/run_benchmark.py --all --type finder

# Run editorial finder benchmark for specific model
benchmark-finder model:
    uv run python benchmarks/run_benchmark.py --model {{model}} --type finder

# Run editorial segmentation benchmark for all models
benchmark-segmentation-all:
    uv run python benchmarks/run_benchmark.py --all --type segmentation

# Run editorial segmentation benchmark for specific model
benchmark-segmentation model:
    uv run python benchmarks/run_benchmark.py --model {{model}} --type segmentation

# View latest finder benchmark results in browser
benchmark-results-finder:
    @xdg-open $(ls -t benchmarks/results/editorial_finder/*.html | head -1) 2>/dev/null || open $(ls -t benchmarks/results/editorial_finder/*.html | head -1) 2>/dev/null || echo "Open this file in browser: $(ls -t benchmarks/results/editorial_finder/*.html | head -1)"

# View latest segmentation benchmark results in browser
benchmark-results-segmentation:
    @xdg-open $(ls -t benchmarks/results/editorial_segmentation/*.html | head -1) 2>/dev/null || open $(ls -t benchmarks/results/editorial_segmentation/*.html | head -1) 2>/dev/null || echo "Open this file in browser: $(ls -t benchmarks/results/editorial_segmentation/*.html | head -1)"

# View latest benchmark results in browser (tries finder first, then segmentation)
benchmark-results:
    @xdg-open $(ls -t benchmarks/results/editorial_finder/*.html benchmarks/results/editorial_segmentation/*.html 2>/dev/null | head -1) 2>/dev/null || open $(ls -t benchmarks/results/editorial_finder/*.html benchmarks/results/editorial_segmentation/*.html 2>/dev/null | head -1) 2>/dev/null || echo "No benchmark results found"

# View latest JSON benchmark results
benchmark-results-json:
    @cat $(ls -t benchmarks/results/editorial_finder/*.json benchmarks/results/editorial_segmentation/*.json 2>/dev/null | head -1)
