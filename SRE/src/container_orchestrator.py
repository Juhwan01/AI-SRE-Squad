"""
Container Pool Orchestrator
Docker 컨테이너 기반 MCP 서버 생명주기 관리
"""

import asyncio
import docker
from docker.models.containers import Container
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContainerStatus:
    """컨테이너 상태 정보"""
    container_id: str
    mcp_server_name: str
    status: str  # "starting", "running", "idle", "stopped"
    started_at: datetime
    last_used_at: datetime
    memory_usage_mb: int = 0
    auto_stop_at: Optional[datetime] = None

    def is_idle(self) -> bool:
        """Idle 상태 확인"""
        return self.status == "idle"

    def should_stop(self) -> bool:
        """자동 종료 시간 도달 확인"""
        if self.auto_stop_at is None:
            return False
        return datetime.now() >= self.auto_stop_at

    def update_last_used(self):
        """마지막 사용 시간 업데이트"""
        self.last_used_at = datetime.now()
        # Idle 타임아웃 재설정 (30분)
        self.auto_stop_at = datetime.now() + timedelta(minutes=30)
        self.status = "running"


@dataclass
class ContainerPoolConfig:
    """컨테이너 풀 설정"""
    max_concurrent_containers: int = 10
    idle_timeout_minutes: int = 30
    max_memory_percent: float = 80.0
    network_name: str = "war-room-network"
    image_prefix: str = "mcp"
    base_memory_limit: str = "200m"
    base_cpu_quota: float = 0.5


class ContainerPoolOrchestrator:
    """
    Docker 컨테이너 풀 오케스트레이터

    주요 기능:
    - MCP 서버 컨테이너 동적 시작/종료
    - Idle 타임아웃 기반 자동 정리
    - 리소스 모니터링 및 제한
    - 컨테이너 상태 추적
    """

    def __init__(self, config: Optional[ContainerPoolConfig] = None):
        """
        Args:
            config: 컨테이너 풀 설정
        """
        self.config = config or ContainerPoolConfig()
        self.docker_client = docker.from_env()
        self.containers: Dict[str, ContainerStatus] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

        # War Room 네트워크 생성
        self._ensure_network()

    def _ensure_network(self):
        """War Room 전용 네트워크 생성"""
        try:
            self.docker_client.networks.get(self.config.network_name)
            logger.info(f"네트워크 '{self.config.network_name}' 존재 확인")
        except docker.errors.NotFound:
            self.docker_client.networks.create(
                self.config.network_name,
                driver="bridge"
            )
            logger.info(f"네트워크 '{self.config.network_name}' 생성 완료")

    async def start_container(
        self,
        mcp_server_name: str,
        image_tag: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> ContainerStatus:
        """
        MCP 서버 컨테이너 시작

        Args:
            mcp_server_name: MCP 서버 이름 (예: "docker-mcp")
            image_tag: Docker 이미지 태그 (기본: latest)
            environment: 환경 변수

        Returns:
            ContainerStatus: 시작된 컨테이너 상태
        """
        # 이미 실행 중인지 확인
        existing = self._find_running_container(mcp_server_name)
        if existing:
            logger.info(f"기존 컨테이너 재사용: {mcp_server_name}")
            existing.update_last_used()
            return existing

        # 동시 실행 제한 확인
        if len(self.containers) >= self.config.max_concurrent_containers:
            logger.warning("최대 컨테이너 수 도달, Idle 컨테이너 정리 중...")
            await self._cleanup_idle_containers()

        # 이미지 준비
        image_name = self._get_image_name(mcp_server_name, image_tag)
        await self._ensure_image(image_name, mcp_server_name)

        # 컨테이너 시작
        container_name = f"{mcp_server_name}-{int(datetime.now().timestamp())}"

        try:
            container = self.docker_client.containers.run(
                image=image_name,
                name=container_name,
                network=self.config.network_name,
                detach=True,
                remove=False,  # 수동 관리
                mem_limit=self.config.base_memory_limit,
                cpu_quota=int(self.config.base_cpu_quota * 100000),
                environment=environment or {},
                # 보안 옵션
                read_only=False,  # MCP 서버는 write 필요할 수 있음
                security_opt=["no-new-privileges"],
                # stdin 유지 (MCP 서버는 stdio 사용)
                stdin_open=True,
                tty=False
            )

            logger.info(f"컨테이너 시작 완료: {container_name} ({container.short_id})")

            # 상태 추적
            status = ContainerStatus(
                container_id=container.id,
                mcp_server_name=mcp_server_name,
                status="running",
                started_at=datetime.now(),
                last_used_at=datetime.now(),
                auto_stop_at=datetime.now() + timedelta(minutes=self.config.idle_timeout_minutes)
            )
            self.containers[container.id] = status

            return status

        except docker.errors.ImageNotFound:
            logger.error(f"이미지를 찾을 수 없음: {image_name}")
            raise
        except docker.errors.APIError as e:
            logger.error(f"컨테이너 시작 실패: {e}")
            raise

    async def stop_container(self, container_id: str, force: bool = False):
        """
        컨테이너 종료

        Args:
            container_id: 컨테이너 ID
            force: 강제 종료 여부
        """
        if container_id not in self.containers:
            logger.warning(f"알 수 없는 컨테이너: {container_id}")
            return

        status = self.containers[container_id]

        try:
            container = self.docker_client.containers.get(container_id)

            if force:
                container.kill()
                logger.info(f"컨테이너 강제 종료: {status.mcp_server_name}")
            else:
                container.stop(timeout=10)
                logger.info(f"컨테이너 정상 종료: {status.mcp_server_name}")

            # 컨테이너 제거
            container.remove()

        except docker.errors.NotFound:
            logger.warning(f"컨테이너가 이미 종료됨: {container_id}")
        except docker.errors.APIError as e:
            logger.error(f"컨테이너 종료 실패: {e}")
        finally:
            # 상태에서 제거
            del self.containers[container_id]

    async def get_container_status(self, container_id: str) -> Optional[ContainerStatus]:
        """컨테이너 상태 조회"""
        return self.containers.get(container_id)

    async def list_containers(self) -> List[ContainerStatus]:
        """모든 컨테이너 목록"""
        # 실제 Docker 상태와 동기화
        for container_id in list(self.containers.keys()):
            await self._sync_container_status(container_id)

        return list(self.containers.values())

    async def _sync_container_status(self, container_id: str):
        """Docker 상태와 동기화"""
        try:
            container = self.docker_client.containers.get(container_id)
            status = self.containers[container_id]

            # 메모리 사용량 업데이트
            stats = container.stats(stream=False)
            memory_usage = stats['memory_stats'].get('usage', 0)
            status.memory_usage_mb = memory_usage // (1024 * 1024)

            # Docker 상태 확인
            container.reload()
            if container.status != "running":
                logger.warning(f"컨테이너가 중단됨: {status.mcp_server_name}")
                status.status = "stopped"

        except docker.errors.NotFound:
            # 컨테이너가 외부에서 삭제됨
            logger.warning(f"컨테이너가 삭제됨: {container_id}")
            del self.containers[container_id]

    async def _cleanup_idle_containers(self):
        """Idle 상태의 컨테이너 정리"""
        now = datetime.now()
        to_stop = []

        for container_id, status in self.containers.items():
            if status.should_stop():
                to_stop.append(container_id)
                logger.info(
                    f"Idle 타임아웃으로 종료 예정: {status.mcp_server_name} "
                    f"(마지막 사용: {(now - status.last_used_at).seconds // 60}분 전)"
                )

        for container_id in to_stop:
            await self.stop_container(container_id)

    async def start_auto_cleanup(self):
        """자동 정리 태스크 시작 (백그라운드)"""
        if self._cleanup_task is not None:
            logger.warning("자동 정리 태스크가 이미 실행 중")
            return

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(60)  # 1분마다 체크
                    await self._cleanup_idle_containers()
                    await self._check_memory_pressure()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"자동 정리 오류: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info("자동 정리 태스크 시작")

    async def stop_auto_cleanup(self):
        """자동 정리 태스크 중지"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("자동 정리 태스크 중지")

    async def _check_memory_pressure(self):
        """메모리 압박 확인 및 대응"""
        # Docker 시스템 정보 조회
        info = self.docker_client.info()
        total_memory = info.get('MemTotal', 0)

        if total_memory == 0:
            return

        # 전체 컨테이너 메모리 사용량 계산
        total_used = sum(status.memory_usage_mb for status in self.containers.values())
        usage_percent = (total_used * 1024 * 1024 / total_memory) * 100

        if usage_percent > self.config.max_memory_percent:
            logger.warning(
                f"메모리 압박 감지: {usage_percent:.1f}% "
                f"(임계값: {self.config.max_memory_percent}%)"
            )

            # Idle 상태인 것부터 종료
            idle_containers = [
                (cid, status) for cid, status in self.containers.items()
                if status.is_idle()
            ]

            # Idle 시간 순으로 정렬 (오래된 것부터)
            idle_containers.sort(key=lambda x: x[1].last_used_at)

            for container_id, status in idle_containers:
                logger.info(f"메모리 확보를 위해 종료: {status.mcp_server_name}")
                await self.stop_container(container_id)

                # 다시 확인
                total_used = sum(s.memory_usage_mb for s in self.containers.values())
                usage_percent = (total_used * 1024 * 1024 / total_memory) * 100

                if usage_percent < (self.config.max_memory_percent - 10):
                    logger.info("메모리 압박 해소됨")
                    break

    def _get_image_name(self, mcp_server_name: str, tag: Optional[str] = None) -> str:
        """이미지 이름 생성"""
        # NPM 패키지명을 Docker 이미지명으로 변환
        # 예: "@modelcontextprotocol/server-docker" -> "mcp/server-docker"
        clean_name = mcp_server_name.replace("@modelcontextprotocol/", "")
        clean_name = clean_name.replace("/", "-")

        image_name = f"{self.config.image_prefix}/{clean_name}"
        if tag:
            image_name += f":{tag}"
        else:
            image_name += ":latest"

        return image_name

    async def _ensure_image(self, image_name: str, mcp_server_name: str):
        """
        이미지 존재 확인 및 다운로드

        이미지가 없으면 빌드 또는 풀
        실제로는 Tier에 따라 다른 전략 사용
        """
        try:
            self.docker_client.images.get(image_name)
            logger.info(f"이미지 존재 확인: {image_name}")
        except docker.errors.ImageNotFound:
            logger.info(f"이미지가 없음, 빌드 필요: {image_name}")
            # 실제로는 MCP 서버 패키지를 기반으로 이미지 빌드
            # 지금은 간단히 기본 이미지 태그만 시도
            raise docker.errors.ImageNotFound(
                f"이미지를 찾을 수 없습니다: {image_name}\n"
                f"MCP 서버 '{mcp_server_name}'의 이미지를 빌드해주세요."
            )

    async def shutdown(self):
        """오케스트레이터 종료 및 정리"""
        logger.info("컨테이너 풀 종료 중...")

        # 자동 정리 중지
        await self.stop_auto_cleanup()

        # 모든 컨테이너 종료
        container_ids = list(self.containers.keys())
        for container_id in container_ids:
            await self.stop_container(container_id)

        # Docker 클라이언트 종료
        self.docker_client.close()

        logger.info("컨테이너 풀 종료 완료")

    def get_stats(self) -> Dict:
        """통계 정보"""
        return {
            "total_containers": len(self.containers),
            "running_containers": sum(
                1 for s in self.containers.values() if s.status == "running"
            ),
            "idle_containers": sum(
                1 for s in self.containers.values() if s.status == "idle"
            ),
            "total_memory_mb": sum(
                s.memory_usage_mb for s in self.containers.values()
            ),
            "containers": [
                {
                    "name": s.mcp_server_name,
                    "status": s.status,
                    "memory_mb": s.memory_usage_mb,
                    "uptime_minutes": int((datetime.now() - s.started_at).seconds / 60),
                    "idle_minutes": int((datetime.now() - s.last_used_at).seconds / 60)
                }
                for s in self.containers.values()
            ]
        }

    def _find_running_container(self, mcp_server_name: str) -> Optional[ContainerStatus]:
        """실행 중인 컨테이너 찾기"""
        for status in self.containers.values():
            if status.mcp_server_name == mcp_server_name and status.status in ["running", "idle"]:
                return status
        return None
