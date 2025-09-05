#!/usr/bin/env python3
"""
FastMCP-based YouTrack MCP server implementation.
"""

import logging

from fastmcp import FastMCP

from youtrack_rocket_mcp.config import config
from youtrack_rocket_mcp.tools.issues import register_issue_tools
from youtrack_rocket_mcp.tools.projects import register_project_tools
from youtrack_rocket_mcp.tools.search import register_search_tools
from youtrack_rocket_mcp.tools.search_guide import register_search_guide_tools
from youtrack_rocket_mcp.tools.users import register_user_tools

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp: FastMCP = FastMCP(config.MCP_SERVER_NAME)


def main():
    """Main entry point for the FastMCP YouTrack server."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info(f'Starting YouTrack FastMCP server ({config.MCP_SERVER_NAME})')
    logger.info('FastMCP tools registered with proper parameter schemas')

    # Register all tools
    register_issue_tools(mcp)
    register_project_tools(mcp)
    register_search_tools(mcp)
    register_search_guide_tools(mcp)
    register_user_tools(mcp)

    # Run the server
    mcp.run()


if __name__ == '__main__':
    main()
