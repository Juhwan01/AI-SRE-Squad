@echo off
REM War Room 2.0 - 테스트 이미지 빌드 (Windows)

echo ======================================
echo War Room 2.0 - 테스트 이미지 빌드
echo ======================================
echo.

echo [1/3] 테스트 MCP 베이스 이미지 빌드...
docker build -t mcp/test-base:latest -f docker/Dockerfile.test-mcp .
if errorlevel 1 (
    echo 빌드 실패!
    exit /b 1
)

echo.
echo [2/3] Docker MCP 이미지 태그...
docker tag mcp/test-base:latest mcp/server-docker:latest
docker tag mcp/test-base:latest mcp/n8n-mcp:latest

echo.
echo [3/3] Postgres MCP 이미지 태그...
docker tag mcp/test-base:latest mcp/server-postgres:latest
docker tag mcp/test-base:latest mcp/mcp-postgres:latest

echo.
echo ======================================
echo ✅ 테스트 이미지 빌드 완료!
echo ======================================
echo.

echo 생성된 이미지:
docker images mcp/*

echo.
echo 이제 War Room을 다시 테스트할 수 있습니다:
echo   uv run python test_quick.py full
