from typing import Literal
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from state import GraphState

load_dotenv()

# =========================
# LLM
# =========================
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)


# =========================
# 라우팅 스키마
# =========================
class RouterDecision(BaseModel):
    next_agent: Literal[
        "db_reliability_agent",
        "network_reliability_agent",
        "system_resource_agent",
        "manager_agent"
    ]
    reasoning: str


router_llm = llm.with_structured_output(RouterDecision)

SYSTEM_PROMPT = """
너는 SRE 인시던트 라우터다.

입력받은 장애 이벤트를 분석해서 가장 적합한 전문가 에이전트를 선택해라.

에이전트 목록:
- db_reliability_agent: DB 연결 오류, 인증 실패, 쿼리 타임아웃 등 데이터베이스 관련 장애
- network_reliability_agent: Nginx 오류(502/504), SSL 문제, 네트워크 타임아웃 등 네트워크/웹서버 관련 장애
- system_resource_agent: CPU/메모리/디스크 고갈, 커널 패닉, 서비스 다운 등 시스템 리소스 관련 장애
- manager_agent: 위 카테고리에 해당하지 않는 경우

이벤트 내용(로그, 서비스명, 에러 메시지 등)을 종합적으로 판단해라.
"""


# =========================
# Supervisor Agent
# =========================
def supervisor_agent(state: GraphState) -> GraphState:
    decision = router_llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("user", f"장애 이벤트:\n{state.event}")
    ])

    state.next_agent = decision.next_agent
    state.logs.append(f"[Supervisor] {decision.reasoning} → {decision.next_agent}")

    return state