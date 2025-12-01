# War Room 2.0 - 프로젝트 구조

## 📁 전체 구조

```
SRE/
├── src/                          # 핵심 소스 코드
│   ├── __init__.py
│   ├── container_orchestrator.py    # Docker 컨테이너 풀 관리
│   ├── tier_manager.py              # 티어 기반 서버 관리
│   ├── integrated_war_room.py       # 통합 메인 시스템
│   ├── mcp_catalog.py               # MCP Catalog 검색
│   └── problem_analyzer.py          # 문제 분석기
│
├── tests/                        # 테스트 스위트
│   ├── test_quick.py                # 빠른 자동 테스트 (추천)
│   ├── test_no_docker.py            # Docker 없이 테스트
│   └── test_integrated_mvp.py       # 통합 테스트
│
├── docker/                       # Docker 설정
│   ├── Dockerfile.manager           # War Room Manager 이미지
│   ├── Dockerfile.mcp-base          # MCP 서버 베이스 이미지
│   ├── Dockerfile.test-mcp          # 테스트용 MCP 이미지
│   ├── docker-compose.yml           # 전체 오케스트레이션
│   └── entrypoint.sh                # MCP 서버 엔트리포인트
│
├── scripts/                      # 유틸리티 스크립트
│   ├── build_test_images.bat        # 테스트 이미지 빌드 (Windows)
│   └── build_test_images.sh         # 테스트 이미지 빌드 (Linux/Mac)
│
├── docs/                         # 문서
│   ├── MVP_DESIGN.md                # 상세 아키텍처 설계
│   ├── QUICKSTART.md                # 빠른 시작 가이드
│   ├── AUTO_CONTAINER_MANAGEMENT.md # 자동 컨테이너 관리 가이드
│   └── DOCKER_GUIDE.md              # Docker 실행 가이드
│
├── README.md                     # 메인 문서 (프로젝트 개요)
├── PROJECT_STRUCTURE.md          # 이 파일 (구조 설명)
├── pyproject.toml                # 프로젝트 설정 (uv)
└── uv.lock                       # 의존성 잠금 파일

```

## 🎯 핵심 파일 설명

### 소스 코드 (src/)

#### 1. `integrated_war_room.py` ⭐ (메인 시스템)
```python
from src.integrated_war_room import IntegratedWarRoom

# 모든 기능이 통합된 메인 시스템
war_room = IntegratedWarRoom()
await war_room.handle_incident(error_log)
```

**역할:**
- 모든 컴포넌트 통합
- End-to-end 장애 처리 워크플로우
- 대화형 CLI 제공

#### 2. `container_orchestrator.py` (컨테이너 관리)
```python
from src.container_orchestrator import ContainerPoolOrchestrator

# Docker 컨테이너 생명주기 관리
orchestrator = ContainerPoolOrchestrator()
await orchestrator.start_container("mcp-server-name")
```

**역할:**
- Docker 컨테이너 시작/종료
- Idle 타임아웃 자동 관리
- 메모리 압박 감지 및 대응

#### 3. `tier_manager.py` (티어 관리)
```python
from src.tier_manager import TierManager

# 사용 패턴 기반 서버 관리
tier_mgr = TierManager()
tier_mgr.register_server("server-name", "package", "1.0.0")
tier_mgr.adjust_tiers()  # 자동 티어 조정
```

**역할:**
- 3단계 티어 시스템 (Hot/Warm/Cold)
- 사용 패턴 학습 및 자동 조정
- 이미지 캐싱 전략

#### 4. `mcp_catalog.py` (MCP 검색)
```python
from src.mcp_catalog import MCPCatalogSync

# NPM Registry에서 MCP 서버 검색
catalog = MCPCatalogSync()
servers = catalog.search_servers(["docker"], limit=5)
```

**역할:**
- NPM Registry 실시간 검색
- 후보 평가 및 점수 계산

#### 5. `problem_analyzer.py` (문제 분석)
```python
from src.problem_analyzer import ProblemAnalyzer

# 에러 로그에서 키워드 추출
analyzer = ProblemAnalyzer()
keywords = analyzer.analyze_problem(error_log)
```

**역할:**
- 패턴 기반 문제 분석
- 키워드 추출

---

### 테스트 (tests/)

#### 1. `test_quick.py` ⭐ (추천)
```bash
# 빠른 테스트 (Docker 불필요)
uv run python tests/test_quick.py quick

# Docker 포함 테스트
uv run python tests/test_quick.py docker

# 전체 시나리오 테스트
uv run python tests/test_quick.py full
```

**특징:**
- 자동 실행 (사용자 입력 불필요)
- 3가지 모드 지원
- 가장 빠르고 간편

#### 2. `test_no_docker.py`
```bash
uv run python tests/test_no_docker.py
```

**특징:**
- Docker 없이 모든 로직 테스트
- Mock 사용
- CI/CD에 적합

#### 3. `test_integrated_mvp.py`
```bash
uv run python tests/test_integrated_mvp.py
```

**특징:**
- 상세한 통합 테스트
- 각 컴포넌트 개별 테스트

---

### Docker (docker/)

#### 1. `docker-compose.yml` ⭐
```bash
cd docker
docker-compose up -d
```

**포함 내용:**
- War Room Manager 서비스
- 네트워크 설정
- 볼륨 설정

#### 2. `Dockerfile.manager`
War Room 관리자 컨테이너 이미지

#### 3. `Dockerfile.mcp-base`
MCP 서버용 베이스 이미지

#### 4. `Dockerfile.test-mcp`
테스트용 간단한 MCP 이미지

---

### 스크립트 (scripts/)

#### 1. `build_test_images.bat` (Windows)
```bash
.\scripts\build_test_images.bat
```

**역할:**
- 테스트용 MCP 서버 이미지 빌드
- 여러 이미지 태그 생성

#### 2. `build_test_images.sh` (Linux/Mac)
```bash
bash scripts/build_test_images.sh
```

동일한 기능 (Linux/Mac용)

---

### 문서 (docs/)

#### 1. `QUICKSTART.md` ⭐
빠른 시작 가이드
- 설치 방법
- 실행 방법
- 사용 예시

#### 2. `MVP_DESIGN.md`
상세 아키텍처 설계
- 시스템 구조
- 컴포넌트 설명
- 성능 지표

#### 3. `AUTO_CONTAINER_MANAGEMENT.md`
자동 컨테이너 관리 가이드
- 자동 시작/종료 설명
- 설정 방법
- 실제 사용 예시

#### 4. `DOCKER_GUIDE.md`
Docker 실행 가이드
- Docker Desktop 설치
- 트러블슈팅

---

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
uv sync
```

### 2. 테스트 이미지 빌드 (한 번만)
```bash
# Windows
.\scripts\build_test_images.bat

# Linux/Mac
bash scripts/build_test_images.sh
```

### 3. 테스트 실행
```bash
# 빠른 테스트
uv run python tests/test_quick.py quick

# 전체 테스트 (Docker 필요)
uv run python tests/test_quick.py full
```

### 4. 실제 사용
```python
from src.integrated_war_room import IntegratedWarRoom
import asyncio

async def main():
    war_room = IntegratedWarRoom()
    await war_room.start()

    result = await war_room.handle_incident(
        "Error: Docker daemon error",
        auto_approve=True
    )

    print(result)
    await war_room.shutdown()

asyncio.run(main())
```

---

## 📊 파일 통계

### 코드
- **Python 파일**: 8개
- **총 코드 라인**: ~1,500줄
- **핵심 소스**: 5개 (src/)
- **테스트**: 3개 (tests/)

### 문서
- **Markdown 파일**: 6개
- **총 문서 라인**: ~1,000줄

### Docker
- **Dockerfile**: 3개
- **설정 파일**: 2개

---

## 🧹 정리된 내용

### 삭제된 파일 (레거시)
- ❌ `war_room.py` (v0.1 메인, 레거시)
- ❌ `dynamic_mcp_manager.py` (v0.1 관리자, 레거시)
- ❌ `quick_demo.py` (중복)
- ❌ `test_mvp.py` (v0.1 테스트)
- ❌ `test_step_by_step.py` (중복)
- ❌ `README.md` (v0.1, v0.2로 대체)
- ❌ `QUICKSTART.md` (루트, docs/로 이동)
- ❌ `MVP_SUMMARY.md` (v0.1 요약)
- ❌ `NOTION_DOC.md` (이전 문서)

### 정리된 구조
- ✅ 테스트 파일 → `tests/` 디렉토리
- ✅ 빌드 스크립트 → `scripts/` 디렉토리
- ✅ 모든 문서 → `docs/` 디렉토리
- ✅ README_MVP_V2.md → README.md

---

## 🎯 핵심 원칙

1. **간결성**: 필요한 파일만 유지
2. **명확성**: 각 파일의 역할이 명확
3. **접근성**: 중요한 파일은 루트에
4. **조직화**: 관련 파일은 같은 디렉토리에

---

**War Room 2.0 v0.2.0**: 깔끔하고 체계적인 프로젝트 구조
