#!/usr/bin/env python

import os
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import time
from datetime import datetime, timedelta
from enum import Enum

import dotenv
import requests
from fastmcp import FastMCP, Context
from warroom_mcp_server.logging_config import get_logger
from warroom_mcp_server.docker_tools import (
    get_container_status,
    get_container_logs,
    restart_container,
    stop_container,
    start_container,
    get_all_containers,
)

dotenv.load_dotenv()
mcp = FastMCP("War Room MCP")

# Cache for metrics list to improve completion performance
_metrics_cache = {"data": None, "timestamp": 0}
_CACHE_TTL = 300  # 5 minutes

# Get logger instance
logger = get_logger()

# Health check tool for Docker containers and monitoring
@mcp.tool(
    description="Health check endpoint for container monitoring and status verification",
    annotations={
        "title": "Health Check",
        "icon": "❤️",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def health_check() -> Dict[str, Any]:
    """Return health status of the MCP server and Prometheus connection.

    Returns:
        Health status including service information, configuration, and connectivity
    """
    try:
        health_status = {
            "status": "healthy",
            "service": "prometheus-mcp-server",
            "version": "1.5.0",
            "timestamp": datetime.utcnow().isoformat(),
            "transport": config.mcp_server_config.mcp_server_transport if config.mcp_server_config else "stdio",
            "configuration": {
                "prometheus_url_configured": bool(config.url),
                "authentication_configured": bool(config.username or config.token),
                "org_id_configured": bool(config.org_id)
            }
        }
        
        # Test Prometheus connectivity if configured
        if config.url:
            try:
                # Quick connectivity test
                make_prometheus_request("query", params={"query": "up", "time": str(int(time.time()))})
                health_status["prometheus_connectivity"] = "healthy"
                health_status["prometheus_url"] = config.url
            except Exception as e:
                health_status["prometheus_connectivity"] = "unhealthy"
                health_status["prometheus_error"] = str(e)
                health_status["status"] = "degraded"
        else:
            health_status["status"] = "unhealthy"
            health_status["error"] = "PROMETHEUS_URL not configured"
        
        logger.info("Health check completed", status=health_status["status"])
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "service": "prometheus-mcp-server",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


class TransportType(str, Enum):
    """Supported MCP server transport types."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"

    @classmethod
    def values(cls) -> list[str]:
        """Get all valid transport values."""
        return [transport.value for transport in cls]

@dataclass
class MCPServerConfig:
    """Global Configuration for MCP."""
    mcp_server_transport: TransportType = None
    mcp_bind_host: str = None
    mcp_bind_port: int = None

    def __post_init__(self):
        """Validate mcp configuration."""
        if not self.mcp_server_transport:
            raise ValueError("MCP SERVER TRANSPORT is required")
        if not self.mcp_bind_host:
            raise ValueError(f"MCP BIND HOST is required")
        if not self.mcp_bind_port:
            raise ValueError(f"MCP BIND PORT is required")

@dataclass
class PrometheusConfig:
    url: str
    url_ssl_verify: bool = True
    disable_prometheus_links: bool = False
    # Optional credentials
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    # Optional Org ID for multi-tenant setups
    org_id: Optional[str] = None
    # Optional Custom MCP Server Configuration
    mcp_server_config: Optional[MCPServerConfig] = None
    # Optional custom headers for Prometheus requests
    custom_headers: Optional[Dict[str, str]] = None

config = PrometheusConfig(
    url=os.environ.get("PROMETHEUS_URL", ""),
    url_ssl_verify=os.environ.get("PROMETHEUS_URL_SSL_VERIFY", "True").lower() in ("true", "1", "yes"),
    disable_prometheus_links=os.environ.get("PROMETHEUS_DISABLE_LINKS", "False").lower() in ("true", "1", "yes"),
    username=os.environ.get("PROMETHEUS_USERNAME", ""),
    password=os.environ.get("PROMETHEUS_PASSWORD", ""),
    token=os.environ.get("PROMETHEUS_TOKEN", ""),
    org_id=os.environ.get("ORG_ID", ""),
    mcp_server_config=MCPServerConfig(
        mcp_server_transport=os.environ.get("PROMETHEUS_MCP_SERVER_TRANSPORT", "stdio").lower(),
        mcp_bind_host=os.environ.get("PROMETHEUS_MCP_BIND_HOST", "127.0.0.1"),
        mcp_bind_port=int(os.environ.get("PROMETHEUS_MCP_BIND_PORT", "8080"))
    ),
    custom_headers=json.loads(os.environ.get("PROMETHEUS_CUSTOM_HEADERS")) if os.environ.get("PROMETHEUS_CUSTOM_HEADERS") else None,
)

def get_prometheus_auth():
    """Get authentication for Prometheus based on provided credentials."""
    if config.token:
        return {"Authorization": f"Bearer {config.token}"}
    elif config.username and config.password:
        return requests.auth.HTTPBasicAuth(config.username, config.password)
    return None

def make_prometheus_request(endpoint, params=None):
    """Make a request to the Prometheus API with proper authentication and headers."""
    if not config.url:
        logger.error("Prometheus configuration missing", error="PROMETHEUS_URL not set")
        raise ValueError("Prometheus configuration is missing. Please set PROMETHEUS_URL environment variable.")
    if not config.url_ssl_verify:
        logger.warning("SSL certificate verification is disabled. This is insecure and should not be used in production environments.", endpoint=endpoint)

    url = f"{config.url.rstrip('/')}/api/v1/{endpoint}"
    url_ssl_verify = config.url_ssl_verify
    auth = get_prometheus_auth()
    headers = {}

    if isinstance(auth, dict):  # Token auth is passed via headers
        headers.update(auth)
        auth = None  # Clear auth for requests.get if it's already in headers
    
    # Add OrgID header if specified
    if config.org_id:
        headers["X-Scope-OrgID"] = config.org_id

    if config.custom_headers:
        headers.update(config.custom_headers)

    try:
        logger.debug("Making Prometheus API request", endpoint=endpoint, url=url, params=params, headers=headers)

        # Make the request with appropriate headers and auth
        response = requests.get(url, params=params, auth=auth, headers=headers, verify=url_ssl_verify)
        
        response.raise_for_status()
        result = response.json()
        
        if result["status"] != "success":
            error_msg = result.get('error', 'Unknown error')
            logger.error("Prometheus API returned error", endpoint=endpoint, error=error_msg, status=result["status"])
            raise ValueError(f"Prometheus API error: {error_msg}")
        
        data_field = result.get("data", {})
        if isinstance(data_field, dict):
            result_type = data_field.get("resultType")
        else:
            result_type = "list"
        logger.debug("Prometheus API request successful", endpoint=endpoint, result_type=result_type)
        return result["data"]
    
    except requests.exceptions.RequestException as e:
        logger.error("HTTP request to Prometheus failed", endpoint=endpoint, url=url, error=str(e), error_type=type(e).__name__)
        raise
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Prometheus response as JSON", endpoint=endpoint, url=url, error=str(e))
        raise ValueError(f"Invalid JSON response from Prometheus: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error during Prometheus request", endpoint=endpoint, url=url, error=str(e), error_type=type(e).__name__)
        raise

def get_cached_metrics() -> List[str]:
    """Get metrics list with caching to improve completion performance.

    This helper function is available for future completion support when
    FastMCP implements the completion capability. For now, it can be used
    internally to optimize repeated metric list requests.
    """
    current_time = time.time()

    # Check if cache is valid
    if _metrics_cache["data"] is not None and (current_time - _metrics_cache["timestamp"]) < _CACHE_TTL:
        logger.debug("Using cached metrics list", cache_age=current_time - _metrics_cache["timestamp"])
        return _metrics_cache["data"]

    # Fetch fresh metrics
    try:
        data = make_prometheus_request("label/__name__/values")
        _metrics_cache["data"] = data
        _metrics_cache["timestamp"] = current_time
        logger.debug("Refreshed metrics cache", metric_count=len(data))
        return data
    except Exception as e:
        logger.error("Failed to fetch metrics for cache", error=str(e))
        # Return cached data if available, even if expired
        return _metrics_cache["data"] if _metrics_cache["data"] is not None else []

# Note: Argument completions will be added when FastMCP supports the completion
# capability. The get_cached_metrics() function above is ready for that integration.

@mcp.tool(
    description="Execute a PromQL instant query against Prometheus",
    annotations={
        "title": "Execute PromQL Query",
        "icon": "📊",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def execute_query(query: str, time: Optional[str] = None) -> Dict[str, Any]:
    """Execute an instant query against Prometheus.

    Args:
        query: PromQL query string
        time: Optional RFC3339 or Unix timestamp (default: current time)

    Returns:
        Query result with type (vector, matrix, scalar, string) and values
    """
    params = {"query": query}
    if time:
        params["time"] = time
    
    logger.info("Executing instant query", query=query, time=time)
    data = make_prometheus_request("query", params=params)

    result = {
        "resultType": data["resultType"],
        "result": data["result"]
    }

    if not config.disable_prometheus_links:
        from urllib.parse import urlencode
        ui_params = {"g0.expr": query, "g0.tab": "0"}
        if time:
            ui_params["g0.moment_input"] = time
        prometheus_ui_link = f"{config.url.rstrip('/')}/graph?{urlencode(ui_params)}"
        result["links"] = [{
            "href": prometheus_ui_link,
            "rel": "prometheus-ui",
            "title": "View in Prometheus UI"
        }]

    logger.info("Instant query completed",
                query=query,
                result_type=data["resultType"],
                result_count=len(data["result"]) if isinstance(data["result"], list) else 1)

    return result

@mcp.tool(
    description="Execute a PromQL range query with start time, end time, and step interval",
    annotations={
        "title": "Execute PromQL Range Query",
        "icon": "📈",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def execute_range_query(query: str, start: str, end: str, step: str, ctx: Context | None = None) -> Dict[str, Any]:
    """Execute a range query against Prometheus.

    Args:
        query: PromQL query string
        start: Start time as RFC3339 or Unix timestamp
        end: End time as RFC3339 or Unix timestamp
        step: Query resolution step width (e.g., '15s', '1m', '1h')

    Returns:
        Range query result with type (usually matrix) and values over time
    """
    params = {
        "query": query,
        "start": start,
        "end": end,
        "step": step
    }

    logger.info("Executing range query", query=query, start=start, end=end, step=step)

    # Report progress if context available
    if ctx:
        await ctx.report_progress(progress=0, total=100, message="Initiating range query...")

    data = make_prometheus_request("query_range", params=params)

    # Report progress
    if ctx:
        await ctx.report_progress(progress=50, total=100, message="Processing query results...")

    result = {
        "resultType": data["resultType"],
        "result": data["result"]
    }

    if not config.disable_prometheus_links:
        from urllib.parse import urlencode
        ui_params = {
            "g0.expr": query,
            "g0.tab": "0",
            "g0.range_input": f"{start} to {end}",
            "g0.step_input": step
        }
        prometheus_ui_link = f"{config.url.rstrip('/')}/graph?{urlencode(ui_params)}"
        result["links"] = [{
            "href": prometheus_ui_link,
            "rel": "prometheus-ui",
            "title": "View in Prometheus UI"
        }]

    # Report completion
    if ctx:
        await ctx.report_progress(progress=100, total=100, message="Range query completed")

    logger.info("Range query completed",
                query=query,
                result_type=data["resultType"],
                result_count=len(data["result"]) if isinstance(data["result"], list) else 1)

    return result

@mcp.tool(
    description="List all available metrics in Prometheus with optional pagination support",
    annotations={
        "title": "List Available Metrics",
        "icon": "📋",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def list_metrics(
    limit: Optional[int] = None,
    offset: int = 0,
    filter_pattern: Optional[str] = None,
    ctx: Context | None = None
) -> Dict[str, Any]:
    """Retrieve a list of all metric names available in Prometheus.

    Args:
        limit: Maximum number of metrics to return (default: all metrics)
        offset: Number of metrics to skip for pagination (default: 0)
        filter_pattern: Optional substring to filter metric names (case-insensitive)

    Returns:
        Dictionary containing:
        - metrics: List of metric names
        - total_count: Total number of metrics (before pagination)
        - returned_count: Number of metrics returned
        - offset: Current offset
        - has_more: Whether more metrics are available
    """
    logger.info("Listing available metrics", limit=limit, offset=offset, filter_pattern=filter_pattern)

    # Report progress if context available
    if ctx:
        await ctx.report_progress(progress=0, total=100, message="Fetching metrics list...")

    data = make_prometheus_request("label/__name__/values")

    if ctx:
        await ctx.report_progress(progress=50, total=100, message=f"Processing {len(data)} metrics...")

    # Apply filter if provided
    if filter_pattern:
        filtered_data = [m for m in data if filter_pattern.lower() in m.lower()]
        logger.debug("Applied filter", original_count=len(data), filtered_count=len(filtered_data), pattern=filter_pattern)
        data = filtered_data

    total_count = len(data)

    # Apply pagination
    start_idx = offset
    end_idx = offset + limit if limit is not None else len(data)
    paginated_data = data[start_idx:end_idx]

    result = {
        "metrics": paginated_data,
        "total_count": total_count,
        "returned_count": len(paginated_data),
        "offset": offset,
        "has_more": end_idx < total_count
    }

    if ctx:
        await ctx.report_progress(progress=100, total=100, message=f"Retrieved {len(paginated_data)} of {total_count} metrics")

    logger.info("Metrics list retrieved",
                total_count=total_count,
                returned_count=len(paginated_data),
                offset=offset,
                has_more=result["has_more"])

    return result

@mcp.tool(
    description="Get metadata for a specific metric",
    annotations={
        "title": "Get Metric Metadata",
        "icon": "ℹ️",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_metric_metadata(metric: str) -> List[Dict[str, Any]]:
    """Get metadata about a specific metric.

    Args:
        metric: The name of the metric to retrieve metadata for

    Returns:
        List of metadata entries for the metric
    """
    logger.info("Retrieving metric metadata", metric=metric)
    endpoint = f"metadata?metric={metric}"
    data = make_prometheus_request(endpoint, params=None)
    if "metadata" in data:
        metadata = data["metadata"]
    elif "data" in data:
        metadata = data["data"]
    else:
        metadata = data
    if isinstance(metadata, dict):
        metadata = [metadata]
    logger.info("Metric metadata retrieved", metric=metric, metadata_count=len(metadata))
    return metadata

@mcp.tool(
    description="Get information about all scrape targets",
    annotations={
        "title": "Get Scrape Targets",
        "icon": "🎯",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_targets() -> Dict[str, List[Dict[str, Any]]]:
    """Get information about all Prometheus scrape targets.

    Returns:
        Dictionary with active and dropped targets information
    """
    logger.info("Retrieving scrape targets information")
    data = make_prometheus_request("targets")
    
    result = {
        "activeTargets": data["activeTargets"],
        "droppedTargets": data["droppedTargets"]
    }
    
    logger.info("Scrape targets retrieved", 
                active_targets=len(data["activeTargets"]), 
                dropped_targets=len(data["droppedTargets"]))
    
    return result

# ==================== WAR ROOM DOCKER TOOLS ====================

@mcp.tool(
    description="Get Docker container status and health information",
    annotations={
        "title": "Get Container Status",
        "icon": "🐳",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def docker_get_container_status(container_name: str) -> Dict[str, Any]:
    """Get the current status of a Docker container.

    Args:
        container_name: Name of the Docker container

    Returns:
        Container status information including health, state, and image
    """
    logger.info("Getting container status", container=container_name)
    result = get_container_status(container_name)
    logger.info("Container status retrieved", container=container_name, status=result.get("status"))
    return result


@mcp.tool(
    description="Recover a failed Docker container by restarting it",
    annotations={
        "title": "Recover Container",
        "icon": "🔧",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
    }
)
async def docker_recover_container(container_name: str, max_retries: int = 3) -> Dict[str, Any]:
    """Recover a failed container by attempting to restart it.

    Args:
        container_name: Name of the Docker container to recover
        max_retries: Maximum number of restart attempts (default: 3)

    Returns:
        Recovery result including success status and actions taken
    """
    logger.info("Starting container recovery", container=container_name, max_retries=max_retries)

    actions = []

    # Check current status
    status = get_container_status(container_name)
    actions.append(f"Checked status: {status.get('status')}")

    if status.get("status") == "error":
        return {
            "success": False,
            "error": status.get("error"),
            "actions": actions,
            "container": container_name
        }

    # Attempt recovery
    for attempt in range(max_retries):
        logger.info("Recovery attempt", container=container_name, attempt=attempt + 1)

        if status.get("status") != "running":
            # Try to start or restart
            if status.get("status") == "exited":
                result = start_container(container_name)
            else:
                result = restart_container(container_name)

            actions.append(f"Attempt {attempt + 1}: {result.get('message', result.get('error'))}")

            if result.get("success"):
                # Verify recovery
                import time
                time.sleep(2)
                final_status = get_container_status(container_name)

                if final_status.get("status") == "running":
                    logger.info("Container recovery successful", container=container_name)
                    return {
                        "success": True,
                        "message": f"Container {container_name} recovered successfully",
                        "actions": actions,
                        "attempts": attempt + 1,
                        "final_status": final_status,
                        "container": container_name
                    }

        # Update status for next attempt
        status = get_container_status(container_name)

    logger.error("Container recovery failed", container=container_name, attempts=max_retries)
    return {
        "success": False,
        "error": f"Failed to recover container after {max_retries} attempts",
        "actions": actions,
        "attempts": max_retries,
        "container": container_name
    }


@mcp.tool(
    description="Get recent logs from a Docker container",
    annotations={
        "title": "Get Container Logs",
        "icon": "📜",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def docker_get_logs(container_name: str, tail: int = 50) -> str:
    """Get recent logs from a Docker container.

    Args:
        container_name: Name of the Docker container
        tail: Number of log lines to retrieve (default: 50)

    Returns:
        Container logs as a string
    """
    logger.info("Retrieving container logs", container=container_name, tail=tail)
    logs = get_container_logs(container_name, tail=tail)
    logger.info("Container logs retrieved", container=container_name, log_length=len(logs))
    return logs


@mcp.tool(
    description="Trigger chaos engineering by stopping a container (for testing)",
    annotations={
        "title": "Trigger Chaos",
        "icon": "💀",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
    }
)
async def docker_trigger_chaos(container_name: str) -> Dict[str, Any]:
    """Trigger a chaos engineering scenario by stopping a container.

    WARNING: This will stop the specified container!

    Args:
        container_name: Name of the Docker container to stop

    Returns:
        Result of the chaos trigger operation
    """
    logger.warning("CHAOS TRIGGERED", container=container_name)
    result = stop_container(container_name)
    logger.warning("Chaos operation completed", container=container_name, success=result.get("success"))
    return result


@mcp.tool(
    description="List all Docker containers and their status",
    annotations={
        "title": "List All Containers",
        "icon": "📦",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def docker_list_containers() -> List[Dict[str, Any]]:
    """List all Docker containers with their current status.

    Returns:
        List of containers with their status information
    """
    logger.info("Listing all containers")
    containers = get_all_containers()
    logger.info("Containers listed", count=len(containers))
    return containers


if __name__ == "__main__":
    logger.info("Starting War Room MCP Server", mode="direct")
    mcp.run()
