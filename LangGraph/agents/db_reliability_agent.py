import asyncio
import os
import sys
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

from state import GraphState

load_dotenv()

# =========================
# LLM
# =========================
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)


# =========================
# 시스템 프롬프트
# =========================
SYSTEM_PROMPT = """
너는 DB 로그 분석 전문가다.

주어진 로그를 분석하고, 필요하면 PostgreSQL 툴로 DB에 직접 쿼리해서 상태를 확인해라.

반드시 아래 형식으로만 답변해라.

[문제 원인 정리]
- ...

[해결 방법 정리]
- ...

규칙:
1. DB 로그가 없으면 "로그가 제공되지 않았습니다"라고 작성
2. 추측하지 말고 로그 및 실제 DB 조회 기반으로 분석
3. 해결 방법은 실무 기준으로 작성
"""


# =========================
# 실행 함수 (MCP 연결 포함)
# =========================
async def analyze_db_log(log_text: str) -> str:
    if not log_text.strip():
        return """
[문제 원인 정리]
- 로그가 제공되지 않았습니다

[해결 방법 정리]
- DB 로그를 입력해주세요
"""

    command = "npx.cmd" if sys.platform == "win32" else "npx"
    db_url = os.getenv("DATABASE_URL", "postgresql://root:3321@svc.sel3.cloudtype.app:30536/root")

    server_params = StdioServerParameters(
        command=command,
        args=["-y", "@modelcontextprotocol/server-postgres", db_url],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(llm, tools)
            result = await agent.ainvoke({
                "messages": [
                    ("system", SYSTEM_PROMPT),
                    ("user", f"다음 DB 로그 분석:\n{log_text}")
                ]
            })

    return result["messages"][-1].content


# =========================
# GraphState Agent
# =========================
def db_reliability_agent(state: GraphState) -> GraphState:
    log_text = state.event.get("log", "")
    analysis = asyncio.run(analyze_db_log(log_text))

    state.context["db"] = {
        "analysis": analysis,
        "actions": analysis
    }

    state.logs.append("[DB-Agent] DB 장애 분석/조치 완료.")
    return state


# =========================
# 테스트
# =========================
if __name__ == "__main__":

    # 테스트 1 로그 없음
    print(asyncio.run(analyze_db_log("")))

    # 테스트 2 로그 있음
    sample_log = """
    ERROR 1045 (28000): Access denied for user 'root'@'localhost'
    """
    print(asyncio.run(analyze_db_log(sample_log)))
