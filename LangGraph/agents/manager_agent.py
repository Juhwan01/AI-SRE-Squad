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
너는 SRE 인시던트 리포터다.

주어진 장애 이벤트와 분석 결과를 바탕으로 Slack 메시지를 작성하고,
slack_post_message 툴로 지정된 채널에 전송해라.

메시지 형식:
🚨 *[장애 알림]* <서비스명>
- 장애 유형: <type>
- 발생 시각: <timestamp>
- 원인 요약: <분석 결과 요약>
- 조치 방법: <해결 방법 요약>
"""


# =========================
# 실행 함수 (MCP 연결 포함)
# =========================
async def send_slack_report(event: dict, context: dict) -> str:
    command = "npx.cmd" if sys.platform == "win32" else "npx"
    channel = os.getenv("TARGET_CHANNEL", "")

    server_params = StdioServerParameters(
        command=command,
        args=["-y", "@modelcontextprotocol/server-slack"],
        env={**os.environ}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(llm, tools)
            result = await agent.ainvoke({
                "messages": [
                    ("system", SYSTEM_PROMPT),
                    ("user", f"장애 이벤트:\n{event}\n\n분석 결과:\n{context}\n\n채널 ID: {channel}")
                ]
            })

    return result["messages"][-1].content


# =========================
# GraphState Agent
# =========================
def manager_agent(state: GraphState) -> GraphState:
    report = asyncio.run(send_slack_report(state.event, state.context))

    state.context["manager"] = {
        "slack_message": report
    }

    state.logs.append("[Manager] Slack 메시지 전송 완료.")
    return state