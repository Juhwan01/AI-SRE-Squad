from state import GraphState

def supervisor_agent(state: GraphState):

    event = state.event

    if state.event["type"].startswith("db"):
        state.next_agent = "db_reliability_agent"
    elif state.event["type"].startswith("nginx"):
        state.next_agent = "network_reliability_agent"
    elif state.event["type"].startswith("resource"):
        state.next_agent = "system_resource_agent"
    else:
        state.next_agent = "manager_agent"
    print(state.next_agent)
    state.logs.append("[Supervisor] 장애 분석 완료. 담당자 배정 대기.")

    return state