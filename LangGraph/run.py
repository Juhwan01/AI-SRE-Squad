from state import GraphState

from agents.supervisor_agent import supervisor_agent
from agents.manager_agent import manager_agent
from agents.db_reliability_agent import db_reliability_agent
from agents.network_reliability_agent import network_reliability_agent
from agents.system_resource_agent import system_resource_agent

from graph import create_graph

graph = create_graph(
    supervisor=supervisor_agent,
    manager=manager_agent,
    db_agent=db_reliability_agent,
    net_agent=network_reliability_agent,
    sys_agent=system_resource_agent
)

event = {
    "type": "db_connection_error",
    "service": "auth",
    "timestamp": "2025-11-26T10:33:00"
}

result = graph.invoke({"event": event})

# --- 결과 출력 ---
print("\n=== Logs ===")
for log in result["logs"]:
    print(log)

print("\n=== Context ===")
print(result["context"])