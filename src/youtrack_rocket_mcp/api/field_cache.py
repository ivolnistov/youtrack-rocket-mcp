"""
Field type caching for YouTrack custom fields.
Gets actual field $type values from existing issues in the project.
"""

import logging
from datetime import datetime, timedelta

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.types import FieldTypes, JSONList

logger = logging.getLogger(__name__)


class FieldTypeCache:
    """Cache for project custom field types to avoid repeated API calls."""

    def __init__(self, cache_duration_minutes: int = 60):
        """
        Initialize the field type cache.

        Args:
            cache_duration_minutes: How long to keep cached data (default: 60 minutes)
        """
        self._cache: dict[str, FieldTypes] = {}
        self._cache_timestamps: dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=cache_duration_minutes)

    def _is_cache_valid(self, project_id: str) -> bool:
        """Check if cached data for a project is still valid."""
        if project_id not in self._cache_timestamps:
            return False

        age = datetime.now() - self._cache_timestamps[project_id]
        return age < self.cache_duration

    def get_field_types(self, project_id: str) -> FieldTypes | None:
        """
        Get cached field types for a project.

        Args:
            project_id: The project ID

        Returns:
            Dictionary mapping field names to their type information, or None if not cached
        """
        if self._is_cache_valid(project_id):
            logger.debug(f'Using cached field types for project {project_id}')
            return self._cache.get(project_id)
        return None

    def set_field_types(self, project_id: str, field_types: FieldTypes) -> None:
        """
        Cache field types for a project.

        Args:
            project_id: The project ID
            field_types: Dictionary mapping field names to their type information
        """
        self._cache[project_id] = field_types
        self._cache_timestamps[project_id] = datetime.now()
        logger.info(f'Cached field types for project {project_id}: {len(field_types)} fields')

    def clear_project_cache(self, project_id: str) -> None:
        """Clear cache for a specific project."""
        if project_id in self._cache:
            del self._cache[project_id]
            del self._cache_timestamps[project_id]
            logger.info(f'Cleared field type cache for project {project_id}')

    def clear_all_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info('Cleared all field type caches')


def extract_field_types_from_issues(issues: JSONList) -> FieldTypes:
    """
    Extract field types from actual issue data returned by the API.
    The API returns the actual $type for each custom field.

    Args:
        issues: List of issues from the API with customFields

    Returns:
        Dictionary mapping field names to their type information
    """
    field_info = {}

    for issue in issues:
        if not isinstance(issue, dict):
            continue
        custom_fields = issue.get('customFields', [])
        if not isinstance(custom_fields, list):
            continue

        for field in custom_fields:
            if not isinstance(field, dict):
                continue
            field_name = field.get('name')
            if not field_name:
                continue

            # Get the actual $type from the API response
            field_type = field.get('$type')
            if not field_type:
                logger.warning(f"Field '{field_name}' has no $type in API response")
                continue

            # Get projectCustomField info if available
            project_field = field.get('projectCustomField', {})
            field_id = project_field.get('id') or field.get('id')

            # Store field information
            if field_name not in field_info:
                field_info[field_name] = {
                    'type': field_type,
                    'id': field_id,
                    'projectCustomFieldId': project_field.get('id'),
                    'sample_value': field.get('value'),
                }
                logger.debug(f"Found field '{field_name}' with type: {field_type}")

    return field_info


async def get_field_types_from_project(client: YouTrackClient, project_id: str) -> FieldTypes | None:
    """
    Try to get field types directly from project configuration.

    Args:
        client: YouTrack API client
        project_id: Project ID

    Returns:
        Dictionary mapping field names to their type information, or None if failed
    """
    try:
        # Map ProjectCustomField $type to IssueCustomField $type
        type_mapping = {
            'EnumProjectCustomField': 'SingleEnumIssueCustomField',
            'StateProjectCustomField': 'StateIssueCustomField',
            'UserProjectCustomField': 'SingleUserIssueCustomField',
            'OwnedProjectCustomField': 'SingleOwnedIssueCustomField',
            'VersionProjectCustomField': 'SingleVersionIssueCustomField',
            'BuildProjectCustomField': 'SingleBuildIssueCustomField',
            'DateProjectCustomField': 'DateIssueCustomField',
            'PeriodProjectCustomField': 'PeriodIssueCustomField',
            'SimpleProjectCustomField': 'SimpleIssueCustomField',
            'TextProjectCustomField': 'TextIssueCustomField',
            'GroupProjectCustomField': 'SingleGroupIssueCustomField',
            'MultiEnumProjectCustomField': 'MultiEnumIssueCustomField',
            'MultiUserProjectCustomField': 'MultiUserIssueCustomField',
            'MultiVersionProjectCustomField': 'MultiVersionIssueCustomField',
        }

        # Try to get project custom fields with field names
        response = await client.get(
            f'admin/projects/{project_id}/customFields', params={'fields': 'id,field(name),canBeEmpty,$type'}
        )

        field_info = {}
        for field_data in response:
            field_id = field_data.get('id')
            project_type = field_data.get('$type')
            field_name = field_data.get('field', {}).get('name') if field_data.get('field') else None
            required = not field_data.get('canBeEmpty', True)

            if field_name and project_type:
                issue_type = type_mapping.get(project_type, 'SingleEnumIssueCustomField')
                field_info[field_name] = {
                    'type': issue_type,
                    'id': field_id,
                    'projectType': project_type,
                    'required': required,
                }
                logger.debug(f"Got field '{field_name}' from project: {project_type} -> {issue_type}")

    except Exception as e:
        logger.debug(f'Could not get field types from project: {e}')
        return None
    else:
        return field_info if field_info else None


# For backward compatibility, use the new function name
analyze_issue_fields = extract_field_types_from_issues


# Global cache instance
field_cache = FieldTypeCache()
