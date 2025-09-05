#!/usr/bin/env python3
"""
FastMCP-based YouTrack MCP server implementation.
"""

import asyncio
import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from youtrack_rocket_mcp.config import config
from youtrack_rocket_mcp.tools.issues import register_issue_tools
from youtrack_rocket_mcp.tools.projects import register_project_tools
from youtrack_rocket_mcp.tools.search import register_search_tools
from youtrack_rocket_mcp.tools.search_guide import register_search_guide_tools
from youtrack_rocket_mcp.tools.users import register_user_tools

logger = logging.getLogger(__name__)


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Handle server startup and shutdown."""
    # Startup
    logger.debug('Server starting up...')
    try:
        yield
    finally:
        # Cleanup on shutdown
        logger.debug('Server shutting down...')
        # Cancel all pending async tasks for clean shutdown
        tasks = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        for task in tasks:
            task.cancel()
        # Wait briefly for tasks to complete cancellation
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Initialize FastMCP server with name, instructions and lifespan
mcp: FastMCP = FastMCP(
    name=config.MCP_SERVER_NAME, instructions=config.MCP_SERVER_INSTRUCTIONS, lifespan=server_lifespan
)


def main():
    """Main entry point for the FastMCP YouTrack server."""

    try:
        # Validate configuration before starting
        config.validate()

        # Try to initialize tools first to catch config errors early
        register_issue_tools(mcp)
        register_project_tools(mcp)
        register_search_tools(mcp)
        register_search_guide_tools(mcp)
        register_user_tools(mcp)

        # Set up logging only after successful initialization
        if config.MCP_DEBUG or os.getenv('DEBUG'):
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            logger.info(f'Starting YouTrack FastMCP server ({config.MCP_SERVER_NAME})')
            logger.info('FastMCP tools registered with proper parameter schemas')
        else:
            # Minimal logging in production
            logging.basicConfig(level=logging.ERROR, format='%(message)s')

        # Run the server - this blocks until interrupted
        mcp.run()

        # If we get here, server exited normally
        sys.exit(0)
    except KeyboardInterrupt:
        # Clean exit on Ctrl-C without showing traceback
        print('\nShutting down...', file=sys.stderr)
        sys.exit(0)
    except ValueError as e:
        # Configuration errors - show user-friendly message
        print(f'\n❌ Configuration Error:\n{e!s}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if config.MCP_DEBUG:
            # Show full traceback in debug mode
            raise
        # Show only the error message in production
        print(f'\n❌ Error starting server: {e!s}', file=sys.stderr)
        print('\n💡 Tip: Set MCP_DEBUG=true for detailed error information.', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
