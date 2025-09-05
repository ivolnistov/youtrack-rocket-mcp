#!/usr/bin/env python3
"""
Final comprehensive test for YouTrack MCP Server.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from youtrack_rocket_mcp.api.client import YouTrackClient
from youtrack_rocket_mcp.api.resources.projects import ProjectsClient
from youtrack_rocket_mcp.api.resources.issues import IssuesClient
from youtrack_rocket_mcp.api.resources.users import UsersClient
from youtrack_rocket_mcp.tools.search import SearchTools


async def main():
    """Run all tests."""
    print("=" * 60)
    print("YOUTRACK MCP SERVER - FINAL TEST RESULTS")
    print("=" * 60)
    
    client = YouTrackClient()
    projects = ProjectsClient(client)
    issues = IssuesClient(client)
    users = UsersClient(client)
    search = SearchTools()
    
    results = []
    
    # Test 1: Connection
    try:
        user = await users.get_current_user()
        results.append(("Connection", "✅", f"Connected as {user.name}"))
    except Exception as e:
        results.append(("Connection", "❌", str(e)))
    
    # Test 2: Projects with leader field
    try:
        project_list = await projects.get_projects()
        project = await projects.get_project('VP')
        results.append(("Projects", "✅", f"{len(project_list)} projects, VP has {len(project.custom_fields)} custom fields"))
    except Exception as e:
        results.append(("Projects", "❌", str(e)))
    
    # Test 3: Custom Fields
    try:
        fields = await projects.get_custom_fields('VP')
        results.append(("Custom Fields", "✅", f"{len(fields)} fields retrieved"))
    except Exception as e:
        results.append(("Custom Fields", "❌", str(e)))
    
    # Test 4: Issue Search
    try:
        search_result = await search.advanced_search("project: VP", limit=2)
        results.append(("Issue Search", "✅", "Advanced search works"))
    except Exception as e:
        results.append(("Issue Search", "❌", str(e)))
    
    # Test 5: Filter Issues
    try:
        filtered = await search.filter_issues(project="VP", state="Open", limit=2)
        results.append(("Filter Issues", "✅", "Filter search works"))
    except Exception as e:
        results.append(("Filter Issues", "❌", str(e)))
    
    # Test 6: User by Login (fixed)
    try:
        user = await users.get_user_by_login("i.volnistov")
        if user:
            results.append(("User by Login", "✅", f"Found {user.name}"))
        else:
            results.append(("User by Login", "❌", "User not found"))
    except Exception as e:
        results.append(("User by Login", "❌", str(e)))
    
    # Test 7: Issue Creation
    try:
        new_issue = await issues.create_issue(
            project_id="VP",
            summary="Test from final_test.py",
            description="Automated test",
            additional_fields={"State": "Open"}
        )
        issue_id = new_issue.idReadable if hasattr(new_issue, 'idReadable') else new_issue.id
        results.append(("Issue Creation", "✅", f"Created {issue_id}"))
        
        # Clean up - add comment
        await issues.add_comment(issue_id, "Test completed")
    except Exception as e:
        results.append(("Issue Creation", "❌", str(e)))
    
    # Print results
    print("\nTest Results:")
    print("-" * 60)
    for test_name, status, message in results:
        print(f"{status} {test_name:20} {message}")
    
    # Summary
    passed = sum(1 for _, status, _ in results if status == "✅")
    total = len(results)
    print("-" * 60)
    print(f"Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The server is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the results above.")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())