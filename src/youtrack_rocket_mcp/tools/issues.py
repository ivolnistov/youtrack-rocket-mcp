"""
YouTrack Issue MCP tools.
"""

import json
import logging

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.resources.issues import IssuesClient
from youtrack_rocket_mcp.api.resources.projects import ProjectsClient
from youtrack_rocket_mcp.api.types import CustomFieldData, JSONDict
from youtrack_rocket_mcp.config import Config

logger = logging.getLogger(__name__)


class IssueTools:
    """Issue-related MCP tools."""

    def __init__(self):
        """Initialize the issue tools."""
        self.client = YouTrackClient()
        self.issues_api = IssuesClient(self.client)

    async def get_issue(self, issue_id: str) -> str:
        """
        Get information about a specific issue.

        FORMAT: get_issue(issue_id="DEMO-123") - You must use the exact parameter name 'issue_id'.

        Args:
            issue_id: The issue ID or readable ID (e.g., PROJECT-123)

        Returns:
            JSON string with issue information
        """
        try:
            # First try to get the issue data with explicit fields
            fields = (
                'id,idReadable,summary,description,created,updated,'
                'project(id,name,shortName),reporter(id,login,name),'
                'assignee(id,login,name),customFields(id,name,value)'
            )
            raw_issue = await self.client.get(f'issues/{issue_id}?fields={fields}')

            # If we got a minimal response, enhance it with default values
            if isinstance(raw_issue, dict) and raw_issue.get('$type') == 'Issue' and 'summary' not in raw_issue:
                raw_issue['summary'] = f'Issue {issue_id}'  # Provide a default summary

            # Return the raw issue data directly - avoid model validation issues
            return json.dumps(raw_issue, indent=2)

        except Exception as e:
            logger.exception(f'Error getting issue {issue_id}')
            return json.dumps({'error': str(e)})

    async def search_issues(self, query: str, limit: int = 10) -> str:
        """
        Search for issues using YouTrack query language.

        FORMAT: search_issues(query="project: DEMO #Unresolved", limit=10)

        Args:
            query: The search query
            limit: Maximum number of issues to return

        Returns:
            JSON string with matching issues
        """
        try:
            # Request with explicit fields to get complete data
            fields = (
                'id,idReadable,summary,description,created,updated,'
                'project(id,name,shortName),reporter(id,login,name),'
                'assignee(id,login,name),customFields(id,name,value)'
            )
            params = {'query': query, '$top': limit, 'fields': fields}
            raw_issues = await self.client.get('issues', params=params)

            # Return the raw issues data directly
            return json.dumps(raw_issues, indent=2)

        except Exception as e:
            logger.exception(f'Error searching issues with query: {query}')
            return json.dumps({'error': str(e)})

    def _extract_parameters_from_dict(
        self, project: dict
    ) -> tuple[str | None, str | None, str | None, CustomFieldData | None]:
        """Extract parameters from a dictionary format (backwards compatibility)."""
        description = project.get('description')
        summary = project.get('summary')
        custom_fields = project.get('custom_fields')
        project_name = project.get('project')
        return project_name, summary, description, custom_fields

    def _generate_issue_url(self, issue_id: str | None, readable_id: str | None) -> str | None:
        """Generate URL for an issue."""
        if not (issue_id or readable_id):
            return None

        base_url = Config.YOUTRACK_URL or 'https://youtrack.gaijin.team'

        # Prefer readable ID for cleaner URLs
        if readable_id:
            return f'{base_url}/issue/{readable_id}'
        if issue_id:
            return f'{base_url}/issue/{issue_id}'
        return None

    def _prepare_issue_response(
        self, issue, issue_url: str | None, summary: str, description: str | None, project: str
    ) -> JSONDict:
        """Prepare the response dictionary for an issue."""
        if hasattr(issue, 'model_dump'):
            result = issue.model_dump()
        elif isinstance(issue, dict):
            result = issue
        else:
            # Fallback - convert to dict
            result = {
                'id': getattr(issue, 'id', None),
                'summary': getattr(issue, 'summary', summary),
                'description': getattr(issue, 'description', description),
                'project': project,
                '$type': 'Issue',
            }

        # Add URL to result
        if issue_url and isinstance(result, dict):
            result['url'] = issue_url
            result['status'] = 'success'
            logger.info(f'Issue created successfully: {issue_url}')

        return result

    async def create_issue(
        self,
        project: str,
        summary: str,
        description: str | None = None,
        custom_fields: CustomFieldData | None = None,
    ) -> str:
        """
        Create a new issue in YouTrack.

        FORMAT: create_issue(
            project="DEMO",
            summary="Bug: Login not working",
            description="Details here",
            custom_fields={"subsystem": "Backend"}
        )

        Args:
            project: The ID or short name of the project
            summary: The issue summary
            description: The issue description (optional)
            custom_fields: Dictionary of custom field names and values (optional)

        Returns:
            JSON string with the created issue information
        """
        try:
            # Check if we got proper parameters
            logger.debug(f'Creating issue with: project={project}, summary={summary}, description={description}')

            # Handle kwargs format from MCP - this check is for backwards compatibility
            # In practice, project should always be a string at this point
            # type: ignore[unreachable]
            if isinstance(project, dict) and 'project' in project and 'summary' in project:  # type: ignore[unreachable]
                # Extract from dict if we got project as a JSON object
                logger.info('Detected project as a dictionary, extracting parameters')  # type: ignore[unreachable]
                project, summary, description, custom_fields = self._extract_parameters_from_dict(project)  # type: ignore[unreachable]

            # Ensure we have valid data
            if not project:
                return json.dumps({'error': 'Project is required', 'status': 'error'})
            if not summary:
                return json.dumps({'error': 'Summary is required', 'status': 'error'})

            # Check if project is a project ID or short name
            project_id = project
            if project and not project.startswith('0-'):
                # Try to get the project ID from the short name (e.g., "DEMO")
                try:
                    logger.info(f'Looking up project ID for: {project}')
                    projects_api = ProjectsClient(self.client)
                    project_obj = await projects_api.get_project_by_name(project)
                    if project_obj:
                        logger.info(f'Found project {project_obj.name} with ID {project_obj.id}')
                        project_id = project_obj.id
                    else:
                        logger.warning(f'Project not found: {project}')
                        return json.dumps({'error': f'Project not found: {project}', 'status': 'error'})
                except Exception as e:
                    logger.warning(f'Error finding project: {e!s}')
                    return json.dumps({'error': f'Error finding project: {e!s}', 'status': 'error'})

            logger.info(f'Creating issue in project {project_id}: {summary}')

            # Prepare additional fields including custom fields
            additional_fields = {}
            if custom_fields:
                # The new API handles custom fields directly, so we just pass them through
                # The API will handle field name resolution and format conversion
                additional_fields = custom_fields
                logger.info(f'Passing custom fields to API: {custom_fields}')

            # Call the API client to create the issue
            try:
                issue = await self.issues_api.create_issue(project_id, summary, description, additional_fields)

                # Check if we got an issue with an ID
                if isinstance(issue, dict) and issue.get('error'):
                    # Handle error returned as a dict
                    return json.dumps(issue)

                # Get issue ID and readable ID for link generation
                issue_id = None
                readable_id = None

                if hasattr(issue, 'id'):
                    issue_id = issue.id
                    if hasattr(issue, 'idReadable'):
                        readable_id = issue.idReadable
                elif isinstance(issue, dict):
                    issue_id = issue.get('id')
                    readable_id = issue.get('idReadable')

                # Generate issue URL
                issue_url = self._generate_issue_url(issue_id, readable_id)

                # Prepare response with issue data and URL
                result = self._prepare_issue_response(issue, issue_url, summary, description, project)

                return json.dumps(result, indent=2)
            except Exception as e:
                error_msg = str(e)
                if hasattr(e, 'response') and e.response:
                    try:
                        # Try to get detailed error message from response
                        error_content = e.response.content.decode('utf-8', errors='replace')
                        error_msg = f'{error_msg} - {error_content}'
                    except Exception:
                        pass
                logger.exception(f'API error creating issue: {error_msg}')
                return json.dumps({'error': error_msg, 'status': 'error'})

        except Exception as e:
            logger.exception(f'Error creating issue in project {project}')
            return json.dumps({'error': str(e), 'status': 'error'})

    async def add_comment(self, issue_id: str, text: str) -> str:
        """
        Add a comment to an issue.

        FORMAT: add_comment(issue_id="DEMO-123", text="This is my comment")

        Args:
            issue_id: The issue ID or readable ID
            text: The comment text

        Returns:
            JSON string with the result
        """
        try:
            result = await self.issues_api.add_comment(issue_id, text)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f'Error adding comment to issue {issue_id}')
            return json.dumps({'error': str(e)})

    def close(self) -> None:
        """Close the API client."""
        self.client.close()

    async def get_issue_raw(self, issue_id: str) -> str:
        """
        Get raw information about a specific issue, bypassing the Pydantic model.

        FORMAT: get_issue_raw(issue_id="DEMO-123")

        Args:
            issue_id: The issue ID or readable ID

        Returns:
            Raw JSON string with the issue data
        """
        try:
            raw_issue = await self.client.get(f'issues/{issue_id}')
            return json.dumps(raw_issue, indent=2)
        except Exception as e:
            logger.exception(f'Error getting raw issue {issue_id}')
            return json.dumps({'error': str(e)})
