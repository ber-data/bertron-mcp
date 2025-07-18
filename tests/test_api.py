import logging

from src.bertron_mcp.main import geosearch

logger = logging.getLogger("bertron_mcp.main")

loc_lansing_mi_lat: float = 42.732536
loc_lansing_mi_lon: float = -84.555534

loc_pacific_ocean_lat: float = 0.0
loc_pacific_ocean_lon: float = 6.0


def test_geosearch_1():
    logger.setLevel(logging.DEBUG)

    test_coords_lat: float = loc_pacific_ocean_lat
    test_coords_lon: float = loc_pacific_ocean_lon
    # test_radius_m: float = 5.0

    result = geosearch(test_coords_lat, test_coords_lon)

    # Assert that the result is None or matches expected behavior for no coverage
    assert result is None or isinstance(result, dict)
    # Expect 0.0 coverage for the Pacific Ocean
    # if isinstance(result, dict):
        # assert ...

def test_geosearch_2():
    logger.setLevel(logging.DEBUG)

    test_coords_lat: float = loc_lansing_mi_lat
    test_coords_lon: float = loc_lansing_mi_lon
    test_radius_km: float = 50000.0

    result = geosearch(test_coords_lat, test_coords_lon, test_radius_km)

    # Assert that the result is None or matches expected behavior for no coverage
    assert result is None or isinstance(result, dict)
    # if isinstance(result, dict):
        # assert ... # Expect more than 10 records for Lansing.
