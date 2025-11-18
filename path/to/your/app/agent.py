from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

# 1. 상태 정의 (메시지들이 쌓이는 메모리)
class State(TypedDict):
    # 메시지 리스트 (새 메시지가 오면 기존 리스트에 더함)
    messages: Annotated[List[str], operator.add]

# 2. 노드 정의 (Sentinel 에이전트의 행동)
def sentinel_agent(state: State):
    # 사용자가 입력한 마지막 메시지 확인
    last_message = state["messages"][-1]
    
    # 로직: "error"라는 단어가 있으면 경고, 아니면 정상
    if "error" in last_message.lower():
        response = "🚨 [CRITICAL] 장애가 감지되었습니다! 엔지니어를 호출합니다."
    else:
        response = "🟢 [NORMAL] 시스템 정상 작동 중입니다."
        
    return {"messages": [response]}

# 3. 그래프 만들기 (워크플로우 연결)
workflow = StateGraph(State)

# 노드 추가
workflow.add_node("sentinel", sentinel_agent)

# 시작점 설정 (사용자가 말하면 sentinel부터 시작)
workflow.set_entry_point("sentinel")

# 끝점 설정 (sentinel이 말하면 끝)
workflow.add_edge("sentinel", END)

# 4. 그래프 컴파일 (LangGraph Studio가 읽을 변수명: graph)
graph = workflow.compile()