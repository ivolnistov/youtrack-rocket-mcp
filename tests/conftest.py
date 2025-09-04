"""
Pytest configuration and shared fixtures.
"""

from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def mock_client():
    """Mock YouTrack API client."""
    client = AsyncMock()
    client.base_url = 'https://test.youtrack.cloud/api'
    client.get = AsyncMock()
    return client


@pytest.fixture
def sample_project_fields():
    """Sample project custom fields response."""
    return [
        {
            'id': '93-1500',
            '$type': 'StateProjectCustomField',
            'field': {'name': 'State', '$type': 'CustomField'},
            'canBeEmpty': False,
        },
        {
            'id': '93-1501',
            '$type': 'EnumProjectCustomField',
            'field': {'name': 'Priority', '$type': 'CustomField'},
            'canBeEmpty': False,
        },
        {
            'id': '93-1507',
            '$type': 'OwnedProjectCustomField',
            'field': {'name': 'Subsystem', '$type': 'CustomField'},
            'canBeEmpty': False,
        },
        {
            'id': '94-191',
            '$type': 'UserProjectCustomField',
            'field': {'name': 'Assignee', '$type': 'CustomField'},
            'canBeEmpty': True,
        },
        {
            'id': '93-2069',
            '$type': 'EnumProjectCustomField',
            'field': {'name': 'Type', '$type': 'CustomField'},
            'canBeEmpty': False,
        },
    ]


@pytest.fixture
def sample_issues_with_fields():
    """Sample issues with custom fields."""
    return [
        {
            'id': 'TEST-1',
            'summary': 'Test Issue 1',
            'customFields': [
                {
                    'id': '93-1500',
                    'name': 'State',
                    '$type': 'StateIssueCustomField',
                    'value': {'name': 'Open', '$type': 'StateBundleElement'},
                    'projectCustomField': {'id': '93-1500'},
                },
                {
                    'id': '93-1501',
                    'name': 'Priority',
                    '$type': 'SingleEnumIssueCustomField',
                    'value': {'name': 'Normal', '$type': 'EnumBundleElement'},
                    'projectCustomField': {'id': '93-1501'},
                },
                {
                    'id': '93-1507',
                    'name': 'Subsystem',
                    '$type': 'SingleOwnedIssueCustomField',
                    'value': {'name': 'Backend', '$type': 'OwnedBundleElement'},
                    'projectCustomField': {'id': '93-1507'},
                },
            ],
        },
        {
            'id': 'TEST-2',
            'summary': 'Test Issue 2',
            'customFields': [
                {
                    'id': '94-191',
                    'name': 'Assignee',
                    '$type': 'SingleUserIssueCustomField',
                    'value': {'login': 'john.doe', 'name': 'John Doe'},
                    'projectCustomField': {'id': '94-191'},
                },
                {
                    'id': '93-2069',
                    'name': 'Type',
                    '$type': 'SingleEnumIssueCustomField',
                    'value': {'name': 'Bug', '$type': 'EnumBundleElement'},
                    'projectCustomField': {'id': '93-2069'},
                },
            ],
        },
    ]


@pytest.fixture
def mock_config():
    """Mock configuration."""
    config = Mock()
    config.YOUTRACK_URL = 'https://test.youtrack.cloud'
    config.YOUTRACK_API_TOKEN = 'test-token'
    config.VERIFY_SSL = True
    return config
