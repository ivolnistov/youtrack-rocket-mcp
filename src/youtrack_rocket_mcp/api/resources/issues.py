"""
YouTrack Issues API client.
"""

import json
import logging

import httpx
from pydantic import BaseModel, Field

from youtrack_rocket_mcp.api.client import YouTrackAPIError, YouTrackClient
from youtrack_rocket_mcp.api.field_cache import (
    extract_field_types_from_issues,
    field_cache,
    get_field_types_from_project,
)
from youtrack_rocket_mcp.api.resources.projects import ProjectsClient
from youtrack_rocket_mcp.api.types import CustomFieldData, FieldTypes, FieldValue, JSONDict

logger = logging.getLogger(__name__)


class Issue(BaseModel):
    """Model for a YouTrack issue."""

    id: str
    idReadable: str | None = None  # Readable ID like ITSFT-123  # noqa: N815
    summary: str | None = None
    description: str | None = None
    created: int | None = None
    updated: int | None = None
    project: JSONDict = Field(default_factory=dict)
    reporter: JSONDict | None = None
    assignee: JSONDict | None = None
    custom_fields: list[JSONDict] = Field(default_factory=list, alias='customFields')

    model_config = {
        'extra': 'allow',  # Allow extra fields from the API
        'populate_by_name': True,  # Allow population by field name (helps with aliases)
    }


class IssuesClient:
    """Client for interacting with YouTrack Issues API."""

    def __init__(self, client: YouTrackClient):
        """
        Initialize the Issues API client.

        Args:
            client: The YouTrack API client
        """
        self.client = client

    def _raise_api_error(self, message: str, status_code: int, response: httpx.Response) -> None:
        """Raise a YouTrackAPIError with the given details."""
        raise YouTrackAPIError(message, status_code, response)

    async def _resolve_project_id(self, project_id: str) -> tuple[str, str]:
        """
        Resolve project short name to ID if needed.

        Returns:
            Tuple of (resolved_project_id, original_project_id)
        """
        original_project_id = project_id
        if project_id and not project_id.startswith('0-'):
            logger.info(f"Attempting to resolve project short name '{project_id}'")
            projects_client = ProjectsClient(self.client)
            project = await projects_client.get_project_by_name(project_id)
            if project:
                project_id = project.id
                logger.info(f"Resolved project '{original_project_id}' to ID: {project_id}")
            else:
                logger.warning(f"Could not resolve project '{project_id}', will try as-is")
        return project_id, original_project_id

    async def _get_field_types(self, project_id: str, original_project_id: str) -> FieldTypes | None:
        """Get field types for a project."""
        cached_field_types = field_cache.get_field_types(project_id) if project_id else None

        if not cached_field_types:
            cached_field_types = await get_field_types_from_project(self.client, project_id)
            if cached_field_types:
                logger.info(f'Got {len(cached_field_types)} field types from project configuration')
                field_cache.set_field_types(project_id, cached_field_types)
            else:
                cached_field_types = await self._fetch_field_types_from_issues(project_id, original_project_id)

        return cached_field_types

    async def _fetch_field_types_from_issues(self, project_id: str, original_project_id: str) -> FieldTypes | None:
        """Fetch field types from sample issues."""
        try:
            logger.info('No field types from project, trying to fetch from issues')
            query = f'project: {original_project_id}' if not original_project_id.startswith('0-') else 'project: ITSFT'
            sample_issues = await self.client.get(
                'issues',
                params={
                    'query': query,
                    '$top': 5,
                    'fields': 'customFields(id,name,value,$type,projectCustomField(id))',
                },
            )
            if sample_issues:
                cached_field_types = extract_field_types_from_issues(sample_issues)
                if project_id and cached_field_types:
                    field_cache.set_field_types(project_id, cached_field_types)
                    logger.info(f'Cached {len(cached_field_types)} field types from issues')
                return cached_field_types
        except Exception as e:
            logger.warning(f'Could not fetch sample issues for field type analysis: {e}')
        return None

    def _format_custom_field(self, field_key: str, field_value: FieldValue, field_type: str | None) -> JSONDict:
        """Format a single custom field for the API."""
        field_entry = {'name': field_key}

        if not field_type:
            logger.warning(f"No type found for field '{field_key}', using default SingleEnumIssueCustomField")
            field_type = 'SingleEnumIssueCustomField'

        field_entry['$type'] = field_type

        if isinstance(field_value, dict) and '$type' in field_value:
            field_entry.update(field_value)
        elif field_type == 'SingleUserIssueCustomField':
            field_entry['value'] = {'login': field_value} if isinstance(field_value, str) else field_value  # type: ignore[assignment]
        elif field_type in ['SingleEnumIssueCustomField', 'StateIssueCustomField']:
            field_entry['value'] = {'name': field_value} if isinstance(field_value, str) else field_value  # type: ignore[assignment]
        elif field_type in [
            'DateIssueCustomField',
            'PeriodIssueCustomField',
            'SimpleIssueCustomField',
            'TextIssueCustomField',
        ] or field_type.startswith('Multi'):
            field_entry['value'] = field_value
        else:
            field_entry['value'] = {'name': field_value} if isinstance(field_value, str) else field_value  # type: ignore[assignment]

        return field_entry

    async def get_issue(self, issue_id: str) -> Issue:
        """
        Get an issue by ID.

        Args:
            issue_id: The issue ID or readable ID (e.g., PROJECT-123)

        Returns:
            The issue data
        """
        response = await self.client.get(f'issues/{issue_id}')

        # If the response doesn't have all needed fields, fetch more details
        if isinstance(response, dict) and response.get('$type') == 'Issue' and 'summary' not in response:
            # Get additional fields we need
            fields = 'summary,description,created,updated,project,reporter,assignee,customFields'
            detailed_response = await self.client.get(f'issues/{issue_id}?fields={fields}')
            return Issue.model_validate(detailed_response)

        return Issue.model_validate(response)

    async def create_issue(
        self,
        project_id: str,
        summary: str,
        description: str | None = None,
        additional_fields: CustomFieldData | None = None,
    ) -> Issue:
        """
        Create a new issue with improved custom field handling.

        Args:
            project_id: The ID or short name of the project (e.g., 'ITSFT' or '0-167')
            summary: The issue summary
            description: The issue description
            additional_fields: Additional fields to set on the issue. Can include:
                - Custom field IDs as keys (e.g., {'93-1507': 'Bender Bot'})
                - Custom field names as keys (e.g., {'Subsystem': 'Bender Bot'})
                - Complex values for bundle fields (e.g., {'Subsystem': {'name': 'Bender Bot'}})

        Returns:
            The created issue data

        Note:
            For custom fields, you can provide values in several formats:
            1. Simple string value: {'Subsystem': 'Bender Bot'}
            2. Object with name: {'Subsystem': {'name': 'Bender Bot'}}
            3. Object with ID: {'Subsystem': {'id': '100-561'}}
            4. By field ID: {'93-1507': 'Bender Bot'}

            The method will attempt to resolve project short names to IDs automatically.
        """
        # Validate input data
        if not project_id:
            raise ValueError('Project ID is required')
        if not summary:
            raise ValueError('Summary is required')

        # Resolve project ID
        project_id, original_project_id = await self._resolve_project_id(project_id)

        # Format request data
        data = {'project': {'id': project_id}, 'summary': summary}
        if description:
            data['description'] = description

        # Process additional fields
        if additional_fields:
            cached_field_types = await self._get_field_types(project_id, original_project_id)
            custom_fields_array = []

            for field_key, field_value in additional_fields.items():
                if field_value is None:
                    continue

                field_type = None
                if cached_field_types and field_key in cached_field_types:
                    field_type = cached_field_types[field_key].get('type')
                    logger.debug(f"Using cached type for field '{field_key}': {field_type}")

                field_entry = self._format_custom_field(field_key, field_value, field_type)
                custom_fields_array.append(field_entry)

            if custom_fields_array:
                data['customFields'] = custom_fields_array  # type: ignore[assignment]

        # Create the issue
        try:
            logger.info(
                f"Creating issue in project '{original_project_id}' (ID: {project_id}) with data: {json.dumps(data)}"
            )

            # Request full fields in response
            fields = (
                'id,idReadable,summary,description,created,updated,'
                'project(id,name,shortName),reporter(id,login,name),customFields(id,name,value)'
            )

            response = await self.client.client.post(
                f'{self.client.base_url}/issues?fields={fields}',
                json=data,
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
            )

            if response.status_code >= 400:
                self._handle_create_error(response, original_project_id)

            # Process response
            try:
                result = response.json()

                # Check if it's an error response with issue_id (workflow creates draft)
                if 'error_issue_id' in result:
                    issue_id = result['error_issue_id']
                    logger.info(f'Issue created (draft/incomplete): {issue_id}')
                    # Return an Issue object preserving input data
                    return Issue(
                        id=issue_id,
                        summary=summary,
                        description=description,
                        project={'id': project_id},
                        custom_fields=[],
                    )

                # Normal successful response
                issue_id = result.get('id', result.get('idReadable', 'unknown'))
                logger.info(f'Successfully created issue: {issue_id}')

                # Try to parse with model, fallback to minimal object
                try:
                    return Issue.model_validate(result)
                except Exception:
                    return Issue(
                        id=issue_id,
                        summary=summary or result.get('summary', ''),
                        description=description or result.get('description'),
                        project={'id': project_id},
                    )
            except Exception:
                logger.exception('Error parsing response')
                # Still return something if we have a response
                return Issue(
                    id=f'response-{response.status_code}', summary=summary or 'Created', project={'id': project_id}
                )

        except Exception:
            logger.exception(f'Error creating issue, Data: {data}')
            raise

    def _handle_create_error(self, response: httpx.Response, original_project_id: str) -> None:
        """Handle error response from issue creation."""
        error_msg = f'Error creating issue: {response.status_code}'
        try:
            error_content = response.json()
            error_msg += f' - {json.dumps(error_content)}'

            # Provide helpful error messages for common issues
            if 'Field required' in str(error_content):
                error_field = error_content.get('error_field', 'Unknown')
                error_msg += f"\n\nHint: The field '{error_field}' is required for this project."
                error_msg += '\nUse get_project_detailed() to see all required fields and their possible values.'
            elif 'Project not found' in str(error_content):
                error_msg += f"\n\nHint: Project '{original_project_id}' was not found."
                error_msg += '\nUse get_projects() to see available projects.'
                error_msg += "\nNote: Use the project short name (e.g., 'ITSFT') not the full name."
        except Exception:
            error_msg += f' - {response.text}'

        logger.error(error_msg)
        self._raise_api_error(error_msg, response.status_code, response)

    async def update_issue(
        self,
        issue_id: str,
        summary: str | None = None,
        description: str | None = None,
        additional_fields: CustomFieldData | None = None,
    ) -> Issue:
        """
        Update an existing issue.

        Args:
            issue_id: The issue ID or readable ID
            summary: The new issue summary
            description: The new issue description
            additional_fields: Additional fields to update

        Returns:
            The updated issue data
        """
        data = {}

        if summary is not None:
            data['summary'] = summary

        if description is not None:
            data['description'] = description

        if additional_fields:
            data.update(additional_fields)

        if not data:
            # Nothing to update
            return await self.get_issue(issue_id)

        response = await self.client.post(f'issues/{issue_id}', data=data)
        return Issue.model_validate(response)

    async def search_issues(self, query: str, limit: int = 10) -> list[Issue]:
        """
        Search for issues using YouTrack query language.

        Args:
            query: The search query
            limit: Maximum number of issues to return

        Returns:
            List of matching issues
        """
        # Request additional fields to ensure we get summary
        fields = 'id,summary,description,created,updated,project,reporter,assignee,customFields'
        params = {'query': query, '$top': limit, 'fields': fields}
        response = await self.client.get('issues', params=params)

        issues = []
        for item in response:
            try:
                issues.append(Issue.model_validate(item))
            except Exception as e:
                # Log the error but continue processing other issues
                logger.warning(f'Failed to validate issue: {e!s}')

        return issues

    async def add_comment(self, issue_id: str, text: str) -> JSONDict:
        """
        Add a comment to an issue.

        Args:
            issue_id: The issue ID or readable ID
            text: The comment text

        Returns:
            The created comment data
        """
        data = {'text': text}
        return await self.client.post(f'issues/{issue_id}/comments', data=data)
