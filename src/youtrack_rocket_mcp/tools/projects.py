"""
YouTrack Project MCP tools.
"""

import json
import logging

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.resources.issues import IssuesClient
from youtrack_rocket_mcp.api.resources.projects import ProjectsClient
from youtrack_rocket_mcp.api.types import ToolRegistry

logger = logging.getLogger(__name__)


class ProjectTools:
    """Project-related MCP tools."""

    def __init__(self):
        """Initialize the project tools."""
        self.client = YouTrackClient()
        self.projects_api = ProjectsClient(self.client)

        # Also initialize the issues API for fetching issue details
        self.issues_api = IssuesClient(self.client)

    async def get_projects(self, include_archived: bool = False) -> str:
        """
        Get a list of all projects.

        Use this to discover available projects before creating issues.
        Each project has a shortName (e.g., 'ITSFT') used in issue IDs.

        FORMAT: get_projects(include_archived=False)

        Args:
            include_archived: Whether to include archived projects

        Returns:
            JSON string with projects information including:
            - id: Internal project ID (e.g., '0-167')
            - shortName: Project key used in issue IDs (e.g., 'ITSFT')
            - name: Full project name (e.g., 'IT Software')
            - description: Project description
            - archived: Whether project is archived
        """
        try:
            projects = await self.projects_api.get_projects(include_archived=include_archived)

            # Handle both Pydantic models and dictionaries in the response
            result = []
            for project in projects:
                if hasattr(project, 'model_dump'):
                    result.append(project.model_dump())
                else:
                    result.append(project)  # Assume it's already a dict

            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception('Error getting projects')
            return json.dumps({'error': str(e)})

    async def get_project(self, project_id: str | None = None, project: str | None = None) -> str:
        """
        Get information about a specific project.

        FORMAT: get_project(project_id="0-0")

        Args:
            project_id: The project ID
            project: Alternative parameter name for project_id

        Returns:
            JSON string with project information
        """
        try:
            # Use either project_id or project parameter
            project_identifier = project_id or project
            if not project_identifier:
                return json.dumps({'error': 'Project ID is required'})

            project_obj = await self.projects_api.get_project(project_identifier)

            # Handle both Pydantic models and dictionaries in the response
            result = project_obj.model_dump() if hasattr(project_obj, 'model_dump') else project_obj

            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f'Error getting project {project_id or project}')
            return json.dumps({'error': str(e)})

    # @sync_wrapper removed
    async def get_project_by_name(self, project_name: str) -> str:
        """
        Find a project by its name.

        FORMAT: get_project_by_name(project_name="DEMO")

        Args:
            project_name: The project name or short name

        Returns:
            JSON string with project information
        """
        try:
            if not project_name:
                return json.dumps({'error': 'Project name is required'})

            project = await self.projects_api.get_project_by_name(project_name)
            if project:
                # Handle both Pydantic models and dictionaries in the response
                result = project.model_dump() if hasattr(project, 'model_dump') else project

                return json.dumps(result, indent=2)
            return json.dumps({'error': f"Project '{project_name}' not found"})
        except Exception as e:
            logger.exception(f'Error finding project by name {project_name}')
            return json.dumps({'error': str(e)})

    # @sync_wrapper removed
    async def get_project_issues(
        self, project_id: str | None = None, project: str | None = None, limit: int = 50
    ) -> str:
        """
        Get issues for a specific project.

        FORMAT: get_project_issues(project_id="0-0", limit=10)

        Args:
            project_id: The project ID (e.g., '0-0')
            project: Alternative parameter name for project_id
            limit: Maximum number of issues to return (default: 50)

        Returns:
            JSON string with the issues
        """
        try:
            # Use either project_id or project parameter
            project_identifier = project_id or project
            if not project_identifier:
                return json.dumps({'error': 'Project ID is required'})

            # First try with the direct project ID
            try:
                issues = await self.projects_api.get_project_issues(project_identifier, limit)
                if issues:
                    return json.dumps(issues, indent=2)
            except Exception as e:
                # If that fails, check if it was a non-ID format error
                if not str(e).startswith('Project not found'):
                    logger.exception(f'Error getting issues for project {project_identifier}')
                    return json.dumps({'error': str(e)})

            # If that failed, try to find project by name
            try:
                project_obj = await self.projects_api.get_project_by_name(project_identifier)
                if project_obj:
                    issues = await self.projects_api.get_project_issues(project_obj.id, limit)
                    return json.dumps(issues, indent=2)
                return json.dumps({'error': f'Project not found: {project_identifier}'})
            except Exception as e:
                logger.exception(f'Error getting issues for project {project_identifier}')
                return json.dumps({'error': str(e)})
        except Exception as e:
            logger.exception(f'Error processing get_project_issues({project_id or project}, {limit})')
            return json.dumps({'error': str(e)})

    # @sync_wrapper removed
    async def get_custom_fields(self, project_id: str | None = None, project: str | None = None) -> str:
        """
        Get custom fields for a project.

        FORMAT: get_custom_fields(project_id="0-0")

        Args:
            project_id: The project ID
            project: Alternative parameter name for project_id

        Returns:
            JSON string with custom fields information
        """
        try:
            # Use either project_id or project parameter
            project_identifier = project_id or project
            if not project_identifier:
                return json.dumps({'error': 'Project ID is required'})

            fields = await self.projects_api.get_custom_fields(project_identifier)

            # Handle various response formats safely
            if fields is None:
                return json.dumps([])

            # If it's a dictionary (direct API response)
            if isinstance(fields, dict):
                return json.dumps(fields, indent=2)

            # If it's a list of objects
            try:
                result = []
                # Try to iterate, but handle errors safely
                for field in fields:
                    if hasattr(field, 'model_dump'):
                        result.append(field.model_dump())
                    elif isinstance(field, dict):
                        result.append(field)
                    else:
                        # Last resort: convert to string
                        result.append(str(field))
                return json.dumps(result, indent=2)
            except Exception as e:
                # If we can't iterate, return the raw string representation
                logger.warning(f'Could not process custom fields response: {e!s}')
                return json.dumps({'custom_fields': str(fields)})
        except Exception as e:
            logger.exception(f'Error getting custom fields for project {project_id or project}')
            return json.dumps({'error': str(e)})

    # @sync_wrapper removed
    async def get_project_detailed(self, project_id: str | None = None, project: str | None = None) -> str:
        """
        Get detailed project information including all custom fields with their configuration.

        IMPORTANT: Use this before creating issues to see:
        - Which fields are required (required: true)
        - Available values for enum/bundle fields (possible_values)
        - Field IDs for precise control (id)
        - Field types (type)

        FORMAT: get_project_detailed(project_id="0-167") or get_project_detailed(project_id="ITSFT")

        Args:
            project_id: The project ID (e.g., '0-167') or short name (e.g., 'ITSFT')
            project: Alternative parameter name for project_id

        Returns:
            JSON string with:
            - project: Basic project information
            - custom_fields: All fields with their configuration
            - required_fields: List of fields that must be provided when creating issues
            - usage_hint: Instructions for using the field information

        Example output for a field:
        {
            "id": "93-1507",
            "name": "Subsystem",
            "type": "OwnedProjectCustomField",
            "required": true,
            "possible_values": [
                {"id": "100-561", "name": "Bender Bot"},
                {"id": "100-562", "name": "Inventory"}
            ]
        }
        """
        try:
            # Use either project_id or project parameter
            project_identifier = project_id or project
            if not project_identifier:
                return json.dumps({'error': 'Project ID is required'})

            detailed_info = await self.projects_api.get_project_detailed(project_identifier)

            # Convert to dict if it's a Pydantic model
            if hasattr(detailed_info, 'model_dump'):
                detailed_info = detailed_info.model_dump()

            return json.dumps(detailed_info, indent=2)
        except Exception as e:
            logger.exception(f'Error getting detailed project info for {project_id or project}')
            return json.dumps({'error': str(e)})

    # @sync_wrapper removed
    async def get_project_fields(self, project_id: str | None = None, project: str | None = None) -> str:
        """
        Get project custom fields information by analyzing actual issues.
        This function extracts field names, types, and sample values from issues.

        FORMAT: get_project_fields(project_id="0-167")

        Args:
            project_id: The project ID
            project: Alternative parameter name for project_id

        Returns:
            JSON string with detailed custom fields information
        """
        try:
            # Use either project_id or project parameter
            project_identifier = project_id or project
            if not project_identifier:
                return json.dumps({'error': 'Project ID is required'})

            fields_info = await self.projects_api.get_project_fields_from_issues(project_identifier)
            return json.dumps(fields_info, indent=2)
        except Exception as e:
            logger.exception(f'Error getting project fields for {project_id or project}')
            return json.dumps({'error': str(e)})

    # @sync_wrapper removed
    async def create_project(self, name: str, short_name: str, lead_id: str, description: str | None = None) -> str:
        """
        Create a new project with a required leader.

        FORMAT: create_project(name="Project Name", short_name="PROJ", lead_id="1-1", description="Description")

        Args:
            name: The name of the project
            short_name: The short name of the project (used as prefix for issues)
            lead_id: The ID of the user who will be the project leader
            description: The project description (optional)

        Returns:
            JSON string with the created project information
        """
        try:
            # Check for missing required parameters
            if not name:
                return json.dumps({'error': 'Project name is required'})
            if not short_name:
                return json.dumps({'error': 'Project short name is required'})
            if not lead_id:
                return json.dumps({'error': 'Project leader ID is required'})

            project = await self.projects_api.create_project(
                name=name, short_name=short_name, lead_id=lead_id, description=description
            )

            # Handle both Pydantic models and dictionaries in the response
            result = project.model_dump() if hasattr(project, 'model_dump') else project

            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f'Error creating project {name}')
            return json.dumps({'error': str(e)})

    # @sync_wrapper removed
    async def update_project(
        self,
        project_id: str | None = None,
        project: str | None = None,
        name: str | None = None,
        description: str | None = None,
        archived: bool | None = None,
        lead_id: str | None = None,
        short_name: str | None = None,
    ) -> str:
        """
        Update an existing project.

        FORMAT: update_project(project_id="0-0", name="New Name", description="New Description", archived=False, lead_id="1-1", short_name="NEWKEY")

        Args:
            project_id: The project ID to update
            project: Alternative parameter name for project_id
            name: The new name for the project (optional)
            description: The new project description (optional)
            archived: Whether the project should be archived (optional)
            lead_id: The ID of the new project leader (optional)
            short_name: The new short name for the project (optional) - used as prefix for issue IDs

        Returns:
            JSON string with the updated project information
        """
        try:
            # Use either project_id or project parameter
            project_identifier = project_id or project
            if not project_identifier:
                return json.dumps({'error': 'Project ID is required'})

            # First, get the existing project to maintain required fields
            try:
                existing_project = await self.projects_api.get_project(project_identifier)
                logger.info(f'Found existing project: {existing_project.name} ({existing_project.id})')

                # Prepare data for direct API call
                data = {}

                # Only include parameters that were explicitly provided
                if name is not None:
                    data['name'] = name
                if description is not None:
                    data['description'] = description
                if archived is not None:
                    data['archived'] = archived  # type: ignore[assignment]
                if lead_id is not None:
                    data['leader'] = {'id': lead_id}  # type: ignore[assignment]
                if short_name is not None:
                    data['shortName'] = short_name

                # If no parameters were provided, return current project
                if not data:
                    logger.info('No parameters to update, returning current project')
                    if hasattr(existing_project, 'model_dump'):
                        return json.dumps(existing_project.model_dump(), indent=2)
                    return json.dumps(existing_project, indent=2)

                # Log the data being sent
                logger.info(f'Updating project with data: {data}')

                # Make direct API call
                try:
                    # Use the client directly instead of the API method
                    await self.client.post(f'admin/projects/{project_identifier}', data=data)
                    logger.info('Update API call successful')
                except Exception as e:
                    logger.warning(f'Update API call error: {e!s}')
                    # Continue anyway as the update might still have worked

                # Get the updated project data
                try:
                    updated_project = await self.projects_api.get_project(project_identifier)
                    logger.info(f'Retrieved updated project: {updated_project.name}')

                    if hasattr(updated_project, 'model_dump'):
                        return json.dumps(updated_project.model_dump(), indent=2)
                    return json.dumps(updated_project, indent=2)
                except Exception as e:
                    logger.exception('Error retrieving updated project')
                    return json.dumps({'error': f'Project was updated but could not retrieve the result: {e!s}'})
            except Exception as e:
                return json.dumps({'error': f'Could not update project: {e!s}'})
        except Exception as e:
            logger.exception(f'Error updating project {project_id or project}')
            return json.dumps({'error': str(e)})

    def close(self) -> None:
        """Close the API client."""
        self.client.close()

    def get_tool_definitions(self) -> ToolRegistry:
        """
        Get the definitions of all project tools.

        Returns:
            Dictionary mapping tool names to their configuration
        """
        return {
            'get_projects': {
                'description': 'Get a list of all projects in YouTrack. Returns basic project information including ID, name, short name, description, and archived status.',
                'parameter_descriptions': {
                    'include_archived': 'Whether to include archived projects (optional, default: false)'
                },
                'examples': [
                    'get_projects() - Get all active projects',
                    'get_projects(include_archived=True) - Get all projects including archived',
                ],
            },
            'get_project': {
                'description': 'Get detailed information about a specific project by its ID or short name. Returns project details including leader, creation date, and custom fields.',
                'parameter_descriptions': {
                    'project_id': "The project ID (e.g., '0-167') or short name (e.g., 'ITSFT')",
                    'project': 'Alternative parameter name for project_id (use either project_id OR project)',
                },
                'examples': [
                    "get_project(project_id='0-167') - Get project by numeric ID",
                    "get_project(project='ITSFT') - Get project by short name",
                ],
            },
            'get_project_by_name': {
                'description': 'Search for a project by its name or short name. Searches in order: exact short name match, exact name match, partial name match. Returns the first matching project.',
                'parameter_descriptions': {
                    'project_name': "The project name or short name to search for (e.g., 'IT Software' or 'ITSFT')"
                },
                'examples': [
                    "get_project_by_name(project_name='ITSFT') - Find by short name",
                    "get_project_by_name(project_name='IT Software') - Find by full name",
                ],
            },
            'get_project_issues': {
                'description': 'Get a list of issues from a specific project. Returns issue details including summary, description, reporter, assignee, and custom fields.',
                'parameter_descriptions': {
                    'project_id': "The project ID (e.g., '0-167') or short name (e.g., 'ITSFT')",
                    'project': 'Alternative parameter name for project_id (use either project_id OR project)',
                    'limit': 'Maximum number of issues to return (optional, default: 50, max: 1000)',
                },
                'examples': [
                    "get_project_issues(project='ITSFT', limit=10) - Get 10 issues from ITSFT project",
                    "get_project_issues(project_id='0-167') - Get default 50 issues",
                ],
            },
            'get_custom_fields': {
                'description': "Get the list of custom fields configured for a project. Returns field definitions including field type, whether it's required, and possible values for enum fields.",
                'parameter_descriptions': {
                    'project_id': "The project ID (e.g., '0-167') or short name (e.g., 'ITSFT')",
                    'project': 'Alternative parameter name for project_id (use either project_id OR project)',
                },
                'examples': ["get_custom_fields(project='ITSFT') - Get custom fields for ITSFT project"],
            },
            'get_project_detailed': {
                'description': 'Get comprehensive project information including all custom fields with their current values extracted from actual issues. Best for understanding what fields are actually used in a project.',
                'parameter_descriptions': {
                    'project_id': "The project ID (e.g., '0-167') or short name (e.g., 'ITSFT')",
                    'project': 'Alternative parameter name for project_id (use either project_id OR project)',
                },
                'examples': [
                    "get_project_detailed(project='ITSFT') - Get all project details including fields analysis"
                ],
                'notes': 'This method analyzes actual issues to determine field usage, making it more accurate than get_custom_fields',
            },
            'get_project_fields': {
                'description': 'Analyze project issues to extract detailed custom field information including field names, types, and actual sample values. Useful for understanding field usage patterns.',
                'parameter_descriptions': {
                    'project_id': "The project ID (e.g., '0-167') or short name (e.g., 'ITSFT')",
                    'project': 'Alternative parameter name for project_id (use either project_id OR project)',
                },
                'examples': ["get_project_fields(project='ITSFT') - Analyze fields used in ITSFT project"],
                'returns': 'Dictionary with field IDs, names, types, sample values, and statistics',
            },
            'create_project': {
                'description': 'Create a new YouTrack project. Requires a project leader to be specified. The short name will be used as a prefix for all issue IDs in this project.',
                'parameter_descriptions': {
                    'name': "The full display name of the project (e.g., 'Customer Support')",
                    'short_name': "The short identifier for the project, used in issue IDs (e.g., 'CS' results in issues like 'CS-1', 'CS-2')",
                    'lead_id': "The user ID of the project leader (required, e.g., '1-621')",
                    'description': "Optional description of the project's purpose",
                },
                'examples': [
                    "create_project(name='Customer Support', short_name='CS', lead_id='1-621', description='Support ticket tracking')"
                ],
                'notes': 'To find user IDs for lead_id, use search_users or get_user_by_login first',
            },
            'update_project': {
                'description': "Update an existing project's properties. All parameters except project_id are optional - only provide what you want to change.",
                'parameter_descriptions': {
                    'project_id': "The project ID to update (e.g., '0-167') or short name (e.g., 'ITSFT')",
                    'project': 'Alternative parameter name for project_id (use either project_id OR project)',
                    'name': 'New display name for the project (optional)',
                    'description': 'New project description (optional)',
                    'archived': 'Set to true to archive the project, false to unarchive (optional)',
                    'lead_id': "New project leader's user ID (optional, e.g., '1-621')",
                    'short_name': 'New short name for the project (optional, affects future issue IDs)',
                },
                'examples': [
                    "update_project(project='ITSFT', description='Updated description')",
                    "update_project(project_id='0-167', archived=true) - Archive a project",
                    "update_project(project='CS', lead_id='1-500', name='Customer Success') - Change leader and name",
                ],
                'warnings': 'Changing short_name only affects new issues; existing issue IDs remain unchanged',
            },
        }
