.PHONY: test-coverage clean install dev format lint all server build upload-test upload release deptry mypy test-mcp test-mcp-extended test-integration test-version test-mcp-protocol test-claude-mcp

# Default target
all: clean install dev test-coverage format lint mypy deptry build test-mcp test-mcp-extended test-integration test-version

# Install everything for development
dev:
	uv sync --group dev

# Install production only
install:
	uv sync

# Run tests with coverage
test-coverage:
	uv run pytest --cov=src/bertron_mcp --cov-report=html --cov-report=term tests/

# Clean up build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -f .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf src/*.egg-info

# Run server mode
server:
	uv run python src/bertron_mcp/main.py

# Format code with ruff
format:
	uv run ruff check --fix src/ tests/

# Lint code with ruff
lint:
	uv run ruff check --fix src/ tests/

# Check for unused dependencies
deptry:
	uvx deptry .

# Type checking
mypy:
	uv run mypy src/

# Build package with uv
build:
	uv build

# Upload to TestPyPI (using token-based auth - set UV_PUBLISH_TOKEN environment variable first)
upload-test:
	uv publish --publish-url https://test.pypi.org/legacy/

# Upload to PyPI (using token-based auth - set UV_PUBLISH_TOKEN environment variable first)  
upload:
	uv publish

# Complete release workflow
release: clean install test-coverage build

# Integration Testing
test-integration:
	@echo "🌤️ Testing BERtron MCP integration..."
	uv run pytest tests/test_api.py -v

# # Real-world Integration Testing
# test-real-world-integration:
# 	@echo "🌐 Testing real-world integration..."
# 	uv run pytest tests/test_real_world_integration.py -v

# MCP Protocol Testing
test-mcp-protocol:
	@echo "🔧 Testing MCP protocol implementation..."
	uv run pytest tests/test_mcp_protocol.py -v

# MCP Server testing
test-mcp:
	@echo "Testing MCP protocol with tools listing..."
	@(echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}, "id": 1}'; \
	 sleep 0.1; \
	 echo '{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}'; \
	 sleep 0.1; \
	 echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 2}') | \
	timeout 5 uv run python src/bertron_mcp/main.py

test-mcp-extended:
	@echo "Testing MCP protocol with tool execution..."
	@(echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}, "id": 1}'; \
	 sleep 0.1; \
	 echo '{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}'; \
	 sleep 0.1; \
	 echo '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "geosearch", "arguments": {"latitude": 28.5383, "longitude": -81.3792, "search_radius_km": 100.0}}, "id": 3}') | \
	uv run python src/bertron_mcp/main.py

# Test version flag
test-version:
	@echo "🔢 Testing version flag..."
	uv run python src/bertron_mcp/main.py --version

# Test with Claude CLI using local config
test-claude-mcp:
	@echo "🤖 Testing BERtron MCP with Claude CLI..."
	claude \
		--debug \
		--verbose \
		--mcp-config .mcp.json \
		--dangerously-skip-permissions \
		--print "Test the bertron-mcp by listing available tools and then search for entities within 100km of latitude 28.5383, longitude -81.3792" \
		2>&1 | tee claude-mcp-test.log


