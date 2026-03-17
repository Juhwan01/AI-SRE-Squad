import docker
import json
from mcp.server.fastmcp import FastMCP

# MCP 서버 초기화
mcp = FastMCP("Docker-Master-SRE")
client = docker.from_env()

# --- [SECTION 1] 컨테이너 관리 (Containers) ---
@mcp.tool()
def list_containers(all: bool = False):
    """실행 중이거나 모든 컨테이너 목록을 조회합니다."""
    try:
        containers = client.containers.list(all=all)
        res = [{"name": c.name, "id": c.short_id, "status": c.status, "image": str(c.image.tags)} for c in containers]
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def container_ops(action: str, name_or_id: str):
    """컨테이너 제어: 'start', 'stop', 'restart', 'pause', 'unpause', 'remove'"""
    try:
        c = client.containers.get(name_or_id)
        getattr(c, action)()
        return f"Successfully performed '{action}' on {name_or_id}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def run_container(image: str, name: str = None, command: str = None, detach: bool = True):
    """새로운 컨테이너를 생성하고 실행합니다 (docker run)."""
    try:
        container = client.containers.run(image, command=command, name=name, detach=detach)
        return f"Started container {container.name} ({container.short_id})"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_logs(name_or_id: str, tail: int = 50):
    """컨테이너의 로그를 확인합니다 (SRE 장애 분석용)."""
    try:
        c = client.containers.get(name_or_id)
        return c.logs(tail=tail).decode('utf-8')
    except Exception as e:
        return f"Error: {str(e)}"

# --- [SECTION 2] 이미지 관리 (Images) ---
@mcp.tool()
def image_ops(action: str, tag: str):
    """이미지 관리: 'pull' (다운로드), 'remove' (삭제)"""
    try:
        if action == 'pull':
            img = client.images.pull(tag)
            return f"Pulled image: {img.tags}"
        elif action == 'remove':
            client.images.remove(image=tag, force=True)
            return f"Removed image: {tag}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def list_images():
    """로컬에 저장된 모든 이미지 목록을 확인합니다."""
    try:
        images = client.images.list()
        res = [{"tags": img.tags, "id": img.short_id, "size_mb": round(img.attrs['Size']/(1024*1024), 2)} for img in images]
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"

# --- [SECTION 3] 네트워크 & 볼륨 (Network & Volume) ---
@mcp.tool()
def inspect_infra():
    """네트워크와 볼륨의 전체 목록을 조회합니다."""
    try:
        networks = [{"name": n.name, "id": n.short_id, "driver": n.attrs['Driver']} for n in client.networks.list()]
        volumes = [{"name": v.name, "driver": v.attrs['Driver']} for v in client.volumes.list()]
        res = {"networks": networks, "volumes": volumes}
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"

# --- [SECTION 4] 시스템 및 리소스 모니터링 (System & Stats) ---
@mcp.tool()
def docker_system_info():
    """도커 엔진의 전체 시스템 정보를 확인합니다 (docker info)."""
    try:
        info = client.info()
        res = {
            "Containers": info.get('Containers'),
            "Images": info.get('Images'),
            "OperatingSystem": info.get('OperatingSystem'),
            "NCPU": info.get('NCPU'),
            "MemTotal": round(info.get('MemTotal')/(1024*1024*1024), 2)
        }
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_resource_stats(name_or_id: str):
    """컨테이너의 CPU/메모리 실시간 사용량을 측정합니다."""
    try:
        c = client.containers.get(name_or_id)
        stats = c.stats(stream=False)
        res = {
            "container": name_or_id,
            "cpu_usage_raw": stats['cpu_stats']['cpu_usage']['total_usage'],
            "mem_usage_mb": round(stats['memory_stats']['usage']/(1024*1024), 2),
            "mem_limit_mb": round(stats['memory_stats']['limit']/(1024*1024), 2)
        }
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def cleanup_system():
    """안 쓰는 컨테이너, 네트워크, 이미지를 모두 청소합니다 (docker prune)."""
    try:
        c_p = client.containers.prune()
        i_p = client.images.prune()
        res = {
            "reclaimed_bytes": c_p.get('SpaceReclaimed', 0) + i_p.get('SpaceReclaimed', 0),
            "status": "Cleanup successful"
        }
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio')