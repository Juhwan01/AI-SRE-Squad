# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-SRE-Squad는 LangGraph 기반 멀티 에이전트 SRE 자동화 프레임워크다. 인시던트 이벤트가 들어오면 Supervisor가 LLM으로 장애 유형을 판단해 전문 에이전트에 라우팅하고, 각 에이전트는 MCP 서버 툴을 사용해 실제 시스템에 접근해 분석 및 조치 후 Slack으로 리포팅한다.

## Architecture

### 전체 흐름

```
장애 이벤트 입력
    ↓
supervisor_agent  ← LLM(ChatOpenAI)이 이벤트 내용 분석 → next_agent 결정
    ↓ (conditional_edges로 자동 분기)
┌─────────────────────────────────────────┐
│  db_reliability_agent                   │  PostgreSQL MCP 툴로 DB 직접 조회
│  network_reliability_agent              │  로그 파싱 + nginx 설정 분석 + patch 생성
│  system_resource_agent                  │  syslog/journalctl/Event Viewer 분석
└─────────────────────────────────────────┘
    ↓
manager_agent  ← Slack MCP 툴로 채널에 리포트 전송 (현재 supervisor fallback으로만 호출됨)
    ↓
END
```

### Supervisor 라우팅 방식

`supervisor_agent.py`는 `ChatOpenAI.with_structured_output(RouterDecision)`을 사용해 LLM이 이벤트 전체 내용을 보고 라우팅 대상을 결정한다. 하드코딩된 문자열 비교 없음.

```python
class RouterDecision(BaseModel):
    next_agent: Literal["db_reliability_agent", "network_reliability_agent", ...]
    reasoning: str  # 판단 근거 (logs에 기록됨)
```

### MCP 통합 방식

각 에이전트는 `langchain-mcp-adapters`의 `load_mcp_tools(session)`으로 MCP 툴을 LangChain Tool 형식으로 변환해 `create_react_agent`에 주입한다. MCP 서버는 **npx로 subprocess 실행(stdio 전송)** — 미리 서버를 켜놓을 필요 없음.

```python
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await load_mcp_tools(session)   # MCP → LangChain Tool 변환
        agent = create_react_agent(llm, tools)
        result = await agent.ainvoke({...})
```

GraphState Agent 함수는 동기 함수(`def`)이므로 `asyncio.run()`으로 비동기 MCP 호출을 브릿지한다.

### GraphState (`LangGraph/state.py`)

| 필드 | 타입 | 역할 |
|------|------|------|
| `event` | `Dict` | 인시던트 원본 데이터 (type, service, timestamp, log, code_repo) |
| `next_agent` | `Optional[str]` | supervisor가 세팅, graph router가 읽어서 분기 |
| `context` | `Dict` | 각 에이전트 분석 결과 누적 (`context["db"]`, `context["network"]` 등) |
| `logs` | `List[str]` | 전체 실행 감사 로그 |
| `result` | `Optional[Any]` | 최종 결과 |

## 실행 방법

### 패키지 설치

```bash
pip install langchain-openai langgraph langchain-mcp-adapters mcp python-dotenv
```

### 환경변수 설정 (`.env`)

```
OPENAI_API_KEY=sk-...

# DB Agent
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Manager Agent (Slack)
SLACK_BOT_TOKEN=xoxb-...
SLACK_TEAM_ID=T...
TARGET_CHANNEL=C...
```

### 워크플로우 실행

```bash
cd LangGraph
python run.py       # nginx 502 시나리오 테스트 이벤트 실행
```

### MCP 연결 단독 테스트

```bash
cd MCP_test/slack_mcp/mcp_server
python test_agent.py        # Slack MCP 연결 테스트

cd MCP_test/postgresql_mcp
python mcp_client.py        # PostgreSQL MCP 연결 테스트
```

## 핵심 파일

| 파일 | 역할 | 수정 시점 |
|------|------|---------|
| `LangGraph/state.py` | 공유 상태 스키마 | 에이전트 간 새 데이터 필드 추가 시 |
| `LangGraph/graph.py` | 노드/엣지 정의 | 에이전트 추가/제거 시 |
| `LangGraph/agents/supervisor_agent.py` | LLM 기반 라우터 | 새 에이전트 추가 시 `RouterDecision.next_agent` Literal에 추가 |
| `LangGraph/agents/db_reliability_agent.py` | PostgreSQL MCP 연동 DB 분석 | DB 분석 프롬프트/로직 수정 시 |
| `LangGraph/agents/network_reliability_agent.py` | nginx 로그 분석 + patch 생성 | 가장 복잡한 에이전트 (2단계 파이프라인) |
| `LangGraph/agents/manager_agent.py` | Slack MCP 연동 리포팅 | Slack 메시지 포맷 수정 시 |
| `LangGraph/run.py` | 테스트 실행 스크립트 | 테스트 이벤트 시나리오 변경 시 |

## 새 에이전트 추가 방법

1. `LangGraph/agents/<domain>_reliability_agent.py` 생성
   - `async def _analyze(...)` — MCP 연결 + `create_react_agent` 실행
   - `def <domain>_reliability_agent(state: GraphState) -> GraphState` — `asyncio.run()` 으로 호출
2. `supervisor_agent.py`의 `RouterDecision.next_agent` Literal에 새 에이전트명 추가
3. `graph.py`의 `create_graph()`에 노드 등록 및 엣지 연결
4. `run.py`에서 import 후 `create_graph()`에 전달

## 새 MCP 서버 연동 방법

```python
server_params = StdioServerParameters(
    command="npx.cmd" if sys.platform == "win32" else "npx",
    args=["-y", "@modelcontextprotocol/server-<name>", ...],
    env={**os.environ}
)
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await load_mcp_tools(session)
```

MCP 서버 목록: https://github.com/modelcontextprotocol/servers

## 현재 알려진 한계

- `manager_agent`는 supervisor가 알 수 없는 이벤트 타입을 받을 때만 호출됨 — 전체 에이전트 완료 후 항상 호출되도록 `graph.py` 수정 필요
- specialist 에이전트들이 순차 실행만 지원 (복합 장애 시 병렬 분기 없음)
- 인시던트 간 상태 영속성 없음 (매 실행마다 새로운 GraphState)
