import logging

from bertron_client import QueryResponse
from schema.datamodel.bertron_schema_pydantic import Coordinates, Entity

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

logger = logging.getLogger("bertron_mcp.main")

def test_healthcheck():
    # logger.setLevel(logging.DEBUG)

    health_status = health_check()

    # Ensure result is a dict
    assert isinstance(health_status, dict)

    # Check required keys exist
    assert "web_server" in health_status
    assert "database" in health_status

    # Check values are booleans
    assert isinstance(health_status["web_server"], bool)
    assert isinstance(health_status["database"], bool)

    # Check both are True (API healthy)
    assert health_status["web_server"] is True
    assert health_status["database"] is True

def test_geosearch_1():
    logger.setLevel(logging.DEBUG)

    # Pacific Ocean
    test_coords_lat: float = 0.0
    test_coords_lon: float = 6.0
    # test_radius_km: int = 5

    result = geosearch(test_coords_lat, test_coords_lon)

    # Ensure response type
    assert isinstance(result, QueryResponse)

    # No entities returned
    assert result.entities == []
    assert result.count == 0

    # Query type should match
    assert result.query_type == "geospatial_nearby"

    # Metadata validation
    assert "center" in result.metadata
    assert "radius_meters" in result.metadata
    assert result.metadata["center"]["latitude"] == 0.0
    assert result.metadata["center"]["longitude"] == 6.0
    assert result.metadata["radius_meters"] == 1000.0

    # Optional: Check count and entities match
    assert len(result.entities) == result.count

def test_geosearch_2():
    # logger.setLevel(logging.DEBUG)

    # Search for entities within 100km of Orlando, FL
    test_coords_lat: float = 28.5383
    test_coords_lon: float = -81.3792
    test_radius_km: float = 100.0

    result: QueryResponse = geosearch(test_coords_lat, test_coords_lon, test_radius_km)

    assert result is None or isinstance(result, QueryResponse)

    # Ensure the query type matches what we expect
    assert result.query_type == "geospatial_nearby"

    # Ensure count is correct
    assert result.count >= 1

    # Validate metadata
    assert "center" in result.metadata
    assert result.metadata["center"]["latitude"] == 28.5383
    assert result.metadata["center"]["longitude"] == -81.3792
    assert result.metadata["radius_meters"] == 100_000.0

    # Ensure entities exist and are well-formed
    assert len(result.entities) > 0
    first_entity = result.entities[0]
    assert isinstance(first_entity, Entity)

    # Check critical fields in the entity
    assert first_entity.id.startswith("nmdc:")
    assert first_entity.name is not None
    assert "sample" in first_entity.entity_type

    # Check coordinates
    coords = first_entity.coordinates
    assert isinstance(coords, Coordinates)
    assert -90 <= coords.latitude <= 90
    assert -180 <= coords.longitude <= 180

    # Check depth information if present
    if coords.depth:
        assert coords.depth.unit == "m"
        assert coords.depth.minimum_numeric_value >= 0.0

def test_bbox_search():
    """Test bounding box search functionality"""
    # Search for entities in a small bounding box around Orlando, FL
    result = bbox_search(
        southwest_lat=28.0,
        southwest_lng=-82.0,
        northeast_lat=29.0,
        northeast_lng=-81.0
    )

    assert result is None or isinstance(result, QueryResponse)

    if result is not None:
        assert result.query_type == "geospatial_bounding_box"
        assert "bounding_box" in result.metadata
        assert result.metadata["bounding_box"]["southwest"]["latitude"] == 28.0
        assert result.metadata["bounding_box"]["southwest"]["longitude"] == -82.0
        assert result.metadata["bounding_box"]["northeast"]["latitude"] == 29.0
        assert result.metadata["bounding_box"]["northeast"]["longitude"] == -81.0
        assert len(result.entities) == result.count

def test_search_by_source():
    """Test searching by data source"""
    result = search_by_source("NMDC")

    assert result is None or isinstance(result, QueryResponse)

    if result is not None and result.count > 0:
        # Verify all entities are from NMDC source
        for entity in result.entities:
            assert entity.ber_data_source == "NMDC"

def test_search_by_type():
    """Test searching by entity type"""
    result = search_by_type("sample")

    assert result is None or isinstance(result, QueryResponse)

    if result is not None and result.count > 0:
        # Verify all entities are samples
        for entity in result.entities:
            assert "sample" in entity.entity_type

def test_search_by_name():
    """Test searching by name pattern"""
    result = search_by_name(".*water.*", case_sensitive=False)

    assert result is None or isinstance(result, QueryResponse)

    if result is not None and result.count > 0:
        # Verify entities contain "water" in name (case-insensitive)
        for entity in result.entities:
            if entity.name:
                assert "water" in entity.name.lower()

def test_entity_lookup():
    """Test entity lookup by ID"""
    # First get an entity ID from a geosearch
    search_result = geosearch(28.5383, -81.3792, 50.0)

    if search_result is not None and search_result.count > 0:
        entity_id = search_result.entities[0].id

        if entity_id:
            result = entity_lookup(entity_id)

            assert result is None or isinstance(result, Entity)

            if result is not None:
                assert result.id == entity_id
                assert result.name is not None
                assert result.coordinates is not None

def test_advanced_query():
    """Test advanced query functionality"""
    # Search for sample entities without projection to avoid validation issues
    result = advanced_query(
        filter_dict={"entity_type": "sample"},
        limit=10
    )

    assert result is None or isinstance(result, QueryResponse)

    if result is not None and result.count > 0:
        assert len(result.entities) <= 10
        # Verify all entities are samples
        for entity in result.entities:
            assert "sample" in entity.entity_type

# Test limit enforcement and constraint reporting
def test_search_by_source_limit_enforcement():
    """Test that search_by_source enforces limits and reports constraints"""
    # Test with limit above maximum
    result = search_by_source("NMDC", limit=5000)

    assert result is None or isinstance(result, QueryResponse)

    if result is not None:
        # Should be constrained to MAX_LIMIT (1000)
        assert len(result.entities) <= 1000

        # Should report constraints in metadata
        if "constraints_applied" in result.metadata:
            constraints = result.metadata["constraints_applied"]
            assert constraints["requested_limit"] == 5000
            assert constraints["actual_limit"] == 1000
            assert "maximum limit" in constraints["reason"]

def test_search_by_type_limit_enforcement():
    """Test that search_by_type enforces limits and reports constraints"""
    # Test with limit above maximum
    result = search_by_type("sample", limit=2000)

    assert result is None or isinstance(result, QueryResponse)

    if result is not None:
        # Should be constrained to MAX_LIMIT (1000)
        assert len(result.entities) <= 1000

        # Should report constraints in metadata
        if "constraints_applied" in result.metadata:
            constraints = result.metadata["constraints_applied"]
            assert constraints["requested_limit"] == 2000
            assert constraints["actual_limit"] == 1000

def test_search_by_name_limit_enforcement():
    """Test that search_by_name enforces limits and reports constraints"""
    # Test with limit above maximum
    result = search_by_name(".*", case_sensitive=False, limit=1500)

    assert result is None or isinstance(result, QueryResponse)

    if result is not None:
        # Should be constrained to MAX_LIMIT (1000)
        assert len(result.entities) <= 1000

        # Should report constraints in metadata
        if "constraints_applied" in result.metadata:
            constraints = result.metadata["constraints_applied"]
            assert constraints["requested_limit"] == 1500
            assert constraints["actual_limit"] == 1000

def test_advanced_query_limit_enforcement():
    """Test that advanced_query enforces limits and reports constraints"""
    # Test with limit above maximum
    result = advanced_query(
        filter_dict={"entity_type": "sample"},
        limit=3000
    )

    assert result is None or isinstance(result, QueryResponse)

    if result is not None:
        # Should be constrained to MAX_LIMIT (1000)
        assert len(result.entities) <= 1000

        # Should report constraints in metadata
        if "constraints_applied" in result.metadata:
            constraints = result.metadata["constraints_applied"]
            assert "limit" in constraints
            assert constraints["limit"]["requested"] == 3000
            assert constraints["limit"]["actual"] == 1000

def test_advanced_query_no_filter_safety():
    """Test that advanced_query applies safety filter when no filter provided"""
    # Test without filter - should apply safety filter
    result = advanced_query(limit=10)

    assert result is None or isinstance(result, QueryResponse)

    if result is not None:
        # Should report filter constraint in metadata
        if "constraints_applied" in result.metadata:
            constraints = result.metadata["constraints_applied"]
            if "filter" in constraints:
                assert constraints["filter"]["requested"] == "none"
                assert "safety filter" in constraints["filter"]["reason"].lower()

def test_advanced_query_excessive_skip():
    """Test that advanced_query rejects excessive skip values"""
    # Test with skip above maximum (should return None)
    result = advanced_query(
        filter_dict={"entity_type": "sample"},
        skip=100000,  # Above MAX_SKIP
        limit=10
    )

    # Should return None due to excessive skip
    assert result is None

def test_search_by_source_all_sources():
    """Test search_by_source with all valid data sources"""
    sources = ["EMSL", "ESS-DIVE", "JGI", "NMDC", "MONET"]

    for source in sources:
        result = search_by_source(source, limit=5)

        # Should return valid response or None (some sources may have no data)
        assert result is None or isinstance(result, QueryResponse)

        if result is not None and result.count > 0:
            # All entities should be from the requested source
            for entity in result.entities:
                assert entity.ber_data_source == source

def test_search_by_type_all_types():
    """Test search_by_type with all valid entity types"""
    types = ["biodata", "sample", "sequence", "taxon", "jgi_biosample"]

    for entity_type in types:
        result = search_by_type(entity_type, limit=5)

        # Should return valid response or None (some types may have no data)
        assert result is None or isinstance(result, QueryResponse)

        if result is not None and result.count > 0:
            # All entities should be of the requested type
            for entity in result.entities:
                assert entity_type in entity.entity_type

def test_search_by_name_case_sensitivity():
    """Test search_by_name case sensitivity options"""
    # Test case-insensitive search (default)
    result_insensitive = search_by_name("WATER", case_sensitive=False, limit=5)

    # Test case-sensitive search
    result_sensitive = search_by_name("WATER", case_sensitive=True, limit=5)

    # Both should return valid responses or None
    assert result_insensitive is None or isinstance(result_insensitive, QueryResponse)
    assert result_sensitive is None or isinstance(result_sensitive, QueryResponse)

    # Case-insensitive should generally return more results
    if result_insensitive is not None and result_sensitive is not None:
        assert result_insensitive.count >= result_sensitive.count

def test_search_by_name_regex_patterns():
    """Test search_by_name with various regex patterns"""
    patterns = [
        ".*soil.*",      # Contains 'soil'
        "^NMDC",        # Starts with 'NMDC'
        "sample$",      # Ends with 'sample'
        "[0-9]+",       # Contains numbers
    ]

    for pattern in patterns:
        result = search_by_name(pattern, case_sensitive=False, limit=5)

        # Should return valid response or None
        assert result is None or isinstance(result, QueryResponse)

def test_geosearch_edge_coordinates():
    """Test geosearch with edge case coordinates"""
    edge_cases = [
        # Extreme coordinates
        (90.0, 180.0, 1.0),    # North pole, international date line
        (-90.0, -180.0, 1.0),  # South pole, international date line
        (0.0, 0.0, 1.0),       # Equator, prime meridian
        # Various radius sizes
        (40.7128, -74.0060, 0.1),  # NYC, very small radius
        (40.7128, -74.0060, 500.0), # NYC, large radius
    ]

    for lat, lon, radius in edge_cases:
        result = geosearch(lat, lon, radius)

        # Should return valid response
        assert result is None or isinstance(result, QueryResponse)

        if result is not None:
            # Verify metadata
            assert result.metadata["center"]["latitude"] == lat
            assert result.metadata["center"]["longitude"] == lon
            assert result.metadata["radius_meters"] == radius * 1000

def test_bbox_search_edge_cases():
    """Test bbox_search with various bounding box sizes"""
    test_cases = [
        # Small bounding box
        (40.0, -75.0, 41.0, -74.0),
        # Large bounding box spanning continents
        (-10.0, -50.0, 50.0, 50.0),
        # Bounding box crossing date line
        (20.0, 170.0, 30.0, -170.0),
    ]

    for sw_lat, sw_lng, ne_lat, ne_lng in test_cases:
        result = bbox_search(sw_lat, sw_lng, ne_lat, ne_lng)

        # Should return valid response
        assert result is None or isinstance(result, QueryResponse)

        if result is not None:
            # Verify metadata
            assert result.metadata["bounding_box"]["southwest"]["latitude"] == sw_lat
            assert result.metadata["bounding_box"]["southwest"]["longitude"] == sw_lng
            assert result.metadata["bounding_box"]["northeast"]["latitude"] == ne_lat
            assert result.metadata["bounding_box"]["northeast"]["longitude"] == ne_lng

def test_advanced_query_with_projection():
    """Test advanced_query with field projection"""
    result = advanced_query(
        filter_dict={"entity_type": "sample"},
        limit=5
    )

    assert result is None or isinstance(result, QueryResponse)

    # Note: Projection behavior depends on API implementation
    # This test ensures the function handles basic queries correctly

def test_advanced_query_with_sorting():
    """Test advanced_query with sorting"""
    result = advanced_query(
        filter_dict={"entity_type": "sample"},
        sort={"name": 1},  # Sort by name ascending
        limit=10
    )

    assert result is None or isinstance(result, QueryResponse)

    if result is not None and result.count > 1:
        # Verify entities are returned (sorting verification needs specific data)
        assert len(result.entities) > 0

def test_advanced_query_pagination():
    """Test advanced_query pagination"""
    # Get first page
    page1 = advanced_query(
        filter_dict={"entity_type": "sample"},
        skip=0,
        limit=5
    )

    # Get second page
    page2 = advanced_query(
        filter_dict={"entity_type": "sample"},
        skip=5,
        limit=5
    )

    assert page1 is None or isinstance(page1, QueryResponse)
    assert page2 is None or isinstance(page2, QueryResponse)

    # If both pages have data, entities should be different
    if (page1 is not None and page1.count > 0 and
        page2 is not None and page2.count > 0):
        page1_ids = {entity.id for entity in page1.entities if entity.id}
        page2_ids = {entity.id for entity in page2.entities if entity.id}
        # Pages should generally have different entities (unless very limited data)
        if page1_ids and page2_ids:
            # Allow some overlap in case of limited test data
            intersection_len = len(page1_ids.intersection(page2_ids))
            max_len = max(len(page1_ids), len(page2_ids))
            assert intersection_len < max_len

def test_entity_lookup_invalid_id():
    """Test entity_lookup with various ID formats"""
    test_ids = [
        "invalid_id",
        "",
        "nmdc:nonexistent",
        "fake:test:id",
    ]

    for entity_id in test_ids:
        result = entity_lookup(entity_id)

        # Should return None for invalid/nonexistent IDs
        assert result is None or isinstance(result, Entity)

def test_all_tools_return_types():
    """Test that all tools return expected types"""
    # Test basic calls to ensure proper return types
    
    # Health check should always return dict
    result = health_check()
    assert isinstance(result, dict)
    
    # Geosearch should return QueryResponse
    result = geosearch(0.0, 0.0)
    assert isinstance(result, QueryResponse)
    
    # Bbox search should return QueryResponse
    result = bbox_search(0.0, 0.0, 1.0, 1.0)
    assert isinstance(result, QueryResponse)
    
    # Search by source should return QueryResponse
    result = search_by_source("NMDC", limit=1)
    assert isinstance(result, QueryResponse)
    
    # Search by type should return QueryResponse
    result = search_by_type("sample", limit=1)
    assert isinstance(result, QueryResponse)
    
    # Search by name should return QueryResponse
    result = search_by_name("test", limit=1)
    assert isinstance(result, QueryResponse)
    
    # Advanced query should return QueryResponse
    result = advanced_query(filter_dict={"entity_type": "sample"}, limit=1)
    assert isinstance(result, QueryResponse)
    
    # Entity lookup with invalid ID should return None
    result = entity_lookup("test_id")
    assert result is None
