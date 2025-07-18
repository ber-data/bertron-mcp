################################################################################
# bertron_mcp/main.py
# This module provides a FastMCP wrapper for the BERtron API.
################################################################################

import logging
import sys
from importlib import metadata
from typing import Optional

from fastmcp import FastMCP

from bertron_client import BertronClient, BertronAPIError, QueryResponse
# from schema.datamodel.bertron_schema_pydantic import Entity, BERSourceType, EntityType

logger = logging.getLogger(__name__)

# Version handling
try:
    __version__ = metadata.version("bertron-mcp")
except metadata.PackageNotFoundError:
    # Fallback to _version.py if package not installed
    try:
        from ._version import __version__
    except ImportError:
        __version__ = "unknown"

BERTRON_API_URL: str = "https://bertron-api.bertron.production.svc.spin.nersc.org/bertron/"

def health_check() -> Optional[dict[str, bool]]:
    """
    Check BERtron API health status.

    Returns:
        Optional[dict[str, str]]: Health status keys include 'web_server' and 'database'.
    """
    client = BertronClient(base_url=BERTRON_API_URL)

    try:
        health_status = client.health_check()
        logger.info("BERtron API is healthy. Web Server: %s, Database: %s",
                    health_status.get("web_server"), health_status.get("database"))
        logger.debug("Full health check response: %s", health_status)
        return health_status

    except BertronAPIError as e:
        import traceback
        logger.error("API connection error: %s", e)
        logger.debug(traceback.format_exc())

    return None

def geosearch(
    latitude: float,
    longitude: float,
    search_radius_km: float = 1.0
) -> QueryResponse | None:
    """
    Search BERtron catalogue for data within a specified distance of a given latitude and longitude.

    Args:
        latitude: latitude of the point (-90.0 to 90.0)
        longitude: longitude of the point (-180.0 to 180.0)
        search_radius_km: the station search radius in m (default 1.0)

    Returns:
        QueryResponse: or None if no data could be retrieved.
        # TODO: Should we return the QueryResponse or extract the entities and return a list of those?
    """
    client = BertronClient(base_url=BERTRON_API_URL) # TODO: Reuse BertronClient instance?

    try:
        result = client.get_entities_in_region(latitude, longitude, search_radius_km) # TODO: geocode docs say meters, but seem to interpret as km
        logger.debug(result)
        return result

    except BertronAPIError as e:
        import traceback
        logger.error("API connection error: %s", e)
        # logger.warning(f"Error processing location {latitude}, {longitude}: {e}")
        logger.debug(traceback.format_exc())

    return None

# MAIN SECTION
# Create the FastMCP instance
mcp: FastMCP = FastMCP("bertron_mcp")

# Register all tools
mcp.tool(geosearch)
mcp.tool(health_check)

def main():
    """Main entry point for the application."""
    # Default log level
    log_level = logging.INFO

    if "--verbose" in sys.argv:
        log_level = logging.DEBUG
        sys.argv.remove("--verbose")  # clean args so this parameter doesn't confuse other code

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    if "--version" in sys.argv:
        print(__version__)
        sys.exit(0)
    if "--health" in sys.argv:
        print(health_check())
        sys.exit(0)
    mcp.run()

if __name__ == "__main__":
    main()
