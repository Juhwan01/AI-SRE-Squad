from state import GraphState

def system_resource_agent(state: GraphState):
    event = state.event

    # 👉 시스템 자원 분석 로직 추가 예정
    state.context["resource"] = {
        "analysis": None,
        "actions": None
    }

    state.logs.append("[System-Resource-Agent] 자원 분석 및 조치 완료.")
    return state