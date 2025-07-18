################################################################################
# bertron_mcp/main.py
# This module provides a FastMCP wrapper for the BERtron API.
################################################################################

import logging
import sys
from importlib import metadata

from fastmcp import FastMCP
# TODO: Is this available as a python package? Check how Jupyter notebook imports the API client.
# from bertron_client import BertronClient, BertronAPIError, QueryResponse
# from schema.datamodel.bertron_schema_pydantic import Entity, BERSourceType, EntityType
#
# # Import data analysis and visualization libraries
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
# from typing import List, Dict, Any

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

def geosearch(
    latitude: float,
    longitude: float,
    search_radius_meters: int = 1000
) -> dict | None:
    """
    Search BERtron catalogue for data within a specified distance of a given latitude and longitude.

    Args:
        latitude: latitude of the point (-90.0 to 90.0)
        longitude: longitude of the point (-180.0 to 180.0)
        search_radius_meters: the station search radius in m

    Returns:
        dict:  or None if no data could be retrieved.
    """

    try:

        results = None # TODO: placeholder for query via bertron_client.py

        logger.debug(f"Results: {results}")

        return results # TODO: determine return type
    except Exception as e:
        import traceback
        logger.warning(f"Error processing location {latitude}, {longitude}: {e}")
        logger.debug(traceback.format_exc())
        return None


# MAIN SECTION
# Create the FastMCP instance
mcp: FastMCP = FastMCP("bertron_mcp")

# Register all tools
mcp.tool(geosearch)
# mcp.tool(get_record)

def main():
    """Main entry point for the application."""
    if "--version" in sys.argv:
        print(__version__)
        sys.exit(0)
    mcp.run()

if __name__ == "__main__":
    main()
