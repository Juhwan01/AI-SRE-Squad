# 🧪 War Room MCP Server - 테스팅 가이드

> 단계별로 따라하면서 War Room MCP Server를 완벽하게 테스트하세요!

---

## 📋 목차

1. [환경 준비](#환경-준비)
2. [기본 테스트](#기본-테스트)
3. [Docker 도구 테스트](#docker-도구-테스트)
4. [실전 시나리오 테스트](#실전-시나리오-테스트)
5. [문제 해결](#문제-해결)

---

## ✅ 환경 준비

### 1. 필수 요구사항 확인

```bash
# Python 버전 확인
python --version
# 출력: Python 3.10.x 이상이어야 함

# Docker 실행 확인
docker ps
# 에러가 나면 Docker Desktop 실행 필요

# uv 설치 확인
powershell -Command "& 'C:\Users\정주환\.local\bin\uv.exe' --version"
# 출력: uv 0.9.10 (또는 최신 버전)
```

### 2. 프로젝트 설치

```bash
# 프로젝트 디렉토리로 이동
cd i:/AI-SRE-Squad/warroom-mcp

# 의존성 설치
powershell -Command "& 'C:\Users\정주환\.local\bin\uv.exe' sync"

# 설치 확인
ls .venv/
```

**예상 출력**:
```
.venv/
├── Lib/
├── Scripts/
└── pyvenv.cfg
```

### 3. 테스트용 컨테이너 준비

```bash
# Nginx 테스트 컨테이너 실행
docker run -d --name test-nginx nginx:alpine

# PostgreSQL 테스트 컨테이너 실행
docker run -d --name test-postgres \
  -e POSTGRES_PASSWORD=password \
  postgres:16-alpine

# Redis 테스트 컨테이너 실행
docker run -d --name test-redis redis:7-alpine

# 컨테이너 확인
docker ps
```

**예상 출력**:
```
CONTAINER ID   IMAGE              STATUS         NAMES
abc123def456   nginx:alpine       Up 2 seconds   test-nginx
def456ghi789   postgres:16-alpine Up 1 second    test-postgres
ghi789jkl012   redis:7-alpine     Up 1 second    test-redis
```

---

## 🔧 기본 테스트

### Test 1: 서버 시작 확인

**목표**: MCP 서버가 정상적으로 시작되는지 확인

```bash
# War Room MCP Server 실행
cd i:/AI-SRE-Squad/warroom-mcp
python -m warroom_mcp_server.server
```

**예상 출력**:
```
[INFO] Starting War Room MCP Server mode=direct
[INFO] FastMCP server initialized name=War Room MCP
[INFO] Registered 11 tools
[INFO] Transport: stdio
Listening on stdio...
```

**확인 사항**:
- ✅ 에러 없이 실행됨
- ✅ "11 tools" 등록 확인 (Prometheus 6개 + Docker 5개)
- ✅ "Listening on stdio" 메시지 확인

**문제 발생 시**:
```bash
# ImportError 발생 시
powershell -Command "& 'C:\Users\정주환\.local\bin\uv.exe' sync"

# Docker 에러 발생 시
# Docker Desktop 실행 확인
```

---

## 🐳 Docker 도구 테스트

### Test 2: 컨테이너 목록 조회

**목표**: `docker_list_containers` 도구 테스트

**방법 1: Python 스크립트로 테스트**

```python
# test_list_containers.py
import asyncio
from warroom_mcp_server.docker_tools import get_all_containers

async def test():
    containers = get_all_containers()
    print("=== 모든 컨테이너 ===")
    for c in containers:
        if 'error' not in c:
            print(f"- {c['name']}: {c['status']} ({c['image']})")
        else:
            print(f"Error: {c['error']}")

asyncio.run(test())
```

```bash
# 실행
python test_list_containers.py
```

**예상 출력**:
```
=== 모든 컨테이너 ===
- test-nginx: running (nginx:alpine)
- test-postgres: running (postgres:16-alpine)
- test-redis: running (redis:7-alpine)
```

**방법 2: MCP Inspector로 테스트**

```bash
# MCP Inspector 설치 (선택)
npm install -g @modelcontextprotocol/inspector

# Inspector 실행
mcp-inspector python -m warroom_mcp_server.server
```

브라우저에서 `http://localhost:5173` 접속 후:
1. Tools 탭 클릭
2. `docker_list_containers` 선택
3. "Execute" 버튼 클릭

---

### Test 3: 컨테이너 상태 조회

**목표**: 특정 컨테이너 상태 확인

```python
# test_container_status.py
import asyncio
from warroom_mcp_server.docker_tools import get_container_status

async def test():
    containers = ["test-nginx", "test-postgres", "test-redis"]

    print("=== 컨테이너 상태 조회 ===")
    for container in containers:
        status = get_container_status(container)
        print(f"\n{container}:")
        print(f"  Status: {status.get('status')}")
        print(f"  Health: {status.get('health')}")
        print(f"  Image: {status.get('image')}")

asyncio.run(test())
```

```bash
python test_container_status.py
```

**예상 출력**:
```
=== 컨테이너 상태 조회 ===

test-nginx:
  Status: running
  Health: unknown
  Image: nginx:alpine

test-postgres:
  Status: running
  Health: unknown
  Image: postgres:16-alpine

test-redis:
  Status: running
  Health: unknown
  Image: redis:7-alpine
```

---

### Test 4: 로그 조회

**목표**: 컨테이너 로그 가져오기

```python
# test_logs.py
import asyncio
from warroom_mcp_server.docker_tools import get_container_logs

async def test():
    container = "test-nginx"

    print(f"=== {container} 로그 (최근 10줄) ===")
    logs = get_container_logs(container, tail=10)
    print(logs)

asyncio.run(test())
```

```bash
python test_logs.py
```

**예상 출력**:
```
=== test-nginx 로그 (최근 10줄) ===
2025-11-25T12:00:00.123Z /docker-entrypoint.sh: Configuration complete
2025-11-25T12:00:01.456Z nginx: [notice] start worker process 29
2025-11-25T12:00:01.789Z nginx: [notice] start worker process 30
```

---

### Test 5: Chaos Engineering (컨테이너 종료)

**목표**: 컨테이너를 강제로 종료하고 복구 테스트

```python
# test_chaos_recovery.py
import asyncio
import time
from warroom_mcp_server.docker_tools import (
    get_container_status,
    stop_container,
    restart_container,
    start_container
)

async def test_chaos_recovery():
    container = "test-nginx"

    print("=== Chaos Engineering Test ===\n")

    # Step 1: 초기 상태 확인
    print("1. 초기 상태:")
    status = get_container_status(container)
    print(f"   Status: {status['status']}")

    # Step 2: Chaos 트리거 (컨테이너 종료)
    print("\n2. 🔥 Chaos 트리거 - 컨테이너 종료")
    result = stop_container(container)
    print(f"   Result: {result['message'] if result['success'] else result['error']}")

    # Step 3: 종료 확인
    time.sleep(2)
    print("\n3. 종료 확인:")
    status = get_container_status(container)
    print(f"   Status: {status['status']}")

    # Step 4: 복구 시도
    print("\n4. 🔧 복구 시도 - 컨테이너 시작")
    result = start_container(container)
    print(f"   Result: {result['message'] if result['success'] else result['error']}")

    # Step 5: 복구 확인
    time.sleep(2)
    print("\n5. 복구 확인:")
    status = get_container_status(container)
    print(f"   Status: {status['status']}")

    if status['status'] == 'running':
        print("\n✅ 테스트 성공: 컨테이너가 정상적으로 복구되었습니다!")
    else:
        print("\n❌ 테스트 실패: 컨테이너 복구 실패")

asyncio.run(test_chaos_recovery())
```

```bash
python test_chaos_recovery.py
```

**예상 출력**:
```
=== Chaos Engineering Test ===

1. 초기 상태:
   Status: running

2. 🔥 Chaos 트리거 - 컨테이너 종료
   Result: Container test-nginx stopped successfully

3. 종료 확인:
   Status: exited

4. 🔧 복구 시도 - 컨테이너 시작
   Result: Container test-nginx started successfully

5. 복구 확인:
   Status: running

✅ 테스트 성공: 컨테이너가 정상적으로 복구되었습니다!
```

---

### Test 6: 자동 복구 테스트

**목표**: `docker_recover_container` 도구의 자동 재시도 기능 테스트

```python
# test_auto_recovery.py
import asyncio
from warroom_mcp_server.server import docker_recover_container, docker_trigger_chaos
from warroom_mcp_server.docker_tools import get_container_status

async def test_auto_recovery():
    container = "test-postgres"

    print("=== 자동 복구 테스트 ===\n")

    # Step 1: Chaos 트리거
    print(f"1. {container} 종료...")
    chaos_result = await docker_trigger_chaos(container)
    print(f"   {chaos_result['message']}")

    # Step 2: 자동 복구 실행
    print(f"\n2. 자동 복구 시작 (최대 3회 재시도)...")
    recovery_result = await docker_recover_container(container, max_retries=3)

    # Step 3: 결과 출력
    print(f"\n3. 복구 결과:")
    print(f"   성공 여부: {recovery_result['success']}")
    print(f"   시도 횟수: {recovery_result['attempts']}")
    print(f"   수행 작업:")
    for action in recovery_result['actions']:
        print(f"      - {action}")

    # Step 4: 최종 상태 확인
    if recovery_result['success']:
        final_status = recovery_result['final_status']
        print(f"\n   최종 상태:")
        print(f"      Status: {final_status['status']}")
        print(f"      Health: {final_status['health']}")
        print("\n✅ 자동 복구 성공!")
    else:
        print(f"\n❌ 자동 복구 실패: {recovery_result.get('error')}")

asyncio.run(test_auto_recovery())
```

```bash
python test_auto_recovery.py
```

**예상 출력**:
```
=== 자동 복구 테스트 ===

1. test-postgres 종료...
   Container test-postgres stopped successfully

2. 자동 복구 시작 (최대 3회 재시도)...

3. 복구 결과:
   성공 여부: True
   시도 횟수: 1
   수행 작업:
      - Checked status: exited
      - Attempt 1: Container test-postgres started successfully

   최종 상태:
      Status: running
      Health: unknown

✅ 자동 복구 성공!
```

---

## 🎬 실전 시나리오 테스트

### Scenario 1: 전체 워크플로우 테스트

**목표**: 감지 → 복구 → 검증 전체 프로세스 테스트

```python
# test_full_workflow.py
import asyncio
import time
from datetime import datetime
from warroom_mcp_server.server import (
    docker_list_containers,
    docker_trigger_chaos,
    docker_recover_container,
    docker_get_logs
)

async def full_workflow_test():
    print("=" * 60)
    print("🚨 WAR ROOM - 전체 워크플로우 테스트")
    print("=" * 60)

    # Phase 1: 모니터링
    print("\n[Phase 1] 📊 시스템 모니터링")
    print(f"Timestamp: {datetime.now().isoformat()}")

    containers = await docker_list_containers()
    print(f"\n발견된 컨테이너: {len(containers)}개")
    for c in containers:
        if 'error' not in c:
            status_icon = "🟢" if c['status'] == 'running' else "🔴"
            print(f"  {status_icon} {c['name']}: {c['status']}")

    # Phase 2: Chaos 트리거
    target = "test-nginx"
    print(f"\n[Phase 2] 💀 Chaos Engineering - {target} 종료")

    chaos_result = await docker_trigger_chaos(target)
    print(f"  Result: {chaos_result['message']}")

    time.sleep(2)

    # Phase 3: 장애 감지
    print(f"\n[Phase 3] 🔍 장애 감지")
    containers = await docker_list_containers()

    failed_containers = [
        c for c in containers
        if 'error' not in c and c['status'] != 'running'
    ]

    if failed_containers:
        print(f"  ⚠️  {len(failed_containers)}개의 장애 컨테이너 발견:")
        for c in failed_containers:
            print(f"     - {c['name']}: {c['status']}")

    # Phase 4: 로그 분석
    print(f"\n[Phase 4] 📜 로그 분석")
    logs = await docker_get_logs(target, tail=5)
    print(f"  최근 로그 (5줄):")
    for line in logs.split('\n')[:5]:
        if line.strip():
            print(f"     {line}")

    # Phase 5: 자동 복구
    print(f"\n[Phase 5] 🔧 자동 복구 실행")
    recovery_result = await docker_recover_container(target, max_retries=3)

    print(f"  복구 상태: {'성공' if recovery_result['success'] else '실패'}")
    print(f"  시도 횟수: {recovery_result['attempts']}")

    # Phase 6: 복구 검증
    print(f"\n[Phase 6] ✅ 복구 검증")
    time.sleep(2)

    containers = await docker_list_containers()
    target_container = next(
        (c for c in containers if c.get('name') == target),
        None
    )

    if target_container and target_container['status'] == 'running':
        print(f"  ✅ {target} 정상 작동 중")
    else:
        print(f"  ❌ {target} 복구 실패")

    # Summary
    print("\n" + "=" * 60)
    print("📊 테스트 요약")
    print("=" * 60)
    print(f"전체 소요 시간: ~10초")
    print(f"장애 감지: ✅")
    print(f"자동 복구: {'✅' if recovery_result['success'] else '❌'}")
    print(f"시스템 상태: {'🟢 정상' if target_container['status'] == 'running' else '🔴 비정상'}")
    print("=" * 60)

asyncio.run(full_workflow_test())
```

```bash
python test_full_workflow.py
```

**예상 출력**:
```
============================================================
🚨 WAR ROOM - 전체 워크플로우 테스트
============================================================

[Phase 1] 📊 시스템 모니터링
Timestamp: 2025-11-25T12:34:56.789

발견된 컨테이너: 3개
  🟢 test-nginx: running
  🟢 test-postgres: running
  🟢 test-redis: running

[Phase 2] 💀 Chaos Engineering - test-nginx 종료
  Result: Container test-nginx stopped successfully

[Phase 3] 🔍 장애 감지
  ⚠️  1개의 장애 컨테이너 발견:
     - test-nginx: exited

[Phase 4] 📜 로그 분석
  최근 로그 (5줄):
     2025-11-25T12:34:00 nginx started
     2025-11-25T12:34:01 worker process started

[Phase 5] 🔧 자동 복구 실행
  복구 상태: 성공
  시도 횟수: 1

[Phase 6] ✅ 복구 검증
  ✅ test-nginx 정상 작동 중

============================================================
📊 테스트 요약
============================================================
전체 소요 시간: ~10초
장애 감지: ✅
자동 복구: ✅
시스템 상태: 🟢 정상
============================================================
```

---

### Scenario 2: 다중 장애 테스트

**목표**: 여러 컨테이너가 동시에 다운되었을 때 복구 테스트

```python
# test_multiple_failures.py
import asyncio
from warroom_mcp_server.server import (
    docker_trigger_chaos,
    docker_recover_container,
    docker_list_containers
)

async def test_multiple_failures():
    print("=== 다중 장애 복구 테스트 ===\n")

    targets = ["test-nginx", "test-postgres", "test-redis"]

    # Step 1: 모든 컨테이너 종료
    print("1. 모든 컨테이너 종료 (Chaos)...")
    for target in targets:
        result = await docker_trigger_chaos(target)
        print(f"   {target}: {result['message']}")

    # Step 2: 상태 확인
    print("\n2. 현재 상태:")
    containers = await docker_list_containers()
    for c in containers:
        if c['name'] in targets:
            print(f"   {c['name']}: {c['status']}")

    # Step 3: 순차 복구
    print("\n3. 순차적 복구 시작...")
    recovery_results = []

    for target in targets:
        print(f"\n   복구 중: {target}")
        result = await docker_recover_container(target)
        recovery_results.append({
            'container': target,
            'success': result['success'],
            'attempts': result['attempts']
        })
        print(f"      결과: {'✅ 성공' if result['success'] else '❌ 실패'}")
        print(f"      시도: {result['attempts']}회")

    # Step 4: 최종 결과
    print("\n4. 최종 결과:")
    success_count = sum(1 for r in recovery_results if r['success'])
    print(f"   성공: {success_count}/{len(targets)}")

    if success_count == len(targets):
        print("\n✅ 모든 컨테이너 복구 성공!")
    else:
        print(f"\n⚠️  {len(targets) - success_count}개 컨테이너 복구 실패")

asyncio.run(test_multiple_failures())
```

```bash
python test_multiple_failures.py
```

---

## ❗ 문제 해결

### 문제 1: Docker 연결 실패

**증상**:
```
Error: Docker not available
```

**해결**:
```bash
# Docker Desktop 실행 확인
docker ps

# Docker 서비스 재시작 (Windows)
# Docker Desktop 우클릭 → Restart

# Docker 권한 확인
docker run hello-world
```

---

### 문제 2: 컨테이너를 찾을 수 없음

**증상**:
```
Container test-nginx not found
```

**해결**:
```bash
# 실행 중인 컨테이너 확인
docker ps -a

# 테스트 컨테이너 다시 실행
docker run -d --name test-nginx nginx:alpine
```

---

### 문제 3: Import 에러

**증상**:
```
ModuleNotFoundError: No module named 'warroom_mcp_server'
```

**해결**:
```bash
# 의존성 재설치
cd i:/AI-SRE-Squad/warroom-mcp
powershell -Command "& 'C:\Users\정주환\.local\bin\uv.exe' sync"

# Python 경로 확인
python -c "import sys; print(sys.path)"
```

---

### 문제 4: 복구 실패

**증상**:
```
Recovery failed after 3 attempts
```

**해결**:
```bash
# 컨테이너 로그 확인
docker logs test-nginx

# 컨테이너 수동 재시작
docker restart test-nginx

# 이미지 문제 확인
docker inspect test-nginx
```

---

## 🎯 테스트 체크리스트

완료한 항목에 ✅ 체크하세요:

### 기본 테스트
- [ ] 서버 시작 확인
- [ ] 컨테이너 목록 조회
- [ ] 컨테이너 상태 조회
- [ ] 로그 조회

### Docker 도구 테스트
- [ ] Chaos Engineering (종료)
- [ ] 수동 복구
- [ ] 자동 복구 (재시도)

### 실전 시나리오
- [ ] 전체 워크플로우
- [ ] 다중 장애 복구
- [ ] 성능 테스트 (선택)

### 정리
- [ ] 테스트 컨테이너 삭제
- [ ] 결과 문서화

---

## 🧹 테스트 후 정리

```bash
# 테스트 컨테이너 정리
docker stop test-nginx test-postgres test-redis
docker rm test-nginx test-postgres test-redis

# 확인
docker ps -a | grep test-
# 아무것도 출력되지 않아야 함
```

---

## 📝 다음 단계

테스트를 모두 완료했다면:

1. **Streamlit UI 추가** - 시각적 대시보드
2. **Claude 통합** - 자연어로 제어
3. **실제 인프라 연동** - 프로덕션 테스트

---

**Happy Testing! 🚀**

*문제가 발생하면 이슈를 남겨주세요!*
