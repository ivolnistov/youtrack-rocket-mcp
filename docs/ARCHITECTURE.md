# YouTrack MCP Server Architecture

## Directory Structure

```
src/
└── youtrack_rocket_mcp/
    ├── api/                    # YouTrack API clients
    │   ├── client.py          # Base HTTP client with httpx
    │   ├── types.py           # Shared type definitions
    │   └── resources/         # API resource clients
    │       ├── __init__.py
    │       ├── issues.py      # Issues API client
    │       ├── projects.py    # Projects API client
    │       ├── users.py       # Users API client
    │       └── search.py      # Search API client
    ├── tools/                 # MCP tool implementations (FastMCP)
    │   ├── __init__.py
    │   ├── issues.py          # Issue management tools
    │   ├── projects.py        # Project management tools
    │   ├── users.py           # User management tools
    │   ├── search.py          # Search tools
    │   └── search_guide.py    # Search syntax guide
    ├── config.py              # Configuration management
    ├── server.py              # FastMCP server with entry point
    └── version.py             # Version information
```

## Architecture Layers

### 1. API Layer (`api/`)
- **HTTP Client**: Uses `httpx` for all HTTP operations
- **Resource Clients**: Classes for each YouTrack resource type
- **Type Definitions**: Pydantic models and type hints for validation

### 2. Tools Layer (`tools/`)
- **FastMCP Tools**: Tools decorated with `@mcp.tool()` for automatic schema generation
- **Tool Registration**: Each module registers its tools with the FastMCP server
- **Parameter Validation**: FastMCP handles parameter validation automatically

### 3. Server Layer
- **FastMCP Server**: Built on FastMCP framework for optimal performance
- **Automatic Schema Generation**: Generates proper JSON schemas from Python type hints
- **Tool Registration**: Tools are registered via module imports

## Data Flow

1. **MCP Client → FastMCP Server** (stdio/HTTP)
2. **FastMCP → Tool Function** (with automatic parameter validation)
3. **Tool Function → API Client** (via httpx)
4. **API Client → YouTrack API** (HTTPS)
5. **Response flows back** through the same layers

## Key Design Decisions

### FastMCP Framework
- Built on FastMCP for automatic schema generation
- Proper parameter names in MCP Inspector (no args/kwargs)
- Full type safety and validation

### API Architecture
- All API interactions use `httpx` for reliability
- Pydantic models for request/response validation
- Comprehensive error handling with retries

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