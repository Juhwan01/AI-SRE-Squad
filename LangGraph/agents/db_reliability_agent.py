from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
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

반드시 아래 형식으로만 답변해라.

[문제 원인 정리]
- ...

[해결 방법 정리]
- ...

규칙:
1. DB 로그가 없으면 "로그가 제공되지 않았습니다"라고 작성
2. 추측하지 말고 로그 기반으로 분석
3. 해결 방법은 실무 기준으로 작성
"""


# =========================
# Agent 생성
# =========================
agent = create_react_agent(
    llm,
    tools=[]
)


# =========================
# 실행 함수
# =========================
def analyze_db_log(log_text: str) -> str:
    if not log_text.strip():
        return """
[문제 원인 정리]
- 로그가 제공되지 않았습니다

[해결 방법 정리]
- DB 로그를 입력해주세요
"""

    result = agent.invoke({
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
    event = state.event
    log_text = event.get("log", "")

    analysis = analyze_db_log(log_text)

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

    # 테스트 1️⃣ 로그 없음
    print(analyze_db_log(""))

    # 테스트 2️⃣ 로그 있음
    sample_log = """
    ERROR 1045 (28000): Access denied for user 'root'@'localhost'
    """

    print(analyze_db_log(sample_log))
