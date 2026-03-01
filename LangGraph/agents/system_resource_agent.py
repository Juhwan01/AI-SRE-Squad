from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

from state import GraphState

load_dotenv()

# =========================
# LLM
# =========================
llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0
)

# =========================
# 시스템 프롬프트
# =========================
SYSTEM_PROMPT = """
너는 시스템 로그 분석 전문가다.

분석 대상:

[Linux]
- syslog, journalctl, kernel 로그

[macOS]
- log show, launchd 서비스 로그

[Windows]
- Event Viewer (System / Application / Security)
- Windows Service 오류
- IIS 로그
- .NET Runtime 오류
- Driver 오류
- BSOD 로그

반드시 아래 형식으로만 답변:

[문제 원인 정리]
- ...

[해결 방법 정리]
- ...

규칙:
1. 로그 없으면 "로그가 제공되지 않았습니다"
2. 로그 기반으로만 분석
3. 해결 방법은 실제 운영 기준
4. 필요한 명령어 또는 설정 방법 포함
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
def analyze_system_log(log_text: str) -> str:

    if not log_text.strip():
        return """
[문제 원인 정리]
- 로그가 제공되지 않았습니다

[해결 방법 정리]
- 시스템 로그를 입력해주세요
"""

    result = agent.invoke({
        "messages": [
            ("system", SYSTEM_PROMPT),
            ("user", f"다음 시스템 로그 분석:\n{log_text}")
        ]
    })

    return result["messages"][-1].content


# =========================
# GraphState Agent
# =========================
def system_resource_agent(state: GraphState) -> GraphState:
    event = state.event
    log_text = event.get("log", "")

    analysis = analyze_system_log(log_text)

    state.context["resource"] = {
        "analysis": analysis,
        "actions": analysis
    }

    state.logs.append("[System-Resource-Agent] 자원 분석 및 조치 완료.")
    return state


# =========================
# 테스트
# =========================
if __name__ == "__main__":
    sample_log = """
    Feb 17 19:05:20 server1 sshd[4455]: Failed password for root from 192.168.1.100 port 54321 ssh2
    """

    print(analyze_system_log(sample_log))
