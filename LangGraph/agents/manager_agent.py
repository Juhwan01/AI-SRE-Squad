from state import GraphState

def manager_agent(state: GraphState):

    event = state.event

    # 👉 Slack 메시지 전송 로직 추가 예정
    state.context["manager"] = {
        "slack_message": None
    }

    state.logs.append("[Manager] Slack 메시지 처리 완료.")
    return state