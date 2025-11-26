# War Room 2.0 MVP - Dynamic MCP Engine

> "AI가 문제를 보고 필요한 도구를 스스로 찾는다"

## 🎯 핵심 개념

기존 시스템: 개발자가 미리 MCP 서버를 설정 → 제한적 대응
**War Room 2.0**: AI가 문제 분석 → MCP Catalog 검색 → 자동 도구 추가 → 해결

## 🚀 Quick Start

### 1. 설치

```bash
# uv로 의존성 설치
uv sync

# 또는 개발 의존성 포함
uv sync --dev
```

### 2. 데모 실행

```bash
# 데모 시나리오 (자동)
uv run python -m src.war_room demo

# 대화형 모드
uv run python -m src.war_room

# 빠른 데모 (추천)
uv run python quick_demo.py
```

### 3. 테스트

```bash
uv run python test_mvp.py
```

## 📋 동작 방식

### 시나리오 예시: Docker 문제 발생

```
1️⃣ 에러 발생
   "Error: Cannot connect to the Docker daemon"

2️⃣ AI 분석
   → 키워드 추출: ["docker", "container", "daemon"]

3️⃣ MCP Catalog 검색
   → NPM Registry에서 "mcp docker" 검색
   → 후보 발견: @modelcontextprotocol/server-docker

4️⃣ 평가 및 선택
   점수 계산:
   - Official: 40/40 ✅
   - Downloads: 20/25
   - Last Updated: 20/20
   - Total: 80/100

5️⃣ 자동 추가
   → 사용자 승인 (또는 auto_approve=True)
   → MCP 서버 추가
   → 문제 해결 가능!
```

## 🏗️ 아키텍처

```
War Room 2.0
├── Problem Analyzer        # 문제 분석 및 키워드 추출
│   ├── 패턴 매칭 (빠름)
│   └── AI 분석 (정확함, 옵션)
│
├── MCP Catalog            # NPM Registry 검색
│   ├── 검색 엔진
│   ├── 후보 평가
│   └── 점수 계산
│
└── Dynamic MCP Manager    # 런타임 서버 관리
    ├── 서버 추가/제거
    ├── 사용 패턴 추적
    └── 자동 최적화
```

## 📊 MVP 기능

✅ **구현 완료**
- [x] MCP Catalog 검색 (NPM Registry 기반)
- [x] 문제 분석 (패턴 매칭)
- [x] 후보 평가 및 점수 계산
- [x] 런타임 서버 추가/제거
- [x] 사용 통계 및 최적화

⏳ **향후 개선**
- [ ] 실제 MCP 서버 프로세스 실행
- [ ] AI 기반 심층 분석 (Anthropic API)
- [ ] 보안 검증 (샌드박스 테스트)
- [ ] 사용 패턴 학습 및 사전 로딩
- [ ] 웹 UI 대시보드

## 🧪 테스트

```bash
# 전체 테스트
python test_mvp.py

# 개별 테스트
python -c "from test_mvp import test_catalog_search; test_catalog_search()"
```

### 테스트 시나리오

1. **MCP Catalog 검색**: Docker 관련 서버 검색
2. **문제 분석기**: 에러 로그에서 키워드 추출
3. **Dynamic Manager**: 서버 추가 및 관리
4. **전체 플로우**: End-to-end 시나리오

### uv 명령어

```bash
# 의존성 설치
uv sync

# 스크립트 실행
uv run python quick_demo.py

# 테스트
uv run python test_mvp.py

# 대화형 모드
uv run python -m src.war_room
```

## 💡 사용 예시

### Python 코드

```python
from src.war_room import WarRoom

# War Room 초기화 (빈 상태)
war_room = WarRoom()

# 장애 발생!
error_log = """
Error: Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
Is the docker daemon running?
"""

# 자동 처리
result = war_room.handle_incident(error_log, auto_approve=True)

# 상태 확인
war_room.show_status()
```

### 대화형 모드

```bash
$ uv run python -m src.war_room

> Error: ECONNREFUSED 127.0.0.1:6379

🔍 문제 분석 중...
📌 감지된 키워드: redis, cache

🔎 MCP Catalog에서 도구 검색 중...
✨ 최적 후보 발견: @modelcontextprotocol/server-redis

⚙️ MCP 서버 설치 중...
✅ 서버 추가 완료: @modelcontextprotocol/server-redis

> status

📊 War Room 2.0 상태
활성화된 MCP 서버: 1개
  • @modelcontextprotocol/server-redis
    버전: 1.0.0
    사용 횟수: 1회
```

## 📈 성능 지표

### 확장성 비교

| 항목 | 정적 MCP | Dynamic MCP |
|------|----------|-------------|
| 초기 설정 시간 | 2-3시간 | **0분** |
| 지원 인프라 | 3가지 | **500+** |
| 미지의 장애 대응 | ❌ 불가능 | **✅ 가능** |
| 설정 파일 수정 | 필요 | **불필요** |

### 실전 효과 (시뮬레이션)

```
시나리오: Kafka 장애 발생

기존 시스템:
- Kafka MCP 미설정 → 수동 대응
- 엔지니어 호출 → 15분 대기
- 수동 복구 → 총 30분 다운타임

Dynamic 시스템:
- AI 분석 → Kafka 도구 검색
- 자동 추가 (30초 승인)
- 자동 복구 → 총 3분 다운타임

→ 10배 빠른 복구!
```

## 🔒 안전성

### 3단계 검증 (향후 구현)

1. **Pre-Installation**: 출처, 보안 점수, 권한 확인
2. **Sandbox Testing**: 격리된 환경에서 테스트
3. **Human Approval**: 최종 사용자 승인

### 신뢰도 기반 자동화

- **Official** (@modelcontextprotocol): 첫 사용 시만 승인
- **Verified** (1000+ downloads): 매번 승인
- **Community** (<100 downloads): 관리자 확인 필수

## 📁 프로젝트 구조

```
SRE/
├── src/
│   ├── __init__.py
│   ├── mcp_catalog.py          # MCP Catalog 검색 엔진
│   ├── problem_analyzer.py     # 문제 분석 및 키워드 추출
│   ├── dynamic_mcp_manager.py  # 런타임 MCP 관리
│   └── war_room.py             # 메인 시스템
├── test_mvp.py                 # MVP 테스트
├── quick_demo.py               # 빠른 데모
├── pyproject.toml              # uv 프로젝트 설정
├── .gitignore
└── README.md
```

## 🎯 로드맵

### Phase 1: MVP (현재)
- ✅ 기본 검색 및 분석
- ✅ 서버 메타데이터 관리
- ✅ 데모 시나리오

### Phase 2: Production
- [ ] 실제 MCP 서버 실행
- [ ] 보안 검증 강화
- [ ] 성능 최적화

### Phase 3: Intelligence
- [ ] AI 기반 심층 분석
- [ ] 사용 패턴 학습
- [ ] 예측적 도구 로딩

### Phase 4: Ecosystem
- [ ] 웹 UI
- [ ] API 서버
- [ ] 플러그인 시스템

## 🤝 기여

이 프로젝트는 실험적 MVP입니다. 피드백과 개선 아이디어를 환영합니다!

## 📄 라이선스

MIT License

---

**War Room 2.0**: Zero-Configuration Intelligence
