# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-SRE-Squad is an AI-powered SRE (Site Reliability Engineering) automation framework for incident response. It uses a multi-agent LangGraph workflow to route incidents to specialist agents, analyze logs, generate fix patches, and report via Slack.

## Architecture

### Two-Tier Design

**LangGraph Tier** (`LangGraph/`) — Multi-agent orchestration:
- `supervisor_agent.py` routes incidents by event type prefix (`db_*`, `nginx_*`, `resource_*`)
- Specialist agents analyze domain-specific logs using LLMs and store findings in shared `GraphState`
- `manager_agent.py` aggregates results for Slack reporting (WIP)

**MCP Tier** — Tool/API integration via Model Context Protocol:
- `client-server/client.py` — AWS Bedrock + MCP client (iterative tool-use loop)
- `weather/weather.py` — FastMCP server example
- `MCP_test/` — Integration tests for Slack and PostgreSQL MCP connections

### State Flow

```
Event → supervisor_agent (routes by type) → specialist agent (LLM analysis) → manager_agent → END
```

All agents share `GraphState` (defined in `LangGraph/state.py`):
- `event`: Incident metadata (type, service, timestamp, log, code_repo)
- `next_agent`: Routing target set by supervisor
- `context`: Dict accumulating per-agent findings
- `logs`: Audit trail
- `result`: Final aggregated output

### MCP Tool-Use Loop Pattern

`client-server/client.py` implements: connect → list tools → invoke Bedrock → if tool_use → execute tool → re-invoke → repeat until stop_reason is not `tool_use` (max 5 iterations)

## Commands

### Running the SRE Workflow

```bash
cd LangGraph
python run.py          # Execute incident response with test event
```

### Running MCP Integration Tests

```bash
cd MCP_test/slack_mcp/mcp_server
python test_agent.py                      # Slack MCP client test

cd MCP_test/postgresql_mcp
python mcp_client.py                      # PostgreSQL MCP client test
```

### Running the MCP Client (Bedrock)

```bash
cd client-server
uv run client.py <path_to_server_script>  # e.g., ../weather/weather.py
```

### LangGraph Template (`path/to/your/app/`)

```bash
cd "path/to/your/app"
make test              # pytest
make lint              # ruff + mypy
make format            # ruff format
langgraph dev          # Start LangGraph Studio
```

## Key Files

| File | Purpose |
|------|---------|
| `LangGraph/state.py` | Shared state schema — modify here when adding new agent fields |
| `LangGraph/graph.py` | Workflow edges — modify when adding/removing agents |
| `LangGraph/agents/supervisor_agent.py` | Routing logic by event type prefix |
| `LangGraph/agents/network_reliability_agent.py` | Most complex agent — LLM log parsing + patch generation |
| `client-server/client.py` | Bedrock + MCP integration reference implementation |

## Environment Variables Required

- `OPENAI_API_KEY` — Used by `network_reliability_agent.py` (ChatOpenAI gpt-4.1-mini)
- AWS credentials — Used by `client-server/client.py` (boto3/Bedrock)
- Slack tokens — Required for `manager_agent.py` and Slack MCP tests

## Extending the System

**Adding a new specialist agent:**
1. Create `LangGraph/agents/<domain>_reliability_agent.py` with `async def <domain>_agent(state: GraphState) -> GraphState`
2. Add routing rule in `supervisor_agent.py` (event type prefix → agent name)
3. Register node and edge in `LangGraph/graph.py`

**Adding a new MCP server:**
- Follow the pattern in `weather/weather.py` (FastMCP decorator-based tool registration)
- Servers communicate via stdio subprocess transport

## Current Limitations

- `manager_agent.py` (Slack reporting) is a stub — not yet fully integrated
- LangGraph specialist agents run in linear sequence (no parallel branch execution)
- No persistent state storage between incidents
