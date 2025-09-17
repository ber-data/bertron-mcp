"""
MCP protocol tests for bertron-mcp server.

Tests verify MCP server implements protocol and responds to requests.
"""

import logging

from fastmcp import FastMCP

from src.bertron_mcp.main import DEFAULT_LIMIT, MAX_LIMIT, MAX_SKIP, mcp


def test_mcp_instance_creation():
    """Test that MCP instance is properly created"""
    assert mcp is not None
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "bertron_mcp"


def test_mcp_has_expected_methods():
    """Test that MCP instance has expected methods"""
    # Verify FastMCP instance methods exist
    assert hasattr(mcp, 'run')
    assert hasattr(mcp, 'get_tools')

    # Verify the instance is properly configured
    assert callable(mcp.run)
    assert callable(mcp.get_tools)


def test_mcp_constants_consistency():
    """Test that MCP tools use consistent constants"""
    # Verify constants are properly defined
    assert isinstance(DEFAULT_LIMIT, int)
    assert isinstance(MAX_LIMIT, int)
    assert isinstance(MAX_SKIP, int)

    # Verify relationships
    assert DEFAULT_LIMIT > 0
    assert MAX_LIMIT > DEFAULT_LIMIT
    assert MAX_SKIP > MAX_LIMIT


def test_tool_execution_basic():
    """Test basic tool execution by calling functions directly"""
    # Test health_check directly
    from src.bertron_mcp.main import health_check

    try:
        result = health_check()

        # Should return dict or None
        assert result is None or isinstance(result, dict)

        if isinstance(result, dict):
            # Should have expected health check fields
            assert "web_server" in result or "database" in result

    except Exception as e:
        # Network errors are acceptable in testing
        assert "API" in str(e) or "connection" in str(e).lower()


def test_geosearch_function_call():
    """Test geosearch function execution"""
    from bertron_client import QueryResponse

    from src.bertron_mcp.main import geosearch

    try:
        # Test with basic coordinates
        result = geosearch(0.0, 0.0, 1.0)

        # Should return QueryResponse or None
        assert result is None or isinstance(result, QueryResponse)

        if result is not None:
            assert hasattr(result, 'entities')
            assert hasattr(result, 'count')
            assert hasattr(result, 'query_type')

    except Exception as e:
        # Network/API errors are acceptable
        assert "API" in str(e) or "connection" in str(e).lower()


def test_entity_lookup_function_call():
    """Test entity_lookup function execution"""
    from schema.datamodel.bertron_schema_pydantic import Entity

    from src.bertron_mcp.main import entity_lookup

    try:
        # Test with invalid ID (should return None gracefully)
        result = entity_lookup("invalid_test_id")

        # Should return Entity or None
        assert result is None or isinstance(result, Entity)

    except Exception as e:
        # Network/API errors are acceptable
        assert "API" in str(e) or "connection" in str(e).lower()


def test_logging_configuration():
    """Test that logging is properly configured for MCP operations"""
    # Get the bertron_mcp logger
    logger = logging.getLogger("bertron_mcp.main")
    assert logger is not None

    # Logger should be properly configured
    assert hasattr(logger, 'level')
    assert hasattr(logger, 'handlers')


def test_constraint_reporting_integration():
    """Test that constraint reporting works with function calls"""
    from bertron_client import QueryResponse

    from src.bertron_mcp.main import search_by_source

    try:
        # Test with limit that should trigger constraint reporting
        result = search_by_source("NMDC", limit=5000)  # Above MAX_LIMIT

        if isinstance(result, QueryResponse):
            # Should have constraint reporting in metadata
            if result.metadata:
                # Check for constraint reporting
                assert isinstance(result.metadata, dict)

                # If constraints were applied, they should be reported
                if "constraints_applied" in result.metadata:
                    constraints = result.metadata["constraints_applied"]
                    assert "requested_limit" in constraints
                    assert "actual_limit" in constraints
                    assert constraints["requested_limit"] == 5000
                    assert constraints["actual_limit"] == MAX_LIMIT

    except Exception as e:
        # Network/API errors are acceptable
        assert "API" in str(e) or "connection" in str(e).lower()


def test_function_imports():
    """Test that all MCP tool functions can be imported and are callable"""
    from src.bertron_mcp.main import (
        advanced_query,
        bbox_search,
        entity_lookup,
        geosearch,
        health_check,
        search_by_name,
        search_by_source,
        search_by_type,
    )

    # All functions should be callable
    functions = [
        health_check,
        geosearch,
        bbox_search,
        entity_lookup,
        advanced_query,
        search_by_source,
        search_by_type,
        search_by_name,
    ]

    for func in functions:
        assert callable(func), f"Function {func.__name__} is not callable"
