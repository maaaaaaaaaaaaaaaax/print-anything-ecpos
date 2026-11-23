check:
    uv run ruff format --check
    uv run ruff check
    uv run ty check
    uv run lint-imports
    uv run pytest
