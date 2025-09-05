# YouTrack MCP Server - Changes

## Date: 2025-01-06

### New Features:

1. **GitHub Release packages and Container Registry support**
   - Added GitHub Packages (ghcr.io) deployment alongside Docker Hub
   - Docker images now available at both:
     - `docker.io/ivolnistov/youtrack-rocket-mcp`
     - `ghcr.io/i-volnistov/youtrack-rocket-mcp`
   - GitHub Releases now include built packages (.whl and .tar.gz files) as attachments
   - Added separate build-packages job to create release artifacts
   - File: `.github/workflows/release.yml`

2. **Efficient issue counting with `issuesGetter/count` endpoint**
   - Replaced inefficient fetching of 1000 issues with dedicated count API endpoint
   - Added retry logic for when YouTrack returns -1 (still calculating)
   - Significantly improves performance for large result sets
   - Both `search_issues` and `search_issues_detailed` now use the count endpoint
   - Files: `src/youtrack_rocket_mcp/tools/issues.py`

3. **Split search functionality into simple and detailed versions**
   - `search_issues`: Returns only ID and summary (default limit: 100)
   - `search_issues_detailed`: Returns full information with custom fields (default limit: 30)
   - Added `custom_fields_filter` parameter to selectively include fields
   - Files: `src/youtrack_rocket_mcp/tools/issues.py`

### Improvements:

1. **Search results metadata**
   - All search functions now return total count, shown count, and limit
   - Display informative message when not all results are shown
   - Removed redundant project field from search results

2. **Fixed async close() method**
   - Changed `def close()` to `async def close()` to fix RuntimeWarning
   - File: `src/youtrack_rocket_mcp/tools/issues.py`

## Date: 2025-01-05

### Fixes and Improvements:

1. **`leader` field in projects**
   - Fixed: `lead` field replaced with `leader` in Project model and API requests
   - File: `src/youtrack_rocket_mcp/api/resources/projects.py`

2. **Custom fields in projects** 
   - Custom fields now loaded only when requesting single project (optimization)
   - Custom fields not loaded when requesting project list
   - File: `src/youtrack_rocket_mcp/api/resources/projects.py`

3. **Fixed `get_user_by_login`**
   - Removed non-working `login:` prefix from search
   - Added exact login match verification
   - File: `src/youtrack_rocket_mcp/api/resources/users.py`

4. **Fixed async/await in search**
   - Added missing `await` before `self.client.get()`
   - File: `src/youtrack_rocket_mcp/tools/search.py`

5. **Custom fields as dictionary**
   - Added `format_custom_fields()` function to convert custom fields to {name: value} dictionary
   - Updated queries to get full field values
   - Files: 
     - `src/youtrack_rocket_mcp/api/resources/search.py`
     - `src/youtrack_rocket_mcp/tools/search.py`
     - `src/youtrack_rocket_mcp/tools/issues.py`

### Testing Results:

✅ All core functions work correctly:
- Server connection
- Getting projects with custom fields
- Searching and filtering issues
- Creating issues and comments
- Searching users by login
- Custom fields returned as dictionary with readable values

### Note:
To apply changes in MCP client, restart the MCP server.