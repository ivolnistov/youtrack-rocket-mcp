# YouTrack Rocket MCP 🚀

A lightning-fast Model Context Protocol (MCP) server implementation for JetBrains YouTrack, built with FastMCP for optimal performance and proper parameter schema generation. Enables AI assistants to interact with YouTrack issue tracking system with full type safety.

![Screenshot](screenshot/CleanShot%202025-04-14%20at%2023.24.21@2x.png)

## What is MCP?

Model Context Protocol (MCP) is an open standard that enables AI models to interact with external tools and services through a unified interface. This project provides an MCP server that exposes YouTrack functionality to AI assistants that support the MCP standard, such as Claude in VS Code, Claude Desktop, GitHub Copilot, and Cursor IDE.

## Features

- **Issue Management**
  - Get issue details
  - Search for issues using YouTrack query language
  - Create new issues
  - Add comments to issues

- **Project Management**
  - Get project list and details
  - Create and update projects
  - Access project issues
  - Manage custom fields

- **User Management**
  - Get current user information
  - Search for users
  - Access user details and groups

- **Search Functionality**
  - Advanced search with custom fields
  - Structured filtering
  - Sorting options

## Documentation

- 📖 [Full Documentation](./docs/README.md)
- 🏗️ [Architecture](./docs/ARCHITECTURE.md)
- 🚀 [Development Guide](./docs/DEVELOPMENT.md)

## Quick Start with Docker

```bash
# Run with Docker (for YouTrack Cloud instances)
docker run -i --rm \
     -e YOUTRACK_URL=https://your-instance.youtrack.cloud \
     -e YOUTRACK_API_TOKEN=perm:your-api-token \
     -e YOUTRACK_CLOUD=true \
     ivolnistov/youtrack-rocket-mcp:latest

# Or for self-hosted YouTrack instances
docker run -i --rm \
     -e YOUTRACK_URL=https://your-instance.youtrack.cloud \
     -e YOUTRACK_API_TOKEN=your-api-token \
     -e YOUTRACK_CLOUD=false \
     ivolnistov/youtrack-rocket-mcp:latest
```

For Cursor IDE, add to `.cursor/mcp.json`:

```json
{
    "mcpServers": {
        "YouTrack": {
            "type": "stdio",
            "command": "docker",
            "args": ["run", "-i", "--rm",
            "-e", "YOUTRACK_URL=https://your-instance.youtrack.cloud",
            "-e", "YOUTRACK_API_TOKEN=perm:your-api-token",
            "-e", "YOUTRACK_CLOUD=true",
            "ivolnistov/youtrack-rocket-mcp:latest"
            ]
        }
    }
}
```

For Claude Desktop, set as MCP server:
```
docker run -i --rm -e YOUTRACK_API_TOKEN=perm:your-api-token -e YOUTRACK_CLOUD=true ivolnistov/youtrack-rocket-mcp:latest
```

## Installation & Usage

### Quick Start with uvx (No Installation Required)

Run it directly without installation using `uvx`:

```bash
# Run directly from PyPI
export YOUTRACK_URL="https://your-instance.youtrack.cloud"
export YOUTRACK_API_TOKEN="perm:your-api-token"
uvx youtrack-rocket-mcp

# Or with specific version
uvx youtrack-rocket-mcp@latest

# Install persistently with uv tool
uv tool install youtrack-rocket-mcp
youtrack-rocket-mcp  # Run after installation
```

### Local Installation with FastMCP (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/ivolnistov/youtrack-rocket-mcp.git
   cd youtrack-rocket-mcp
   ```

2. Install dependencies with UV:
   ```bash
   # Install all dependencies including dev group (pytest, ruff, mypy, etc.)
   uv sync
   # Note: uv sync includes dev dependencies by default
   ```

3. Run the server:
   ```bash
   uv run python -m youtrack_rocket_mcp.server
   
   # Or with activated virtual environment
   python -m youtrack_rocket_mcp.server
   ```

### Testing with MCP Inspector

For development and testing, use the included inspector script:

```bash
# Make it executable (first time only)
chmod +x inspector.sh

# Run with MCP Inspector
./inspector.sh
```

This will open a browser with MCP Inspector where you can test all tools with proper parameter names (not args/kwargs).

### Using Docker Hub Image

1. Pull the Docker image:
   ```bash
   docker pull ivolnistov/youtrack-rocket-mcp:latest
   ```

2. Run the container with your YouTrack credentials:
   ```bash
   docker run -i --rm \
     -e YOUTRACK_URL=https://your-instance.youtrack.cloud \
     -e YOUTRACK_API_TOKEN=perm:your-api-token \
     ivolnistov/youtrack-rocket-mcp:latest
   ```

### Alternative: Build from Source

If you prefer to build the image yourself:

1. Clone the repository:
   ```bash
   git clone https://github.com/youtrack-rocket-mcp.git
   cd youtrack-rocket-mcp
   ```

2. Build the Docker image:
   ```bash
   docker build -t youtrack-rocket-mcp .
   ```

3. Run your locally built container:
   ```bash
   docker run -i --rm \
     -e YOUTRACK_URL=https://your-instance.youtrack.cloud \
     -e YOUTRACK_API_TOKEN=your-api-token \
     youtrack-rocket-mcp
   ```

### Building Multi-Platform Images

To build and push multi-architecture images (for both ARM64 and AMD64 platforms):

1. Make sure you have Docker BuildX set up:
   ```bash
   docker buildx create --use
   ```

2. Build and push for multiple platforms:
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 \
     -t ivolnistov/youtrack-rocket-mcp:latest \
     --push .
   ```

This builds the image for both ARM64 (Apple Silicon) and AMD64 (Intel/AMD) architectures and pushes it with both version-specific and latest tags.

### Security Considerations

⚠️ **API Token Security**

- Treat your mcp.json file as .env
- Rotate your YouTrack API tokens periodically
- Use tokens with the minimum required permissions for your use case

## Using with AI Applications

### Cursor IDE

To use your YouTrack MCP server with Cursor IDE:

#### Option 1: Using uvx (Recommended)

Create a `.cursor/mcp.json` file in your project:

```json
{
    "mcpServers": {
        "YouTrack": {
            "type": "stdio",
            "command": "uvx",
            "args": ["youtrack-rocket-mcp"],
            "env": {
                "YOUTRACK_URL": "https://your-instance.youtrack.cloud",
                "YOUTRACK_API_TOKEN": "perm:your-api-token",
                "YOUTRACK_CLOUD": "true"
            }
        }
    }
}
```

#### Option 2: Using Docker

```json
{
    "mcpServers": {
        "YouTrack": {
            "type": "stdio",
            "command": "docker",
            "args": ["run", "-i", "--rm",
            "-e", "YOUTRACK_API_TOKEN=perm:your-api-token",
            "-e", "YOUTRACK_URL=https://your-instance.youtrack.cloud",
            "-e", "YOUTRACK_CLOUD=true",
            "ivolnistov/youtrack-rocket-mcp:latest"
            ]
        }
    }
}
```

2. Replace `yourinstance.youtrack.cloud` with your actual YouTrack instance URL and `perm:your-token` with your actual API token.

3. Restart Cursor or reload the project for the changes to take effect.

### Claude Desktop

To use with Claude Desktop:

#### Option 1: Using uvx (Recommended)

1. Open Claude Desktop preferences
2. Navigate to the MCP section
3. Click Edit
4. Open claude_desktop_config.json
5. Add a new MCP server:

```json
{
    "mcpServers": {
        "YouTrack": {
            "type": "stdio",
            "command": "uvx",
            "args": ["youtrack-rocket-mcp"],
            "env": {
                "YOUTRACK_URL": "https://your-instance.youtrack.cloud",
                "YOUTRACK_API_TOKEN": "perm:your-api-token",
                "YOUTRACK_CLOUD": "true"
            }
        }
    }
}
```

#### Option 2: Using Docker

```json
{
    "mcpServers": {
        "YouTrack": {
            "type": "stdio",
            "command": "docker",
            "args": ["run", "-i", "--rm",
            "-e", "YOUTRACK_API_TOKEN=perm:your-api-token",
            "-e", "YOUTRACK_URL=https://your-instance.youtrack.cloud",
            "-e", "YOUTRACK_CLOUD=true",
            "ivolnistov/youtrack-rocket-mcp:latest"
            ]
        }
    }
}
```

Replace the URL and token with your actual values.

### Claude Code CLI

For Claude Code users, add the MCP server using one of these commands:

**Option 1: Using uvx (Recommended)**
```bash
# Remove old server if exists
claude mcp remove youtrack-rocket-mcp

# Add new server with uvx
claude mcp add youtrack-rocket-mcp \
  --env YOUTRACK_URL=https://your-instance.youtrack.cloud \
  --env YOUTRACK_API_TOKEN=perm:your-api-token \
  --env YOUTRACK_CLOUD=true \
  --scope user \
  -- uvx youtrack-rocket-mcp
```

**Option 2: Using Local Installation with Python**
```bash
# Add new server with Python
claude mcp add youtrack-rocket-mcp \
  --env YOUTRACK_URL=https://your-youtrack-instance.com \
  --env YOUTRACK_API_TOKEN=your-api-token \
  --scope user \
  -- uv run --directory /path/to/youtrack-rocket-mcp python -m youtrack_rocket_mcp.server
```

**Option 3: Using Docker**
```bash
claude mcp add youtrack-rocket-mcp --env YOUTRACK_URL=https://your-youtrack-instance.com --env YOUTRACK_API_TOKEN=your-api-token --scope user -- docker run -i --rm tonyzorin/youtrack-mcp:latest
```

**Option 3: Using uv for dependency management**
```bash
claude mcp add youtrack-rocket-mcp --env YOUTRACK_URL=https://your-youtrack-instance.com --env YOUTRACK_API_TOKEN=your-api-token --scope user -- uv run --directory /path/to/youtrack-rocket-mcp python __main__.py
```

**Key syntax notes:**
- Environment variables (`--env`) must come **before** the `--` separator
- The command to run comes **after** the `--` separator
- Use `--scope user` for global access across all projects
- Replace `/path/to/youtrack-rocket-mcp` with your actual installation path

Replace the URL and API token with your actual YouTrack credentials.

**Example with real paths:**
```bash
# Working example (adjust path to your installation)
claude mcp add youtrack-rocket-mcp --env YOUTRACK_URL=https://youtrack.gaijin.team --env YOUTRACK_API_TOKEN=perm-your-token-here --scope user -- uv run --directory /Users/username/.mcp/youtrack-rocket-mcp python -m youtrack_rocket_mcp.server
```

### VS Code with Claude Extension

To use the YouTrack MCP server with VS Code:

1. Create a `.vscode/mcp.json` file with the following content:

   ```json
   {
     "servers": {
       "YouTrack": {
         "type": "stdio",
         "command": "docker",
         "args": ["run", "-i", "--rm",
           "-e", "YOUTRACK_API_TOKEN=perm:your-api-token",
           "-e", "YOUTRACK_URL=https://your-instance.youtrack.cloud",
           "-e", "YOUTRACK_CLOUD=true",
           "youtrack-rocket-mcp:latest"
         ]
       }
     }
   }
   ```

2. Replace `yourinstance.youtrack.cloud` with your actual YouTrack instance URL and `perm:your-token` with your actual API token.

## Available Tools (19 total)

The YouTrack MCP server provides the following tools with proper parameter schemas generated by FastMCP:

### Issues

- `get_issue` - Get details of a specific issue by ID
- `search_issues` - Search for issues using YouTrack query language
- `create_issue` - Create a new issue with custom fields support
- `add_comment` - Add a comment to an existing issue

### Projects

- `get_projects` - Get a list of all projects
- `get_project` - Get details of a specific project
- `get_project_by_name` - Get project by its full name
- `get_project_issues` - Get issues for a specific project
- `get_custom_fields` - Get custom fields configuration for a project

### Users

- `get_current_user` - Get information about the currently authenticated user
- `get_user` - Get information about a specific user
- `search_users` - Search for users
- `get_user_by_login` - Find a user by login name
- `get_user_groups` - Get groups for a user

### Search

- `advanced_search` - Advanced search with sorting options
- `filter_issues` - Search with structured filtering (supports date ranges)
- `search_with_custom_fields` - Search using custom field values
- `get_search_syntax_guide` - Get comprehensive guide for YouTrack search query syntax
- `get_common_queries` - Get common search query examples organized by use case

## Tool Parameter Format

When using the YouTrack MCP tools, it's important to use the correct parameter format to ensure your requests are processed correctly. Here's how to use the most common tools:

### Get Issue

To get information about a specific issue, you must provide the `issue_id` parameter:

```python
# Correct format
get_issue(issue_id="DEMO-123")
```

The issue ID can be either the readable ID (e.g., "DEMO-123") or the internal ID (e.g., "3-14").

### Add Comment

To add a comment to an issue, you must provide both the `issue_id` and `text` parameters:

```python
# Correct format
add_comment(issue_id="DEMO-123", text="This is a test comment")
```

### Create Issue

To create a new issue, you must provide at least the `project` and `summary` parameters:

```python
# Correct format
create_issue(project="DEMO", summary="Bug: Login page not working")

# With optional description and custom fields
create_issue(
    project="DEMO",
    summary="Bug: Login page not working",
    description="Users cannot log in after the latest update",
    custom_fields={"Priority": "Critical", "Type": "Bug"}
)
```

The project parameter can be either the project's short name (e.g., "DEMO") or its internal ID.

### Search Issues

To search for issues using YouTrack query language:

```python
# Simple search
search_issues(query="project: DEMO #Unresolved", limit=10)

# Advanced search with sorting
advanced_search(
    query="assignee: me priority: Critical created: {this week}",
    limit=20,
    sort_by="updated",
    sort_order="desc"
)

# Structured filter search
filter_issues(
    project="DEMO",
    assignee="me",
    state="Open",
    priority="High",
    created_after="2024-01-01",
    limit=10
)
```

#### Common Search Query Examples

- `project: MyProject #Unresolved` - All unresolved issues in MyProject
- `assignee: me state: Open` - Open issues assigned to current user
- `priority: Critical, Major` - Critical OR Major priority issues
- `created: today` - Issues created today
- `updated: {this week}` - Issues updated this week
- `"exact phrase"` - Search for exact phrase in summary/description
- `-state: Resolved` - Exclude resolved issues
- `type: Bug has: attachments` - Bugs with attachments

Use `get_search_syntax_guide()` to get a comprehensive reference of all search attributes and syntax.

### Working with Custom Fields

YouTrack projects often have required custom fields. Here's how to work with them effectively:

#### Getting Project Field Information

Before creating issues, use `get_custom_fields()` to see all custom fields:

```python
# Get custom fields for a project
get_custom_fields(project_id="ITSFT")
# or
get_custom_fields(project="ITSFT")
```

This returns:
- All custom fields with their IDs and names
- Whether each field is required or optional
- Possible values for enum/bundle fields
- Sample values from existing issues

#### Creating Issues with Custom Fields

```python
# Basic issue creation
create_issue(
    project="ITSFT",
    summary="Test task for Benderbot",
    description="Testing the Benderbot subsystem"
)

# With custom fields (use field names)
create_issue(
    project="ITSFT",
    summary="Server monitoring issue",
    description="Need to monitor server health",
    custom_fields={
        "Subsystem": "Bender Bot",
        "Type": "Task",
        "Priority": "Normal"
    }
)

# With custom fields (using field IDs for precise control)
create_issue(
    project="ITSFT",
    summary="Server monitoring issue",
    custom_fields={
        "93-1507": "Bender Bot",  # Subsystem field ID
        "93-2069": "Task",        # Type field ID
        "93-1505": "Normal"       # Priority field ID
    }
)
```

#### Common Custom Field Types

1. **Enum Fields** (Type, Priority, Severity):
   - Use the exact value name from possible_values
   - Case-sensitive matching

2. **Bundle Fields** (Subsystem, Component):
   - Use the name or ID from the bundle values
   - Example: "Bender Bot" or "100-561"

3. **User Fields** (Assignee, Owner):
   - Use login name or user ID
   - Example: "john.doe" or "1-234"

4. **Date Fields** (Due Date, Start Date):
   - Use timestamp in milliseconds
   - Example: 1750420800000

5. **Version Fields** (Fix Version, Affected Version):
   - Use version name or ID
   - Example: "2.0" or "99-123"

### Common MCP Format Issues

When using MCP tools through AI assistants, parameters may sometimes be passed in different formats. The YouTrack MCP server is designed to handle various parameter formats, but using the explicit format above is recommended for best results.

If you encounter errors with parameter format, try using the explicit key=value format shown in the examples above.

### Troubleshooting Issue Creation

If you get errors when creating issues:

1. **"Field required" error**:
   - Use `get_project_detailed()` to see required fields
   - Add the missing field to custom_fields

2. **"Project not found" error**:
   - Use `get_projects()` to list all projects
   - Use the project short name (e.g., "ITSFT") not the full name
   - Check if you have access to the project

3. **"Invalid field value" error**:
   - Check possible_values in get_project_detailed() output
   - Field values are often case-sensitive
   - For bundle fields, use exact names from the bundle

## Examples

Here are some examples of using the YouTrack MCP server with AI assistants:

### Get Issue

```
Can you get the details for issue DEMO-1?
```

### Search for Issues

```
Find all open issues assigned to me that are high priority
```

### Create a New Issue

```
Create a new bug report in the PROJECT with the summary "Login page is not working" and description "Users are unable to log in after the recent update."
```

### Add a Comment

```
Add a comment to issue PROJECT-456 saying "I've fixed this issue in the latest commit. Please review."
```

## Technical Details

### FastMCP Implementation

This server is built with FastMCP, which provides:
- Automatic JSON Schema generation from Python type hints
- Proper parameter validation
- Correct parameter names in MCP Inspector (no more args/kwargs)
- Full async support for optimal performance

### Configuration

The server can be configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `YOUTRACK_URL` | YouTrack instance URL | (required) |
| `YOUTRACK_API_TOKEN` | YouTrack permanent API token | (required) |
| `YOUTRACK_VERIFY_SSL` | Verify SSL certificates | `true` |
| `MCP_SERVER_NAME` | Name of the MCP server | `youtrack-rocket-mcp` |
| `MCP_SERVER_DESCRIPTION` | Description of the MCP server | `YouTrack MCP Server` |
| `MCP_DEBUG` | Enable debug logging | `false` |

### SSL Certificate Verification

For self-hosted instances with self-signed SSL certificates, you can disable SSL verification:

```bash
docker run -i --rm \
  -e YOUTRACK_URL=https://youtrack.internal.company.com \
  -e YOUTRACK_API_TOKEN=perm:your-permanent-token \
  -e YOUTRACK_VERIFY_SSL=false \
  ivolnistov/youtrack-rocket-mcp:latest
```

This option is only recommended for development or in controlled environments where you cannot add the certificate to the trust store.

### Debug Mode

You can enable debug logging for troubleshooting:

```bash
docker run -i --rm \
  -e YOUTRACK_URL=https://your-instance.youtrack.cloud \
  -e YOUTRACK_API_TOKEN=perm:your-permanent-token \
  -e MCP_DEBUG=true \
  ivolnistov/youtrack-rocket-mcp:latest
```
