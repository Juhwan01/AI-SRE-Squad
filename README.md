# 🚨 AI-SRE-Squad

AI-powered DevOps and SRE automation projects using MCP (Model Context Protocol)

## 📂 Projects

### 1. 🚨 War Room MCP (`warroom-mcp/`)
**AI SRE Squad - Multi-Agent Crisis Management System**

- **Based on**: [Prometheus MCP Server](https://github.com/pab1it0/prometheus-mcp-server)
- **Features**:
  - 🐳 Docker container management
  - 🔧 Auto-recovery system
  - 💀 Chaos engineering tools
  - 📊 Prometheus metrics integration
- **Status**: ✅ POC Ready

[→ Go to War Room](./warroom-mcp/)

### 2. 🌤️ Weather MCP (`weather/`)
**Weather information MCP server**

- Simple MCP server for weather data
- Uses NWS (National Weather Service) API
- Example from Anthropic MCP tutorials

### 3. 🔌 Client-Server (`client-server/`)
**MCP client with AWS Bedrock integration**

- Connects to MCP servers
- Uses AWS Bedrock Claude
- Reference client implementation

### 4. 📦 LangGraph App (`path/to/your/app/`)
**LangGraph Studio testing project**

- Multi-agent system experiments
- LangGraph workflow testing

## 🚀 Quick Start

### War Room MCP (Recommended)

```bash
cd warroom-mcp

# Install
powershell -Command "& 'C:\Users\정주환\.local\bin\uv.exe' sync"

# Run server
python -m warroom_mcp_server.server
```

### Weather MCP

```bash
cd weather
uv sync
uv run weather.py
```

### Client

```bash
cd client-server
uv sync
uv run client.py ../weather/weather.py
```

## 🎯 Main Focus: War Room MCP

The **War Room** is the primary project - an AI-powered SRE system that:

1. **Detects** system anomalies and container failures
2. **Recovers** failed services automatically
3. **Reports** incidents with post-mortem analysis
4. **Integrates** with Prometheus for metrics

### Docker Tools Available

- `docker_get_container_status` - Check container health
- `docker_recover_container` - Auto-restart failed containers
- `docker_get_logs` - Retrieve container logs
- `docker_trigger_chaos` - Simulate failures
- `docker_list_containers` - List all containers

## 📚 Technology Stack

- **MCP**: Model Context Protocol (Anthropic)
- **FastMCP**: Rapid MCP server development
- **Docker**: Container management
- **Prometheus**: Metrics collection
- **AWS Bedrock**: Claude AI integration
- **Python 3.10+**: Core language
- **uv**: Package management

## 📖 Documentation

- [War Room Implementation Plan](./WARROOM_IMPLEMENTATION_PLAN.md)
- [War Room README](./warroom-mcp/README_WARROOM.md)

## 🔗 References

- [Model Context Protocol](https://modelcontextprotocol.io)
- [Prometheus MCP Server](https://github.com/pab1it0/prometheus-mcp-server)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Anthropic MCP Servers](https://github.com/modelcontextprotocol/servers)

## 📝 License

MIT

---

**Built with ❤️ using MCP and Claude Code**
