import logging

from bertron_client import QueryResponse
from schema.datamodel.bertron_schema_pydantic import Coordinates, Entity

from src.bertron_mcp.main import geosearch, health_check

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
        assert coords.depth.has_unit == "m"
        assert coords.depth.has_minimum_numeric_value >= 0.0
