"""
YouTrack Search MCP tools.
"""

import json
import logging
from datetime import datetime
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.resources.issues import IssuesClient
from youtrack_rocket_mcp.api.resources.search import SearchClient
from youtrack_rocket_mcp.api.types import CustomFieldData, ToolRegistry

logger = logging.getLogger(__name__)


class SearchTools:
    """Advanced search tools for YouTrack."""

    def __init__(self):
        """Initialize the search tools."""
        self.client = YouTrackClient()
        self.issues_api = IssuesClient(self.client)

    async def advanced_search(
        self, query: str, limit: int = 10, sort_by: str | None = None, sort_order: str | None = None
    ) -> str:
        """
        Advanced search for issues using YouTrack query language with sorting.

        FORMAT: advanced_search(query="project: DEMO #Unresolved", limit=10, sort_by="created", sort_order="desc")

        Common query syntax:
        - Project: project: MyProject or #MyProject
        - Assignee: assignee: me, assignee: john.doe, assignee: Unassigned
        - State: state: Open, #Unresolved, #Resolved
        - Priority: priority: Critical, priority: Major
        - Date ranges: created: today, updated: {this week}, created: 2024-01-01 .. 2024-12-31
        - Text search: "exact phrase", word1 word2 (AND), word1 or word2 (OR)
        - Custom fields: Environment: Production, Sprint: {Sprint 23}
        - Operators: -state: Resolved (NOT), (state: Open or state: In Progress)

        Use get_search_syntax_guide() for comprehensive syntax reference.

        Args:
            query: The search query using YouTrack query language
            limit: Maximum number of issues to return
            sort_by: Field to sort by (e.g., created, updated, priority)
            sort_order: Sort order (asc or desc)

        Returns:
            JSON string with search results
        """
        try:
            # Create sort specification if provided
            sort_param = None
            if sort_by:
                # Default to descending order if not specified
                order = sort_order or 'desc'
                sort_param = f'{sort_by} {order}'
                logger.info(f'Sorting by: {sort_param}')

            # Request with explicit fields to get complete data
            fields = 'id,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value(id,name,login,text,localizedName))'
            params = {'query': query, '$top': limit, 'fields': fields}

            if sort_param:
                params['$sort'] = sort_param

            raw_issues = await self.client.get('issues', params=params)

            # Format custom fields for each issue
            for issue in raw_issues:
                if 'customFields' in issue:
                    issue['custom_fields'] = SearchClient.format_custom_fields(issue['customFields'])
                    # Remove original customFields - keep only formatted version
                    del issue['customFields']

            # Return the formatted issues data
            return json.dumps(raw_issues, indent=2)

        except Exception as e:
            logger.exception(f'Error performing advanced search with query: {query}')
            return json.dumps({'error': str(e)})

    async def filter_issues(
        self,
        project: str | None = None,
        author: str | None = None,
        assignee: str | None = None,
        state: str | None = None,
        priority: str | None = None,
        text: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        limit: int = 10,
    ) -> str:
        """
        Search for issues using a structured filter approach.

        FORMAT: filter_issues(project="DEMO", author="user", assignee="user", state="Open", priority="High", text="bug", created_after="2023-01-01", created_before="2023-06-30", updated_after="2023-01-01", updated_before="2023-06-30", limit=10)

        Args:
            project: Filter by project (name or ID)
            author: Filter by issue reporter/author
            assignee: Filter by issue assignee
            state: Filter by issue state (e.g., Open, Resolved)
            priority: Filter by priority (e.g., Critical, High)
            text: Text to search in summary and description
            created_after: Filter issues created after this date (YYYY-MM-DD)
            created_before: Filter issues created before this date (YYYY-MM-DD)
            updated_after: Filter issues updated after this date (YYYY-MM-DD)
            updated_before: Filter issues updated before this date (YYYY-MM-DD)
            limit: Maximum number of issues to return

        Returns:
            JSON string with matching issues
        """
        try:
            # Build YouTrack query from structured filters
            query_parts = []

            if project:
                query_parts.append(f'project: {project}')

            if author:
                query_parts.append(f'reporter: {author}')

            if assignee:
                query_parts.append(f'assignee: {assignee}')

            if state:
                # Handle common states
                if state.lower() == 'open' or state.lower() == 'unresolved':
                    query_parts.append('#Unresolved')
                elif state.lower() == 'resolved':
                    query_parts.append('#Resolved')
                else:
                    query_parts.append(f'State: {state}')

            if priority:
                query_parts.append(f'Priority: {priority}')

            if text:
                # Search in summary and description
                query_parts.append(f'"{text}"')

            # Handle date filters - combine created dates into single range if both present
            if created_after and created_before:
                try:
                    # Validate both dates
                    datetime.strptime(created_after, '%Y-%m-%d')
                    datetime.strptime(created_before, '%Y-%m-%d')
                    query_parts.append(f'created: {created_after} .. {created_before}')
                except ValueError as e:
                    logger.warning(f'Invalid date format for created dates: {e}')
            elif created_after:
                try:
                    # Validate date format
                    datetime.strptime(created_after, '%Y-%m-%d')
                    query_parts.append(f'created: {created_after} ..')
                except ValueError:
                    logger.warning(f'Invalid date format for created_after: {created_after}')
            elif created_before:
                try:
                    datetime.strptime(created_before, '%Y-%m-%d')
                    query_parts.append(f'created: .. {created_before}')
                except ValueError:
                    logger.warning(f'Invalid date format for created_before: {created_before}')

            # Handle updated dates similarly
            if updated_after and updated_before:
                try:
                    datetime.strptime(updated_after, '%Y-%m-%d')
                    datetime.strptime(updated_before, '%Y-%m-%d')
                    query_parts.append(f'updated: {updated_after} .. {updated_before}')
                except ValueError as e:
                    logger.warning(f'Invalid date format for updated dates: {e}')
            elif updated_after:
                try:
                    datetime.strptime(updated_after, '%Y-%m-%d')
                    query_parts.append(f'updated: {updated_after} ..')
                except ValueError:
                    logger.warning(f'Invalid date format for updated_after: {updated_after}')
            elif updated_before:
                try:
                    datetime.strptime(updated_before, '%Y-%m-%d')
                    query_parts.append(f'updated: .. {updated_before}')
                except ValueError:
                    logger.warning(f'Invalid date format for updated_before: {updated_before}')

            # Combine all parts into a single query
            query = ' '.join(query_parts) if query_parts else ''

            logger.info(f'Constructed filter query: {query}')

            # Call advanced_search with the constructed query
            return await self.advanced_search(query=query, limit=limit)

        except Exception as e:
            logger.exception('Error filtering issues')
            return json.dumps({'error': str(e)})

    async def search_with_custom_fields(self, query: str, custom_fields: str | CustomFieldData, limit: int = 10) -> str:
        """
        Search for issues with specific custom field values.

        FORMAT: search_with_custom_fields(query="project: DEMO", custom_fields={"Priority": "High", "Type": "Bug"}, limit=10)

        Args:
            query: Base search query
            custom_fields: Dictionary of custom field names and values, or a JSON string
            limit: Maximum number of issues to return

        Returns:
            JSON string with matching issues
        """
        try:
            # Parse custom_fields if it's a string
            if isinstance(custom_fields, str):
                try:
                    custom_fields = json.loads(custom_fields)
                except json.JSONDecodeError:
                    logger.warning(f'Failed to parse custom_fields as JSON: {custom_fields}')
                    custom_fields = {}

            # Ensure custom_fields is a dictionary
            if not isinstance(custom_fields, dict):
                logger.warning(f'custom_fields is not a dictionary: {custom_fields}')
                custom_fields = {}

            # Add custom field conditions to the query
            query_parts = [query] if query else []

            for field_name, field_value in custom_fields.items():
                # Handle special case for empty values
                if field_value is None or field_value == '':
                    query_parts.append(f'{field_name}: empty')
                else:
                    query_parts.append(f'{field_name}: {field_value}')

            # Combine all parts into a single query
            combined_query = ' '.join(query_parts)
            logger.info(f'Search with custom fields query: {combined_query}')

            # Call advanced_search with the combined query
            return await self.advanced_search(query=combined_query, limit=limit)

        except Exception as e:
            logger.exception('Error searching with custom fields')
            return json.dumps({'error': str(e)})

    def close(self) -> None:
        """Close the API client."""
        self.client.close()

    def get_tool_definitions(self) -> ToolRegistry:
        """
        Get the definitions of all search tools.

        Returns:
            Dictionary mapping tool names to their configuration
        """
        return {
            'advanced_search': {
                'function': self.advanced_search,
                'description': "Perform advanced issue search using YouTrack's full query language with sorting capabilities. This is the most powerful search method supporting all YouTrack query features.",
                'parameters': {
                    'query': 'Search query using YouTrack query language syntax',
                    'limit': 'Maximum number of issues to return (optional, default: 10, max: 1000)',
                    'sort_by': "Field to sort results by (optional, e.g., 'created', 'updated', 'priority', 'votes')",
                    'sort_order': "Sort direction: 'asc' for ascending or 'desc' for descending (optional, default: 'desc')",
                },
                'examples': [
                    "advanced_search(query='project: ITSFT State: {In Progress} assignee: me') - My in-progress issues in ITSFT",
                    "advanced_search(query='Priority: Critical created: {This week}', sort_by='created', sort_order='desc') - Recent critical issues",
                    "advanced_search(query='Type: Bug State: -Closed has: votes', sort_by='votes') - Open bugs with votes",
                    "advanced_search(query='tag: security #Unresolved', limit=50) - Unresolved security issues",
                ],
                'query_features': [
                    'Logical operators: AND (space), OR, NOT (-)',
                    'Grouping with parentheses: (A or B) and C',
                    'Date ranges: {Today}, {Yesterday}, {This week}, {Last month}, date .. date',
                    'Wildcards: * for any characters, ? for single character',
                    'Special tags: #Unresolved, #Resolved, #{In Progress}',
                    'has/is operators: has: comments, is: reported-by-me',
                ],
            },
            'filter_issues': {
                'function': self.filter_issues,
                'description': 'Search for issues using a structured parameter approach. Ideal when you have specific field values to filter by without constructing a query string.',
                'parameters': {
                    'project': "Project name or short name to filter by (optional, e.g., 'ITSFT')",
                    'author': 'Username or login of issue reporter/author (optional)',
                    'assignee': "Username or login of issue assignee, or 'me' for current user (optional)",
                    'state': "Issue state name (optional, e.g., 'Open', 'In Progress', 'Closed')",
                    'priority': "Priority level (optional, e.g., 'Critical', 'High', 'Normal', 'Low')",
                    'text': 'Text to search in issue summary and description (optional)',
                    'created_after': 'Filter issues created after this date in YYYY-MM-DD format (optional)',
                    'created_before': 'Filter issues created before this date in YYYY-MM-DD format (optional)',
                    'updated_after': 'Filter issues updated after this date in YYYY-MM-DD format (optional)',
                    'updated_before': 'Filter issues updated before this date in YYYY-MM-DD format (optional)',
                    'limit': 'Maximum number of issues to return (optional, default: 10)',
                },
                'examples': [
                    "filter_issues(project='ITSFT', state='Open', assignee='me') - My open issues in ITSFT",
                    "filter_issues(priority='Critical', created_after='2025-01-01') - Recent critical issues",
                    "filter_issues(text='memory leak', state='Open', limit=20) - Open issues mentioning memory leak",
                    "filter_issues(project='CS', author='john.doe', updated_after='2025-01-15') - John's recently updated CS issues",
                ],
                'notes': 'All parameters are optional and combined with AND logic',
            },
            'search_with_custom_fields': {
                'function': self.search_with_custom_fields,
                'description': 'Search for issues filtering by specific custom field values. Use this when you need to filter by project-specific fields like Type, Severity, Component, etc.',
                'parameters': {
                    'query': "Base search query to combine with custom field filters (e.g., 'project: ITSFT')",
                    'custom_fields': 'Dictionary mapping custom field names to their values, or a JSON string',
                    'limit': 'Maximum number of issues to return (optional, default: 10)',
                },
                'examples': [
                    "search_with_custom_fields(query='project: ITSFT', custom_fields={'Type': 'Bug', 'Severity': 'Critical'})",
                    "search_with_custom_fields(query='State: Open', custom_fields={'Subsystem': 'Backend', 'Priority': 'High'})",
                    "search_with_custom_fields(query='assignee: me', custom_fields={'Type': 'Task', 'Sprint': 'Current Sprint'})",
                ],
                'custom_fields_format': {
                    'Dictionary format': "{'FieldName': 'Value', 'AnotherField': 'AnotherValue'}",
                    'JSON string format': '\'{"Type": "Bug", "Priority": "High"}\'',
                    'Empty value': "Use 'empty' to find issues where field is not set",
                },
                'tips': [
                    'Use get_project_fields() first to see available custom fields for a project',
                    'Field names are case-sensitive',
                    "Use 'empty' as value to find issues with unset fields",
                ],
            },
        }


def register_search_tools(mcp: FastMCP) -> None:
    """Register search tools with the MCP server."""
    search_tools = SearchTools()

    @mcp.tool()
    async def advanced_search(
        query: Annotated[
            str,
            Field(
                description="""
        Same as search_issues + SORTING. All YouTrack syntax supported.
        Use for: newest issues, highest priority, most commented, etc.
        """
            ),
        ],
        limit: Annotated[int, Field(description='Max results')] = 10,
        sort_by: Annotated[
            str | None, Field(description='Sort by: created, updated, priority, votes, comments')
        ] = None,
        sort_order: Annotated[str | None, Field(description='asc (oldest first) or desc (newest first)')] = None,
    ) -> str:
        """Search and sort issues. Use to find newest bugs, high priority tasks, or most voted features. Supports full query syntax."""
        return await search_tools.advanced_search(query, limit, sort_by, sort_order)

    @mcp.tool()
    async def filter_issues(
        project: Annotated[str | None, Field(description='Project short name (e.g. ITSFT)')] = None,
        author: Annotated[str | None, Field(description='Author login or "me" for current user')] = None,
        assignee: Annotated[str | None, Field(description='Assignee login, "me", or "Unassigned"')] = None,
        state: Annotated[str | None, Field(description='Issue state (use get_project to see available values)')] = None,
        priority: Annotated[
            str | None, Field(description='Priority level (use get_project to see available values)')
        ] = None,
        text: Annotated[str | None, Field(description='Search in summary and description')] = None,
        created_after: Annotated[str | None, Field(description='Date YYYY-MM-DD')] = None,
        created_before: Annotated[str | None, Field(description='Date YYYY-MM-DD')] = None,
        updated_after: Annotated[str | None, Field(description='Date YYYY-MM-DD')] = None,
        updated_before: Annotated[str | None, Field(description='Date YYYY-MM-DD')] = None,
        limit: Annotated[int, Field(description='Max results')] = 10,
    ) -> str:
        """Filter issues by multiple criteria. Use when you need precise AND filtering. All parameters optional."""
        return await search_tools.filter_issues(
            project,
            author,
            assignee,
            state,
            priority,
            text,
            created_after,
            created_before,
            updated_after,
            updated_before,
            limit,
        )

    @mcp.tool()
    async def search_with_custom_fields(
        query: Annotated[str, Field(description='Base query (supports all YouTrack syntax)')],
        custom_fields: Annotated[
            str | list | dict,
            Field(
                description="""
            Custom field filters: {'Type': 'Bug', 'Severity': 'Critical', 'Subsystem': 'Backend'}
            Use 'empty' to find unset fields: {'Sprint': 'empty'}
            """
            ),
        ],
        limit: Annotated[int, Field(description='Max results')] = 10,
    ) -> str:
        """Search by custom fields. Use to find bugs in specific sprint or critical severity issues. Combines with base query."""
        # Handle custom_fields as string, list or dict
        if not isinstance(custom_fields, str):
            custom_fields = json.dumps(custom_fields)
        return await search_tools.search_with_custom_fields(query, custom_fields, limit)
