"""
Base client for YouTrack REST API using httpx for async support.
"""

import asyncio
import logging
import random
from types import TracebackType
from typing import TYPE_CHECKING, Any

from youtrack_rocket_mcp.api.types import JSONDict, JSONValue, QueryParams

if TYPE_CHECKING:
    pass

import httpx
from pydantic import BaseModel, ConfigDict

from youtrack_rocket_mcp.config import config

logger = logging.getLogger(__name__)


class YouTrackAPIError(Exception):
    """Base exception for YouTrack API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: httpx.Response | None = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class RateLimitError(YouTrackAPIError):
    """Exception for API rate limiting errors."""


class ResourceNotFoundError(YouTrackAPIError):
    """Exception for 404 Not Found errors."""


class AuthenticationError(YouTrackAPIError):
    """Exception for authentication errors."""


class PermissionDeniedError(YouTrackAPIError):
    """Exception for permission-related errors."""


class ValidationError(YouTrackAPIError):
    """Exception for validation errors in API requests."""


class ServerError(YouTrackAPIError):
    """Exception for server-side errors."""


class YouTrackModel(BaseModel):
    """Base model for YouTrack API resources."""

    model_config = ConfigDict(
        extra='allow',  # Allow extra fields in the model
        populate_by_name=True,  # Allow population by field name
    )

    id: str


class YouTrackClient:
    """Async client for YouTrack REST API using httpx."""

    def __init__(
        self,
        base_url: str | None = None,
        api_token: str | None = None,
        verify_ssl: bool | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize YouTrack API client.

        Args:
            base_url: YouTrack instance URL, defaults to config.get_base_url()
            api_token: API token for authentication, defaults to config.YOUTRACK_API_TOKEN
            verify_ssl: Whether to verify SSL certificates, defaults to config.VERIFY_SSL
            max_retries: Maximum number of retries for transient errors
            retry_delay: Initial delay between retries in seconds (increases exponentially)
        """
        self.base_url = base_url or config.get_base_url()
        self.api_token = api_token or config.YOUTRACK_API_TOKEN
        self.verify_ssl = verify_ssl if verify_ssl is not None else config.VERIFY_SSL
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Validate required configuration
        if not self.api_token:
            raise ValueError('API token is required')

        # HTTP client for async requests
        self.client = httpx.AsyncClient(
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'YouTrack-Rocket-MCP/1.0.0',
            },
            verify=self.verify_ssl,
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

        logger.info(f'Initialized YouTrack API client for {self.base_url}')

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: QueryParams | None = None,
        data: JSONDict | None = None,
        **kwargs: Any,
    ) -> JSONValue:
        """
        Make an HTTP request to the YouTrack API with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            data: Request body data
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response

        Raises:
            YouTrackAPIError: If the request fails after all retries
        """
        url = f'{self.base_url}/{endpoint}'

        # Handle JSON data
        if data is not None:
            kwargs['json'] = data

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, url, params=params, **kwargs)

                # Handle different status codes
                if response.status_code in {200, 201}:
                    return response.json()
                if response.status_code == 204:
                    return {}  # No content
                if response.status_code == 401:
                    raise AuthenticationError(
                        'Authentication failed. Check your API token.', response.status_code, response
                    )
                if response.status_code == 403:
                    raise PermissionDeniedError(
                        f'Permission denied for {method} {endpoint}', response.status_code, response
                    )
                if response.status_code == 404:
                    raise ResourceNotFoundError(f'Resource not found: {endpoint}', response.status_code, response)
                if response.status_code == 429:
                    # Rate limiting - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    if attempt < self.max_retries - 1:
                        logger.warning(f'Rate limited. Waiting {retry_after} seconds before retry...')
                        await asyncio.sleep(retry_after)
                        continue
                    raise RateLimitError(f'Rate limit exceeded. Retry after {retry_after} seconds.', 429, response)
                if response.status_code == 422:
                    # Validation error
                    error_details = response.json() if response.text else {}
                    raise ValidationError(f'Validation error: {error_details}', response.status_code, response)
                if response.status_code >= 500:
                    # Server error - retry with exponential backoff
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2**attempt) + random.uniform(0, 1)
                        logger.warning(f'Server error {response.status_code}. Retrying in {delay:.2f} seconds...')
                        await asyncio.sleep(delay)
                        continue
                    raise ServerError(f'Server error: {response.status_code}', response.status_code, response)
                # Unexpected status code
                raise YouTrackAPIError(
                    f'Unexpected status code {response.status_code}: {response.text}', response.status_code, response
                )

            except httpx.ConnectError as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(f'Connection error: {e}. Retrying in {delay:.2f} seconds...')
                    await asyncio.sleep(delay)
                    continue
                raise YouTrackAPIError(f'Connection failed after {self.max_retries} attempts: {e}') from e
            except httpx.TimeoutException as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(f'Request timeout. Retrying in {delay:.2f} seconds...')
                    await asyncio.sleep(delay)
                    continue
                raise YouTrackAPIError(f'Request timeout after {self.max_retries} attempts: {e}') from e
            except httpx.HTTPError as e:
                raise YouTrackAPIError(f'HTTP error: {e}') from e

        # Should never reach here
        raise YouTrackAPIError(f'Request failed after {self.max_retries} attempts')

    async def get(self, endpoint: str, params: QueryParams | None = None, **kwargs: Any) -> JSONValue:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            **kwargs: Additional request arguments

        Returns:
            Parsed JSON response
        """
        return await self._make_request('GET', endpoint, params=params, **kwargs)

    async def post(self, endpoint: str, data: JSONDict | None = None, **kwargs: Any) -> JSONValue:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional request arguments

        Returns:
            Parsed JSON response
        """
        return await self._make_request('POST', endpoint, data=data, **kwargs)

    async def put(self, endpoint: str, data: JSONDict | None = None, **kwargs: Any) -> JSONValue:
        """
        Make a PUT request.

        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional request arguments

        Returns:
            Parsed JSON response
        """
        return await self._make_request('PUT', endpoint, data=data, **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> JSONValue:
        """
        Make a DELETE request.

        Args:
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            Parsed JSON response
        """
        return await self._make_request('DELETE', endpoint, **kwargs)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> 'YouTrackClient':
        """Async context manager entry."""
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """Async context manager exit."""
        await self.close()
