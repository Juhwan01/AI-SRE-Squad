# 🚀 War Room 2.0 MVP - Quick Start

## 설치 및 실행 (3분 완성)

### 1️⃣ 의존성 설치
```bash
uv sync
```

### 2️⃣ 빠른 데모 실행
```bash
uv run python quick_demo.py
```

이것만 하면 끝입니다! 🎉

---

## 📖 상세 사용법

### 대화형 모드
```bash
uv run python -m src.war_room
```

대화형 모드에서 사용 가능한 명령어:
- `status` - 현재 활성화된 MCP 서버 목록 확인
- `optimize` - 미사용 서버 자동 제거
- `exit` - 종료
- 기타 입력 - 에러 로그로 처리하여 자동 분석

### 자동 데모 시나리오
```bash
uv run python -m src.war_room demo
```

3가지 시나리오 자동 실행:
1. Docker 컨테이너 문제
2. PostgreSQL 데이터베이스 문제
3. Redis 캐시 문제

### 테스트 실행
```bash
uv run python test_mvp.py
```

4가지 테스트 수행:
1. MCP Catalog 검색
2. 문제 분석기
3. Dynamic MCP Manager
4. 전체 플로우 (End-to-End)

---

## 💡 사용 예시

### 예시 1: Python 코드로 사용

```python
from src.war_room import WarRoom

# War Room 초기화
war_room = WarRoom()

# 장애 처리
error = "Error: Cannot connect to the Docker daemon"
result = war_room.handle_incident(error, auto_approve=True)

# 상태 확인
war_room.show_status()

# 종료
war_room.close()
```

### 예시 2: 대화형 모드

```bash
$ uv run python -m src.war_room

War Room 2.0 - Dynamic MCP Engine
============================================================

대화형 모드 시작
명령어:
  status  - 현재 상태 확인
  optimize - 시스템 최적화
  exit    - 종료
  기타    - 에러 로그로 인식하여 처리

> Error: ECONNREFUSED 127.0.0.1:6379

============================================================
🔍 문제 분석 중...
============================================================

📌 감지된 키워드: redis, cache

🔎 MCP Catalog에서 도구 검색 중...

✨ 최적 후보 발견:
   이름: @modelcontextprotocol/server-redis
   설명: MCP server for Redis operations
   점수: 75.0/100

⚙️ MCP 서버 설치 중...
✅ 서버 추가 완료: @modelcontextprotocol/server-redis

✅ 장애 처리 완료!
   사용된 도구: @modelcontextprotocol/server-redis

> status

============================================================
📊 War Room 2.0 상태
============================================================

활성화된 MCP 서버: 1개

  • @modelcontextprotocol/server-redis
    버전: 1.0.0
    상태: installed
    사용 횟수: 1회

통계:
  • 총 서버 수: 1
  • 총 사용 횟수: 1
  • 가장 많이 사용: @modelcontextprotocol/server-redis

> exit
```

---

## 🎯 핵심 원리

```
장애 발생
    ↓
【1단계】 문제 분석
   - 패턴 매칭으로 키워드 추출
   - 예: "docker", "postgres", "redis"
    ↓
【2단계】 MCP Catalog 검색
   - NPM Registry에서 "mcp {keyword}" 검색
   - 후보 발견 및 평가
    ↓
【3단계】 후보 평가
   - Official (40점)
   - Downloads (25점)
   - Last Updated (20점)
   - Capabilities (15점)
    ↓
【4단계】 사용자 승인
   - auto_approve=True면 자동 승인
   - False면 사용자에게 확인 요청
    ↓
【5단계】 서버 추가
   - 메타데이터 저장
   - .war-room/mcp-config.json에 기록
    ↓
✅ 준비 완료!
```

---

## 📊 현재 MVP 범위

### ✅ 구현됨
- [x] NPM Registry 기반 MCP 서버 검색
- [x] 패턴 매칭 기반 문제 분석
- [x] 후보 평가 및 점수 계산 시스템
- [x] 런타임 서버 추가/제거
- [x] 사용 통계 및 최적화
- [x] 대화형 인터페이스
- [x] 데모 시나리오

### 🔜 향후 구현 예정
- [ ] 실제 MCP 서버 프로세스 실행
- [ ] AI 기반 심층 분석 (Anthropic API)
- [ ] 보안 샌드박스 테스트
- [ ] 사용 패턴 학습 및 예측적 로딩
- [ ] 웹 UI 대시보드

---

## 🐛 문제 해결

### uv sync 실패
```bash
# Python 버전 확인 (3.10 이상 필요)
python --version

# uv 업데이트
uv self update

# 캐시 정리 후 재시도
uv cache clean
uv sync
```

### Import 에러
```bash
# 가상환경이 활성화되었는지 확인
uv run python -c "import sys; print(sys.prefix)"

# 패키지 재설치
uv sync --reinstall
```

---

## 📚 추가 자료

- [README.md](README.md) - 전체 문서
- [src/](src/) - 소스 코드
- [test_mvp.py](test_mvp.py) - 테스트 스크립트

---

**War Room 2.0**: Zero-Configuration Intelligence 🚀
