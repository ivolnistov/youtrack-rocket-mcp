# Configuration Guide

## Overview

YouTrack Rocket MCP uses a simplified configuration approach that requires minimal setup. The server automatically detects whether you're using YouTrack Cloud or a self-hosted instance based on your configuration.

## Environment Variables

### Required

#### `YOUTRACK_API_TOKEN`
**Required** - Your YouTrack API token for authentication.

- **For YouTrack Cloud**: Use the format `perm:username.workspace.xxxxx`
  - The workspace is automatically extracted from the token
  - No URL configuration needed
- **For Self-hosted**: Use your token directly (e.g., `perm:xxxxx`)
  - Must also provide `YOUTRACK_URL`

**How to get a token:**
1. Go to your YouTrack instance
2. Navigate to Profile → Account Security
3. Click "New token"
4. Give it a descriptive name
5. Select appropriate permissions (recommended: read/write for issues and projects)

### Optional

#### `YOUTRACK_URL`
**Optional** - The URL of your YouTrack instance.

- **Leave empty** for YouTrack Cloud (workspace will be extracted from token)
- **Required** for self-hosted instances (e.g., `https://youtrack.example.com`)
- Do not include `/api` suffix - it will be added automatically

#### `YOUTRACK_VERIFY_SSL`
**Default**: `true`

Whether to verify SSL certificates. Set to `false` only for self-hosted instances with self-signed certificates.

```bash
export YOUTRACK_VERIFY_SSL=false  # Only for testing/development
```

#### `YOUTRACK_WORKSPACE`
**Optional** - Only needed for special token formats.

If your cloud token is in the format `perm-base64.base64.hash` (without workspace information), you'll need to specify the workspace separately:

```bash
export YOUTRACK_WORKSPACE="myworkspace"
export YOUTRACK_API_TOKEN="perm-base64encoded.morebase64.hash"
```

### Advanced Settings

#### `YOUTRACK_MAX_RETRIES`
**Default**: `3`

Maximum number of retry attempts for failed API requests.

#### `YOUTRACK_RETRY_DELAY`
**Default**: `1.0`

Initial delay in seconds between retry attempts (uses exponential backoff).

#### `MCP_DEBUG`
**Default**: `false`

Enable debug logging for troubleshooting.

```bash
export MCP_DEBUG=true
```

#### `MCP_SERVER_NAME`
**Default**: `youtrack-rocket-mcp`

The name of the MCP server (shown in MCP clients).

#### `MCP_SERVER_INSTRUCTIONS`
**Default**: Comprehensive usage instructions for AI assistants

Instructions for AI assistants on how to use this server. These are passed to FastMCP and help the AI understand the server's capabilities and best practices. You can customize these instructions to guide the AI's behavior when working with your YouTrack instance.

## Configuration Examples

### YouTrack Cloud (Simplest)

```bash
# Only token needed - workspace extracted automatically
export YOUTRACK_API_TOKEN="perm:john.acme.5f4d3c2b1a"
```

### Self-Hosted YouTrack

```bash
export YOUTRACK_URL="https://youtrack.company.com"
export YOUTRACK_API_TOKEN="perm:1234567890abcdef"
```

### Self-Hosted with Self-Signed Certificate

```bash
export YOUTRACK_URL="https://youtrack.internal.local"
export YOUTRACK_API_TOKEN="perm:1234567890abcdef"
export YOUTRACK_VERIFY_SSL=false
```

### Using .env File

Create a `.env` file in the project root:

```env
# For YouTrack Cloud
YOUTRACK_API_TOKEN=perm:username.workspace.xxxxx

# OR for self-hosted
# YOUTRACK_URL=https://youtrack.example.com
# YOUTRACK_API_TOKEN=perm:xxxxx
# YOUTRACK_VERIFY_SSL=true

# Optional settings
MCP_DEBUG=false
YOUTRACK_MAX_RETRIES=3
YOUTRACK_RETRY_DELAY=1.0
```

## Configuration Priority

The server determines the YouTrack instance URL in this order:

1. **If `YOUTRACK_URL` is set**: Use it as a self-hosted instance
2. **If only token is set**:
   - Extract workspace from token format `perm:username.workspace.xxx`
   - Use `https://workspace.youtrack.cloud/api`
3. **Special token format** (`perm-xxx`):
   - Requires `YOUTRACK_WORKSPACE` environment variable
   - Uses `https://workspace.youtrack.cloud/api`

## Troubleshooting

### Error: "YouTrack API token is required"

**Solution**: Set the `YOUTRACK_API_TOKEN` environment variable.

### Error: "Your token format (perm-...) requires workspace specification"

**Solution**: Your token doesn't contain workspace information. Either:
- Set `YOUTRACK_WORKSPACE` environment variable
- Or provide the full URL with `YOUTRACK_URL`

### Connection Issues

1. **Check token permissions**: Ensure your token has appropriate permissions in YouTrack
2. **Verify URL**: For self-hosted, ensure the URL is correct (without `/api` suffix)
3. **SSL issues**: For self-signed certificates, set `YOUTRACK_VERIFY_SSL=false`
4. **Enable debug**: Set `MCP_DEBUG=true` for detailed error messages

### Rate Limiting

The server automatically handles rate limiting with exponential backoff. If you encounter persistent rate limit issues:

1. Increase `YOUTRACK_RETRY_DELAY`
2. Reduce the frequency of API calls
3. Check your YouTrack instance's rate limit settings

## Security Best Practices

1. **Never commit tokens**: Add `.env` to `.gitignore`
2. **Use environment variables**: Don't hardcode tokens in scripts
3. **Minimal permissions**: Create tokens with only necessary permissions
4. **Rotate tokens**: Periodically regenerate API tokens
5. **Use SSL**: Always verify SSL certificates in production
6. **Secure storage**: Store tokens in secure credential managers when possible

## Docker Configuration

When using Docker, pass environment variables with `-e`:

```bash
# YouTrack Cloud
docker run -i --rm \
  -e YOUTRACK_API_TOKEN="perm:username.workspace.xxxxx" \
  ivolnistov/youtrack-rocket-mcp:latest

# Self-hosted
docker run -i --rm \
  -e YOUTRACK_URL="https://youtrack.example.com" \
  -e YOUTRACK_API_TOKEN="perm:xxxxx" \
  -e YOUTRACK_VERIFY_SSL=true \
  ivolnistov/youtrack-rocket-mcp:latest
```

## Integration Examples

### Claude Desktop

```json
{
  "mcpServers": {
    "youtrack": {
      "command": "uvx",
      "args": ["youtrack-rocket-mcp"],
      "env": {
        "YOUTRACK_API_TOKEN": "perm:username.workspace.xxxxx"
      }
    }
  }
}
```

### Cursor IDE

```json
{
  "mcpServers": {
    "youtrack": {
      "type": "stdio",
      "command": "uvx",
      "args": ["youtrack-rocket-mcp"],
      "env": {
        "YOUTRACK_API_TOKEN": "perm:username.workspace.xxxxx"
      }
    }
  }
}
```
