# YouTrack MCP Server Architecture

## Directory Structure

```
src/
└── youtrack_mcp/
    ├── api/                    # Low-level YouTrack API clients
    │   ├── client.py          # Base HTTP client (async with httpx)
    │   ├── field_cache.py     # Field type caching logic
    │   └── resources/         # API resource clients (all async)
    │       ├── __init__.py
    │       ├── issues.py      # Issues API client
    │       ├── projects.py    # Projects API client
    │       ├── users.py       # Users API client
    │       └── search.py      # Search API client
    ├── tools/                 # MCP tool implementations
    │   ├── __init__.py
    │   ├── issues.py          # Issue management tools
    │   ├── projects.py        # Project management tools
    │   ├── users.py           # User management tools
    │   ├── search.py          # Search tools
    │   ├── search_guide.py    # Search syntax guide
    │   └── loader.py          # Tool loading logic
    ├── config.py              # Configuration management
    ├── server.py              # Main MCP server with entry point
    ├── mcp_wrappers.py        # MCP wrappers & async bridge
    └── version.py             # Version information
```

## Architecture Layers

### 1. API Layer (`api/`)
- **Async HTTP Client**: Uses `httpx` for all HTTP operations
- **Resource Clients**: Async classes for each YouTrack resource type
- **Field Cache**: Intelligent caching for custom field types

### 2. Tools Layer (`tools/`)
- **MCP Tools**: Synchronous wrappers that bridge to async API
- **Dynamic Loading**: Automatic tool discovery and registration
- **Parameter Normalization**: Handles various MCP parameter formats

### 3. Server Layer
- **MCP Server**: Implements the Model Context Protocol
- **Async Bridge**: `run_async_in_sync` function for calling async from sync context
- **Tool Registration**: Dynamic registration of available tools

## Data Flow

1. **MCP Client → Tool Function** (synchronous)
2. **Tool Function → Async Wrapper** (`run_async_in_sync`)
3. **Async Wrapper → API Client** (async/await)
4. **API Client → YouTrack API** (HTTPS)
5. **Response flows back** through the same layers

## Key Design Decisions

### Async Architecture
- All API interactions are async using `httpx`
- Tools remain synchronous for MCP compatibility
- Bridge layer handles async-sync conversion

### Field Type Caching
- Automatic detection of custom field types
- Caching to reduce API calls
- Fallback strategies for permissions

### Error Handling
- Comprehensive error types for different scenarios
- Retry logic with exponential backoff
- Detailed error messages for debugging

## Configuration

Environment variables or `.env` file:
- `YOUTRACK_URL`: YouTrack instance URL
- `YOUTRACK_API_TOKEN`: API authentication token
- `YOUTRACK_CLOUD`: Boolean for cloud vs self-hosted
- `YOUTRACK_VERIFY_SSL`: SSL verification (default: true)

## Tool Categories

### Issue Tools
- `get_issue`: Retrieve issue details
- `create_issue`: Create new issues with custom fields
- `add_comment`: Add comments to issues
- `search_issues`: Search using YouTrack query language

### Project Tools
- `get_project`: Get project details
- `get_projects`: List all projects
- `create_project`: Create new projects
- `update_project`: Modify project settings
- `get_project_issues`: Get issues for a project

### User Tools
- `get_current_user`: Current user information
- `get_user`: Get user details
- `search_users`: Find users
- `get_user_groups`: Get user's groups

### Search Tools
- `advanced_search`: Complex searches with sorting
- `filter_issues`: Structured filtering
- `search_with_custom_fields`: Custom field queries
- `get_search_syntax_guide`: Query language documentation