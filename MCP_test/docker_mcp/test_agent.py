import operator
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage

# 에이전트 상태 정의
class AgentState(TypedDict):
    incident_data: dict
    analysis: str
    plan: str
    logs: str

# 노드 1: 장애 분석 (Log 분석 및 원인 파악)
def analyze_incident(state: AgentState):
    data = state["incident_data"]
    layer = data.get("layer")
    details = data.get("details")
    
    analysis = f"[{layer}] 레이어에서 장애 감지. 상세 내용: {details}. "
    if "500" in details or "EXCEPTION" in details.upper():
        analysis += "애플리케이션 내부 로직 에러로 판단됨."
    else:
        analysis += "인프라 또는 연결 이슈 가능성 검토 필요."
    
    return {"analysis": analysis}

# 노드 2: 복구 계획 수립
def create_recovery_plan(state: AgentState):
    analysis = state["analysis"]
    target = state["incident_data"].get("target")
    
    if "로직 에러" in analysis:
        plan = f"컨테이너 '{target}'의 상태가 불안정하므로 재시작(Restart)을 권고함."
    else:
        plan = f"컨테이너 '{target}'의 리소스 및 네트워크 설정을 재검토해야 함."
        
    return {"plan": plan}

# 그래프 구축
workflow = StateGraph(AgentState)

workflow.add_node("analyze", analyze_incident)
workflow.add_node("plan_recovery", create_recovery_plan)

workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "plan_recovery")
workflow.add_edge("plan_recovery", END)

# 컴파일
agent_app = workflow.compile()

def run_sre_agent(incident_report: dict):
    print(f"\n🤖 [LangGraph Agent] 장애 대응 시작...")
    initial_state = {"incident_data": incident_report, "analysis": "", "plan": "", "logs": ""}
    result = agent_app.invoke(initial_state)
    
    print(f"🧐 분석 결과: {result['analysis']}")
    print(f"🛠️  조치 계획: {result['plan']}\n")
    return result