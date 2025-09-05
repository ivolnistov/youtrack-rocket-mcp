"""
YouTrack Projects API client.
"""

import json
import logging

from pydantic import BaseModel, Field

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.types import JSONDict, JSONList


class Project(BaseModel):
    """Model for a YouTrack project."""

    id: str
    name: str
    shortName: str  # noqa: N815
    description: str | None = None
    archived: bool = False
    created: int | None = None
    updated: int | None = None
    leader: JSONDict | None = None
    custom_fields: JSONList = Field(default_factory=list)


class ProjectsClient:
    """Client for interacting with YouTrack Projects API."""

    def __init__(self, client: YouTrackClient):
        """
        Initialize the Projects API client.

        Args:
            client: The YouTrack API client
        """
        self.client = client

    async def get_projects(self, include_archived: bool = False) -> list[Project]:
        """
        Get all projects.

        Args:
            include_archived: Whether to include archived projects

        Returns:
            List of projects
        """
        params = {'fields': 'id,name,shortName,description,archived,created,updated,leader(id,name,login)'}
        if not include_archived:
            params['$filter'] = 'archived eq false'

        response = await self.client.get('admin/projects', params=params)
        return [Project.model_validate(project) for project in response]

    async def get_project(self, project_id: str) -> Project:
        """
        Get a project by ID with custom fields.

        Args:
            project_id: The project ID

        Returns:
            The project data with custom fields
        """
        response = await self.client.get(
            f'admin/projects/{project_id}',
            params={'fields': 'id,name,shortName,description,archived,created,updated,leader(id,name,login)'},
        )

        # Get custom fields for this specific project
        try:
            custom_fields = await self.get_custom_fields(project_id)
            response['custom_fields'] = custom_fields
        except Exception as e:
            # Log error but don't fail if we can't get custom fields
            logger = logging.getLogger(__name__)
            logger.warning(f'Could not fetch custom fields for project {project_id}: {e}')
            response['custom_fields'] = []

        return Project.model_validate(response)

    async def get_project_by_name(self, project_name: str) -> Project | None:
        """
        Get a project by its name or short name.

        Args:
            project_name: The project name or short name

        Returns:
            The project data or None if not found
        """
        projects = await self.get_projects(include_archived=True)

        # First try to match by short name (exact match)
        for project in projects:
            if project.shortName.lower() == project_name.lower():
                return project

        # Then try to match by full name (case insensitive)
        for project in projects:
            if project.name.lower() == project_name.lower():
                return project

        # Finally try to match if project_name is contained in the name
        for project in projects:
            if project_name.lower() in project.name.lower():
                return project

        return None

    async def get_project_issues(self, project_id: str, limit: int = 10) -> JSONList:
        """
        Get issues for a specific project.

        Args:
            project_id: The project ID
            limit: Maximum number of issues to return

        Returns:
            List of issues in the project
        """
        logger = logging.getLogger(__name__)
        logger.info(f'Getting issues for project {project_id}, limit {limit}')

        # Request more fields to get complete issue information
        fields = (
            'id,summary,description,created,updated,'
            'reporter(id,login,name),assignee(id,login,name),'
            'project(id,name,shortName),'
            'customFields(id,name,value($type,name,text,id),projectCustomField(field(name)))'
        )

        # First try to get project by shortName if project_id looks like a short name
        if project_id and not project_id.startswith('0-'):
            # This might be a short name, try to find the project first
            project = await self.get_project_by_name(project_id)
            if project:
                project_id = project.id
                logger.info(f'Resolved project short name to ID: {project_id}')

        params = {'$filter': f'project/id eq "{project_id}"', '$top': limit, 'fields': fields}

        try:
            issues = await self.client.get('issues', params=params)
            logger.info(f'Retrieved {len(issues) if isinstance(issues, list) else 0} issues')
        except Exception:
            logger.exception(f'Error getting issues for project {project_id}')
            # Return empty list on error
            return []
        else:
            return issues

    async def create_project(
        self, name: str, short_name: str, description: str | None = None, lead_id: str | None = None
    ) -> Project:
        """
        Create a new project.

        Args:
            name: The project name
            short_name: The project short name (used in issue IDs)
            description: Optional project description
            lead_id: Optional project lead user ID

        Returns:
            The created project data
        """
        if not name:
            raise ValueError('Project name is required')
        if not short_name:
            raise ValueError('Project short name is required')

        data = {'name': name, 'shortName': short_name}

        if description:
            data['description'] = description

        if lead_id:
            # The YouTrack API expects "leader", not "lead_id"
            data['leader'] = {'id': lead_id}  # type: ignore[assignment]

        # Debug logging
        logger = logging.getLogger(__name__)
        logger.info(f'Creating project with data: {json.dumps(data)}')
        logger.info(f'Base URL: {self.client.base_url}, API endpoint: admin/projects')

        try:
            response = await self.client.post('admin/projects', data=data)
            logger.info(f'Create project response: {json.dumps(response)}')

            # The response might not include all required fields,
            # Try to get the complete project now
            if isinstance(response, dict) and 'id' in response:
                try:
                    # Get the full project details
                    created_project = await self.get_project(response['id'])
                    logger.info(f'Successfully retrieved full project details: {created_project.name}')
                except Exception as e:
                    logger.warning(f'Could not retrieve full project details: {e!s}')
                    # Fall back to creating a model with the available data
                    # We need to ensure shortName is present
                    if 'shortName' not in response and short_name:
                        response['shortName'] = short_name
                    if 'name' not in response and name:
                        response['name'] = name
                else:
                    return created_project

            # Try to validate the model, which might fail if fields are missing
            try:
                return Project.model_validate(response)
            except Exception as e:
                logger.warning(f'Could not validate project model: {e!s}')
                # As a last resort, create a minimal valid project
                minimal_project = {
                    'id': response.get('id', 'unknown'),
                    'name': name,
                    'shortName': short_name,
                    'description': description,
                }
                return Project.model_validate(minimal_project)
        except Exception:
            logger.exception('Error creating project')
            raise

    async def update_project(
        self,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
        lead_id: str | None = None,
        archived: bool | None = None,
    ) -> Project:
        """
        Update an existing project.

        Args:
            project_id: The project ID
            name: The new project name
            description: The new project description
            lead_id: The new project lead user ID
            archived: Whether the project should be archived

        Returns:
            The updated project data
        """
        # First get the existing project data
        logger = logging.getLogger(__name__)
        logger.info(f'Getting existing project data for {project_id}')

        try:
            # Prepare data for update API call
            data = {}

            # Include any provided parameters
            if name is not None:
                data['name'] = name
            if description is not None:
                data['description'] = description
            if lead_id is not None:
                data['leader'] = {'id': lead_id}  # type: ignore[assignment]
            if archived is not None:
                data['archived'] = archived  # type: ignore[assignment]

            # Make sure we have at least one parameter to update
            if not data:
                logger.info('No parameters to update, returning current project data')
                return await self.get_project(project_id)

            logger.info(f'Updating project with data: {data}')
            response = await self.client.post(f'admin/projects/{project_id}', data=data)
            logger.info(f'Update project response: {response}')

            # The API response might not contain all required fields,
            # so we need to get the full project data after the update
            try:
                # Get the updated project data
                updated_project = await self.get_project(project_id)
                logger.info(f'Successfully retrieved updated project: {updated_project.name}')
            except Exception:
                logger.exception('Error getting updated project')
                # If we can't get the updated project, create a partial project with the data we have
                if isinstance(response, dict) and 'id' in response:
                    logger.info(f'Creating partial project from response: {response}')
                    # Try to get the original project to fill in missing fields
                    try:
                        original_project = await self.get_project(project_id)
                        # Update with new values
                        for key, value in data.items():
                            if key == 'leader':
                                original_project.leader = value  # type: ignore[assignment]
                            else:
                                setattr(original_project, key, value)
                    except Exception:
                        # If we can't get the original project either, just return the response
                        logger.warning(f'Unable to get original project, returning response: {response}')
                        return response  # type: ignore[return-value]
                    else:
                        return original_project
                else:
                    # If the response doesn't have an ID, just return it
                    return response
            else:
                return updated_project
        except Exception:
            logger.exception(f'Error updating project {project_id}')
            raise

    async def delete_project(self, project_id: str) -> None:
        """
        Delete a project.

        Args:
            project_id: The project ID
        """
        await self.client.delete(f'admin/projects/{project_id}')

    async def get_custom_fields(self, project_id: str) -> JSONList:
        """
        Get custom fields for a project with detailed information.

        Args:
            project_id: The project ID

        Returns:
            List of custom fields with detailed information including names and possible values
        """
        # Use comprehensive fields parameter to get all available information
        # Based on YouTrack API documentation for ProjectCustomField entities
        fields = (
            'id,canBeEmpty,emptyFieldText,ordinal,isPublic,field(id,name,fieldType(id,valueType,presentation)),$type'
        )

        # For bundle-based fields (Enum, State, etc.), we need to fetch bundle values separately
        # The bundle field is only available on specific subtypes like EnumProjectCustomField
        params = {'fields': fields}

        logger = logging.getLogger(__name__)
        try:
            result = await self.client.get(f'admin/projects/{project_id}/customFields', params=params)
            field_count = len(result) if isinstance(result, list) else 0
            logger.info(f'Successfully retrieved {field_count} custom fields for project {project_id}')

            # Now enhance the result with bundle values for applicable field types
            enhanced_fields = []
            for field in result:
                field_type = field.get('$type', '')

                # For bundle-based field types, try to get the bundle values
                if field_type in [
                    'EnumProjectCustomField',
                    'StateProjectCustomField',
                    'OwnedProjectCustomField',
                    'VersionProjectCustomField',
                ]:
                    try:
                        # Try to get this specific field with bundle information
                        field_id = field.get('id')
                        if field_id:
                            bundle_fields = 'id,field(name),bundle(id,values(id,name,description,archived,ordinal))'
                            bundle_params = {'fields': bundle_fields}

                            # Get the specific field with bundle info
                            field_with_bundle = await self.client.get(
                                f'admin/projects/{project_id}/customFields/{field_id}', params=bundle_params
                            )

                            # Merge the bundle info into the original field
                            if 'bundle' in field_with_bundle:
                                field['bundle'] = field_with_bundle['bundle']
                    except Exception as bundle_error:
                        logger.debug(f'Could not get bundle for field {field.get("id")}: {bundle_error!s}')

                enhanced_fields.append(field)

        except Exception:
            logger.exception(f'Error getting detailed custom fields for project {project_id}')
            # Fallback to basic request without fields parameter
            try:
                basic_result = await self.client.get(f'admin/projects/{project_id}/customFields')
                logger.warning(f'Falling back to basic custom fields request for project {project_id}')
            except Exception:
                logger.exception('Fallback request also failed')
                raise
            else:
                return basic_result
        else:
            return enhanced_fields

    async def add_custom_field(self, project_id: str, field_id: str, empty_field_text: str | None = None) -> JSONDict:
        """
        Add a custom field to a project.

        Args:
            project_id: The project ID
            field_id: The custom field ID
            empty_field_text: Optional text to show for empty fields

        Returns:
            The added custom field
        """
        data = {'field': {'id': field_id}}

        if empty_field_text:
            data['emptyFieldText'] = empty_field_text  # type: ignore[assignment]

        return await self.client.post(f'admin/projects/{project_id}/customFields', data=data)

    async def get_project_fields_from_issues(self, project_id: str) -> JSONDict:
        """
        Get project custom field information by analyzing actual issues in the project.
        This is a workaround for when the admin API doesn't return detailed field info.

        Args:
            project_id: The project ID

        Returns:
            Dictionary with field information extracted from issues
        """
        logger = logging.getLogger(__name__)

        try:
            # Get sample issues from the project
            issues = await self.get_project_issues(project_id, limit=10)

            # Analyze custom fields from the issues
            field_info = {}

            for issue in issues:
                custom_fields = issue.get('customFields', [])
                for field in custom_fields:
                    field_id = field.get('id')
                    field_name = field.get('name')
                    field_type = field.get('$type', '')

                    if field_id and field_name:
                        if field_id not in field_info:
                            field_info[field_id] = {
                                'id': field_id,
                                'name': field_name,
                                'type': field_type,
                                'sample_values': set(),
                                'is_required': False,
                                'value_type': None,
                            }

                        # Analyze the value to understand the field type
                        value = field.get('value')
                        if value is not None:
                            if isinstance(value, dict):
                                if '$type' in value:
                                    field_info[field_id]['value_type'] = value.get('$type')
                                    display_value = (
                                        value.get('name') or value.get('text') or value.get('login') or str(value)
                                    )
                                else:
                                    display_value = str(value)
                            elif isinstance(value, list):
                                field_info[field_id]['value_type'] = 'array'
                                display_value = (
                                    f'[{", ".join(str(v) for v in value[:3])}{"..." if len(value) > 3 else ""}]'
                                )
                            else:
                                display_value = str(value)

                            field_info[field_id]['sample_values'].add(display_value)

            # Convert sets to lists for JSON serialization
            for _field_id, field_data in field_info.items():
                field_data['sample_values'] = list(field_data['sample_values'])

            return {
                'project_id': project_id,
                'fields': list(field_info.values()),
                'total_fields': len(field_info),
                'analyzed_issues': len(issues),
            }

        except Exception:
            logger.exception(f'Error analyzing project fields from issues for {project_id}')
            raise

    async def get_project_detailed(self, project_id: str) -> JSONDict:
        """
        Get detailed project information including custom fields with their names, possible values,
        and requirement status.

        This method combines multiple API calls to provide comprehensive information about:
        - Basic project information (name, description, etc.)
        - Custom fields configured for the project
        - Possible values for enum/bundle fields
        - Whether each field is required or optional
        - Sample values from existing issues

        Args:
            project_id: The project ID or short name (e.g., 'ITSFT' or '0-167')

        Returns:
            Detailed project information with custom fields, including:
            - project info: Basic project details
            - custom_fields: List of all custom fields with:
                - id: Field ID for API calls
                - name: Human-readable field name
                - type: Field type (enum, state, user, date, etc.)
                - required: Whether the field is required
                - possible_values: For enum fields, list of valid values
                - empty_text: Text shown when field is empty
        """
        logger = logging.getLogger(__name__)

        try:
            # First resolve project ID if short name was provided
            if project_id and not project_id.startswith('0-'):
                logger.info(f"Resolving project short name '{project_id}' to ID")
                project = await self.get_project_by_name(project_id)
                if project:
                    project_id = project.id
                    logger.info(f'Resolved to project ID: {project_id}')

            # Get basic project info
            project_info = await self.get_project(project_id)

            # Get custom fields with bundle information
            custom_fields = await self.get_custom_fields(project_id)

            # Get field information from existing issues for additional context
            fields_from_issues = await self.get_project_fields_from_issues(project_id)

            # Create a comprehensive field map
            field_details = []
            for field in custom_fields:
                field_detail = {
                    'id': field.get('id'),
                    'name': field.get('field', {}).get('name', 'Unknown'),
                    'type': field.get('$type', ''),
                    'required': not field.get('canBeEmpty', True),
                    'empty_text': field.get('emptyFieldText', ''),
                    'ordinal': field.get('ordinal', 999),
                    'is_public': field.get('isPublic', True),
                    'possible_values': [],
                }

                # Extract possible values from bundle if available
                if 'bundle' in field and 'values' in field['bundle']:
                    field_detail['possible_values'] = [
                        {
                            'id': val.get('id'),
                            'name': val.get('name'),
                            'description': val.get('description'),
                            'archived': val.get('archived', False),
                        }
                        for val in field['bundle']['values']
                        if not val.get('archived', False)  # Exclude archived values by default
                    ]

                # Add sample values from issues if available
                field_id = field.get('id')
                for issue_field in fields_from_issues.get('fields', []):
                    if issue_field.get('id') == field_id:
                        field_detail['sample_values'] = issue_field.get('sample_values', [])
                        break

                field_details.append(field_detail)

            # Sort fields by ordinal to match UI order
            field_details.sort(key=lambda x: x.get('ordinal', 999))

            # Combine all information
            return {
                'project': project_info.model_dump() if hasattr(project_info, 'model_dump') else project_info,
                'custom_fields': field_details,
                'total_fields': len(field_details),
                'required_fields': [f for f in field_details if f['required']],
                'usage_hint': (
                    'When creating issues in this project:\n'
                    "1. Use the 'id' field value when setting custom fields\n"
                    "2. For enum/bundle fields, use values from 'possible_values'\n"
                    '3. Required fields must be provided or the issue creation will fail\n'
                    '4. For user fields, provide user ID or login\n'
                    '5. For date fields, use timestamp in milliseconds'
                ),
            }

        except Exception:
            logger.exception(f'Error getting detailed project info for {project_id}')
            raise
