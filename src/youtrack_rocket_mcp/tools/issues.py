"""
YouTrack Issue MCP tools.
"""

import asyncio
import json
import logging
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.resources.issues import IssuesClient
from youtrack_rocket_mcp.api.resources.projects import ProjectsClient
from youtrack_rocket_mcp.api.resources.search import SearchClient
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
                'assignee(id,login,name),customFields(id,name,value(id,name,login,text,localizedName))'
            )
            raw_issue = await self.client.get(f'issues/{issue_id}?fields={fields}')

            # If we got a minimal response, enhance it with default values
            if isinstance(raw_issue, dict) and raw_issue.get('$type') == 'Issue' and 'summary' not in raw_issue:
                raw_issue['summary'] = f'Issue {issue_id}'  # Provide a default summary

            # Format custom fields if present
            if isinstance(raw_issue, dict) and 'customFields' in raw_issue:
                raw_issue['custom_fields'] = SearchClient.format_custom_fields(raw_issue['customFields'])
                # Remove original customFields - keep only formatted version
                del raw_issue['customFields']

            # Return the raw issue data directly - avoid model validation issues
            return json.dumps(raw_issue, indent=2)

        except Exception as e:
            logger.exception(f'Error getting issue {issue_id}')
            return json.dumps({'error': str(e)})

    async def search_issues(self, query: str, limit: int = 100) -> str:
        """
        Search for issues using YouTrack query language (simplified version).
        Returns only idReadable and summary for quick overview.

        FORMAT: search_issues(query="project: DEMO #Unresolved", limit=100)

        Args:
            query: The search query
            limit: Maximum number of issues to return

        Returns:
            JSON string with issue IDs and summaries
        """
        try:
            # Request only minimal fields for quick overview
            fields = 'idReadable,summary'
            params = {'query': query, '$top': limit, 'fields': fields}
            raw_issues = await self.client.get('issues', params=params)

            # Get total count of matching issues using the count endpoint
            total_count = len(raw_issues)
            if len(raw_issues) == limit:
                # There might be more, use the issuesGetter/count endpoint
                try:
                    count_response = await self.client.post('issuesGetter/count?fields=count', data={'query': query})
                    if isinstance(count_response, dict) and 'count' in count_response:
                        count_value = count_response['count']
                        # If count is -1, YouTrack is still counting, retry once
                        if count_value == -1:
                            await asyncio.sleep(0.5)
                            count_response = await self.client.post(
                                'issuesGetter/count?fields=count', data={'query': query}
                            )
                            count_value = count_response.get('count', -1)

                        if count_value >= 0:
                            total_count = count_value
                except Exception:
                    # Fallback to current count if request fails
                    total_count = len(raw_issues)

            # Create result with metadata
            result = {'total': total_count, 'shown': len(raw_issues), 'limit': limit, 'issues': raw_issues}

            if total_count > len(raw_issues):
                result['message'] = (
                    f'Showing {len(raw_issues)} of {total_count} total issues. Increase limit to see more.'
                )

            # Return the formatted issues data
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.exception(f'Error searching issues with query: {query}')
            return json.dumps({'error': str(e)})

    async def search_issues_detailed(
        self, query: str, limit: int = 30, custom_fields_filter: list[str] | None = None
    ) -> str:
        """
        Search for issues using YouTrack query language (detailed version).
        Returns full issue information including custom fields.

        FORMAT: search_issues_detailed(query="project: DEMO #Unresolved", limit=30, custom_fields_filter=["Priority", "State"])

        Args:
            query: The search query
            limit: Maximum number of issues to return
            custom_fields_filter: Optional list of custom field names to include. If None, all fields are included.

        Returns:
            JSON string with detailed issue information
        """
        try:
            # Request with explicit fields to get complete data (removed redundant project field)
            fields = (
                'id,idReadable,summary,description,created,updated,'
                'reporter(id,login,name),'
                'assignee(id,login,name),customFields(id,name,value(id,name,login,text,localizedName))'
            )
            params = {'query': query, '$top': limit, 'fields': fields}
            raw_issues = await self.client.get('issues', params=params)

            # Get total count of matching issues using the count endpoint
            total_count = len(raw_issues)
            if len(raw_issues) == limit:
                # There might be more, use the issuesGetter/count endpoint
                try:
                    count_response = await self.client.post('issuesGetter/count?fields=count', data={'query': query})
                    if isinstance(count_response, dict) and 'count' in count_response:
                        count_value = count_response['count']
                        # If count is -1, YouTrack is still counting, retry once
                        if count_value == -1:
                            await asyncio.sleep(0.5)
                            count_response = await self.client.post(
                                'issuesGetter/count?fields=count', data={'query': query}
                            )
                            count_value = count_response.get('count', -1)

                        if count_value >= 0:
                            total_count = count_value
                except Exception:
                    # Fallback to current count if request fails
                    total_count = len(raw_issues)

            # Format custom fields for each issue
            for issue in raw_issues:
                if isinstance(issue, dict) and 'customFields' in issue:
                    formatted_fields = SearchClient.format_custom_fields(issue['customFields'])

                    # Filter custom fields if filter is provided
                    if custom_fields_filter:
                        filtered_fields = {}
                        for field_name in custom_fields_filter:
                            if field_name in formatted_fields:
                                filtered_fields[field_name] = formatted_fields[field_name]
                        issue['custom_fields'] = filtered_fields
                    else:
                        issue['custom_fields'] = formatted_fields

                    # Remove original customFields - keep only formatted version
                    del issue['customFields']

            # Create result with metadata
            result = {'total': total_count, 'shown': len(raw_issues), 'limit': limit, 'issues': raw_issues}

            if total_count > len(raw_issues):
                result['message'] = (
                    f'Showing {len(raw_issues)} of {total_count} total issues. Increase limit to see more.'
                )

            # Return the formatted issues data
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.exception(f'Error searching issues with detailed query: {query}')
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

    async def execute_command(
        self, command: str, issues: list[str] | str, comment: str | None = None, silent: bool = False
    ) -> str:
        """
        Execute a YouTrack command on one or more issues.

        FORMAT: execute_command(
            command="for me state in progress",
            issues=["DEMO-123", "DEMO-124"],
            comment="Taking over these issues",
            silent=False
        )

        Common commands:
        - "for me" - assign to yourself
        - "state Fixed" - change state
        - "Priority Critical" - set priority
        - "tag Bug" - add tag
        - "assignee john.doe" - assign to user
        - "due date next week" - set due date

        Args:
            command: The YouTrack command to execute
            issues: Issue ID(s) or readable ID(s) - can be a string or list
            comment: Optional comment to add with the command
            silent: If True, no notifications will be sent

        Returns:
            JSON string with the result
        """
        try:
            # Ensure issues is a list
            if isinstance(issues, str):
                issues = [issues]

            # Build the request payload
            payload: dict[str, Any] = {'query': command, 'issues': [], 'silent': silent}

            # Format issues for the API (can use either id or idReadable)
            for issue in issues:
                # Check if it looks like a readable ID (contains hyphen)
                if '-' in issue and not issue.startswith('2-'):
                    payload['issues'].append({'idReadable': issue})
                else:
                    payload['issues'].append({'id': issue})

            # Add comment if provided
            if comment:
                payload['comment'] = comment

            logger.info(f'Executing command "{command}" on {len(issues)} issue(s)')

            # Execute the command via API
            # The API returns 200 OK with empty body on success (unless fields param is specified)
            # We still capture it to ensure the request completed successfully
            await self.client.post('commands', data=payload)

            # If we get here without exception, command was successful
            logger.info(f'Successfully executed command "{command}"')

            # Return success response
            result = {
                'status': 'success',
                'command': command,
                'issues_count': len(issues),
                'issues': issues,
                'silent': silent,
            }
            if comment:
                result['comment'] = comment

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.exception(f'Error executing command "{command}" on issues')
            return json.dumps({'error': str(e), 'command': command, 'issues': issues})

    async def close(self) -> None:
        """Close the API client."""
        await self.client.close()

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
            # Get all fields including raw customFields
            fields = (
                'id,idReadable,summary,description,created,updated,resolved,'
                'project(id,name,shortName),reporter(id,login,name),'
                'assignee(id,login,name),customFields(id,name,value($type,name,login,text,localizedName,id))'
            )
            raw_issue = await self.client.get(f'issues/{issue_id}?fields={fields}')
            # Return raw data without any formatting
            return json.dumps(raw_issue, indent=2)
        except Exception as e:
            logger.exception(f'Error getting raw issue {issue_id}')
            return json.dumps({'error': str(e)})


def register_issue_tools(mcp: FastMCP) -> None:
    """Register issue tools with the MCP server."""
    issue_tools = IssueTools()

    @mcp.tool()
    async def get_issue(
        issue_id: Annotated[str, Field(description='Issue ID (e.g., ITSFT-123 or 2-12345)')],
    ) -> str:
        """Retrieve complete issue details. Use to view bug reports, feature requests, or task status. Returns JSON with all issue fields."""
        return await issue_tools.get_issue(issue_id)

    @mcp.tool()
    async def get_issue_raw(
        issue_id: Annotated[str, Field(description='Issue ID (e.g., ITSFT-123 or 2-12345)')],
    ) -> str:
        """Fetch raw API response for an issue. Use when standard get_issue doesn't provide needed fields. Returns unprocessed JSON."""
        return await issue_tools.get_issue_raw(issue_id)

    @mcp.tool()
    async def create_issue(
        project: Annotated[str, Field(description='Project short name (e.g., ITSFT) or ID')],
        summary: Annotated[str, Field(description='Issue title/summary')],
        description: Annotated[str | None, Field(description='Issue description (markdown supported)')] = None,
        custom_fields: Annotated[
            dict[str, Any] | str | None,
            Field(
                description='Custom field values as dict: {"Priority": "Critical", "Type": "Bug"}. '
                'Use get_project to see available fields and values.'
            ),
        ] = None,
    ) -> str:
        """Create new bug report, feature request, or task. Automatically generates issue ID. Returns created issue with URL."""
        # Handle custom_fields as either dict or JSON string
        parsed_custom_fields: dict[str, Any] | None = None
        if isinstance(custom_fields, str):
            try:
                parsed_custom_fields = json.loads(custom_fields)
            except json.JSONDecodeError:
                return f'Error: custom_fields must be a valid JSON string or dictionary, got: {custom_fields}'
        elif custom_fields is not None:
            parsed_custom_fields = custom_fields

        return await issue_tools.create_issue(project, summary, description, parsed_custom_fields)

    @mcp.tool()
    async def add_comment(
        issue_id: Annotated[str, Field(description='Issue ID (e.g., ITSFT-123 or 2-12345)')],
        text: Annotated[str, Field(description='Comment text (markdown supported)')],
    ) -> str:
        """Post comment on issue for discussion, updates, or clarifications. Supports markdown. Returns success confirmation."""
        return await issue_tools.add_comment(issue_id, text)

    @mcp.tool()
    async def search_issues(
        query: Annotated[
            str,
            Field(
                description="""
        YouTrack query. Examples:
        • 'project: ITSFT' • 'assignee: me' • '#Unresolved'
        • 'created: today' • 'updated: {this week}' • 'due: 2024-01-01 .. 2024-12-31'
        • 'Type: Bug Priority: Critical' • 'has: comments' • 'tag: important'
        • '"exact phrase"' • 'summary: bug*' • state: Open OR state: {In Progress}
        """
            ),
        ],
        limit: Annotated[int, Field(description='Max results (default: 100)')] = 100,
    ) -> str:
        """Find issues using YouTrack query syntax. Returns only ID and summary for quick overview. Use search_issues_detailed for full information."""
        return await issue_tools.search_issues(query, limit)

    @mcp.tool()
    async def search_issues_detailed(
        query: Annotated[
            str,
            Field(
                description="""
        YouTrack query. Examples:
        • 'project: ITSFT' • 'assignee: me' • '#Unresolved'
        • 'created: today' • 'updated: {this week}' • 'due: 2024-01-01 .. 2024-12-31'
        • 'Type: Bug Priority: Critical' • 'has: comments' • 'tag: important'
        • '"exact phrase"' • 'summary: bug*' • state: Open OR state: {In Progress}
        """
            ),
        ],
        limit: Annotated[int, Field(description='Max results (default: 30)')] = 30,
        custom_fields_filter: Annotated[
            list[str] | str | None,
            Field(
                description='Optional list of custom field names to include (e.g., ["Priority", "State", "Type"]). If not specified, all fields are included.'
            ),
        ] = None,
    ) -> str:
        """Find issues with full details including custom fields, assignee, reporter, dates. Use for comprehensive issue information."""
        # Handle custom_fields_filter as either list or JSON string
        parsed_filter: list[str] | None = None
        if isinstance(custom_fields_filter, str):
            try:
                parsed_filter = json.loads(custom_fields_filter)
            except json.JSONDecodeError:
                return f'Error: custom_fields_filter must be a valid JSON array, got: {custom_fields_filter}'
        elif custom_fields_filter is not None:
            parsed_filter = custom_fields_filter
        return await issue_tools.search_issues_detailed(query, limit, parsed_filter)

    @mcp.tool()
    async def execute_command(
        command: Annotated[
            str, Field(description='Command: "for me", "state Fixed", "Priority High" (use get_project for values)')
        ],
        issues: Annotated[list[str] | str, Field(description='Issue ID(s) - single string or list (e.g., ITSFT-123)')],
        comment: Annotated[str | None, Field(description='Optional comment to add with the command')] = None,
        silent: Annotated[bool, Field(description='If True, no notifications will be sent')] = False,
    ) -> str:
        """Batch update issues using commands like 'for me', 'state Fixed', 'Priority High'. Efficient for bulk operations."""
        return await issue_tools.execute_command(command, issues, comment, silent)
