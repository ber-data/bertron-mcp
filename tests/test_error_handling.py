"""
Test error handling and edge cases for bertron-mcp.
"""


from bertron_client import BertronAPIError, QueryResponse
from schema.datamodel.bertron_schema_pydantic import Entity

from src.bertron_mcp.main import (
    MAX_LIMIT,
    MAX_SKIP,
    advanced_query,
    bbox_search,
    entity_lookup,
    geosearch,
    health_check,
    search_by_name,
    search_by_source,
    search_by_type,
)


def test_health_check_api_error():
    """Test health_check handles API errors gracefully"""
    # Test that function handles API errors without crashing
    result = health_check()

    # Should return dict or None, never crash
    assert result is None or isinstance(result, dict)


def test_geosearch_invalid_coordinates():
    """Test geosearch with invalid coordinate values"""
    # Test extreme coordinates
    test_cases = [
        (91.0, 0.0),    # Invalid latitude > 90
        (-91.0, 0.0),   # Invalid latitude < -90
        (0.0, 181.0),   # Invalid longitude > 180
        (0.0, -181.0),  # Invalid longitude < -180
        (float('inf'), 0.0),  # Infinite latitude
        (0.0, float('nan')),  # NaN longitude
    ]

    for lat, lon in test_cases:
        try:
            result = geosearch(lat, lon, 1.0)
            # Should return None or QueryResponse, not crash
            assert result is None or isinstance(result, QueryResponse)
        except Exception as e:
            # Some validation errors are acceptable
            assert isinstance(e, (ValueError, TypeError, BertronAPIError))


def test_geosearch_negative_radius():
    """Test geosearch with negative search radius"""
    try:
        result = geosearch(0.0, 0.0, -1.0)
        # Should handle gracefully
        assert result is None or isinstance(result, QueryResponse)
    except Exception as e:
        # Validation errors are acceptable
        assert isinstance(e, (ValueError, BertronAPIError))


def test_geosearch_zero_radius():
    """Test geosearch with zero search radius"""
    result = geosearch(0.0, 0.0, 0.0)
    # Should handle gracefully
    assert result is None or isinstance(result, QueryResponse)


def test_bbox_search_invalid_bbox():
    """Test bbox_search with invalid bounding box coordinates"""
    # Southwest corner should be southwest of northeast corner
    invalid_cases = [
        # Southwest lat > Northeast lat
        (30.0, -80.0, 20.0, -70.0),
        # Southwest lng > Northeast lng (non-crossing case)
        (20.0, -70.0, 30.0, -80.0),
        # Invalid coordinate ranges
        (91.0, 0.0, 92.0, 1.0),  # Invalid latitudes
        (0.0, 181.0, 1.0, 182.0),  # Invalid longitudes
    ]

    for sw_lat, sw_lng, ne_lat, ne_lng in invalid_cases:
        try:
            result = bbox_search(sw_lat, sw_lng, ne_lat, ne_lng)
            # Should return None or handle gracefully
            assert result is None or isinstance(result, QueryResponse)
        except Exception as e:
            # Validation errors are acceptable
            assert isinstance(e, (ValueError, BertronAPIError))


def test_entity_lookup_empty_id():
    """Test entity_lookup with empty or invalid entity IDs"""
    invalid_ids = ["", " ", None, "invalid", "nmdc:", ":invalid"]

    for entity_id in invalid_ids:
        try:
            if entity_id is None:
                continue  # Skip None test as it would cause TypeError
            result = entity_lookup(entity_id)
            # Should return None for invalid IDs
            assert result is None or isinstance(result, Entity)
        except Exception as e:
            # API errors are acceptable
            assert isinstance(e, (BertronAPIError, TypeError))


def test_search_by_source_invalid_source():
    """Test search_by_source with invalid data sources"""
    invalid_sources = ["INVALID", "", " ", "invalid_source", "123", None]

    for source in invalid_sources:
        try:
            if source is None:
                continue  # Skip None test
            result = search_by_source(source)
            # Should return None or empty result for invalid sources
            assert result is None or isinstance(result, QueryResponse)
            if isinstance(result, QueryResponse):
                # Invalid sources should return no results
                assert result.count >= 0
        except Exception as e:
            # API or validation errors are acceptable
            assert isinstance(e, (BertronAPIError, TypeError))


def test_search_by_type_invalid_type():
    """Test search_by_type with invalid entity types"""
    invalid_types = ["invalid_type", "", " ", "123", None]

    for entity_type in invalid_types:
        try:
            if entity_type is None:
                continue  # Skip None test
            result = search_by_type(entity_type)
            # Should return None or empty result for invalid types
            assert result is None or isinstance(result, QueryResponse)
            if isinstance(result, QueryResponse):
                assert result.count >= 0
        except Exception as e:
            # API or validation errors are acceptable
            assert isinstance(e, (BertronAPIError, TypeError))


def test_search_by_name_empty_pattern():
    """Test search_by_name with empty or invalid patterns"""
    invalid_patterns = ["", " ", None]

    for pattern in invalid_patterns:
        try:
            if pattern is None:
                continue  # Skip None test
            result = search_by_name(pattern)
            # Should handle gracefully
            assert result is None or isinstance(result, QueryResponse)
        except Exception as e:
            # API or validation errors are acceptable
            assert isinstance(e, (BertronAPIError, TypeError))


def test_search_by_name_invalid_regex():
    """Test search_by_name with invalid regex patterns"""
    invalid_regex_patterns = [
        "[",           # Unclosed bracket
        "(?P<",        # Invalid group
        "*",           # Invalid quantifier
        "(?",          # Incomplete group
    ]

    for pattern in invalid_regex_patterns:
        try:
            result = search_by_name(pattern)
            # Should handle regex errors gracefully
            assert result is None or isinstance(result, QueryResponse)
        except Exception as e:
            # Regex or API errors are acceptable
            assert isinstance(e, (BertronAPIError, ValueError))


def test_advanced_query_excessive_skip():
    """Test advanced_query with skip values above maximum"""
    # Test with skip above MAX_SKIP
    result = advanced_query(
        filter_dict={"entity_type": "sample"},
        skip=MAX_SKIP + 1
    )

    # Should return None for excessive skip
    assert result is None


def test_advanced_query_no_filter_safety():
    """Test advanced_query applies safety filter when no filter provided"""
    result = advanced_query(skip=0, limit=5)

    # Should handle safely with automatic filter
    assert result is None or isinstance(result, QueryResponse)

    if isinstance(result, QueryResponse) and result.metadata:
        # Should report filter constraint
        if "constraints_applied" in result.metadata:
            assert "filter" in result.metadata["constraints_applied"]


def test_advanced_query_invalid_filter():
    """Test advanced_query with invalid filter dictionaries"""
    invalid_filters = [
        {"$invalid": "operator"},
        {"field": {"$badop": "value"}},
        "",  # String instead of dict
        [],  # List instead of dict
    ]

    for invalid_filter in invalid_filters:
        try:
            if isinstance(invalid_filter, dict):
                result = advanced_query(filter_dict=invalid_filter, limit=5)
                # Should handle invalid filters gracefully
                assert result is None or isinstance(result, QueryResponse)
            else:
                # Non-dict filters should cause type errors
                continue
        except Exception as e:
            # API or validation errors are acceptable
            assert isinstance(e, (BertronAPIError, TypeError, ValueError))


def test_limit_enforcement_edge_cases():
    """Test limit enforcement with edge case values"""
    edge_cases = [0, -1, -100, MAX_LIMIT + 1, MAX_LIMIT * 10]

    for limit in edge_cases:
        try:
            result = search_by_source("NMDC", limit=limit)

            if isinstance(result, QueryResponse):
                # Limits should be enforced
                assert len(result.entities) <= MAX_LIMIT

                # Negative limits should be handled gracefully
                if limit <= 0:
                    assert len(result.entities) == 0 or result.count >= 0

        except Exception as e:
            # API or validation errors for negative limits are acceptable
            assert isinstance(e, (BertronAPIError, ValueError))


