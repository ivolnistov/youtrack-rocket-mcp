"""
Integration tests for YouTrack MCP issue creation flow.
"""

import json
from unittest.mock import AsyncMock, Mock

import pytest

from youtrack_rocket_mcp.api.field_cache import field_cache
from youtrack_rocket_mcp.api.resources.issues import IssuesClient
from youtrack_rocket_mcp.tools.issues import IssueTools


@pytest.fixture
def mock_youtrack_services(mocker):
    """Mock all YouTrack service dependencies."""
    # Mock client
    mock_client = AsyncMock()
    mocker.patch('youtrack_rocket_mcp.tools.issues.YouTrackClient', return_value=mock_client)

    # Mock projects client
    mock_projects = AsyncMock()
    mock_projects.get_project_by_name = AsyncMock()
    mocker.patch('youtrack_rocket_mcp.tools.issues.ProjectsClient', return_value=mock_projects)

    # Mock issues client
    mock_issues = AsyncMock()
    mock_issues.create_issue = AsyncMock()
    mocker.patch('youtrack_rocket_mcp.tools.issues.IssuesClient', return_value=mock_issues)

    return {'client': mock_client, 'projects': mock_projects, 'issues': mock_issues}


@pytest.mark.asyncio
async def test_create_issue_complete_flow(mock_youtrack_services):
    """Test complete flow from tool to API with field type detection."""
    # Setup project mock
    mock_project = Mock()
    mock_project.id = '0-167'
    mock_project.name = 'IT Software'
    mock_youtrack_services['projects'].get_project_by_name.return_value = mock_project

    # Setup issue creation response
    mock_issue = Mock()
    mock_issue.id = 'ITSFT-123'
    mock_issue.summary = 'Test Issue'
    mock_issue.model_dump.return_value = {'id': 'ITSFT-123', 'summary': 'Test Issue', '$type': 'Issue'}
    mock_youtrack_services['issues'].create_issue.return_value = mock_issue

    # Create issue using IssueTools
    tools = IssueTools()
    result_json = await tools.create_issue(
        project='ITSFT',
        summary='Test Issue',
        description='Test Description',
        custom_fields={'Priority': 'Normal', 'Subsystem': 'Backend'},
    )

    # Parse result
    result = json.loads(result_json)

    # Verify project lookup
    mock_youtrack_services['projects'].get_project_by_name.assert_called_once_with('ITSFT')

    # Verify issue creation
    mock_youtrack_services['issues'].create_issue.assert_called_once()
    call_args = mock_youtrack_services['issues'].create_issue.call_args
    assert call_args[0][0] == '0-167'  # project_id
    assert call_args[0][1] == 'Test Issue'  # summary
    assert call_args[0][2] == 'Test Description'  # description
    assert call_args[0][3] == {'Priority': 'Normal', 'Subsystem': 'Backend'}  # custom_fields

    # Verify result
    assert result['id'] == 'ITSFT-123'
    assert result['summary'] == 'Test Issue'


@pytest.mark.asyncio
async def test_field_type_caching_flow(mocker):
    """Test that field types are cached and reused."""

    # Clear cache
    field_cache.clear_all_cache()

    # Setup mock client
    mock_client = AsyncMock()
    mock_client.base_url = 'https://test.youtrack.cloud/api'
    mock_client.client = AsyncMock()
    mocker.patch('youtrack_rocket_mcp.api.client.YouTrackClient', return_value=mock_client)

    # Setup field types from project
    mock_get_field_types = mocker.patch('youtrack_rocket_mcp.api.resources.issues.get_field_types_from_project')
    mock_get_field_types.return_value = {
        'Priority': {'type': 'SingleEnumIssueCustomField', 'id': '93-1501', 'required': True},
        'Subsystem': {'type': 'SingleOwnedIssueCustomField', 'id': '93-1507', 'required': True},
    }

    # Mock successful POST response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'id': 'TEST-1', '$type': 'Issue'}
    mock_client.client.post.return_value = mock_response

    # Create issues client
    issues_client = IssuesClient(mock_client)

    # First issue creation - should fetch field types
    await issues_client.create_issue(
        '0-167', 'First Issue', additional_fields={'Priority': 'Normal', 'Subsystem': 'Backend'}
    )

    # Verify field types were fetched
    assert mock_get_field_types.call_count == 1

    # Second issue creation - should use cached field types
    await issues_client.create_issue(
        '0-167', 'Second Issue', additional_fields={'Priority': 'High', 'Subsystem': 'Frontend'}
    )

    # Field types should NOT be fetched again (still 1 call)
    assert mock_get_field_types.call_count == 1

    # Verify both issues were created with correct field types
    assert mock_client.client.post.call_count == 2

    # Check first issue request
    first_call = mock_client.client.post.call_args_list[0]
    first_data = first_call[1]['json']
    assert first_data['customFields'][0]['$type'] == 'SingleEnumIssueCustomField'
    assert first_data['customFields'][1]['$type'] == 'SingleOwnedIssueCustomField'

    # Check second issue request
    second_call = mock_client.client.post.call_args_list[1]
    second_data = second_call[1]['json']
    assert second_data['customFields'][0]['$type'] == 'SingleEnumIssueCustomField'
    assert second_data['customFields'][1]['$type'] == 'SingleOwnedIssueCustomField'


@pytest.mark.asyncio
async def test_error_handling_flow(mock_youtrack_services):
    """Test error handling through the complete flow."""
    # Project not found
    mock_youtrack_services['projects'].get_project_by_name.return_value = None

    # Create issue using IssueTools
    tools = IssueTools()
    result_json = await tools.create_issue(project='NONEXISTENT', summary='Test Issue')

    # Parse result
    result = json.loads(result_json)

    # Should return error
    assert 'error' in result
    assert 'Project not found' in result['error']


@pytest.mark.asyncio
async def test_fallback_to_issues_flow(mocker):
    """Test fallback to extracting field types from issues."""

    # Clear cache
    field_cache.clear_all_cache()

    # Setup mock client
    mock_client = AsyncMock()
    mock_client.base_url = 'https://test.youtrack.cloud/api'
    mock_client.client = AsyncMock()
    mocker.patch('youtrack_rocket_mcp.api.client.YouTrackClient', return_value=mock_client)

    # Project field types not available
    mock_get_field_types = mocker.patch('youtrack_rocket_mcp.api.resources.issues.get_field_types_from_project')
    mock_get_field_types.return_value = None

    # Mock getting issues
    sample_issues = [
        {
            'id': 'TEST-1',
            'customFields': [{'name': 'Priority', '$type': 'SingleEnumIssueCustomField', 'value': {'name': 'Normal'}}],
        }
    ]
    mock_client.get.return_value = sample_issues

    # Mock field extraction
    mock_extract = mocker.patch('youtrack_rocket_mcp.api.resources.issues.extract_field_types_from_issues')
    mock_extract.return_value = {'Priority': {'type': 'SingleEnumIssueCustomField', 'id': '93-1501'}}

    # Mock successful POST response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'id': 'TEST-1', '$type': 'Issue'}
    mock_client.client.post.return_value = mock_response

    # Create issues client
    issues_client = IssuesClient(mock_client)

    # Create issue - should fallback to extracting from issues
    await issues_client.create_issue('0-167', 'Test Issue', additional_fields={'Priority': 'High'})

    # Verify attempted to get field types from project
    assert mock_get_field_types.called

    # Verify fetched issues for field extraction
    mock_client.get.assert_called_once()
    assert 'issues' in mock_client.get.call_args[0][0]

    # Verify field extraction was called
    mock_extract.assert_called_once_with(sample_issues)
