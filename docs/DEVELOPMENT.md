# Development Guide

## Prerequisites

- Python 3.12+
- [UV](https://github.com/astral-sh/uv) - Modern Python package manager (optional, but recommended)

## Setup

```bash
# Clone the repository
git clone https://github.com/ivolnistov/youtrack-rocket-mcp.git
cd youtrack-rocket-mcp

# Install all dependencies including dev group for development
uv sync

# This will:
# - Create a virtual environment if it doesn't exist
# - Install all runtime dependencies
# - Install all dev group dependencies (pytest, ruff, mypy, etc.)
# - Install the package in editable mode

# Note: uv sync includes the dev group by default.
# To install without dev dependencies: uv sync --no-dev
```


## Running the Server

### From PyPI (after installation)

```bash
# Using uvx (no installation required)
uvx youtrack-rocket-mcp

# Or if installed with uv tool
uv tool install youtrack-rocket-mcp
youtrack-rocket-mcp

# Or if installed with pip
youtrack-rocket-mcp
```

### During Development

```bash
# Run directly with UV (manages virtual environment automatically)
uv run python -m youtrack_rocket_mcp.server

# Or if virtual environment is activated
python -m youtrack_rocket_mcp.server

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

## Environment Configuration

Set up your environment variables:

```bash
# Create .env file
cat > .env << EOF
YOUTRACK_URL=https://your-instance.youtrack.cloud
YOUTRACK_API_TOKEN=perm:your-api-token
YOUTRACK_CLOUD=true
EOF

# Or export directly
export YOUTRACK_URL="https://your-instance.youtrack.cloud"
export YOUTRACK_API_TOKEN="perm:your-api-token"
```

## FastMCP Architecture

This project is built with FastMCP, which provides:
- Automatic JSON Schema generation from Python type hints
- Proper parameter validation
- Correct parameter names in MCP Inspector (no more args/kwargs)
- Full async support for optimal performance

The API layer uses `httpx` for HTTP operations with comprehensive error handling and retry logic.

## Testing

```bash
# Run all tests with UV
uv run pytest

# Run with coverage
uv run pytest --cov=youtrack_rocket_mcp

# Run specific test file
uv run pytest tests/test_issues.py

# Run tests in verbose mode
uv run pytest -v
```

## Code Quality

```bash
# Format code (auto-fix)
uv run ruff format src/

# Check linting
uv run ruff check src/

# Check linting with auto-fix
uv run ruff check src/ --fix

# Type checking
uv run mypy src/youtrack_rocket_mcp
```

## Building and Publishing

```bash
# Build the package
uv build

# This creates wheel and source distributions in dist/
ls dist/
# youtrack_rocket_mcp-X.Y.Z.tar.gz
# youtrack_rocket_mcp-X.Y.Z-py3-none-any.whl

# The package is published automatically via GitHub Actions
# when a version tag is pushed (e.g., vX.Y.Z)
```
