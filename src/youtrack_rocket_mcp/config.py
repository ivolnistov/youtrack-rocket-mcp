"""
Configuration for YouTrack MCP server.

This module handles all configuration for the YouTrack MCP server including:
- API credentials and URL configuration
- SSL certificate verification settings
- Cloud vs self-hosted instance detection
- MCP server settings

Important notes for using the server:
1. Always use get_project_detailed() before creating issues to see required fields
2. Project short names (e.g., 'ITSFT') are automatically resolved to IDs
3. Custom field values must match exactly from possible_values (case-sensitive)
4. Use field names or IDs when setting custom fields
"""

import os
import ssl

# Optional import for dotenv
try:
    from dotenv import load_dotenv

    # Load environment variables from .env file if it exists
    load_dotenv()
except ImportError:
    # dotenv is not required
    pass


class Config:
    """Configuration settings for YouTrack MCP server."""

    # YouTrack API configuration
    YOUTRACK_URL: str = os.getenv('YOUTRACK_URL', '')
    YOUTRACK_API_TOKEN: str = os.getenv('YOUTRACK_API_TOKEN', '')
    VERIFY_SSL: bool = os.getenv('YOUTRACK_VERIFY_SSL', 'true').lower() in ('true', '1', 'yes')

    # API client configuration
    MAX_RETRIES: int = int(os.getenv('YOUTRACK_MAX_RETRIES', '3'))
    RETRY_DELAY: float = float(os.getenv('YOUTRACK_RETRY_DELAY', '1.0'))

    # MCP Server configuration
    MCP_SERVER_NAME: str = os.getenv('MCP_SERVER_NAME', 'youtrack-rocket-mcp')
    MCP_DEBUG: bool = os.getenv('MCP_DEBUG', 'false').lower() in ('true', '1', 'yes')

    # Instructions for AI assistants on how to use this server
    MCP_SERVER_INSTRUCTIONS: str = os.getenv(
        'MCP_SERVER_INSTRUCTIONS',
        """
YouTrack MCP Server - Issue tracking integration for AI assistants.

Key capabilities:
- Search issues using YouTrack query language
- Create issues with custom fields (use get_project first to see required fields)
- Add comments and execute batch commands on issues
- Get project configurations and field values

Best practices:
1. Always use get_project() before creating issues to understand required fields
2. Use search_issues() for quick searches (returns only ID and summary)
3. Use search_issues_detailed() when you need full issue information
4. Use execute_command() for batch operations like assigning or changing state
5. Check get_search_syntax_guide() for query syntax help
    """.strip(),
    )

    @classmethod
    def from_dict(cls, config_dict: dict[str, str | int | float | bool]) -> None:
        """
        Update configuration from a dictionary.

        Args:
            config_dict: Dictionary with configuration values
        """
        # Set configuration values from the dictionary
        for key, value in config_dict.items():
            if hasattr(cls, key):
                setattr(cls, key, value)

    @classmethod
    def validate(cls) -> None:
        """
        Validate the configuration settings.

        Raises:
            ValueError: If required settings are missing or invalid
        """
        # API token is always required
        if not cls.YOUTRACK_API_TOKEN:
            raise ValueError(
                '\n🔧 YouTrack Configuration Required\n'
                '\n'
                'Please set your YouTrack API token:\n'
                '\n'
                '1. For YouTrack Cloud:\n'
                '   export YOUTRACK_API_TOKEN="perm:username.workspace.xxxxx"\n'
                '\n'
                '2. For self-hosted YouTrack:\n'
                '   export YOUTRACK_URL="https://youtrack.company.com"\n'
                '   export YOUTRACK_API_TOKEN="perm:xxxxx"\n'
                '\n'
                'Get your token from YouTrack: Profile → Account Security → New token\n'
            )

        # If URL is provided, ensure it doesn't end with a trailing slash
        if cls.YOUTRACK_URL:
            cls.YOUTRACK_URL = cls.YOUTRACK_URL.rstrip('/')

        # Try to get base URL to ensure configuration is valid
        try:
            cls.get_base_url()
        except ValueError as e:
            # Re-raise with cleaner error message
            raise ValueError(str(e)) from None

    @classmethod
    def get_ssl_context(cls) -> ssl.SSLContext | None:
        """
        Get SSL context for HTTPS requests.

        Returns:
            SSLContext with proper configuration or None for default behavior
        """
        if not cls.VERIFY_SSL:
            # Create a context that doesn't verify certificates
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context

        return None

    @classmethod
    def is_cloud_instance(cls) -> bool:
        """
        Check if the configured YouTrack instance is a cloud instance.

        Returns:
            True if cloud instance, False if self-hosted
        """
        # If URL is explicitly provided, it's self-hosted
        # No URL = cloud by default
        return not cls.YOUTRACK_URL

    @classmethod
    def get_base_url(cls) -> str:
        """
        Get the base URL for the YouTrack instance API.

        Priority:
        1. If YOUTRACK_URL is set - use it (self-hosted mode)
        2. If only token is set - extract workspace from token (cloud mode)
        3. If token doesn't contain workspace - use YOUTRACK_WORKSPACE env var

        Returns:
            Base URL for the YouTrack API
        """
        # Priority 1: Explicit URL (self-hosted)
        if cls.YOUTRACK_URL:
            # Ensure URL has /api suffix
            url = cls.YOUTRACK_URL.rstrip('/')
            if not url.endswith('/api'):
                url += '/api'
            return url

        # Priority 2: Extract from token (cloud)
        if cls.YOUTRACK_API_TOKEN:
            # Token format: perm:username.workspace.12345... (standard cloud format)
            if cls.YOUTRACK_API_TOKEN.startswith('perm:'):
                token_parts = cls.YOUTRACK_API_TOKEN.split('.')
                if len(token_parts) >= 3:
                    # Extract workspace from token (second part after perm:username)
                    workspace = token_parts[1]
                    return f'https://{workspace}.youtrack.cloud/api'

            # Token format: perm-base64.base64.hash (needs YOUTRACK_WORKSPACE)
            if cls.YOUTRACK_API_TOKEN.startswith('perm-'):
                workspace_env = os.getenv('YOUTRACK_WORKSPACE')
                if workspace_env:
                    return f'https://{workspace_env}.youtrack.cloud/api'

                # Error: perm- token needs workspace
                raise ValueError(
                    '\n🔧 YouTrack Configuration Required\n'
                    '\n'
                    'Your token format (perm-...) requires workspace specification.\n'
                    '\n'
                    'Please set YOUTRACK_WORKSPACE:\n'
                    '   export YOUTRACK_WORKSPACE="yourworkspace"\n'
                    '\n'
                    'Or provide full URL:\n'
                    '   export YOUTRACK_URL="https://yourworkspace.youtrack.cloud"\n'
                )

        # No token provided
        raise ValueError(
            '\n🔧 YouTrack Configuration Required\n'
            '\n'
            'Please set your YouTrack API token:\n'
            '\n'
            '1. For YouTrack Cloud (recommended):\n'
            '   export YOUTRACK_API_TOKEN="perm:username.workspace.xxxxx"\n'
            '\n'
            '2. For self-hosted YouTrack:\n'
            '   export YOUTRACK_URL="https://youtrack.company.com"\n'
            '   export YOUTRACK_API_TOKEN="perm:xxxxx"\n'
            '\n'
            'Get your token from YouTrack: Profile → Account Security → New token\n'
            '\n'
            'See README.md for detailed setup instructions.'
        )


# Create a global config instance
config = Config()
