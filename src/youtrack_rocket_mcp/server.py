#!/usr/bin/env python3
"""
FastMCP-based YouTrack MCP server implementation with proper schema generation.
"""

import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from youtrack_rocket_mcp.config import config
from youtrack_rocket_mcp.tools.issues import IssueTools
from youtrack_rocket_mcp.tools.projects import ProjectTools
from youtrack_rocket_mcp.tools.search import SearchTools
from youtrack_rocket_mcp.tools.search_guide import SearchGuide
from youtrack_rocket_mcp.tools.users import UserTools

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(config.MCP_SERVER_NAME)

# Initialize tool instances
issue_tools = IssueTools()
project_tools = ProjectTools()
search_tools = SearchTools()
search_guide = SearchGuide()
user_tools = UserTools()


# Issue Tools
@mcp.tool()
async def get_issue(
    issue_id: Annotated[str, Field(description='The issue ID or readable ID (e.g., PROJECT-123)')],
) -> str:
    """Get information about a specific issue by its ID."""
    return await issue_tools.get_issue(issue_id)


@mcp.tool()
async def get_issue_raw(
    issue_id: Annotated[str, Field(description='The issue ID or readable ID (e.g., PROJECT-123)')],
) -> str:
    """Get raw information about a specific issue by its ID."""
    return await issue_tools.get_issue_raw(issue_id)


@mcp.tool()
async def create_issue(
    project: Annotated[str, Field(description='Project ID or short name where the issue will be created')],
    summary: Annotated[str, Field(description='Brief summary/title of the issue')],
    description: Annotated[str | None, Field(description='Detailed description of the issue')] = None,
    custom_fields: Annotated[
        dict[str, str] | None,
        Field(
            description='Dictionary mapping custom field names to their values. '
            "Example: {'Priority': 'Critical', 'Type': 'Bug', 'Subsystem': 'Backend'}"
        ),
    ] = None,
) -> str:
    """Create a new issue in a project."""
    return await issue_tools.create_issue(project, summary, description, custom_fields)


@mcp.tool()
async def add_comment(
    issue_id: Annotated[str, Field(description='The issue ID or readable ID (e.g., PROJECT-123)')],
    text: Annotated[str, Field(description='The comment text to add to the issue')],
) -> str:
    """Add a comment to an existing issue."""
    return await issue_tools.add_comment(issue_id, text)


@mcp.tool()
async def search_issues(
    query: Annotated[str, Field(description="YouTrack search query (e.g., 'project: PROJECT-KEY')")],
    limit: Annotated[int, Field(description='Maximum number of issues to return')] = 10,
) -> str:
    """Search for issues using YouTrack query syntax."""
    return await issue_tools.search_issues(query, limit)


# Project Tools
@mcp.tool()
async def get_projects(
    include_archived: Annotated[bool, Field(description='Include archived projects in the results')] = False,
) -> str:
    """Get list of all projects."""
    return await project_tools.get_projects(include_archived)


@mcp.tool()
async def get_project(
    project_id: Annotated[str | None, Field(description='Project ID or short name to retrieve information for')] = None,
    project: Annotated[str | None, Field(description='Alternative parameter name for project ID')] = None,
) -> str:
    """Get detailed information about a specific project."""
    return await project_tools.get_project(project_id, project)


@mcp.tool()
async def get_project_by_name(
    project_name: Annotated[str, Field(description='The full name of the project to search for')],
) -> str:
    """Get project information by project name."""
    return await project_tools.get_project_by_name(project_name)


@mcp.tool()
async def get_project_issues(
    project_id: Annotated[str | None, Field(description='Project ID or short name to get issues from')] = None,
    project: Annotated[str | None, Field(description='Alternative parameter name for project ID')] = None,
    limit: Annotated[int, Field(description='Maximum number of issues to return')] = 50,
) -> str:
    """Get all issues for a specific project."""
    return await project_tools.get_project_issues(project_id, project, limit)


@mcp.tool()
async def get_custom_fields(
    project_id: Annotated[str | None, Field(description='Project ID or short name to get custom fields from')] = None,
    project: Annotated[str | None, Field(description='Alternative parameter name for project ID')] = None,
) -> str:
    """Get custom fields for a project."""
    return await project_tools.get_custom_fields(project_id, project)


# Search Tools
@mcp.tool()
async def advanced_search(
    query: Annotated[str, Field(description='YouTrack search query')],
    limit: Annotated[int, Field(description='Maximum number of results to return')] = 10,
    sort_by: Annotated[str | None, Field(description='Field to sort by (e.g., created, updated, priority)')] = None,
    sort_order: Annotated[str | None, Field(description='Sort order (asc or desc)')] = None,
) -> str:
    """Perform advanced search with filters and custom fields."""
    return await search_tools.advanced_search(query, limit, sort_by, sort_order)


@mcp.tool()
async def filter_issues(
    project: Annotated[str | None, Field(description='Project ID or short name to filter issues from')] = None,
    author: Annotated[str | None, Field(description='Filter by author login')] = None,
    assignee: Annotated[str | None, Field(description='Filter by assignee login')] = None,
    state: Annotated[str | None, Field(description='Filter by issue state')] = None,
    priority: Annotated[str | None, Field(description='Filter by priority level')] = None,
    text: Annotated[str | None, Field(description='Search in issue text')] = None,
    created_after: Annotated[str | None, Field(description='Filter by creation date (YYYY-MM-DD format)')] = None,
    created_before: Annotated[str | None, Field(description='Filter by creation date (YYYY-MM-DD format)')] = None,
    updated_after: Annotated[str | None, Field(description='Filter by update date (YYYY-MM-DD format)')] = None,
    updated_before: Annotated[str | None, Field(description='Filter by update date (YYYY-MM-DD format)')] = None,
    limit: Annotated[int, Field(description='Maximum number of results to return')] = 10,
) -> str:
    """Filter issues by various criteria."""
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
    query: Annotated[str, Field(description='YouTrack search query')],
    custom_fields: Annotated[str, Field(description='JSON string of custom fields to include in results')],
    limit: Annotated[int, Field(description='Maximum number of issues to return')] = 10,
) -> str:
    """Search issues with custom field values included."""
    return await search_tools.search_with_custom_fields(query, custom_fields, limit)


# User Tools
@mcp.tool()
async def get_user(
    user_id: Annotated[str | None, Field(description='User ID to retrieve information for')] = None,
    user: Annotated[str | None, Field(description='Alternative parameter name for user ID')] = None,
) -> str:
    """Get information about a specific user by ID."""
    return await user_tools.get_user(user_id, user)


@mcp.tool()
async def get_user_by_login(
    login: Annotated[str, Field(description='User login/username to retrieve information for')],
) -> str:
    """Get information about a specific user by login."""
    return await user_tools.get_user_by_login(login)


@mcp.tool()
async def search_users(
    query: Annotated[str, Field(description='Search query for user name or login')],
    limit: Annotated[int, Field(description='Maximum number of users to return')] = 10,
) -> str:
    """Search for users by name or login."""
    return await user_tools.search_users(query, limit)


@mcp.tool()
async def get_current_user() -> str:
    """Get information about the currently authenticated user."""
    return await user_tools.get_current_user()


# Search Guide Tools
@mcp.tool()
async def get_search_syntax_guide() -> str:
    """Get comprehensive guide for YouTrack search syntax."""
    return await search_guide.get_search_syntax_guide()


@mcp.tool()
async def get_common_queries() -> str:
    """Get examples of common YouTrack search queries."""
    return await search_guide.get_common_queries()


def main():
    """Main entry point for the FastMCP YouTrack server."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info(f'Starting YouTrack FastMCP server ({config.MCP_SERVER_NAME})')
    logger.info('FastMCP tools registered with proper parameter schemas')

    # Run the server
    mcp.run()


if __name__ == '__main__':
    main()
