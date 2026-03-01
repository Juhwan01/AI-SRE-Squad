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
    "type": "nginx_502",
    "service": "auth",
    "timestamp": "2025-11-26T10:33:00",
    "log": """
2025/11/26 10:33:00 [error] 32#32: *1 connect() failed (111: Connection refused)
while connecting to upstream, client: 192.168.1.1, server: example.com,
request: "POST /api/login HTTP/1.1", upstream: "http://127.0.0.1:8000/api/login",
host: "example.com"
2025/11/26 10:33:00 [warn] 32#32: *1 upstream server temporarily disabled
while connecting to upstream, client: 192.168.1.1, server: example.com,
request: "POST /api/login HTTP/1.1", upstream: "http://127.0.0.1:8000/api/login"
""",
    "code_repo": {
        "nginx/nginx.conf": """
worker_processes 1;

events { worker_connections 1024; }

http {
    upstream backend {
        server 127.0.0.1:8000;
    }

    server {
        listen 80;
        server_name example.com;

        location /api/ {
            proxy_pass http://backend;
            proxy_connect_timeout 5s;
            proxy_read_timeout 5s;
        }
    }
}
""",
        "nginx/sites-enabled/default": """
server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate /etc/ssl/certs/example.crt;
    ssl_certificate_key /etc/ssl/private/example.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
"""
    }
}

result = graph.invoke({"event": event})

# --- 결과 출력 ---
print("\n=== Logs ===")
for log in result["logs"]:
    print(log)

print("\n=== Context ===")
print(result["context"])