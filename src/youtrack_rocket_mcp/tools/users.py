import json
import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.resources.users import UsersClient
from youtrack_rocket_mcp.api.types import ToolRegistry

logger = logging.getLogger(__name__)


class UserTools:
    """User-related MCP tools."""

    def __init__(self):
        """Initialize the user tools."""
        self.client = YouTrackClient()
        self.users_api = UsersClient(self.client)

    async def get_current_user(self) -> str:
        """
        Get information about the currently authenticated user.

        FORMAT: get_current_user()

        Returns:
            JSON string with current user information
        """
        try:
            user = await self.users_api.get_current_user()
            return json.dumps(user.model_dump(), indent=2)
        except Exception as e:
            logger.exception('Error getting current user')
            return json.dumps({'error': str(e)})

    async def get_user(self, user_id: str | None = None, user: str | None = None) -> str:
        """
        Get information about a specific user.

        FORMAT: get_user(user_id="1-1")

        Args:
            user_id: The user ID
            user: Alternative parameter name for user_id

        Returns:
            JSON string with user information
        """
        try:
            # Use either user_id or user parameter
            user_identifier = user_id or user
            if not user_identifier:
                return json.dumps({'error': 'User ID is required'})

            user_obj = await self.users_api.get_user(user_identifier)

            # Handle both Pydantic models and dictionaries in the response
            if user_obj is None:
                return json.dumps({'error': 'User not found'})

            result = user_obj.model_dump() if hasattr(user_obj, 'model_dump') else user_obj

            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f'Error getting user {user_id or user}')
            return json.dumps({'error': str(e)})

    async def get_user_by_login(self, login: str) -> str:
        """
        Get a user by their login name.

        FORMAT: get_user_by_login(login="johndoe")

        Args:
            login: The user's login name

        Returns:
            JSON string with user information
        """
        try:
            if not login:
                return json.dumps({'error': 'Login is required'})

            user = await self.users_api.get_user_by_login(login)

            # Handle both Pydantic models and dictionaries in the response
            if user is None:
                return json.dumps({'error': 'User not found'})

            result = user.model_dump() if hasattr(user, 'model_dump') else user

            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f'Error getting user with login {login}')
            return json.dumps({'error': str(e)})

    async def get_user_groups(self, user_id: str | None = None, user: str | None = None) -> str:
        """
        Get groups for a user.

        FORMAT: get_user_groups(user_id="1-1")

        Args:
            user_id: The user ID
            user: Alternative parameter name for user_id

        Returns:
            JSON string with user groups
        """
        try:
            # Use either user_id or user parameter
            user_identifier = user_id or user
            if not user_identifier:
                return json.dumps({'error': 'User ID is required'})

            groups = await self.users_api.get_user_groups(user_identifier)

            # Handle various response formats safely
            if groups is None:
                return json.dumps([])

            # If it's a dictionary (direct API response)
            if isinstance(groups, dict):
                return json.dumps(groups, indent=2)

            # If it's a list of objects
            try:
                result = []
                # Try to iterate, but handle errors safely
                for group in groups:
                    if hasattr(group, 'model_dump'):
                        result.append(group.model_dump())
                    elif isinstance(group, dict):
                        result.append(group)
                    else:
                        # Last resort: convert to string
                        result.append(str(group))
                return json.dumps(result, indent=2)
            except Exception as e:
                # If we can't iterate, return the raw string representation
                logger.warning(f'Could not process groups response: {e!s}')
                return json.dumps({'groups': str(groups)})
        except Exception as e:
            logger.exception(f'Error getting groups for user {user_id or user}')
            return json.dumps({'error': str(e)})

    async def search_users(self, query: str, limit: int = 10) -> str:
        """
        Search for users using YouTrack query.

        FORMAT: search_users(query="John", limit=10)

        Args:
            query: The search query
            limit: Maximum number of users to return (default: 10)

        Returns:
            JSON string with matching users
        """
        try:
            users = await self.users_api.search_users(query, limit=limit)
            return json.dumps([u.model_dump() for u in users], indent=2)
        except Exception as e:
            logger.exception(f'Error searching users with query {query}')
            return json.dumps({'error': str(e)})

    def close(self) -> None:
        """Close the API client."""
        self.client.close()

    def get_tool_definitions(self) -> ToolRegistry:
        """
        Get the definitions of all user tools.

        Returns:
            Dictionary mapping tool names to their configuration
        """
        return {
            'get_current_user': {
                'function': self.get_current_user,
                'description': 'Get information about the currently authenticated user. FORMAT: get_current_user()',
                'parameters': {},
            },
            'get_user': {
                'function': self.get_user,
                'description': 'Get information about a specific user. FORMAT: get_user(user_id="1-1")',
                'parameters': {'user_id': 'The user ID', 'user': 'Alternative parameter name for user_id'},
            },
            'get_user_by_login': {
                'function': self.get_user_by_login,
                'description': 'Get a user by their login name. FORMAT: get_user_by_login(login="johndoe")',
                'parameters': {'login': "The user's login name"},
            },
            'get_user_groups': {
                'function': self.get_user_groups,
                'description': 'Get groups for a user. FORMAT: get_user_groups(user_id="1-1")',
                'parameters': {'user_id': 'The user ID', 'user': 'Alternative parameter name for user_id'},
            },
            'search_users': {
                'function': self.search_users,
                'description': 'Search for users using YouTrack query. FORMAT: search_users(query="John", limit=10)',
                'parameters': {
                    'query': 'The search query',
                    'limit': 'Maximum number of users to return (optional, default: 10)',
                },
            },
        }


def register_user_tools(mcp: FastMCP) -> None:
    """Register user tools with the MCP server."""
    user_tools = UserTools()

    @mcp.tool()
    async def get_user(
        user_id: Annotated[str | None, Field(description='User ID to retrieve information for')] = None,
        user: Annotated[str | None, Field(description='Alternative parameter name for user ID')] = None,
    ) -> str:
        """Fetch user details by ID. Use to get user's email, groups, or full name. Returns user profile."""
        return await user_tools.get_user(user_id, user)

    @mcp.tool()
    async def get_user_by_login(
        login: Annotated[str, Field(description='User login/username to retrieve information for')],
    ) -> str:
        """Find user by login name. Use when you have username not ID. Returns user details."""
        return await user_tools.get_user_by_login(login)

    @mcp.tool()
    async def search_users(
        query: Annotated[str, Field(description='Search query for user name or login')],
        limit: Annotated[int, Field(description='Maximum number of users to return')] = 10,
    ) -> str:
        """Search users by name or login. Use to find team members or assignees. Returns matching users."""
        return await user_tools.search_users(query, limit)

    @mcp.tool()
    async def get_current_user() -> str:
        """Get current API user. Use to check authentication or get 'me' for searches. Returns authenticated user."""
        return await user_tools.get_current_user()
