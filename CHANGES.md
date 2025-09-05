# YouTrack MCP Server - Changes

## Version 0.4.6 - 2025-01-06

### 🐛 Bug Fixes
- **Fixed execute_command API error** - Changed incorrect `json_data` parameter to `data` in execute_command
  - Was causing "AsyncClient.request() got an unexpected keyword argument 'json_data'" error
  - Commands like "State Closed Resolution Fixed" now work correctly

### 📦 Dependencies
- **Removed redundant mcp dependency** - Already included via FastMCP
- **Documented why Docker builds install many packages** - FastMCP depends on mcp which brings uvicorn, starlette, rich, pyperclip etc.

## Version 0.4.5 - 2025-01-06

### 🎯 Major Changes

#### Simplified Configuration
- **Removed `YOUTRACK_CLOUD` variable** - Server now automatically detects cloud vs self-hosted instances
- **Removed `MCP_SERVER_DESCRIPTION`** - Consolidated into `MCP_SERVER_INSTRUCTIONS` for FastMCP
- **Minimal setup required** - Only API token needed for YouTrack Cloud instances
- **Smart detection** - Workspace automatically extracted from token format `perm:username.workspace.xxxxx`

#### Improved Error Handling
- **Configuration validation** - Server validates settings at startup with clear error messages
- **Graceful shutdown** - Fixed Ctrl-C handling without traceback or thread errors
- **FastMCP lifespan management** - Added async context manager for proper startup/shutdown
- **Smart interrupt handling**:
  - First Ctrl-C: Normal graceful shutdown with sys.exit(0)
  - Multiple Ctrl-C: Force quit with os._exit(0) without errors
- **Async task cleanup** - Cancels all pending async tasks on shutdown
- **User-friendly messages** - Clear instructions when configuration is missing or invalid

### 📝 Configuration Changes

#### Before (Complex)
```env
YOUTRACK_URL=https://workspace.youtrack.cloud
YOUTRACK_API_TOKEN=perm:username.workspace.xxxxx
YOUTRACK_CLOUD=true
MCP_SERVER_DESCRIPTION=My Server
```

#### After (Simple)
```env
# For Cloud - just token!
YOUTRACK_API_TOKEN=perm:username.workspace.xxxxx

# For self-hosted - token + URL
YOUTRACK_URL=https://youtrack.example.com
YOUTRACK_API_TOKEN=perm:xxxxx
```

### 🔧 Technical Details

1. **Configuration (`src/youtrack_rocket_mcp/config.py`)**
   - Removed `YOUTRACK_CLOUD` variable
   - Added `MCP_SERVER_INSTRUCTIONS` with comprehensive AI guidance
   - Improved `validate()` method with actionable error messages
   - Smart `get_base_url()` with automatic workspace detection

2. **Server (`src/youtrack_rocket_mcp/server.py`)**
   - Added configuration validation on startup
   - Improved KeyboardInterrupt handling with clean exit
   - Added FastMCP lifespan context manager for proper async cleanup
   - Better error reporting without stack traces
   - Single Ctrl-C now properly terminates the server

3. **Documentation**
   - Created comprehensive `docs/CONFIGURATION.md`
   - Updated all README files and examples
   - Removed obsolete configuration references
   - Added troubleshooting guides

### 🐛 Bug Fixes
- Fixed async task cleanup on shutdown with proper cancellation
- Fixed traceback display on Ctrl-C - now exits cleanly
- Fixed single Ctrl-C termination - server now shuts down properly on first interrupt
- Fixed validation for tokens without workspace info

### 📚 Documentation Updates
- `docs/CONFIGURATION.md` - New comprehensive configuration guide
- `README.md` - Simplified setup instructions
- `.env.example` - Updated with new configuration format
- `Dockerfile` - Removed obsolete environment variables
- All examples updated to use new configuration

### Updated Features:

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
