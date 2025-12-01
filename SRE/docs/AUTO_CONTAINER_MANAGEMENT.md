# War Room 2.0 - 자동 컨테이너 관리 가이드

## 🤖 자동 컨테이너 관리 개요

War Room 2.0은 **완전 자동으로 MCP 서버 컨테이너를 시작하고 종료**합니다.

## 🔄 전체 자동화 플로우

```
1. 장애 발생
   "Error: Cannot connect to Docker daemon"

2. War Room이 자동 분석
   → 키워드: ["docker", "daemon"]

3. War Room이 자동 검색
   → NPM Registry에서 MCP 서버 검색
   → 최적 서버 선택: @modelcontextprotocol/server-docker

4. War Room이 자동 시작 ⚡
   → Docker 컨테이너 자동 생성 및 시작
   → 3초 이내 실행 (Tier 1인 경우)

5. 문제 해결 후 자동 대기
   → 30분간 Idle 상태로 대기 (재사용 대비)

6. War Room이 자동 종료 🗑️
   → 30분간 미사용 시 자동 종료
   → 메모리 100MB 회수
```

## ⚡ 자동 시작 (Auto Start)

### 언제 시작하나요?

```python
# 예시: Docker 장애 발생
error_log = "Error: Cannot connect to Docker daemon"

# War Room이 자동으로:
result = await war_room.handle_incident(error_log, auto_approve=True)

# 내부 동작:
# 1. 문제 분석
# 2. MCP 서버 검색
# 3. 티어 확인
# 4. ✅ 컨테이너 자동 시작 ← 여기!
```

### 실제 명령어 (War Room이 자동 실행)

```bash
# War Room이 내부적으로 이렇게 실행:
docker run \
  --name docker-mcp-1733024400 \
  --network war-room-network \
  --memory 200M \
  --cpus 0.5 \
  --rm \
  --env MCP_PACKAGE=@modelcontextprotocol/server-docker \
  mcp/server-docker:latest
```

**사용자는 아무것도 하지 않아도 됩니다!**

## 🗑️ 자동 종료 (Auto Stop)

### 3가지 자동 종료 조건

#### 1. Idle 타임아웃 (기본 30분)

```
컨테이너 시작
    ↓
작업 완료
    ↓
Idle 상태 진입 (대기 중)
    ↓
30분 경과... ⏰
    ↓
✅ 자동 종료
```

**로그 예시:**
```
2025-12-01 10:00:00 - 컨테이너 시작: docker-mcp-123
2025-12-01 10:05:00 - 작업 완료, Idle 상태 진입
2025-12-01 10:35:00 - Idle 타임아웃 (30분), 자동 종료
2025-12-01 10:35:01 - 메모리 100MB 회수
```

#### 2. 메모리 압박 (80% 초과)

```
현재 메모리 사용: 85%
    ↓
War Room 감지
    ↓
가장 오래된 Idle 컨테이너 찾기
    ↓
✅ 우선순위 기반 자동 종료
    ↓
메모리 사용: 65% (정상)
```

**로그 예시:**
```
2025-12-01 10:00:00 - 메모리 압박 감지: 85%
2025-12-01 10:00:01 - 종료 대상: postgres-mcp (Idle 45분)
2025-12-01 10:00:02 - 자동 종료 완료
2025-12-01 10:00:03 - 메모리 사용: 65%
```

#### 3. 동시 실행 제한 (기본 10개)

```
현재 컨테이너: 10개 (최대 도달)
    ↓
새로운 컨테이너 필요
    ↓
가장 오래된 Idle 컨테이너 자동 종료
    ↓
✅ 새 컨테이너 시작
```

## 🎛️ 설정 커스터마이징

### 자동 종료 시간 변경

```python
from src.container_orchestrator import ContainerPoolConfig

config = ContainerPoolConfig(
    idle_timeout_minutes=15,  # 기본 30분 → 15분으로 변경
    max_concurrent_containers=5,  # 기본 10개 → 5개로 제한
    max_memory_percent=70.0,  # 기본 80% → 70%로 변경
)

war_room = IntegratedWarRoom(container_config=config)
```

### 자동 승인 여부

```python
# 자동 승인 (컨테이너 즉시 시작)
result = await war_room.handle_incident(error_log, auto_approve=True)

# 수동 승인 (사용자 확인 필요)
result = await war_room.handle_incident(error_log, auto_approve=False)
# → "컨테이너를 시작하시겠습니까? (yes/no):"
```

## 📊 백그라운드 자동 관리

War Room은 **백그라운드 태스크**를 실행합니다:

```python
# War Room 시작 시 자동으로 실행됨
await war_room.start()

# 백그라운드에서 1분마다 실행:
async def cleanup_loop():
    while True:
        await asyncio.sleep(60)  # 1분 대기

        # 1. Idle 컨테이너 정리
        await cleanup_idle_containers()

        # 2. 메모리 압박 확인
        await check_memory_pressure()
```

**사용자는 신경 쓸 필요 없음!** War Room이 알아서 관리합니다.

## 🎯 실제 사용 예시

### 예시 1: Docker 장애 자동 처리

```python
from src.integrated_war_room import IntegratedWarRoom
import asyncio

async def main():
    war_room = IntegratedWarRoom()
    await war_room.start()  # 백그라운드 자동 관리 시작

    # Docker 장애 발생
    error = "Error: Cannot connect to Docker daemon"

    # 자동 처리 (컨테이너 시작부터 종료까지 모두 자동)
    result = await war_room.handle_incident(error, auto_approve=True)

    # 결과만 확인
    print(result['message'])
    # "MCP 서버 시작 완료: @modelcontextprotocol/server-docker"

    # 30분 후 자동 종료됨 (신경 안 써도 됨)

    await war_room.shutdown()

asyncio.run(main())
```

**출력:**
```
🔍 문제 분석 중...
📌 키워드: ['docker']

🔎 MCP Catalog 검색 중...
✨ 최적 후보: @modelcontextprotocol/server-docker (점수: 80/100)

⚙️ 컨테이너 시작 중...
✅ 컨테이너 시작 완료: abc123

MCP 서버 시작 완료: @modelcontextprotocol/server-docker
```

### 예시 2: 여러 장애 동시 처리

```python
# 동시 3개 장애
errors = [
    "Docker daemon error",
    "PostgreSQL connection failed",
    "Redis ECONNREFUSED",
]

for error in errors:
    await war_room.handle_incident(error, auto_approve=True)

# 결과:
# - 3개 컨테이너 자동 시작
# - 30분 후 각각 자동 종료
```

### 예시 3: 재사용 시나리오

```
10:00 - Docker 장애 발생
        → War Room이 docker-mcp 컨테이너 시작

10:05 - 문제 해결 완료
        → 컨테이너 Idle 상태 (30분 대기)

10:20 - 다시 Docker 장애 발생
        → War Room이 기존 컨테이너 재사용 (즉시, 0초)

10:25 - 문제 해결 완료
        → 다시 Idle 상태 (30분 대기)

10:55 - 30분 경과
        → War Room이 컨테이너 자동 종료
```

## 🔍 상태 모니터링

### 실시간 상태 확인

```python
# 현재 실행 중인 컨테이너 확인
await war_room.show_status()
```

**출력:**
```
📊 War Room 2.0 - 시스템 상태
============================================

🐳 컨테이너 풀:
  • 실행 중: 2개
  • Idle 상태: 1개
  • 총 메모리: 300MB

  상세:
    - docker-mcp
      상태: running, 메모리: 100MB
      가동: 5분, Idle: 0분

    - postgres-mcp
      상태: idle, 메모리: 100MB
      가동: 45분, Idle: 15분
      → 15분 후 자동 종료 예정
```

### 로그 확인

War Room이 자동으로 로깅합니다:

```
2025-12-01 10:00:00 - INFO - 컨테이너 시작: docker-mcp-123
2025-12-01 10:05:00 - INFO - Idle 상태 진입: docker-mcp-123
2025-12-01 10:35:00 - INFO - Idle 타임아웃 종료: docker-mcp-123
2025-12-01 11:00:00 - WARNING - 메모리 압박 감지: 85%
2025-12-01 11:00:01 - INFO - 메모리 확보 종료: postgres-mcp-456
```

## ✅ 정리

### War Room이 자동으로 하는 것:

1. ✅ **컨테이너 시작**
   - 문제 분석
   - MCP 서버 검색
   - 티어 확인
   - 컨테이너 생성 및 시작

2. ✅ **컨테이너 관리**
   - 상태 추적
   - 메모리 모니터링
   - 재사용 판단

3. ✅ **컨테이너 종료**
   - 30분 Idle 타임아웃
   - 메모리 압박 시 우선순위 기반 종료
   - 리소스 정리

4. ✅ **최적화**
   - 티어 자동 조정
   - 사용 패턴 학습
   - 이미지 캐싱

### 사용자가 할 것:

1. **Docker Desktop 실행** (한 번만)
2. **War Room 시작** (`await war_room.start()`)
3. **장애 처리 요청** (`handle_incident()`)
4. **끝!** 나머지는 War Room이 알아서 처리

---

**War Room 2.0**: "당신은 문제만 알려주세요. 나머지는 제가 다 합니다."
