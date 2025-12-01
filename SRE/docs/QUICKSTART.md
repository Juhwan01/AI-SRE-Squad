# War Room 2.0 - Quick Start Guide

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.10+
- Docker & Docker Compose
- uv (Python 패키지 관리자)

### 1. 의존성 설치

```bash
# uv 설치 (없는 경우)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 의존성 설치
uv sync
```

### 2. Docker 환경 확인

```bash
# Docker 실행 확인
docker info

# Docker Compose 버전 확인
docker-compose --version
```

### 3. 실행 방법

#### 방법 A: Python으로 직접 실행 (개발)

```bash
# 대화형 모드
uv run python -m src.integrated_war_room

# 데모 시나리오
uv run python -m src.integrated_war_room demo

# 테스트
uv run python test_integrated_mvp.py
```

#### 방법 B: Docker Compose로 실행 (프로덕션)

```bash
# War Room Manager 빌드 및 시작
cd docker
docker-compose up -d

# 로그 확인
docker-compose logs -f war-room-manager

# 상태 확인
docker-compose ps

# 종료
docker-compose down
```

## 📝 사용 예시

### 시나리오 1: Docker 장애 처리

```python
from src.integrated_war_room import IntegratedWarRoom
import asyncio

async def handle_docker_issue():
    war_room = IntegratedWarRoom()
    await war_room.start()

    error_log = """
    Error: Cannot connect to the Docker daemon.
    Is the docker daemon running?
    """

    result = await war_room.handle_incident(error_log, auto_approve=True)
    print(result)

    await war_room.shutdown()

asyncio.run(handle_docker_issue())
```

**동작 과정:**
1. 에러 로그 분석 → 키워드: ["docker", "daemon", "container"]
2. MCP Catalog 검색 → `@modelcontextprotocol/server-docker` 발견
3. 티어 확인 → Tier 2 (Official 서버)
4. 컨테이너 시작 (~3초)
5. 문제 해결

### 시나리오 2: 상태 모니터링

```bash
# 대화형 모드 시작
uv run python -m src.integrated_war_room

> status
📊 War Room 2.0 - 시스템 상태
==============================================

🐳 컨테이너 풀:
  • 실행 중: 2개
  • Idle 상태: 1개
  • 총 메모리: 300MB

📈 티어 관리:
  • 등록된 서버: 5개
  • 총 사용 횟수: 28회
  • 주간 사용: 12회

  티어 분포:
    - Hot Pool (자주 사용): 2개
    - Warm Pool (가끔 사용): 2개
    - Cold Pool (드물게 사용): 1개
```

### 시나리오 3: 시스템 최적화

```bash
> optimize
🧹 시스템 최적화 시작...
  1️⃣ Idle 컨테이너 정리 중...
    ✅ postgres-mcp 종료 (45분 미사용)
  2️⃣ 티어 최적화 중...
    🔄 redis-mcp: Warm Pool → Hot Pool
  3️⃣ 리소스 확인 중...
    ✅ 메모리 사용률: 45% (정상)
✅ 시스템 최적화 완료
```

## 🧪 테스트

### 단위 테스트

```bash
# 티어 관리자 테스트
uv run python -c "
from test_integrated_mvp import test_tier_manager
import asyncio
asyncio.run(test_tier_manager())
"

# 전체 테스트
uv run python test_integrated_mvp.py
```

### 통합 테스트 (Docker 필요)

```bash
# 전체 시나리오 테스트
uv run python test_integrated_mvp.py
# → "전체 시나리오 테스트를 실행하시겠습니까?" → yes
```

## 🏗️ 아키텍처 이해

### 컴포넌트 구조

```
IntegratedWarRoom (메인 시스템)
    │
    ├─ ContainerPoolOrchestrator
    │   └─ Docker 컨테이너 생명주기 관리
    │
    ├─ TierManager
    │   └─ 사용 패턴 기반 서버 계층화
    │
    ├─ MCPCatalog
    │   └─ NPM Registry 검색
    │
    └─ ProblemAnalyzer
        └─ 에러 로그 분석
```

### 동작 플로우

```
1. 장애 발생
    ↓
2. ProblemAnalyzer: 키워드 추출
    ↓
3. MCPCatalog: 서버 검색 및 평가
    ↓
4. TierManager: 티어 확인/등록
    ↓
5. ContainerPoolOrchestrator: 컨테이너 시작
    ↓
6. TierManager: 사용 기록
    ↓
7. 자동 최적화 (백그라운드)
```

## 📊 리소스 관리

### 기본 설정

- **War Room Manager**: 200-512MB
- **MCP 서버 컨테이너**: 평균 100MB/개
- **최대 동시 실행**: 10개
- **Idle 타임아웃**: 30분
- **메모리 임계값**: 80%

### 커스텀 설정

```python
from src.container_orchestrator import ContainerPoolConfig

config = ContainerPoolConfig(
    max_concurrent_containers=5,     # 최대 5개
    idle_timeout_minutes=15,          # 15분 타임아웃
    max_memory_percent=70.0,          # 메모리 70% 임계값
    base_memory_limit="150m"          # 컨테이너당 150MB
)

war_room = IntegratedWarRoom(container_config=config)
```

## 🔧 트러블슈팅

### 문제: Docker 연결 실패

```
Error: Error while fetching server API version
```

**해결:**
```bash
# Docker 실행 확인
sudo systemctl start docker

# Docker 소켓 권한 확인
sudo chmod 666 /var/run/docker.sock
```

### 문제: 컨테이너 시작 실패 (이미지 없음)

```
ImageNotFound: mcp/server-docker:latest
```

**해결:**

현재 MVP는 이미지 자동 빌드를 지원하지 않습니다.
다음 단계:
1. MCP 베이스 이미지 빌드
2. 개별 MCP 서버 이미지 빌드

```bash
# 베이스 이미지 빌드
docker-compose --profile build-only up mcp-base-builder

# 개별 MCP 서버 이미지 빌드 (예정)
```

### 문제: 메모리 부족

```
MemoryError: Container pool memory limit exceeded
```

**해결:**
```bash
# 최적화 실행
> optimize

# 또는 수동으로 Idle 컨테이너 정리
docker ps -a | grep "mcp-" | awk '{print $1}' | xargs docker rm -f
```

## 🎯 다음 단계

1. **이미지 자동 빌드**: MCP 서버 이미지 자동 생성
2. **AI 분석 통합**: Anthropic API 기반 심층 분석
3. **웹 UI**: 대시보드 및 모니터링
4. **클라우드 배포**: AWS/GCP/Azure 배포 가이드

## 📚 추가 문서

- [설계 문서](MVP_DESIGN.md) - 아키텍처 상세 설명
- [README](../README.md) - 프로젝트 개요
- [GitHub Issues](https://github.com/your-repo/issues) - 버그 리포트 및 기능 요청

---

**War Room 2.0**: Zero-Config, Self-Learning AI SRE
