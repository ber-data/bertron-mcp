################################################################################
# bertron_mcp/main.py
# This module provides a FastMCP wrapper for the BERtron API.
################################################################################

import logging
import sys
from importlib import metadata

# Suppress SSL warnings for development/testing with self-signed certificates
import urllib3
from bertron_client import BertronAPIError, BertronClient, QueryResponse
from fastmcp import FastMCP

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def health_check() -> dict[str, bool] | None:
    """
    Check BERtron API health status.

    Returns:
        Optional[dict[str, bool]]: Health status with 'web_server' and 'database'.
    """
    client = BertronClient(base_url=BERTRON_API_URL)
    # Disable SSL verification for self-signed certificates in testing
    client.session.verify = False

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
    Search BERtron catalogue for data within distance of given coordinates.

    Args:
        latitude: latitude of the point (-90.0 to 90.0)
        longitude: longitude of the point (-180.0 to 180.0)
        search_radius_km: the station search radius in m (default 1.0)

    Returns:
        QueryResponse: or None if no data could be retrieved.
        # TODO: Return QueryResponse or extract entities?
    """
    client = BertronClient(base_url=BERTRON_API_URL)
    # Disable SSL verification for self-signed certificates in testing
    client.session.verify = False # TODO: Reuse BertronClient instance?

    try:
        # TODO: geocode docs say meters, but seem to interpret as km
        result = client.get_entities_in_region(latitude, longitude, search_radius_km)
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
        sys.argv.remove("--verbose")  # clean args for other code

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
