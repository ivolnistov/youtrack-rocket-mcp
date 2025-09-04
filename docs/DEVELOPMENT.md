# Development Guide

## Prerequisites

- Python 3.12+
- [UV](https://github.com/astral-sh/uv) - Modern Python package manager

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```

## Running the Server

Use UV to run commands (automatically manages virtual environment):

```bash
# Check version
uv run youtrack-rocket-mcp --version

# Run the MCP server
uv run youtrack-rocket-mcp

# Run tests
uv run pytest

# Format code
uv run ruff format src/

# Check linting
uv run ruff check src/

# Type checking
uv run mypy src/
```

## Project Structure

```
youtrack-rocket-mcp/
├── src/                    # Source code (src-layout)
│   └── youtrack_rocket_mcp/       # Main package
│       ├── api/            # API client modules
│       ├── tools/          # MCP tools
│       └── server.py       # MCP server implementation
├── tests/                  # Test files
├── pyproject.toml          # Project configuration
└── .venv/                  # Virtual environment (managed by UV)
```

## Why UV?

This project uses UV for dependency management because:
- **Fast**: Written in Rust, significantly faster than pip
- **Modern**: Follows latest Python packaging standards
- **Simple**: No need to manually activate virtual environments
- **Reliable**: Ensures consistent dependency resolution

## Installing in Development Mode

The project is automatically installed in editable mode when you run `uv sync`.

## Adding Dependencies

```bash
# Add a runtime dependency
uv add <package>

# Add a development dependency
uv add --group dev <package>
```

## Async Architecture

The entire API layer uses async/await pattern with httpx for better performance.
MCP tools use a sync wrapper (`run_async_in_sync`) to bridge with the async API.