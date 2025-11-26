import asyncio
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_COMMAND = "npx"
MCP_ARGS = [
    "-y",
    "@modelcontextprotocol/server-postgres",
    "postgresql://root:3321@svc.sel3.cloudtype.app:30536/root"
]


async def query_postgres(sql: str):
    """PostgreSQL MCP 서버의 query 툴 실행 함수"""
    
    server_params = StdioServerParameters(
        command=MCP_COMMAND,
        args=MCP_ARGS,
        env=None  # 필요시 환경변수 추가
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 서버 초기화
                logger.info("서버 초기화 중...")
                init_result = await session.initialize()
                logger.info(f"초기화 완료: {init_result}")

                # 사용 가능한 도구 목록 확인
                logger.info("도구 목록 조회 중...")
                tools = await session.list_tools()
                logger.info(f"사용 가능한 도구: {tools}")

                # query 도구 실행
                logger.info(f"SQL 실행 중: {sql}")
                result = await session.call_tool(
                    name="query",  # 'tool' 대신 'name' 사용
                    arguments={"sql": sql}
                )

                return result
                
    except Exception as e:
        logger.error(f"❌ 오류 발생: {type(e).__name__}: {e}")
        raise


async def main():
    print("🔗 PostgreSQL MCP 서버에 연결 중...\n")

    try:
        # 조회할 SQL
        sql = "SELECT * FROM users LIMIT 5;"

        res = await query_postgres(sql)

        print("\n✅ 쿼리 결과:")
        print(res)
        
    except Exception as e:
        print(f"\n❌ 실행 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())