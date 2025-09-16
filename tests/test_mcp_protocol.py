"""
MCP protocol tests for bertron-mcp server.

Tests verify MCP server implements protocol and responds to requests.
"""

def test_mcp_tool_registration():
    """Test that MCP tools are properly registered."""
    from src.bertron_mcp.main import mcp

    # Verify that the MCP instance is properly initialized
    assert mcp is not None
    assert mcp.name == "bertron_mcp"

    # Import the functions to verify they exist
    from src.bertron_mcp.main import geosearch

    # Verify functions are callable
    assert callable(geosearch)
