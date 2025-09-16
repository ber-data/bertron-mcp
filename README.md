# bertron-mcp

A Model Context Protocol (MCP) server providing access to the BERtron API, which aggregates genomic and environmental data from multiple Biological and Environmental Research (BER) data sources including EMSL, ESS-DIVE, JGI, MONET, and NMDC.

## Features

- 🔍 **Geospatial Search**: Find entities within a specified radius of geographic coordinates
- 💊 **Health Check**: Verify BERtron API connectivity and database status
- 🌍 **Multi-Source Data**: Access data from major BER research facilities
- 🔌 **MCP Integration**: Seamless integration with Claude, Goose, and other MCP-compatible AI tools

## Requirements

- Python 3.12+
- UV package manager (recommended)
- Access to BERtron API (https://bertron-api.bertron.production.svc.spin.nersc.org)

## Installation

### From Source (Development)
```bash
git clone https://github.com/ber-data/bertron-mcp.git
cd bertron-mcp
make dev
```

### From PyPI (Coming Soon)
```bash
pip install bertron-mcp
```

## Available Tools

### `geosearch`
Search for entities within a specified distance of geographic coordinates.

**Parameters:**
- `latitude` (float): Latitude coordinate (-90.0 to 90.0)
- `longitude` (float): Longitude coordinate (-180.0 to 180.0) 
- `search_radius_km` (float, optional): Search radius in kilometers (default: 1.0)

**Returns:** QueryResponse with entities, count, and metadata

### `health_check`
Check the health status of the BERtron API.

**Parameters:** None

**Returns:** Dictionary with web_server and database boolean status

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

Test specific components:
```bash
# API integration tests
make test-integration

# MCP protocol tests  
make test-mcp
make test-mcp-extended

# Test with Claude CLI
make test-claude-mcp

# Version check
make test-version
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

## Usage Examples

### Using with Claude
```
Search for genomic samples near Orlando, FL within 100km radius:
> Use the bertron-mcp to search for entities near latitude 28.5383, longitude -81.3792 within 100km
```

### Direct MCP Protocol
```bash
# Test geosearch tool
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "geosearch", "arguments": {"latitude": 28.5383, "longitude": -81.3792, "search_radius_km": 100.0}}, "id": 1}' | uv run python src/bertron_mcp/main.py
```

## Development

### Code Quality
```bash
# Format and lint code
make format
make lint

# Type checking
make mypy

# Dependency analysis
make deptry
```

### Building and Publishing
```bash
# Build package
make build

# Full release workflow
make release
```

## Data Sources

BERtron aggregates data from:
- **EMSL** - Environmental Molecular Sciences Laboratory
- **ESS-DIVE** - ESS Data and Information for Virtual Ecosystems  
- **JGI** - Joint Genome Institute
- **MONET** - Molecular Observation Network
- **NMDC** - National Microbiome Data Collaborative

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run the test suite: `make all`
5. Commit your changes: `git commit -m "Add your feature"`
6. Push to the branch: `git push origin feature/your-feature`
7. Submit a pull request

## License

BSD-3-Clause
