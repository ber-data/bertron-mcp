# bertron-mcp

A Model Context Protocol (MCP) server providing access to the BERtron API, which aggregates genomic and environmental data from multiple Biological and Environmental Research (BER) data sources.

## Quick Start

### Install and run directly from GitHub
```bash
# Run directly without installing
uvx --from git+https://github.com/ber-data/bertron-mcp.git bertron-mcp

# Or install first, then run
uvx --from git+https://github.com/ber-data/bertron-mcp.git bertron-mcp --version
```

## MCP Integration

### Claude Desktop Configuration
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "bertron-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/ber-data/bertron-mcp.git", "bertron-mcp"]
    }
  }
}
```

### Claude Code MCP Setup
```bash
claude mcp add bertron-mcp "uvx --from git+https://github.com/ber-data/bertron-mcp.git bertron-mcp"
```

### Goose Setup
```bash
goose session --with-extension "uvx --from git+https://github.com/ber-data/bertron-mcp.git bertron-mcp"
```

## Available Tools

- **geosearch**: Find entities within a specified radius of geographic coordinates
- **health_check**: Verify BERtron API connectivity and database status

## Development Setup

```bash
git clone https://github.com/ber-data/bertron-mcp.git
cd bertron-mcp
make dev
make all  # Run tests
```
