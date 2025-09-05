#!/bin/bash
# Script to run YouTrack MCP server with MCP Inspector

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting YouTrack MCP server with Inspector..."

# Load environment variables from .env file if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "📋 Loading environment from .env file..."
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
fi

# Check if required environment variables are set
if [ -z "$YOUTRACK_API_TOKEN" ]; then
    echo "❌ Error: YOUTRACK_API_TOKEN is not set"
    echo "Please create a .env file with:"
    echo "  YOUTRACK_API_TOKEN=perm:username.workspace.xxxxx  # For YouTrack Cloud"
    echo "  # or"
    echo "  YOUTRACK_URL=https://youtrack.example.com  # For self-hosted"
    echo "  YOUTRACK_API_TOKEN=perm:xxxxx"
    exit 1
fi

if [ -n "$YOUTRACK_URL" ]; then
    echo "✅ Using self-hosted YouTrack: $YOUTRACK_URL"
else
    echo "✅ Using YouTrack Cloud (workspace from token)"
fi
echo ""

# Change to script directory and run the MCP Inspector with the FastMCP server using uv
cd "$SCRIPT_DIR"
npx -y @modelcontextprotocol/inspector uv run python -m youtrack_rocket_mcp.server
