"""Docker management tools for War Room MCP Server."""

import docker
from docker.errors import DockerException, NotFound
from typing import Dict, List, Any


class DockerManager:
    """Manages Docker operations for the War Room system."""

    def __init__(self):
        """Initialize Docker client."""
        try:
            self.client = docker.from_env()
            self.available = True
        except DockerException as e:
            print(f"Warning: Docker client initialization failed: {e}")
            self.client = None
            self.available = False

    def is_available(self) -> bool:
        """Check if Docker is available."""
        return self.available and self.client is not None


# Global instance
_docker_manager = DockerManager()


def get_container_status(container_name: str) -> Dict[str, Any]:
    """
    Get the current status of a Docker container.

    Args:
        container_name: Name of the container

    Returns:
        Dictionary with status information
    """
    if not _docker_manager.is_available():
        return {
            "status": "error",
            "error": "Docker not available",
            "container": container_name
        }

    try:
        container = _docker_manager.client.containers.get(container_name)
        return {
            "container": container_name,
            "status": container.status,
            "health": container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown"),
            "started_at": container.attrs.get("State", {}).get("StartedAt", ""),
            "image": container.image.tags[0] if container.image.tags else "unknown",
        }
    except NotFound:
        return {
            "status": "not_found",
            "error": f"Container {container_name} not found",
            "container": container_name
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "container": container_name
        }


def get_container_logs(container_name: str, tail: int = 50) -> str:
    """
    Get recent logs from a container.

    Args:
        container_name: Name of the container
        tail: Number of lines to retrieve

    Returns:
        Log output as string
    """
    if not _docker_manager.is_available():
        return "Error: Docker not available"

    try:
        container = _docker_manager.client.containers.get(container_name)
        logs = container.logs(tail=tail, timestamps=True).decode('utf-8', errors='ignore')
        return logs
    except NotFound:
        return f"Error: Container {container_name} not found"
    except Exception as e:
        return f"Error: {str(e)}"


def restart_container(container_name: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Restart a Docker container.

    Args:
        container_name: Name of the container
        timeout: Timeout in seconds

    Returns:
        Result dictionary
    """
    if not _docker_manager.is_available():
        return {"success": False, "error": "Docker not available"}

    try:
        container = _docker_manager.client.containers.get(container_name)
        container.restart(timeout=timeout)
        return {
            "success": True,
            "message": f"Container {container_name} restarted successfully",
            "container": container_name
        }
    except NotFound:
        return {
            "success": False,
            "error": f"Container {container_name} not found",
            "container": container_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "container": container_name
        }


def stop_container(container_name: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Stop a Docker container.

    Args:
        container_name: Name of the container
        timeout: Timeout in seconds

    Returns:
        Result dictionary
    """
    if not _docker_manager.is_available():
        return {"success": False, "error": "Docker not available"}

    try:
        container = _docker_manager.client.containers.get(container_name)
        container.stop(timeout=timeout)
        return {
            "success": True,
            "message": f"Container {container_name} stopped successfully",
            "container": container_name
        }
    except NotFound:
        return {
            "success": False,
            "error": f"Container {container_name} not found",
            "container": container_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "container": container_name
        }


def start_container(container_name: str) -> Dict[str, Any]:
    """
    Start a Docker container.

    Args:
        container_name: Name of the container

    Returns:
        Result dictionary
    """
    if not _docker_manager.is_available():
        return {"success": False, "error": "Docker not available"}

    try:
        container = _docker_manager.client.containers.get(container_name)
        container.start()
        return {
            "success": True,
            "message": f"Container {container_name} started successfully",
            "container": container_name
        }
    except NotFound:
        return {
            "success": False,
            "error": f"Container {container_name} not found",
            "container": container_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "container": container_name
        }


def get_all_containers() -> List[Dict[str, Any]]:
    """
    Get status of all running containers.

    Returns:
        List of container status dictionaries
    """
    if not _docker_manager.is_available():
        return [{"error": "Docker not available"}]

    try:
        containers = _docker_manager.client.containers.list(all=True)
        return [{
            "name": c.name,
            "status": c.status,
            "image": c.image.tags[0] if c.image.tags else "unknown",
            "short_id": c.short_id,
        } for c in containers]
    except Exception as e:
        return [{"error": str(e)}]
