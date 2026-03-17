import asyncio
import sys
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_sre_agent():
    server_script = os.path.join(os.path.dirname(__file__), "server.py")
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=os.environ.copy()
    )

    print("--- [AI-SRE-Squad] Docker 에이전트 가동 ---")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ MCP 서버와 연결되었습니다.")

                tools = await session.list_tools()
                print(f"🛠️  활성화된 도구: {[t.name for t in tools.tools]}")

                # 작업 수행 함수 (중복 제거용)
                async def run_test(tool_name, args):
                    print(f"\n[작업] {tool_name} 실행 중...")
                    res = await session.call_tool(tool_name, arguments=args)
                    if res.content:
                        print(f"결과:\n{res.content[0].text}")
                    else:
                        print(f"⚠️ 결과가 비어있습니다: {res}")

                # 테스트 실행
                await run_test("docker_system_info", {})
                await run_test("list_containers", {"all": True})
                await run_test("list_images", {})

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(run_sre_agent())