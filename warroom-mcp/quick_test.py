#!/usr/bin/env python
"""Quick test script for War Room MCP Server Docker tools"""

import asyncio
from warroom_mcp_server.docker_tools import (
    get_all_containers,
    get_container_status,
    get_container_logs,
    restart_container,
    start_container,
)


async def main():
    print("=" * 60)
    print("🧪 War Room MCP Server - Docker Tools Quick Test")
    print("=" * 60)

    # Test 1: List all containers
    print("\n[Test 1] 📦 List All Containers")
    print("-" * 60)
    containers = get_all_containers()

    if containers and 'error' not in containers[0]:
        for c in containers:
            status_icon = "🟢" if c['status'] == 'running' else "🔴"
            print(f"{status_icon} {c['name']:20} {c['status']:10} {c['image']}")
    else:
        print("❌ Error listing containers")

    # Test 2: Get specific container status
    print("\n[Test 2] 🔍 Get Container Status (test-nginx)")
    print("-" * 60)
    status = get_container_status("test-nginx")
    print(f"Container: {status.get('container')}")
    print(f"Status:    {status.get('status')}")
    print(f"Health:    {status.get('health')}")
    print(f"Image:     {status.get('image')}")

    # Test 3: Get container logs
    print("\n[Test 3] 📜 Get Container Logs (test-nginx, last 5 lines)")
    print("-" * 60)
    logs = get_container_logs("test-nginx", tail=5)
    log_lines = logs.split('\n')[:5]
    for line in log_lines:
        if line.strip():
            print(f"  {line}")

    # Test 4: Test recovery on failed container
    print("\n[Test 4] 🔧 Test Auto-Recovery (test-failing)")
    print("-" * 60)
    print("Attempting to recover 'test-failing' container...")

    # Check status first
    status = get_container_status("test-failing")
    print(f"Initial status: {status.get('status')}")

    # Try to start the container
    if status.get('status') == 'exited':
        result = start_container("test-failing")
        print(f"Start result: {result.get('message') if result.get('success') else result.get('error')}")
    else:
        result = restart_container("test-failing")
        print(f"Restart result: {result.get('message') if result.get('success') else result.get('error')}")

    # Summary
    print("\n" + "=" * 60)
    print("✅ All Tests Completed!")
    print("=" * 60)
    print("\n💡 Next Steps:")
    print("  1. Test chaos engineering: docker_trigger_chaos()")
    print("  2. Check TESTING_GUIDE.md for more scenarios")
    print("  3. Use MCP Inspector for interactive testing")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
