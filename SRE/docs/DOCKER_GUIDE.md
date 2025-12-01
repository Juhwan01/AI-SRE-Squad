# Docker Desktop 실행 가이드

## 🚀 간단한 방법

### 1. Docker Desktop 실행
- Windows 시작 메뉴에서 "Docker Desktop" 검색
- 앱 실행

### 2. 대기 (20-30초)
Docker Desktop 창 하단에서 확인:
- ❌ "Starting..." → 대기 중
- ✅ "Docker Desktop is running" → 준비 완료

또는 작업 표시줄 아이콘 확인:
- 🟡 노란색/회색 → 시작 중
- 🟢 초록색 → 실행 중

### 3. 확인
터미널에서 실행:
```bash
docker ps
```

**성공 예시:**
```
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
(비어있어도 정상 - 에러만 안 나면 OK!)
```

**실패 예시:**
```
Error: Cannot connect to the Docker daemon
→ Docker Desktop이 아직 시작 중이거나 꺼져있음
```

## ✅ War Room 2.0 테스트 실행

Docker Desktop이 실행되면:

```bash
# 전체 테스트 (Docker 포함)
uv run python test_quick.py docker

# 또는 완전한 시나리오 테스트
uv run python test_quick.py full
```

## 🔧 트러블슈팅

### Q: Docker Desktop을 켰는데도 에러가 나요
**A:** 완전히 시작될 때까지 기다리세요 (30초~1분)
```bash
# 상태 확인
docker info
```

### Q: "Docker Desktop is not running" 메시지
**A:**
1. Docker Desktop 앱을 종료
2. 다시 시작
3. 1분 정도 대기

### Q: WSL 관련 에러
**A:** Docker Desktop 설정에서:
- Settings → General
- "Use WSL 2 based engine" 확인
- 필요시 WSL 업데이트

## 📝 참고

War Room 2.0은:
- **Docker 없이도** 핵심 기능 테스트 가능 (검색, 티어 관리, 분석)
- **Docker 있으면** 실제 컨테이너 시작/종료 테스트 가능

Docker Desktop은 **백그라운드에서 계속 실행**되어야 합니다.
