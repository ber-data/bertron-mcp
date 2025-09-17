"""
Integration tests for bertron-mcp with real API calls.
"""

from bertron_client import QueryResponse
from schema.datamodel.bertron_schema_pydantic import Entity

from src.bertron_mcp.main import (
    MAX_LIMIT,
    advanced_query,
    bbox_search,
    entity_lookup,
    geosearch,
    health_check,
    search_by_name,
    search_by_source,
    search_by_type,
)


def test_full_workflow_geospatial_search():
    """Test a complete workflow: health check -> geosearch -> entity lookup"""
    # Step 1: Verify API is healthy
    health = health_check()
    if health is None:
        return  # Skip if API is not available

    # Step 2: Search for entities near a known location (Orlando, FL)
    search_result = geosearch(28.5383, -81.3792, 50.0)

    if search_result is not None and isinstance(search_result, QueryResponse):
        # Verify basic properties
        assert search_result.count >= 0
        assert len(search_result.entities) == search_result.count

        # Step 3: If we found entities, look up the first one
        if search_result.entities:
            first_entity = search_result.entities[0]
            if hasattr(first_entity, 'id') and first_entity.id:
                detailed_entity = entity_lookup(first_entity.id)

                if detailed_entity is not None:
                    assert isinstance(detailed_entity, Entity)
                    assert detailed_entity.id == first_entity.id


def test_search_by_source_workflow():
    """Test searching by data source and validating results"""
    # Test with a known data source
    result = search_by_source("NMDC", limit=10)

    if result is not None and isinstance(result, QueryResponse):
        assert result.count >= 0
        assert len(result.entities) <= 10

        # All entities should be from NMDC source
        for entity in result.entities:
            if hasattr(entity, 'ber_data_source'):
                assert entity.ber_data_source == "NMDC"


def test_search_by_type_workflow():
    """Test searching by entity type and validating results"""
    # Test with sample entity type
    result = search_by_type("sample", limit=5)

    if result is not None and isinstance(result, QueryResponse):
        assert result.count >= 0
        assert len(result.entities) <= 5

        # All entities should be samples
        for entity in result.entities:
            if hasattr(entity, 'entity_type'):
                assert "sample" in entity.entity_type


def test_advanced_query_with_filters():
    """Test advanced query with realistic filters"""
    # Test with entity type filter
    result = advanced_query(
        filter_dict={"entity_type": "sample"},
        limit=5
    )

    if result is not None and isinstance(result, QueryResponse):
        assert result.count >= 0
        assert len(result.entities) <= 5

        # Verify all entities match the filter
        for entity in result.entities:
            if hasattr(entity, 'entity_type'):
                assert "sample" in entity.entity_type


def test_bounding_box_search_realistic():
    """Test bounding box search with realistic coordinates"""
    # Search around Florida
    result = bbox_search(
        southwest_lat=24.0,
        southwest_lng=-85.0,
        northeast_lat=31.0,
        northeast_lng=-80.0
    )

    if result is not None and isinstance(result, QueryResponse):
        assert result.count >= 0
        assert len(result.entities) == result.count

        # Verify metadata
        if result.metadata and "bounding_box" in result.metadata:
            bbox = result.metadata["bounding_box"]
            assert bbox["southwest"]["latitude"] == 24.0
            assert bbox["southwest"]["longitude"] == -85.0
            assert bbox["northeast"]["latitude"] == 31.0
            assert bbox["northeast"]["longitude"] == -80.0


def test_name_search_realistic():
    """Test name search with realistic patterns"""
    # Search for water-related samples
    result = search_by_name(".*water.*", case_sensitive=False, limit=5)

    assert isinstance(result, QueryResponse)
    assert result.count >= 0
    assert len(result.entities) <= 5

    # If we found results, verify they contain "water" in name
    for entity in result.entities:
        if hasattr(entity, 'name') and entity.name:
            assert "water" in entity.name.lower()


def test_limit_constraint_enforcement():
    """Test that limits are actually enforced"""
    # Test with limit above maximum
    result = search_by_source("NMDC", limit=MAX_LIMIT + 100)

    if result is not None and isinstance(result, QueryResponse):
        # Should be constrained to MAX_LIMIT
        assert len(result.entities) <= MAX_LIMIT

        # Should report constraints in metadata
        if result.metadata and "constraints_applied" in result.metadata:
            constraints = result.metadata["constraints_applied"]
            assert constraints["requested_limit"] == MAX_LIMIT + 100
            assert constraints["actual_limit"] == MAX_LIMIT


def test_entity_data_quality():
    """Test that returned entities have expected data quality"""
    result = geosearch(28.5383, -81.3792, 100.0)

    if result is not None and isinstance(result, QueryResponse) and result.entities:
        for entity in result.entities[:3]:  # Check first 3 entities
            # Should have basic required fields
            assert hasattr(entity, 'id')
            assert hasattr(entity, 'name')
            assert hasattr(entity, 'entity_type')

            # ID should be meaningful
            if entity.id:
                assert len(entity.id) > 0
                assert not entity.id.isspace()

            # Name should be meaningful if present
            if entity.name:
                assert len(entity.name) > 0
                assert not entity.name.isspace()

            # Should have coordinates if it's a geospatial result
            if hasattr(entity, 'coordinates') and entity.coordinates:
                assert hasattr(entity.coordinates, 'latitude')
                assert hasattr(entity.coordinates, 'longitude')
                assert -90 <= entity.coordinates.latitude <= 90
                assert -180 <= entity.coordinates.longitude <= 180


def test_error_recovery():
    """Test that functions handle edge cases appropriately"""
    # Test with edge case inputs

    # Very small radius should work and return valid QueryResponse
    result = geosearch(0.0, 0.0, 0.1)
    assert isinstance(result, QueryResponse)
    assert result.count >= 0  # Empty results are fine

    # Invalid ID should return None (documented behavior)
    result = entity_lookup("invalid_id")
    assert result is None

    # Invalid source should return QueryResponse with no results
    result = search_by_source("INVALID_SOURCE")
    assert isinstance(result, QueryResponse)
    assert result.count == 0  # Should be empty but not None

    # Invalid type should return QueryResponse with no results
    result = search_by_type("invalid_type")
    assert isinstance(result, QueryResponse)
    assert result.count == 0  # Should be empty but not None

    # Nonexistent field should return QueryResponse (API should handle gracefully)
    result = advanced_query(filter_dict={"nonexistent_field": "value"})
    assert isinstance(result, QueryResponse)
    assert result.count >= 0  # Empty results are acceptable


def test_pagination_workflow():
    """Test pagination with skip and limit"""
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

    if (page1 is not None and isinstance(page1, QueryResponse) and
        page2 is not None and isinstance(page2, QueryResponse)):

        # Both pages should have valid results
        assert page1.count >= 0
        assert page2.count >= 0

        # If both have entities, they should generally be different
        if page1.entities and page2.entities:
            page1_ids = {e.id for e in page1.entities if hasattr(e, 'id') and e.id}
            page2_ids = {e.id for e in page2.entities if hasattr(e, 'id') and e.id}

            # Should be mostly different entities (allow some overlap for limited data)
            if page1_ids and page2_ids:
                overlap = len(page1_ids.intersection(page2_ids))
                total_unique = len(page1_ids.union(page2_ids))
                if total_unique > 0:
                    overlap_ratio = overlap / total_unique
                    assert overlap_ratio < 0.8  # Less than 80% overlap


def test_comprehensive_data_sources():
    """Test all known data sources return valid results"""
    sources = ["EMSL", "ESS-DIVE", "JGI", "NMDC", "MONET"]

    for source in sources:
        result = search_by_source(source, limit=3)

        # Each source should return valid result or None
        assert result is None or isinstance(result, QueryResponse)

        if result is not None:
            assert result.count >= 0
            assert len(result.entities) <= 3

            # All entities should be from the correct source
            for entity in result.entities:
                if hasattr(entity, 'ber_data_source'):
                    assert entity.ber_data_source == source


def test_comprehensive_entity_types():
    """Test all known entity types return valid results"""
    types = ["biodata", "sample", "sequence", "taxon", "jgi_biosample"]

    for entity_type in types:
        result = search_by_type(entity_type, limit=3)

        # Each type should return valid result or None
        assert result is None or isinstance(result, QueryResponse)

        if result is not None:
            assert result.count >= 0
            assert len(result.entities) <= 3

            # All entities should be of the correct type
            for entity in result.entities:
                if hasattr(entity, 'entity_type'):
                    assert entity_type in entity.entity_type
