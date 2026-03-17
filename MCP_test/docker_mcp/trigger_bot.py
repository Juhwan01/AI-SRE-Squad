import docker
import json
import time
import threading
import logging
import sys
from datetime import datetime
from test_agent import run_sre_agent  # LangGraph 에이전트 연동

# 1. 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SRE-TriggerBot")

class DockerSREBot:
    def __init__(self):
        # 윈도우 Named Pipe 및 일반 환경 대응
        try:
            self.client = docker.DockerClient(base_url='npipe:////./pipe/docker_engine')
            self.client.ping()
            logger.info("✅ Docker 엔진 연결 성공 (Named Pipe).")
        except Exception:
            try:
                self.client = docker.from_env()
                self.client.ping()
                logger.info("✅ Docker 엔진 연결 성공 (Env).")
            except Exception as e:
                logger.error(f"❌ Docker 연결 실패: {e}")
                sys.exit(1)

        # 감시 키워드 설정
        self.error_keywords = ["ERROR", "EXCEPTION", "FATAL", "500", "CRITICAL", "TIMEOUT"]
        self.monitored_containers = set()

    # --- [Layer 1 & 3 Helper] 로그 감시 스레드 실행 ---
    def start_log_tailing(self, container):
        if container.id in self.monitored_containers:
            return
        
        self.monitored_containers.add(container.id)
        
        def tail_logic():
            try:
                logger.info(f"🔍 [로그 감시 시작] {container.name}")
                # tail=0: 봇 시작 이후 로그만 감시
                for line in container.logs(stream=True, follow=True, tail=0):
                    log_content = line.decode('utf-8', errors='ignore').strip()
                    upper_log = log_content.upper()
                    
                    for keyword in self.error_keywords:
                        if keyword in upper_log:
                            self.report_incident("Log-based", container.name, f"키워드 발견: {keyword} (원본: {log_content})")
            except Exception as e:
                logger.error(f"로그 분석 중단 ({container.name}): {e}")
            finally:
                if container.id in self.monitored_containers:
                    self.monitored_containers.remove(container.id)

        threading.Thread(target=tail_logic, daemon=True).start()

    # --- [Layer 1] Docker Events (상태 변화 및 신규 컨테이너) ---
    def watch_events(self):
        logger.info("📡 [Layer 1] 이벤트 모니터링 가동 중...")
        for event in self.client.events(decode=True):
            status = event.get('status')
            container_name = event.get('Actor', {}).get('Attributes', {}).get('name')
            container_id = event.get('id')

            # 장애 이벤트 감지
            if status in ['die', 'oom', 'kill', 'health_status: unhealthy']:
                self.report_incident("Event-based", container_name, f"시스템 상태: {status}")
            
            # 새로 시작된 컨테이너가 있으면 즉시 로그 감시 연결
            if status == 'start':
                try:
                    new_container = self.client.containers.get(container_id)
                    self.start_log_tailing(new_container)
                except: pass

    # --- [Layer 2] Health Check (주기적 순회) ---
    def watch_health(self):
        logger.info("🏥 [Layer 2] 헬스체크 모니터링 가동 중...")
        while True:
            try:
                for container in self.client.containers.list():
                    container.reload() 
                    health_status = container.attrs.get('State', {}).get('Health', {}).get('Status')
                    if health_status == 'unhealthy':
                        self.report_incident("Health-based", container.name, "Health Check Failed")
            except Exception as e:
                logger.error(f"헬스체크 루프 에러: {e}")
            time.sleep(5)

    # --- 공통 리포팅 및 LangGraph 에이전트 호출 ---
    def report_incident(self, layer, container, reason):
        incident_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report = {
            "timestamp": incident_time,
            "layer": layer,
            "target": container,
            "details": reason
        }
        
        logger.warning(f"🚨 [장애 탐지] {json.dumps(report, indent=2, ensure_ascii=False)}")
        
        # LangGraph 에이전트에게 분석 요청 (비동기 스레드 실행)
        threading.Thread(target=run_sre_agent, args=(report,), daemon=True).start()

    def start_monitoring(self):
        # 현재 실행 중인 컨테이너 모두 감시 시작
        for container in self.client.containers.list():
            self.start_log_tailing(container)

        # 각 감시 레이어 실행
        threading.Thread(target=self.watch_events, daemon=True).start()
        threading.Thread(target=self.watch_health, daemon=True).start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("SRE 관측 시스템 종료...")

if __name__ == "__main__":
    bot = DockerSREBot()
    bot.start_monitoring()