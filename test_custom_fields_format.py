#!/usr/bin/env python3
"""
Test custom fields formatting.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from youtrack_rocket_mcp.tools.issues import IssueTools
from youtrack_rocket_mcp.tools.search import SearchTools


async def main():
    """Test custom fields formatting."""
    issue_tools = IssueTools()
    search_tools = SearchTools()
    
    print("=" * 60)
    print("TESTING CUSTOM FIELDS FORMATTING")
    print("=" * 60)
    
    # Test 1: Get single issue
    print("\n1. Testing get_issue with custom fields...")
    result = await issue_tools.get_issue("VP-817")
    data = json.loads(result)
    
    if 'custom_fields' in data:
        print("   ✅ custom_fields present as dictionary")
        print("   Custom fields:")
        for field_name, field_value in data['custom_fields'].items():
            print(f"     - {field_name}: {field_value}")
    else:
        print("   ❌ custom_fields not found")
    
    # Test 2: Search issues
    print("\n2. Testing search_issues with custom fields...")
    result = await issue_tools.search_issues("project: VP", limit=2)
    data = json.loads(result)
    
    if isinstance(data, list) and len(data) > 0:
        first_issue = data[0]
        if 'custom_fields' in first_issue:
            print("   ✅ custom_fields present in search results")
            print("   First issue custom fields:")
            for field_name, field_value in first_issue['custom_fields'].items():
                print(f"     - {field_name}: {field_value}")
        else:
            print("   ❌ custom_fields not found in search results")
    
    # Test 3: Advanced search
    print("\n3. Testing advanced_search with custom fields...")
    result = await search_tools.advanced_search("project: VP State: Open", limit=1)
    data = json.loads(result)
    
    if isinstance(data, list) and len(data) > 0:
        first_issue = data[0]
        if 'custom_fields' in first_issue:
            print("   ✅ custom_fields present in advanced search")
            print("   Custom fields:")
            for field_name, field_value in first_issue['custom_fields'].items():
                print(f"     - {field_name}: {field_value}")
        else:
            print("   ❌ custom_fields not found in advanced search")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())