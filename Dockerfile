FROM python:3.12-alpine

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git gcc musl-dev python3-dev libffi-dev openssl-dev

# Copy pyproject.toml and README first to leverage Docker cache
COPY pyproject.toml README.md ./

# Copy source code
COPY src/ src/

# Install the package with pip (without dev dependencies since dotenv is optional)
RUN pip install --no-cache-dir .

# Default environment variables (will be overridden at runtime)
ENV MCP_SERVER_NAME="youtrack-rocket-mcp"
ENV MCP_SERVER_DESCRIPTION="🚀 YouTrack Rocket MCP Server"
ENV MCP_DEBUG="false"
ENV YOUTRACK_VERIFY_SSL="true"
ENV YOUTRACK_CLOUD="false"

# Run the MCP server in stdio mode for Claude integration by default
ENTRYPOINT ["python", "-m", "youtrack_rocket_mcp.server"]