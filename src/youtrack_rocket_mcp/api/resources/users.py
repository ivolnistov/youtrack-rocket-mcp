"""
YouTrack Users API client.
"""

import logging

from pydantic import BaseModel

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.types import JSONList

logger = logging.getLogger(__name__)


class User(BaseModel):
    """Model for a YouTrack user."""

    id: str
    login: str | None = None
    name: str | None = None
    email: str | None = None
    jabber: str | None = None
    ring_id: str | None = None
    guest: bool | None = None
    online: bool | None = None
    banned: bool | None = None

    model_config = {
        'extra': 'allow',  # Allow extra fields from the API
        'populate_by_name': True,  # Allow population by field name (helps with aliases)
    }


class UsersClient:
    """Client for interacting with YouTrack Users API."""

    def __init__(self, client: YouTrackClient):
        """
        Initialize the Users API client.

        Args:
            client: The YouTrack API client
        """
        self.client = client

    async def get_current_user(self) -> User:
        """
        Get the current authenticated user.

        Returns:
            The user data
        """
        fields = 'id,login,name,email,jabber,ringId,guest,online,banned'
        response = await self.client.get(f'users/me?fields={fields}')
        return User.model_validate(response)

    async def get_user(self, user_id: str) -> User:
        """
        Get a user by ID.

        Args:
            user_id: The user ID

        Returns:
            The user data
        """
        fields = 'id,login,name,email,jabber,ringId,guest,online,banned'
        response = await self.client.get(f'users/{user_id}?fields={fields}')
        return User.model_validate(response)

    async def search_users(self, query: str, limit: int = 10) -> list[User]:
        """
        Search for users.

        Args:
            query: The search query (name, login, or email)
            limit: Maximum number of users to return

        Returns:
            List of matching users
        """
        # Request additional fields to ensure we get complete user data
        fields = 'id,login,name,email,jabber,ringId,guest,online,banned'
        params = {'query': query, '$top': limit, 'fields': fields}
        response = await self.client.get('users', params=params)

        users = []
        for item in response:
            try:
                users.append(User.model_validate(item))
            except Exception as e:
                # Log the error but continue processing other users
                logger.warning(f'Failed to validate user: {e!s}')

        return users

    async def get_user_by_login(self, login: str) -> User | None:
        """
        Get a user by login name.

        Args:
            login: The user login name

        Returns:
            The user data or None if not found
        """
        # Search for the exact login
        users = await self.search_users(f'login: {login}', limit=1)
        return users[0] if users else None

    async def get_user_groups(self, user_id: str) -> JSONList:
        """
        Get groups for a user.

        Args:
            user_id: The user ID

        Returns:
            List of group data
        """
        return await self.client.get(f'users/{user_id}/groups')

    async def check_user_permissions(self, user_id: str, permission: str) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user_id: The user ID
            permission: The permission to check

        Returns:
            True if the user has the permission, False otherwise
        """
        try:
            # YouTrack doesn't have a direct API for checking permissions,
            # but we can check user's groups and infer permissions
            groups = await self.get_user_groups(user_id)

            # Different permissions might require different group checks
            # This is a simplified example
            return any(permission.lower() in (group.get('name', '').lower() or '') for group in groups)
        except Exception:
            # If we can't determine, assume no permission
            return False
