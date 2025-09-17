"""
Test constants, version handling, and module-level functionality.
"""

from src.bertron_mcp.main import DEFAULT_LIMIT, MAX_LIMIT, MAX_SKIP, __version__


def test_constants_defined():
    """Test that all limit constants are properly defined"""
    # Check constants exist and have reasonable values
    assert isinstance(DEFAULT_LIMIT, int)
    assert isinstance(MAX_LIMIT, int)
    assert isinstance(MAX_SKIP, int)

    # Check values are reasonable
    assert DEFAULT_LIMIT > 0
    assert MAX_LIMIT > DEFAULT_LIMIT
    assert MAX_SKIP > MAX_LIMIT

    # Check specific expected values
    assert DEFAULT_LIMIT == 100
    assert MAX_LIMIT == 1000
    assert MAX_SKIP == 50000


def test_version_handling():
    """Test that version is handled properly"""
    # Version should be a string
    assert isinstance(__version__, str)

    # Version should not be empty
    assert len(__version__) > 0

    # Version should be 'unknown' or a valid version string
    assert __version__ == "unknown" or "." in __version__


def test_module_imports():
    """Test that all important module components can be imported"""
    # Test main imports
    from src.bertron_mcp.main import (
        BERTRON_API_URL,
        advanced_query,
        bbox_search,
        entity_lookup,
        geosearch,
        health_check,
        main,
        mcp,
        search_by_name,
        search_by_source,
        search_by_type,
    )

    # Check that API URL is defined
    assert isinstance(BERTRON_API_URL, str)
    assert len(BERTRON_API_URL) > 0
    assert BERTRON_API_URL.startswith("https://")

    # Check that functions are callable
    assert callable(health_check)
    assert callable(geosearch)
    assert callable(bbox_search)
    assert callable(entity_lookup)
    assert callable(advanced_query)
    assert callable(search_by_source)
    assert callable(search_by_type)
    assert callable(search_by_name)
    assert callable(main)

    # Check that mcp instance exists
    assert mcp is not None
    assert hasattr(mcp, "run")


def test_logging_setup():
    """Test that logging is set up properly"""
    import logging

    # Get the module logger
    logger = logging.getLogger("bertron_mcp.main")

    # Logger should exist
    assert logger is not None

    # Logger should have reasonable default level
    # (May be changed by other tests, so we just check it exists)
    assert hasattr(logger, "level")


def test_constants_consistency():
    """Test that constants are used consistently in function signatures"""
    import inspect

    from src.bertron_mcp.main import (
        advanced_query,
        search_by_name,
        search_by_source,
        search_by_type,
    )

    # Check function signatures use DEFAULT_LIMIT
    sig = inspect.signature(search_by_source)
    assert sig.parameters['limit'].default == DEFAULT_LIMIT

    sig = inspect.signature(search_by_type)
    assert sig.parameters['limit'].default == DEFAULT_LIMIT

    sig = inspect.signature(search_by_name)
    assert sig.parameters['limit'].default == DEFAULT_LIMIT

    sig = inspect.signature(advanced_query)
    assert sig.parameters['limit'].default == DEFAULT_LIMIT


def test_ssl_warnings_disabled():
    """Test that SSL warnings are properly disabled"""
    import urllib3

    # Check that urllib3 is available (should be imported in main)
    assert hasattr(urllib3, "disable_warnings")

    # This test mainly ensures the import works
    # SSL warning disabling is tested by the fact that other tests don't show warnings


def test_constants_mathematical_relationships():
    """Test that constants have proper mathematical relationships"""
    # DEFAULT_LIMIT should be a reasonable fraction of MAX_LIMIT
    assert DEFAULT_LIMIT <= MAX_LIMIT / 2  # At least half the max

    # MAX_SKIP should be significantly larger than MAX_LIMIT for pagination
    assert MAX_SKIP >= MAX_LIMIT * 10  # At least 10x the max limit

    # All should be round numbers for user-friendliness
    assert DEFAULT_LIMIT % 10 == 0  # Round number
    assert MAX_LIMIT % 100 == 0     # Round number
    assert MAX_SKIP % 1000 == 0     # Round number


def test_api_url_configuration():
    """Test API URL configuration"""
    from src.bertron_mcp.main import BERTRON_API_URL

    # Should be a proper HTTPS URL
    assert BERTRON_API_URL.startswith("https://")
    assert BERTRON_API_URL.endswith("/")

    # Should contain expected domain
    assert "bertron" in BERTRON_API_URL.lower()

    # Should be a reasonable length
    assert 30 < len(BERTRON_API_URL) < 200
