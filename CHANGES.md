# YouTrack MCP Server - Changes

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