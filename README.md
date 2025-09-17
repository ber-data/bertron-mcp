# bertron-mcp

A Model Context Protocol (MCP) server providing access to the BERtron API, which aggregates genomic and environmental data from multiple Biological and Environmental Research (BER) data sources including EMSL, ESS-DIVE, JGI, MONET, and NMDC.

## Quick Start

### Install and run directly from GitHub
```bash
# Run directly without installing
uvx --from git+https://github.com/ber-data/bertron-mcp.git bertron-mcp

# Or install first, then run
uvx --from git+https://github.com/ber-data/bertron-mcp.git bertron-mcp --version
```

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

### `bbox_search`
Search for entities within a rectangular geographic bounding box.

**Parameters:**
- `southwest_lat` (float): Southwest corner latitude (-90.0 to 90.0)
- `southwest_lng` (float): Southwest corner longitude (-180.0 to 180.0)
- `northeast_lat` (float): Northeast corner latitude (-90.0 to 90.0)
- `northeast_lng` (float): Northeast corner longitude (-180.0 to 180.0)

**Returns:** QueryResponse with entities within the bounding box

### `entity_lookup`
Retrieve detailed information for a specific entity by its unique ID.

**Parameters:**
- `entity_id` (string): Unique identifier of the entity (e.g., "nmdc:bsm-12-abc123")

**Returns:** Entity object with complete metadata

### `advanced_query`
Execute complex MongoDB queries with filtering, projection, and sorting.

**Parameters:**
- `filter_dict` (dict, optional): MongoDB filter criteria (e.g., {"entity_type": "sample"})
- `projection` (dict, optional): Fields to include/exclude (e.g., {"name": 1, "coordinates": 1})
- `skip` (int, optional): Number of documents to skip for pagination (default: 0)
- `limit` (int, optional): Maximum number of documents to return (default: 100)
- `sort` (dict, optional): Sort criteria (e.g., {"name": 1} for ascending)

**Returns:** QueryResponse with matching entities

### `search_by_source`
Find entities from a specific BER data source.

**Parameters:**
- `source` (string): BER data source name (EMSL, ESS-DIVE, JGI, NMDC, MONET)

**Returns:** QueryResponse with entities from the specified source

### `search_by_type`
Find entities of a specific entity type.

**Parameters:**
- `entity_type` (string): Entity type (biodata, sample, sequence, taxon, jgi_biosample)

**Returns:** QueryResponse with entities of the specified type

### `search_by_name`
Search for entities by name using regex pattern matching.

**Parameters:**
- `name_pattern` (string): Name pattern to search for (supports regex)
- `case_sensitive` (bool, optional): Whether search should be case sensitive (default: False)

**Returns:** QueryResponse with entities matching the name pattern

### `health_check`
Check the health status of the BERtron API.

**Parameters:** None

**Returns:** Dictionary with web_server and database boolean status

## API Limits and Constraints

To prevent overwhelming responses and protect system resources, the following limits are enforced:

### Default Limits
- **Default result limit**: 100 items per query
- **Maximum result limit**: 1,000 items per query
- **Maximum pagination offset**: 50,000 items

### Constraint Reporting
When limits are applied, tools automatically report constraints in the response metadata:

```json
{
  "entities": [...],
  "count": 1000,
  "metadata": {
    "constraints_applied": {
      "requested_limit": 5000,
      "actual_limit": 1000,
      "reason": "Exceeded maximum limit of 1000"
    }
  }
}
```

### Tools with Limit Parameters
The following tools accept optional `limit` parameters:
- `search_by_source(source, limit=100)`
- `search_by_type(entity_type, limit=100)`  
- `search_by_name(name_pattern, case_sensitive=False, limit=100)`
- `advanced_query(filter_dict=None, limit=100, skip=0, ...)`

### Safety Features
- **`advanced_query`** requires filter criteria to prevent accidental full database dumps
- All limits are enforced server-side with automatic constraint reporting
- Deep pagination (skip > 50,000) is blocked to prevent performance issues

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

**Option 1: From GitHub (Recommended)**
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

**Option 2: Local Development**
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

**From GitHub:**
```bash
claude mcp add bertron-mcp "uvx --from git+https://github.com/ber-data/bertron-mcp.git bertron-mcp"
```

**Local development:**
```bash
claude mcp add -s project bertron-mcp uv run python src/bertron_mcp/main.py
```

**Production (after publishing to PyPI):**
```bash
claude mcp add -s project bertron-mcp uvx bertron-mcp
```

### Goose Setup

**From GitHub:**
```bash
goose session --with-extension "uvx --from git+https://github.com/ber-data/bertron-mcp.git bertron-mcp"
```

**Local development:**
```bash
goose session --with-extension "uv run python src/bertron_mcp/main.py"
```

## Usage Examples

### Using with Claude
```
Search for genomic samples near Orlando, FL within 100km radius:
> Use the bertron-mcp to search for entities near latitude 28.5383, longitude -81.3792 within 100km

Search for entities in a bounding box covering Yellowstone National Park:
> Use bbox_search to find entities between southwest corner (44.0, -125.0) and northeast corner (49.0, -110.0)

Find all NMDC sample entities:
> Search for all sample entities from the NMDC data source

Look up detailed information for a specific entity:
> Use entity_lookup to get details for entity ID "nmdc:bsm-12-abc123"
```

### Direct MCP Protocol
```bash
# Test geosearch tool
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "geosearch", "arguments": {"latitude": 28.5383, "longitude": -81.3792, "search_radius_km": 100.0}}, "id": 1}' | uv run python src/bertron_mcp/main.py

# Test bounding box search
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "bbox_search", "arguments": {"southwest_lat": 44.0, "southwest_lng": -125.0, "northeast_lat": 49.0, "northeast_lng": -110.0}}, "id": 2}' | uv run python src/bertron_mcp/main.py

# Test search by data source
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "search_by_source", "arguments": {"source": "NMDC"}}, "id": 3}' | uv run python src/bertron_mcp/main.py

# Test advanced query with filtering
echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "advanced_query", "arguments": {"filter_dict": {"entity_type": "sample"}, "limit": 10}}, "id": 4}' | uv run python src/bertron_mcp/main.py
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
