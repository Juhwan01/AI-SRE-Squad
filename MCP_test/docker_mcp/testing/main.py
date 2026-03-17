from fastapi import FastAPI
import logging

app = FastAPI()
logger = logging.getLogger("SRE-Test")

# 헬스체크 상태를 강제로 바꿀 플래그
is_active = True

@app.get("/docs") # Docker HEALTHCHECK가 바라보는 곳
def health_check():
    if not is_active:
        # 이 응답이 500이 되면 Docker가 Unhealthy로 판정함
        raise Exception("Health Check Failed: Service Inactive")
    return {"status": "ok"}

@app.get("/make-unhealthy")
def fail():
    global is_active
    is_active = False # 이제부터 /docs 호출 시 에러 발생
    logger.error("🔥 [ALERT] User triggered manual failure!")
    raise Exception("인위적인 실패 유도")