from langgraph.graph import StateGraph, END
from state import GraphState

# === Router: Supervisor가 next_agent에 적어준 이름으로 분기 ===
def router(state: GraphState):
    if not state.next_agent:
        return END
    return state.next_agent


def create_graph(
        supervisor,
        manager,
        db_agent,
        net_agent,
        sys_agent):

    graph = StateGraph(GraphState)

    graph.add_node("supervisor", supervisor)
    graph.add_node("manager_agent", manager)
    graph.add_node("db_reliability_agent", db_agent)
    graph.add_node("network_reliability_agent", net_agent)
    graph.add_node("system_resource_agent", sys_agent)

    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        router,
        {
            "manager_agent": "manager_agent",
            "db_reliability_agent": "db_reliability_agent",
            "network_reliability_agent": "network_reliability_agent",
            "system_resource_agent": "system_resource_agent",
            END: END
        }
    )
    
    graph.add_edge("manager_agent", END)
    graph.add_edge("db_reliability_agent", END)
    graph.add_edge("network_reliability_agent", END)
    graph.add_edge("system_resource_agent", END)

    return graph.compile()