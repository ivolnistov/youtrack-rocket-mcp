"""
Unit tests for field_cache module.
"""

from datetime import timedelta

import pytest

from youtrack_rocket_mcp.api.field_cache import (
    FieldTypeCache,
    extract_field_types_from_issues,
    get_field_types_from_project,
)

# Tests for FieldTypeCache class


def test_cache_initialization():
    """Test cache initializes correctly."""
    cache = FieldTypeCache(cache_duration_minutes=30)
    assert cache.cache_duration == timedelta(minutes=30)
    assert cache._cache == {}
    assert cache._cache_timestamps == {}


def test_set_and_get_field_types():
    """Test setting and getting field types from cache."""
    cache = FieldTypeCache()
    project_id = 'TEST-PROJECT'
    field_types = {
        'Priority': {'type': 'SingleEnumIssueCustomField', 'id': '93-1501'},
        'State': {'type': 'StateIssueCustomField', 'id': '93-1500'},
    }

    # Set field types
    cache.set_field_types(project_id, field_types)

    # Get field types - should return cached value
    cached = cache.get_field_types(project_id)
    assert cached == field_types


def test_cache_expiration():
    """Test that cache expires after duration."""
    cache = FieldTypeCache(cache_duration_minutes=0)  # Instant expiration
    project_id = 'TEST-PROJECT'
    field_types = {'Priority': {'type': 'SingleEnumIssueCustomField'}}

    cache.set_field_types(project_id, field_types)

    # Should return None as cache expired immediately
    cached = cache.get_field_types(project_id)
    assert cached is None


def test_clear_project_cache():
    """Test clearing cache for specific project."""
    cache = FieldTypeCache()
    project1 = 'PROJECT-1'
    project2 = 'PROJECT-2'

    cache.set_field_types(project1, {'Field1': {'type': 'Type1'}})
    cache.set_field_types(project2, {'Field2': {'type': 'Type2'}})

    # Clear cache for project1
    cache.clear_project_cache(project1)

    # Project1 cache should be cleared
    assert cache.get_field_types(project1) is None
    # Project2 cache should remain
    assert cache.get_field_types(project2) is not None


def test_clear_all_cache():
    """Test clearing all cache."""
    cache = FieldTypeCache()

    cache.set_field_types('PROJECT-1', {'Field1': {'type': 'Type1'}})
    cache.set_field_types('PROJECT-2', {'Field2': {'type': 'Type2'}})

    # Clear all cache
    cache.clear_all_cache()

    # All caches should be cleared
    assert cache.get_field_types('PROJECT-1') is None
    assert cache.get_field_types('PROJECT-2') is None


# Tests for extract_field_types_from_issues function


def test_extract_from_empty_issues():
    """Test extracting from empty issue list."""
    result = extract_field_types_from_issues([])
    assert result == {}


def test_extract_from_issues_with_fields(sample_issues_with_fields):
    """Test extracting field types from issues."""
    result = extract_field_types_from_issues(sample_issues_with_fields)

    # Check that all fields were extracted
    assert 'State' in result
    assert 'Priority' in result
    assert 'Subsystem' in result
    assert 'Assignee' in result
    assert 'Type' in result

    # Check correct types
    assert result['State']['type'] == 'StateIssueCustomField'
    assert result['Priority']['type'] == 'SingleEnumIssueCustomField'
    assert result['Subsystem']['type'] == 'SingleOwnedIssueCustomField'
    assert result['Assignee']['type'] == 'SingleUserIssueCustomField'
    assert result['Type']['type'] == 'SingleEnumIssueCustomField'

    # Check IDs are preserved
    assert result['State']['id'] == '93-1500'
    assert result['Priority']['id'] == '93-1501'


def test_extract_handles_missing_type():
    """Test that fields without $type are skipped."""
    issues = [
        {
            'id': 'TEST-1',
            'customFields': [
                {'name': 'Field1', '$type': 'SingleEnumIssueCustomField'},
                {'name': 'Field2'},  # Missing $type
                {'name': 'Field3', '$type': 'StateIssueCustomField'},
            ],
        }
    ]

    result = extract_field_types_from_issues(issues)

    # Only fields with $type should be included
    assert 'Field1' in result
    assert 'Field2' not in result
    assert 'Field3' in result


def test_extract_handles_missing_name():
    """Test that fields without name are skipped."""
    issues = [
        {
            'id': 'TEST-1',
            'customFields': [
                {'name': 'Field1', '$type': 'SingleEnumIssueCustomField'},
                {'$type': 'StateIssueCustomField'},  # Missing name
            ],
        }
    ]

    result = extract_field_types_from_issues(issues)

    # Only fields with name should be included
    assert 'Field1' in result
    assert len(result) == 1


# Tests for get_field_types_from_project function


@pytest.mark.asyncio
async def test_get_field_types_success(mock_client, sample_project_fields):
    """Test successfully getting field types from project."""
    mock_client.get.return_value = sample_project_fields

    result = await get_field_types_from_project(mock_client, '0-167')

    # Check API was called correctly
    mock_client.get.assert_called_once_with(
        'admin/projects/0-167/customFields', params={'fields': 'id,field(name),canBeEmpty,$type'}
    )

    # Check all fields were processed
    assert 'State' in result
    assert 'Priority' in result
    assert 'Subsystem' in result
    assert 'Assignee' in result
    assert 'Type' in result

    # Check type mapping
    assert result['State']['type'] == 'StateIssueCustomField'
    assert result['Priority']['type'] == 'SingleEnumIssueCustomField'
    assert result['Subsystem']['type'] == 'SingleOwnedIssueCustomField'
    assert result['Assignee']['type'] == 'SingleUserIssueCustomField'

    # Check required flag
    assert result['State']['required']
    assert result['Priority']['required']
    assert not result['Assignee']['required']


@pytest.mark.asyncio
async def test_get_field_types_handles_api_error(mock_client):
    """Test handling API errors gracefully."""
    mock_client.get.side_effect = Exception('API Error')

    result = await get_field_types_from_project(mock_client, '0-167')

    # Should return None on error
    assert result is None


@pytest.mark.asyncio
async def test_get_field_types_handles_missing_field_name(mock_client):
    """Test handling fields without names."""
    mock_client.get.return_value = [
        {
            'id': '93-1500',
            '$type': 'StateProjectCustomField',
            # Missing field.name
            'canBeEmpty': False,
        },
        {'id': '93-1501', '$type': 'EnumProjectCustomField', 'field': {'name': 'Priority'}, 'canBeEmpty': False},
    ]

    result = await get_field_types_from_project(mock_client, '0-167')

    # Only field with name should be included
    assert result is not None
    assert 'Priority' in result
    assert len(result) == 1


@pytest.mark.parametrize(
    'project_type,expected_issue_type',
    [
        ('EnumProjectCustomField', 'SingleEnumIssueCustomField'),
        ('StateProjectCustomField', 'StateIssueCustomField'),
        ('UserProjectCustomField', 'SingleUserIssueCustomField'),
        ('OwnedProjectCustomField', 'SingleOwnedIssueCustomField'),
        ('DateProjectCustomField', 'DateIssueCustomField'),
        ('PeriodProjectCustomField', 'PeriodIssueCustomField'),
        ('SimpleProjectCustomField', 'SimpleIssueCustomField'),
        ('TextProjectCustomField', 'TextIssueCustomField'),
        ('VersionProjectCustomField', 'SingleVersionIssueCustomField'),
        ('BuildProjectCustomField', 'SingleBuildIssueCustomField'),
        ('MultiEnumProjectCustomField', 'MultiEnumIssueCustomField'),
        ('UnknownProjectCustomField', 'SingleEnumIssueCustomField'),  # Default
    ],
)
@pytest.mark.asyncio
async def test_type_mapping(mock_client, project_type, expected_issue_type):
    """Test ProjectCustomField to IssueCustomField mapping."""
    mock_client.get.return_value = [
        {'id': 'test-id', '$type': project_type, 'field': {'name': 'TestField'}, 'canBeEmpty': True}
    ]

    result = await get_field_types_from_project(mock_client, '0-167')

    assert result is not None
    assert result['TestField']['type'] == expected_issue_type
