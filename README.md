# bertron-mcp
MCP interface for BERtron API

## Setup

### Development
Install dependencies for development:
```bash
make dev
```

### Testing
Run the complete test suite:
```bash
make all
```

## MCP Integration

### Claude Desktop Configuration
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "bertron-mcp": {
      "command": "uv",
      "args": ["run", "python", "src/bertron_mcp/main.py"],
      "cwd": "/path/to/bertron-mcp"
    }
  }
}
```

### Claude Code MCP Setup
For local development:
```bash
claude mcp add -s project bertron-mcp uv run python src/bertron_mcp/main.py
```

For production (after publishing to PyPI):
```bash
claude mcp add -s project bertron-mcp uvx bertron-mcp
```

### Goose Setup
For local development:
```bash
goose session --with-extension "uv run python src/bertron_mcp/main.py"
```
