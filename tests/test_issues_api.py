"""
Unit tests for issues API.
"""

from unittest.mock import Mock, patch

import pytest

from youtrack_rocket_mcp.api.client import YouTrackAPIError
from youtrack_rocket_mcp.api.resources.issues import Issue, IssuesClient

# Tests for IssuesClient class


@pytest.fixture
def issues_client(mock_client):
    """Create IssuesClient instance with mock client."""
    return IssuesClient(mock_client)


@pytest.mark.asyncio
async def test_get_issue_success(issues_client, mock_client):
    """Test successfully getting an issue."""
    mock_response = {
        'id': 'TEST-1',
        'summary': 'Test Issue',
        'description': 'Test Description',
        'created': 1234567890,
        'project': {'id': '0-1', 'name': 'Test Project'},
        '$type': 'Issue',
    }
    mock_client.get.return_value = mock_response

    result = await issues_client.get_issue('TEST-1')

    # Check API was called correctly
    assert mock_client.get.call_count == 1
    call_args = mock_client.get.call_args
    assert 'issues/TEST-1' in call_args[0][0]

    # Check result
    assert isinstance(result, Issue)
    assert result.id == 'TEST-1'
    assert result.summary == 'Test Issue'


@pytest.mark.asyncio
async def test_search_issues(issues_client, mock_client):
    """Test searching for issues."""
    mock_response = [
        {'id': 'TEST-1', 'summary': 'Issue 1', '$type': 'Issue'},
        {'id': 'TEST-2', 'summary': 'Issue 2', '$type': 'Issue'},
    ]
    mock_client.get.return_value = mock_response

    result = await issues_client.search_issues('project: TEST', limit=10)

    # Check API was called correctly
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert call_args[0][0] == 'issues'
    assert call_args[1]['params']['query'] == 'project: TEST'
    assert call_args[1]['params']['$top'] == 10

    # Check result
    assert len(result) == 2
    assert all(isinstance(issue, Issue) for issue in result)


@patch('youtrack_rocket_mcp.api.resources.issues.field_cache')
@patch('youtrack_rocket_mcp.api.resources.issues.get_field_types_from_project')
@pytest.mark.asyncio
async def test_create_issue_with_custom_fields(mock_get_field_types, mock_cache, issues_client, mock_client):
    """Test creating an issue with custom fields."""
    # Setup mocks
    mock_cache.get_field_types.return_value = None
    mock_get_field_types.return_value = {
        'Priority': {'type': 'SingleEnumIssueCustomField', 'id': '93-1501'},
        'Subsystem': {'type': 'SingleOwnedIssueCustomField', 'id': '93-1507'},
        'Assignee': {'type': 'SingleUserIssueCustomField', 'id': '94-191'},
    }

    # Mock successful issue creation
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'id': 'TEST-123', '$type': 'Issue'}
    mock_client.client.post.return_value = mock_response
    mock_client.base_url = 'https://test.youtrack.cloud/api'

    # Create issue with custom fields
    await issues_client.create_issue(
        project_id='0-167',
        summary='Test Issue',
        description='Test Description',
        additional_fields={'Priority': 'High', 'Subsystem': 'Backend', 'Assignee': 'john.doe'},
    )

    # Check that field types were fetched
    mock_get_field_types.assert_called_once_with(mock_client, '0-167')

    # Check API call
    mock_client.client.post.assert_called_once()
    call_args = mock_client.client.post.call_args

    # Verify request data
    request_data = call_args[1]['json']
    assert request_data['project']['id'] == '0-167'
    assert request_data['summary'] == 'Test Issue'
    assert request_data['description'] == 'Test Description'

    # Verify custom fields
    custom_fields = request_data['customFields']
    assert len(custom_fields) == 3

    # Check Priority field
    priority_field = next(f for f in custom_fields if f['name'] == 'Priority')
    assert priority_field['$type'] == 'SingleEnumIssueCustomField'
    assert priority_field['value'] == {'name': 'High'}

    # Check Subsystem field
    subsystem_field = next(f for f in custom_fields if f['name'] == 'Subsystem')
    assert subsystem_field['$type'] == 'SingleOwnedIssueCustomField'
    assert subsystem_field['value'] == {'name': 'Backend'}

    # Check Assignee field
    assignee_field = next(f for f in custom_fields if f['name'] == 'Assignee')
    assert assignee_field['$type'] == 'SingleUserIssueCustomField'
    assert assignee_field['value'] == {'login': 'john.doe'}


@patch('youtrack_rocket_mcp.api.resources.issues.field_cache')
@patch('youtrack_rocket_mcp.api.resources.issues.get_field_types_from_project')
@patch('youtrack_rocket_mcp.api.resources.issues.extract_field_types_from_issues')
@pytest.mark.asyncio
async def test_create_issue_fallback_to_issues(
    mock_extract, mock_get_field_types, mock_cache, issues_client, mock_client
):
    """Test fallback to extracting field types from issues."""
    # Setup mocks - no cached types, no project types
    mock_cache.get_field_types.return_value = None
    mock_get_field_types.return_value = None

    # Mock getting issues for field extraction
    sample_issues = [{'id': 'TEST-1', 'customFields': [{'name': 'Priority', '$type': 'SingleEnumIssueCustomField'}]}]
    mock_client.get.return_value = sample_issues

    # Mock field extraction
    mock_extract.return_value = {'Priority': {'type': 'SingleEnumIssueCustomField', 'id': '93-1501'}}

    # Mock successful issue creation
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'id': 'TEST-123', '$type': 'Issue'}
    mock_client.client.post.return_value = mock_response
    mock_client.base_url = 'https://test.youtrack.cloud/api'

    # Create issue
    await issues_client.create_issue(project_id='0-167', summary='Test Issue', additional_fields={'Priority': 'High'})

    # Check that we tried to get issues for field extraction
    mock_client.get.assert_called_once()
    call_args = mock_client.get.call_args
    assert call_args[0][0] == 'issues'
    assert 'query' in call_args[1]['params']

    # Check that field extraction was called
    mock_extract.assert_called_once_with(sample_issues)


@patch('youtrack_rocket_mcp.api.resources.issues.field_cache')
@patch('youtrack_rocket_mcp.api.resources.issues.get_field_types_from_project')
@pytest.mark.asyncio
async def test_create_issue_no_field_types_uses_default(mock_get_field_types, mock_cache, issues_client, mock_client):
    """Test that missing field types use default SingleEnumIssueCustomField."""
    # Setup mocks - no field types available
    mock_cache.get_field_types.return_value = None
    mock_get_field_types.return_value = None
    mock_client.get.side_effect = Exception('Cannot get issues')

    # Mock successful issue creation
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'id': 'TEST-123', '$type': 'Issue'}
    mock_client.client.post.return_value = mock_response
    mock_client.base_url = 'https://test.youtrack.cloud/api'

    # Create issue with unknown field
    await issues_client.create_issue(
        project_id='0-167', summary='Test Issue', additional_fields={'UnknownField': 'Value'}
    )

    # Check API call
    call_args = mock_client.client.post.call_args
    request_data = call_args[1]['json']
    custom_fields = request_data['customFields']

    # Check that default type was used
    unknown_field = custom_fields[0]
    assert unknown_field['name'] == 'UnknownField'
    assert unknown_field['$type'] == 'SingleEnumIssueCustomField'  # Default
    assert unknown_field['value'] == {'name': 'Value'}


@pytest.mark.asyncio
async def test_create_issue_handles_api_error(issues_client, mock_client):
    """Test handling API errors during issue creation."""
    # Mock API error response
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {'error': 'Field required', 'error_field': 'Subsystem'}
    mock_response.text = 'Field required'
    mock_client.client.post.return_value = mock_response
    mock_client.base_url = 'https://test.youtrack.cloud/api'

    # Should raise YouTrackAPIError
    with pytest.raises(YouTrackAPIError) as exc_info:
        await issues_client.create_issue('0-167', 'Test Issue')

    assert 'Field required' in str(exc_info.value)
    assert 'Subsystem' in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_comment(issues_client, mock_client):
    """Test adding a comment to an issue."""
    mock_response = {'id': 'comment-1', 'text': 'Test comment'}
    mock_client.post.return_value = mock_response

    result = await issues_client.add_comment('TEST-1', 'Test comment')

    # Check API was called correctly
    mock_client.post.assert_called_once_with('issues/TEST-1/comments', data={'text': 'Test comment'})

    # Check result
    assert result == mock_response


# Tests for Issue Pydantic model


def test_issue_model_validation():
    """Test Issue model validates correctly."""
    issue_data = {
        'id': 'TEST-1',
        'summary': 'Test Issue',
        'description': 'Description',
        'created': 1234567890,
        'project': {'id': '0-1', 'name': 'Test'},
        'customFields': [{'name': 'Priority', 'value': 'High'}],
    }

    issue = Issue.model_validate(issue_data)

    assert issue.id == 'TEST-1'
    assert issue.summary == 'Test Issue'
    assert issue.description == 'Description'
    assert issue.created == 1234567890
    assert len(issue.custom_fields) == 1
    assert issue.custom_fields[0]['name'] == 'Priority'


def test_issue_model_allows_extra_fields():
    """Test Issue model allows extra fields."""
    issue_data = {'id': 'TEST-1', 'summary': 'Test', 'extraField': 'Extra Value', '$type': 'Issue'}

    issue = Issue.model_validate(issue_data)

    assert issue.id == 'TEST-1'
    # Extra fields should be preserved
    assert hasattr(issue, 'extraField') or '$type' in issue.model_dump()


def test_issue_model_optional_fields():
    """Test Issue model with minimal required fields."""
    issue_data = {'id': 'TEST-1'}

    issue = Issue.model_validate(issue_data)

    assert issue.id == 'TEST-1'
    assert issue.summary is None
    assert issue.description is None
    assert issue.created is None
