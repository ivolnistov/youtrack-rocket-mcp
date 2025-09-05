"""
YouTrack MCP Server - A Model Context Protocol server for JetBrains YouTrack.
"""

try:
    from youtrack_rocket_mcp._version import __version__
except ImportError:
    # Package is not installed, or version file not generated
    __version__ = '0.0.0-dev'

__all__ = ['__version__']
