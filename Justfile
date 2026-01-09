# Codeforces Editorial Finder - Just commands

# List available commands
default:
    @just --list

# Build the package
build:
    uv build

# Run linting checks
lint:
    uv run ruff check .

# Run linting with auto-fix
lint-fix:
    uv run ruff check --fix .

# Run type checking
typecheck:
    uv run ty check

# Format code
format:
    uv run ruff format .

# Run tests
test:
    uv run pytest
