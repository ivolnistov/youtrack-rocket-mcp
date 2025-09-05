#!/usr/bin/env python3
"""
Comprehensive test for all YouTrack MCP Server functions.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.resources.projects import ProjectsClient
from youtrack_rocket_mcp.api.resources.issues import IssuesClient
from youtrack_rocket_mcp.api.resources.users import UsersClient
from youtrack_rocket_mcp.api.resources.search import SearchClient


async def test_all_functions():
    """Test all YouTrack functions."""
    client = YouTrackClient()
    projects_api = ProjectsClient(client)
    issues_api = IssuesClient(client)
    users_api = UsersClient(client)
    search_api = SearchClient(client)
    
    print("=" * 60)
    print("YOUTRACK MCP SERVER - COMPREHENSIVE FUNCTION TEST")
    print("=" * 60)
    
    # Test 1: Connection
    print("\n1. Testing Connection...")
    try:
        current_user = await users_api.get_current_user()
        print(f"   ✅ Connected as: {current_user.name} ({current_user.login})")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # Test 2: Projects
    print("\n2. Testing Projects...")
    try:
        # Get all projects
        projects = await projects_api.get_projects()
        print(f"   ✅ Found {len(projects)} projects")
        
        # Get single project with custom fields
        if projects:
            project = await projects_api.get_project(projects[0].id)
            print(f"   ✅ Retrieved project: {project.shortName}")
            print(f"   ✅ Custom fields: {len(project.custom_fields)} fields")
            print(f"   ✅ Leader field: {'Present' if project.leader else 'None'}")
    except Exception as e:
        print(f"   ❌ Projects test failed: {e}")
    
    # Test 3: Custom Fields
    print("\n3. Testing Custom Fields...")
    try:
        custom_fields = await projects_api.get_custom_fields('VP')
        print(f"   ✅ Retrieved {len(custom_fields)} custom fields for VP project")
        if custom_fields:
            field = custom_fields[0]
            field_name = field.get('field', {}).get('name', 'Unknown')
            print(f"   ✅ First field: {field_name}")
    except Exception as e:
        print(f"   ❌ Custom fields test failed: {e}")
    
    # Test 4: Issues
    print("\n4. Testing Issues...")
    try:
        # Search issues
        issues = await search_api.search_issues("project: VP", limit=3)
        print(f"   ✅ Found {len(issues)} issues in VP project")
        
        if issues:
            # Get issue details
            issue_id = issues[0].get('idReadable', issues[0].get('id'))
            issue = await issues_api.get_issue(issue_id)
            print(f"   ✅ Retrieved issue: {issue.get('idReadable', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Issues test failed: {e}")
    
    # Test 5: Users
    print("\n5. Testing Users...")
    try:
        # Search users
        users = await users_api.search_users("volnistov", limit=3)
        print(f"   ✅ Found {len(users)} users matching 'volnistov'")
        
        # Get user by login (fixed method)
        user = await users_api.get_user_by_login("i.volnistov")
        if user:
            print(f"   ✅ get_user_by_login works: {user.name}")
        else:
            print(f"   ❌ get_user_by_login returned None")
            
    except Exception as e:
        print(f"   ❌ Users test failed: {e}")
    
    # Test 6: Search
    print("\n6. Testing Search...")
    try:
        # Advanced search
        results = await search_api.advanced_search(
            "project: VP State: Open",
            limit=5
        )
        print(f"   ✅ Advanced search found {len(results)} results")
    except Exception as e:
        print(f"   ❌ Search test failed: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_all_functions())