# YouTrack MCP Documentation

## Documentation Structure

- [Architecture](./ARCHITECTURE.md) - System architecture and design
- [Development Guide](./DEVELOPMENT.md) - Development setup with UV
- [Configuration Guide](./CONFIGURATION.md) - Configuration options and setup

## Quick Start

### Minimal Configuration

The server requires only an API token to work with YouTrack Cloud:

```bash
export YOUTRACK_API_TOKEN="perm:username.workspace.xxxxx"
uvx youtrack-rocket-mcp
```

For self-hosted YouTrack, also provide the URL:

```bash
export YOUTRACK_URL="https://youtrack.example.com"
export YOUTRACK_API_TOKEN="perm:xxxxx"
uvx youtrack-rocket-mcp
```

For development setup, see [Development Guide](./DEVELOPMENT.md).

## API Documentation

The YouTrack MCP Server provides tools for:
- Issue management (create, search, comment, update)
- Project management (list projects, get fields, custom fields)
- User management (get users, search users)
- Advanced search functionality with YouTrack query language

See [Architecture](./ARCHITECTURE.md) for detailed API structure.
