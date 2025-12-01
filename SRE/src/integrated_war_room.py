"""
Integrated War Room 2.0 - Production Ready
컨테이너 풀 오케스트레이션과 티어 기반 관리를 통합한 실제 서비스
"""

import asyncio
import logging
from typing import Optional, Dict
from pathlib import Path

from .container_orchestrator import ContainerPoolOrchestrator, ContainerPoolConfig
from .tier_manager import TierManager, ServerTier
from .mcp_catalog import MCPCatalogSync, MCPServerCandidate
from .problem_analyzer import ProblemAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegratedWarRoom:
    """
    통합 War Room 2.0 시스템

    주요 기능:
    - 문제 분석 및 MCP 서버 자동 검색
    - 티어 기반 서버 관리
    - 동적 컨테이너 풀 오케스트레이션
    - 자동 최적화 및 리소스 관리
    """

    def __init__(
        self,
        config_dir: str = ".war-room",
        container_config: Optional[ContainerPoolConfig] = None
    ):
        """
        Args:
            config_dir: 설정 파일 디렉토리
            container_config: 컨테이너 풀 설정
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 컴포넌트 초기화
        self.orchestrator = ContainerPoolOrchestrator(container_config)
        self.tier_manager = TierManager(
            str(self.config_dir / "tier-config.json")
        )
        self.catalog = MCPCatalogSync()
        self.analyzer = ProblemAnalyzer()

        logger.info("War Room 2.0 초기화 완료")

    async def handle_incident(
        self,
        error_log: str,
        auto_approve: bool = False
    ) -> Dict:
        """
        장애 자동 처리

        Args:
            error_log: 에러 로그
            auto_approve: 자동 승인 여부

        Returns:
            처리 결과
        """
        logger.info("=" * 60)
        logger.info("🚨 장애 감지 및 분석 시작")
        logger.info("=" * 60)

        # 1단계: 문제 분석
        logger.info("\n🔍 1단계: 문제 분석 중...")
        keywords = self.analyzer.analyze_problem(error_log)

        if not keywords:
            return {
                "success": False,
                "message": "문제 분석 실패: 키워드를 찾을 수 없습니다",
                "error_log": error_log
            }

        logger.info(f"📌 키워드 추출: {keywords}")

        # 2단계: MCP Catalog 검색
        logger.info("\n🔎 2단계: MCP Catalog 검색 중...")
        candidates = self.catalog.search_servers(keywords, limit=3)

        if not candidates:
            return {
                "success": False,
                "message": "적합한 MCP 서버를 찾을 수 없습니다",
                "keywords": keywords
            }

        # 3단계: 최적 후보 선택
        best_candidate = candidates[0]
        logger.info(
            f"✨ 최적 후보 발견: {best_candidate.name} "
            f"(점수: {best_candidate.score:.0f}/100)"
        )

        # 4단계: 티어 확인 또는 등록
        server_info = self.tier_manager.servers.get(best_candidate.name)
        if not server_info:
            logger.info(f"🆕 새 서버 등록: {best_candidate.name}")
            server_info = self.tier_manager.register_server(
                name=best_candidate.name,
                package=best_candidate.name,
                version=best_candidate.version
            )

        logger.info(f"📊 현재 티어: {server_info.tier.display_name}")
        logger.info(f"⏱️ 예상 시작 시간: ~{server_info.tier.expected_start_time}초")

        # 5단계: 승인 확인
        if not auto_approve:
            approval = input(f"\n{best_candidate.name} 컨테이너를 시작하시겠습니까? (yes/no): ").strip().lower()
            if approval not in ['yes', 'y']:
                return {
                    "success": False,
                    "message": "사용자가 거부했습니다",
                    "candidate": best_candidate.name
                }

        # 6단계: 컨테이너 시작
        logger.info(f"\n⚙️ 3단계: MCP 서버 컨테이너 시작 중...")

        try:
            container_status = await self.orchestrator.start_container(
                mcp_server_name=best_candidate.name,
                environment={
                    "MCP_PACKAGE": best_candidate.name,
                    "MCP_VERSION": best_candidate.version
                }
            )

            # 사용 기록
            self.tier_manager.record_usage(best_candidate.name)

            logger.info(f"✅ 컨테이너 시작 완료: {container_status.container_id[:12]}")
            logger.info(f"📦 상태: {container_status.status}")

            return {
                "success": True,
                "message": f"MCP 서버 시작 완료: {best_candidate.name}",
                "server_name": best_candidate.name,
                "container_id": container_status.container_id,
                "tier": server_info.tier.value,
                "keywords": keywords
            }

        except Exception as e:
            logger.error(f"❌ 컨테이너 시작 실패: {e}")
            return {
                "success": False,
                "message": f"컨테이너 시작 실패: {str(e)}",
                "server_name": best_candidate.name,
                "error": str(e)
            }

    async def show_status(self):
        """현재 시스템 상태 표시"""
        print("\n" + "=" * 70)
        print("📊 War Room 2.0 - 시스템 상태")
        print("=" * 70)

        # 컨테이너 풀 상태
        containers = await self.orchestrator.list_containers()
        container_stats = self.orchestrator.get_stats()

        print(f"\n🐳 컨테이너 풀:")
        print(f"  • 실행 중: {container_stats['running_containers']}개")
        print(f"  • Idle 상태: {container_stats['idle_containers']}개")
        print(f"  • 총 메모리: {container_stats['total_memory_mb']}MB")

        if containers:
            print(f"\n  상세:")
            for c in container_stats['containers']:
                print(f"    - {c['name']}")
                print(f"      상태: {c['status']}, 메모리: {c['memory_mb']}MB")
                print(f"      가동: {c['uptime_minutes']}분, Idle: {c['idle_minutes']}분")

        # 티어 관리 상태
        tier_stats = self.tier_manager.get_stats()

        print(f"\n📈 티어 관리:")
        print(f"  • 등록된 서버: {tier_stats['total_servers']}개")
        print(f"  • 총 사용 횟수: {tier_stats['total_usage']}회")
        print(f"  • 주간 사용: {tier_stats['weekly_usage']}회")

        print(f"\n  티어 분포:")
        for tier_name, count in tier_stats['tier_distribution'].items():
            print(f"    - {tier_name}: {count}개")

        if tier_stats['most_used_server']:
            most_used = tier_stats['most_used_server']
            print(f"\n  가장 많이 사용:")
            print(f"    - {most_used['name']}")
            print(f"      티어: {most_used['tier']}")
            print(f"      사용: {most_used['usage']}회 (주간: {most_used['weekly_usage']}회)")

        # 캐시 정보
        cache_stats = self.tier_manager.get_cache_summary()
        print(f"\n💾 이미지 캐시:")
        print(f"  • 캐시된 이미지: {cache_stats['cached_count']}개")
        print(f"  • 총 크기: {cache_stats['total_size_mb']}MB")

        print("\n" + "=" * 70)

    async def optimize(self):
        """시스템 최적화"""
        logger.info("\n🧹 시스템 최적화 시작...")

        # 1. Idle 컨테이너 정리
        logger.info("  1️⃣ Idle 컨테이너 정리 중...")
        await self.orchestrator._cleanup_idle_containers()

        # 2. 티어 최적화
        logger.info("  2️⃣ 티어 최적화 중...")
        changes = self.tier_manager.optimize()

        if changes:
            logger.info(f"    ✅ {len(changes)}개 서버 티어 조정:")
            for name, change in changes.items():
                logger.info(f"      - {name}: {change}")
        else:
            logger.info("    ℹ️ 티어 변경 사항 없음")

        # 3. 메모리 압박 확인
        logger.info("  3️⃣ 리소스 확인 중...")
        await self.orchestrator._check_memory_pressure()

        logger.info("✅ 시스템 최적화 완료")

    async def start(self):
        """War Room 시스템 시작"""
        logger.info("🚀 War Room 2.0 시작")

        # 자동 정리 태스크 시작
        await self.orchestrator.start_auto_cleanup()

        logger.info("✅ War Room 2.0 실행 중")

    async def shutdown(self):
        """War Room 시스템 종료"""
        logger.info("🛑 War Room 2.0 종료 중...")

        # 오케스트레이터 종료 (모든 컨테이너 정리)
        await self.orchestrator.shutdown()

        # Catalog 클라이언트 종료
        self.catalog.close()

        logger.info("✅ War Room 2.0 종료 완료")


# ========================================
# CLI 인터페이스
# ========================================

async def demo_scenarios():
    """데모 시나리오"""
    war_room = IntegratedWarRoom()

    try:
        await war_room.start()

        print("\n" + "=" * 70)
        print("🎬 War Room 2.0 - 통합 데모 시나리오")
        print("=" * 70)

        # 시나리오 1: Docker 문제
        print("\n\n【시나리오 1】 Docker 컨테이너 장애")
        print("-" * 70)
        error_1 = """
        Error: Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
        Is the docker daemon running?
        """
        result = await war_room.handle_incident(error_1, auto_approve=True)
        print(f"\n결과: {result['message']}")

        # 잠시 대기
        await asyncio.sleep(2)

        # 시나리오 2: PostgreSQL 문제
        print("\n\n【시나리오 2】 PostgreSQL 연결 실패")
        print("-" * 70)
        error_2 = """
        psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed:
        Connection refused. Is the server running?
        """
        result = await war_room.handle_incident(error_2, auto_approve=True)
        print(f"\n결과: {result['message']}")

        # 상태 확인
        await asyncio.sleep(1)
        await war_room.show_status()

        # 최적화
        await asyncio.sleep(2)
        await war_room.optimize()

    finally:
        await war_room.shutdown()


async def interactive_mode():
    """대화형 모드"""
    war_room = IntegratedWarRoom()

    try:
        await war_room.start()

        print("\n" + "=" * 70)
        print("War Room 2.0 - 대화형 모드")
        print("=" * 70)
        print("\n명령어:")
        print("  status    - 시스템 상태 확인")
        print("  optimize  - 시스템 최적화")
        print("  exit      - 종료")
        print("  기타      - 에러 로그로 인식하여 처리")
        print()

        while True:
            try:
                user_input = input("\n> ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "exit":
                    break
                elif user_input.lower() == "status":
                    await war_room.show_status()
                elif user_input.lower() == "optimize":
                    await war_room.optimize()
                else:
                    # 에러 로그로 처리
                    result = await war_room.handle_incident(user_input)
                    print(f"\n결과: {result['message']}")

            except KeyboardInterrupt:
                print("\n\n종료 중...")
                break

    finally:
        await war_room.shutdown()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(demo_scenarios())
    else:
        asyncio.run(interactive_mode())
