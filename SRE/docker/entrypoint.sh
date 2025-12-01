#!/bin/bash
# MCP Server Entrypoint Script

set -e

# MCP_PACKAGE 환경 변수가 설정되어 있으면 해당 패키지 실행
if [ -n "$MCP_PACKAGE" ]; then
    echo "Starting MCP Server: $MCP_PACKAGE"

    # NPX로 MCP 서버 실행 (설치 없이 바로 실행)
    exec npx -y "$MCP_PACKAGE"
else
    # 기본 명령 실행
    exec "$@"
fi
