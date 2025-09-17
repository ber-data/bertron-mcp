################################################################################
# bertron_mcp/main.py
# This module provides a FastMCP wrapper for the BERtron API.
################################################################################

import logging
import sys
from importlib import metadata
from typing import Any

# Suppress SSL warnings for development/testing with self-signed certificates
import urllib3
from bertron_client import BertronAPIError, BertronClient, Entity, QueryResponse
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

# API Response Limits - prevent overwhelming responses and protect system resources
DEFAULT_LIMIT = 100        # Default number of results returned
MAX_LIMIT = 1000          # Maximum allowed results per query
MAX_SKIP = 50000          # Maximum pagination offset to prevent deep scanning

def health_check() -> dict[str, bool] | None:
    """
    Check if the BERtron API is online and accessible.

    Verifies both the web server and database connectivity to ensure
    the genomic data service is fully operational.

    Returns:
        Status information showing if web server and database are healthy
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
    Find genomic and environmental samples near a geographic location.

    Search for biological samples, field sites, and environmental data
    collected within a specified distance of any point on Earth.
    Useful for finding relevant research data for environmental studies.

    Args:
        latitude: Geographic latitude (-90.0 to 90.0)
        longitude: Geographic longitude (-180.0 to 180.0)
        search_radius_km: Search radius in kilometers (default: 1.0)

    Returns:
        Collection of nearby samples and research sites with metadata
    """
    # TODO: Reuse BertronClient instance?
    client = BertronClient(base_url=BERTRON_API_URL)
    # Disable SSL verification for self-signed certificates in testing
    client.session.verify = False

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

def bbox_search(
    southwest_lat: float,
    southwest_lng: float,
    northeast_lat: float,
    northeast_lng: float
) -> QueryResponse | None:
    """
    Find all genomic samples within a rectangular geographic region.

    Search for biological samples and environmental data within a defined
    rectangular area on Earth. Perfect for regional studies covering
    states, ecosystems, or research transects.

    Args:
        southwest_lat: Southwest corner latitude (-90.0 to 90.0)
        southwest_lng: Southwest corner longitude (-180.0 to 180.0)
        northeast_lat: Northeast corner latitude (-90.0 to 90.0)
        northeast_lng: Northeast corner longitude (-180.0 to 180.0)

    Returns:
        All samples and research sites within the specified rectangular area
    """
    client = BertronClient(base_url=BERTRON_API_URL)
    client.session.verify = False

    try:
        result = client.find_entities_in_bounding_box(
            southwest_lat, southwest_lng, northeast_lat, northeast_lng
        )
        logger.debug(result)
        return result

    except BertronAPIError as e:
        import traceback
        logger.error("API connection error: %s", e)
        logger.debug(traceback.format_exc())

    return None

def entity_lookup(entity_id: str) -> Entity | None:
    """
    Get detailed information about a specific biological sample or dataset.

    Look up comprehensive metadata for any sample, including collection
    details, environmental conditions, processing methods, and associated
    research projects.

    Args:
        entity_id: Sample or dataset identifier (e.g., "nmdc:bsm-12-abc123")

    Returns:
        Complete sample metadata including collection and analysis details
    """
    client = BertronClient(base_url=BERTRON_API_URL)
    client.session.verify = False

    try:
        result = client.get_entity_by_id(entity_id)
        logger.debug(result)
        return result

    except BertronAPIError as e:
        import traceback
        logger.error("API connection error: %s", e)
        logger.debug(traceback.format_exc())

    return None

def advanced_query(
    filter_dict: dict[str, Any] | None = None,
    projection: dict[str, Any] | None = None,
    skip: int = 0,
    limit: int = DEFAULT_LIMIT,
    sort: dict[str, int] | None = None
) -> QueryResponse | None:
    """
    Perform complex searches with custom filters and sorting options.

    Create sophisticated searches combining multiple criteria such as
    sample type, date ranges, environmental conditions, or research
    projects. Includes pagination and custom result ordering.

    Args:
        filter_dict: Search criteria (e.g., {"entity_type": "sample"})
        projection: Specific fields to return (e.g., {"name": 1, "coordinates": 1})
        skip: Number of results to skip for pagination (default: 0)
        limit: Maximum results to return (default: 100, max: 1000)
        sort: Sort order (e.g., {"name": 1} for A-Z, {"name": -1} for Z-A)

    Returns:
        Search results matching the specified criteria
    """
    # Track original values to report constraints
    original_limit = limit
    constraints_applied = {}

    # Enforce maximum limits to prevent overwhelming responses
    if limit is None or limit > MAX_LIMIT:
        limit = MAX_LIMIT
        logger.warning(f"Limit constrained to maximum of {MAX_LIMIT}")
        constraints_applied["limit"] = {
            "requested": original_limit,
            "actual": limit,
            "reason": f"Exceeded maximum limit of {MAX_LIMIT}"
        }

    if skip > MAX_SKIP:
        logger.error(f"Skip value {skip} exceeds maximum of {MAX_SKIP}")
        return None

    # Require some filter to prevent accidental full database dumps
    if not filter_dict:
        logger.warning(
            "Advanced query requires filter criteria to prevent full database access"
        )
        filter_dict = {"entity_type": {"$exists": True}}  # Basic safety filter
        constraints_applied["filter"] = {
            "requested": "none",
            "actual": filter_dict,
            "reason": "Safety filter applied to prevent full database access"
        }

    client = BertronClient(base_url=BERTRON_API_URL)
    client.session.verify = False

    try:
        result = client.find_entities(
            filter_dict=filter_dict,
            projection=projection,
            skip=skip,
            limit=limit,
            sort=sort
        )

        # Add constraint information to metadata if any were applied
        if result and constraints_applied:
            if not result.metadata:
                result.metadata = {}
            result.metadata["constraints_applied"] = constraints_applied

        logger.debug(result)
        return result

    except BertronAPIError as e:
        import traceback
        logger.error("API connection error: %s", e)
        logger.debug(traceback.format_exc())

    return None

def search_by_source(source: str, limit: int = DEFAULT_LIMIT) -> QueryResponse | None:
    """
    Find samples and datasets from a specific research facility.

    Search for data from major U.S. Department of Energy biological
    and environmental research facilities. Each facility specializes
    in different types of research and data collection methods.

    Args:
        source: Research facility name (EMSL, ESS-DIVE, JGI, NMDC, MONET)
        limit: Maximum number of results to return (default: 100, max: 1000)

    Returns:
        Samples and datasets from the specified research facility
    """
    # Enforce maximum limit to prevent overwhelming responses
    original_limit = limit
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
        logger.warning(f"Limit constrained to maximum of {MAX_LIMIT}")

    client = BertronClient(base_url=BERTRON_API_URL)
    client.session.verify = False

    try:
        # Use find_entities with explicit limit instead of find_entities_by_source
        result = client.find_entities(
            filter_dict={"ber_data_source": source},
            limit=limit
        )

        # Add constraint information to metadata
        if result and original_limit != limit:
            if not result.metadata:
                result.metadata = {}
            result.metadata["constraints_applied"] = {
                "requested_limit": original_limit,
                "actual_limit": limit,
                "reason": f"Exceeded maximum limit of {MAX_LIMIT}"
            }

        logger.debug(result)
        return result

    except BertronAPIError as e:
        import traceback
        logger.error("API connection error: %s", e)
        logger.debug(traceback.format_exc())

    return None

def search_by_type(
    entity_type: str, limit: int = DEFAULT_LIMIT
) -> QueryResponse | None:
    """
    Find all data of a specific research type (samples, sequences, etc.).

    Search by the kind of biological or environmental data you need.
    Choose from physical samples, genetic sequences, taxonomic data,
    or processed datasets depending on your research goals.

    Args:
        entity_type: Type of data (sample, sequence, biodata, taxon, jgi_biosample)
        limit: Maximum number of results to return (default: 100, max: 1000)

    Returns:
        Data entries matching the specified research data type
    """
    # Enforce maximum limit to prevent overwhelming responses
    original_limit = limit
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
        logger.warning(f"Limit constrained to maximum of {MAX_LIMIT}")

    client = BertronClient(base_url=BERTRON_API_URL)
    client.session.verify = False

    try:
        # Use find_entities with explicit limit instead of find_entities_by_entity_type
        result = client.find_entities(
            filter_dict={"entity_type": entity_type},
            limit=limit
        )

        # Add constraint information to metadata
        if result and original_limit != limit:
            if not result.metadata:
                result.metadata = {}
            result.metadata["constraints_applied"] = {
                "requested_limit": original_limit,
                "actual_limit": limit,
                "reason": f"Exceeded maximum limit of {MAX_LIMIT}"
            }

        logger.debug(result)
        return result

    except BertronAPIError as e:
        import traceback
        logger.error("API connection error: %s", e)
        logger.debug(traceback.format_exc())

    return None

def search_by_name(
    name_pattern: str, case_sensitive: bool = False, limit: int = DEFAULT_LIMIT
) -> QueryResponse:
    """
    Search for samples and datasets by name or description.

    Find research data by searching through sample names, project titles,
    and descriptions. Supports pattern matching to find related studies
    or samples from similar environments.

    Args:
        name_pattern: Text to search for in names and descriptions
        case_sensitive: Whether to match exact case (default: False)
        limit: Maximum number of results to return (default: 100, max: 1000)

    Returns:
        Samples and datasets with names or descriptions matching the pattern
    """
    import re

    # Validate regex pattern first
    try:
        re.compile(name_pattern)
    except re.error as e:
        logger.warning(f"Invalid regex pattern '{name_pattern}': {e}")
        # Return empty QueryResponse for invalid patterns
        empty_result = QueryResponse(entities=[], count=0)
        empty_result.metadata = {
            "constraints_applied": {
                "pattern": name_pattern,
                "reason": f"Invalid regex pattern: {e}"
            }
        }
        return empty_result

    # Enforce maximum limit to prevent overwhelming responses
    original_limit = limit
    constraints_applied = {}
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
        logger.warning(f"Limit constrained to maximum of {MAX_LIMIT}")
        constraints_applied["limit"] = {
            "requested": original_limit,
            "actual": limit,
            "reason": f"Exceeded maximum limit of {MAX_LIMIT}"
        }

    client = BertronClient(base_url=BERTRON_API_URL)
    client.session.verify = False

    try:
        # Use find_entities with regex filter and explicit limit
        regex_filter = {"name": {"$regex": name_pattern}}
        if not case_sensitive:
            regex_filter["name"]["$options"] = "i"

        result = client.find_entities(
            filter_dict=regex_filter,
            limit=limit
        )

        # Add constraint information to metadata if any were applied
        if result and constraints_applied:
            if not result.metadata:
                result.metadata = {}
            result.metadata["constraints_applied"] = constraints_applied

        logger.debug(result)
        return result

    except BertronAPIError as e:
        import traceback
        logger.error("API connection error: %s", e)
        logger.debug(traceback.format_exc())

        # Return empty QueryResponse instead of None
        empty_result = QueryResponse(entities=[], count=0)
        empty_result.metadata = {
            "error": f"API connection error: {e}",
            "constraints_applied": constraints_applied if constraints_applied else {}
        }
        return empty_result

# MAIN SECTION
# Create the FastMCP instance
mcp: FastMCP = FastMCP("bertron_mcp")

# Register all tools with enhanced metadata and structured descriptions
mcp.tool(
    geosearch,
    title="Geographic Sample Search",
    description=(
        "Find genomic and environmental samples near any location on Earth "
        "using latitude/longitude coordinates"
    ),
    tags={"geospatial", "environmental", "samples", "basic"},
    annotations={
        "use_cases": [
            "Find samples near research sites",
            "Environmental impact studies",
            "Regional biodiversity analysis"
        ],
        "examples": [
            "Samples within 50km of Orlando, FL",
            "Marine samples near coastlines"
        ],
        "complexity": "beginner"
    },
    meta={"category": "search", "requires_coordinates": True}
)

mcp.tool(
    health_check,
    title="API Health Status",
    description=(
        "Verify that the BERtron API and database are online and "
        "responding correctly"
    ),
    tags={"system", "health", "diagnostics", "monitoring"},
    annotations={
        "use_cases": [
            "Troubleshoot connection issues",
            "Monitor system status",
            "Verify API availability"
        ],
        "examples": ["Check if database is accessible", "Verify web server status"],
        "complexity": "beginner"
    },
    meta={"category": "system", "requires_coordinates": False}
)

mcp.tool(
    bbox_search,
    title="Regional Bounding Box Search",
    description=(
        "Find all samples within a rectangular geographic region "
        "defined by corner coordinates"
    ),
    tags={"geospatial", "environmental", "regional", "basic"},
    annotations={
        "use_cases": [
            "State or province-wide studies",
            "Ecosystem boundary analysis",
            "Research transects"
        ],
        "examples": [
            "All samples in Yellowstone region",
            "Great Lakes watershed samples"
        ],
        "complexity": "beginner"
    },
    meta={"category": "search", "requires_coordinates": True}
)

mcp.tool(
    entity_lookup,
    title="Sample Details Lookup",
    description=(
        "Get comprehensive metadata for a specific biological sample "
        "or dataset using its unique identifier"
    ),
    tags={"lookup", "metadata", "details", "basic"},
    annotations={
        "use_cases": [
            "Get full sample details",
            "Verify sample information",
            "Access collection metadata"
        ],
        "examples": [
            "Look up sample nmdc:bsm-12-abc123",
            "Get processing details for a dataset"
        ],
        "complexity": "beginner"
    },
    meta={"category": "lookup", "requires_coordinates": False}
)

mcp.tool(
    advanced_query,
    title="Advanced Database Query",
    description=(
        "Execute sophisticated searches with custom filters, field selection, "
        "pagination, and sorting options"
    ),
    tags={"query", "advanced", "filtering", "complex"},
    annotations={
        "use_cases": [
            "Complex multi-criteria searches",
            "Custom data analysis",
            "Bulk data retrieval with specific fields"
        ],
        "examples": [
            "Samples from 2023 with pH > 7",
            "Sequence data with specific gene markers"
        ],
        "complexity": "advanced",
        "warning": (
            "Requires knowledge of database field names and MongoDB query syntax"
        )
    },
    meta={
        "category": "search",
        "requires_coordinates": False,
        "technical_skill": "intermediate"
    }
)

mcp.tool(
    search_by_source,
    title="Search by Research Facility",
    description=(
        "Find samples and datasets from specific DOE research facilities "
        "(EMSL, ESS-DIVE, JGI, NMDC, MONET)"
    ),
    tags={"source", "facility", "institution", "basic"},
    annotations={
        "use_cases": [
            "Compare data across facilities",
            "Find facility-specific datasets",
            "Institutional research analysis"
        ],
        "examples": [
            "All NMDC microbiome samples (up to 1000 results)",
            "JGI genomic sequences with limit=500",
            "EMSL proteomics data"
        ],
        "complexity": "beginner"
    },
    meta={"category": "search", "requires_coordinates": False}
)

mcp.tool(
    search_by_type,
    title="Search by Data Type",
    description=(
        "Find specific types of biological or environmental data "
        "(samples, sequences, biodata, taxa)"
    ),
    tags={"type", "category", "filtering", "basic"},
    annotations={
        "use_cases": [
            "Find all samples vs sequences",
            "Get taxonomic data only",
            "Filter by data type"
        ],
        "examples": [
            "All biological samples",
            "Genomic sequence data",
            "Taxonomic classifications"
        ],
        "complexity": "beginner"
    },
    meta={"category": "search", "requires_coordinates": False}
)

mcp.tool(
    search_by_name,
    title="Text Search by Name/Description",
    description=(
        "Search through sample names, project titles, and descriptions "
        "using text patterns and keywords"
    ),
    tags={"text", "name", "description", "pattern", "basic"},
    annotations={
        "use_cases": [
            "Find samples by project name",
            "Search descriptions for keywords",
            "Pattern-based discovery"
        ],
        "examples": [
            "Samples with 'forest' in description",
            "Projects containing 'soil microbiome'"
        ],
        "complexity": "beginner"
    },
    meta={"category": "search", "requires_coordinates": False}
)

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
