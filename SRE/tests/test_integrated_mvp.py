"""
War Room 2.0 통합 MVP 테스트
"""

import asyncio
import logging
from src.integrated_war_room import IntegratedWarRoom
from src.tier_manager import ServerTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_tier_manager():
    """티어 관리자 테스트"""
    print("\n" + "=" * 70)
    print("🧪 테스트 1: Tier Manager")
    print("=" * 70)

    from src.tier_manager import TierManager

    tier_manager = TierManager(".war-room-test/tier-config.json")

    # 서버 등록
    print("\n1. 서버 등록...")
    docker_server = tier_manager.register_server(
        name="@modelcontextprotocol/server-docker",
        package="@modelcontextprotocol/server-docker",
        version="1.0.0"
    )
    print(f"  ✅ 등록: {docker_server.name}")
    print(f"  📊 초기 티어: {docker_server.tier.display_name}")

    # 사용 기록
    print("\n2. 사용 패턴 시뮬레이션...")
    for i in range(12):
        tier_manager.record_usage(docker_server.name)
        print(f"  📈 사용 {i+1}회 기록")

    # 티어 조정
    print("\n3. 티어 자동 조정...")
    changes = tier_manager.adjust_tiers()
    if changes:
        for name, change in changes.items():
            print(f"  🔄 {name}: {change}")
    else:
        print("  ℹ️ 변경 사항 없음")

    # 통계
    print("\n4. 통계 확인...")
    stats = tier_manager.get_stats()
    print(f"  • 총 서버: {stats['total_servers']}개")
    print(f"  • 총 사용: {stats['total_usage']}회")
    print(f"  • 티어 분포:")
    for tier_name, count in stats['tier_distribution'].items():
        print(f"    - {tier_name}: {count}개")

    print("\n✅ Tier Manager 테스트 완료\n")


async def test_container_orchestrator():
    """컨테이너 오케스트레이터 테스트 (Mock)"""
    print("\n" + "=" * 70)
    print("🧪 테스트 2: Container Orchestrator (Mock)")
    print("=" * 70)

    from src.container_orchestrator import (
        ContainerPoolOrchestrator,
        ContainerPoolConfig
    )

    # 테스트용 설정
    config = ContainerPoolConfig(
        max_concurrent_containers=5,
        idle_timeout_minutes=1,  # 테스트용 짧은 시간
        network_name="war-room-test-network"
    )

    print("\n1. 오케스트레이터 초기화...")
    # NOTE: 실제 Docker 없이 테스트하기 위해 try-catch 사용
    try:
        orchestrator = ContainerPoolOrchestrator(config)
        print("  ✅ 초기화 완료")

        # 통계 확인
        print("\n2. 초기 상태 확인...")
        stats = orchestrator.get_stats()
        print(f"  • 총 컨테이너: {stats['total_containers']}개")
        print(f"  • 실행 중: {stats['running_containers']}개")

        print("\n✅ Container Orchestrator 테스트 완료")

    except Exception as e:
        print(f"  ⚠️ Docker 환경 필요: {e}")
        print("  ℹ️ Docker가 설치되고 실행 중인 환경에서 테스트하세요")

    print()


async def test_integrated_war_room():
    """통합 War Room 테스트"""
    print("\n" + "=" * 70)
    print("🧪 테스트 3: Integrated War Room")
    print("=" * 70)

    war_room = IntegratedWarRoom(config_dir=".war-room-test")

    print("\n1. War Room 시작...")
    try:
        await war_room.start()
        print("  ✅ 시작 완료")
    except Exception as e:
        print(f"  ⚠️ 시작 실패 (Docker 필요): {e}")
        return

    # 문제 분석 테스트
    print("\n2. 문제 분석 및 MCP 서버 검색...")
    error_log = """
    Error: Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
    Is the docker daemon running?
    """

    result = await war_room.handle_incident(error_log, auto_approve=True)

    if result['success']:
        print(f"  ✅ 성공: {result['message']}")
        print(f"  📦 서버: {result['server_name']}")
        print(f"  🏷️ 티어: {result['tier']}")
    else:
        print(f"  ⚠️ 실패: {result['message']}")
        if 'error' in result:
            print(f"  오류: {result['error']}")

    # 상태 확인
    print("\n3. 시스템 상태 확인...")
    await war_room.show_status()

    # 종료
    print("\n4. War Room 종료...")
    await war_room.shutdown()
    print("  ✅ 종료 완료")

    print("\n✅ Integrated War Room 테스트 완료\n")


async def test_full_scenario():
    """전체 시나리오 테스트"""
    print("\n" + "=" * 70)
    print("🧪 테스트 4: 전체 시나리오 (End-to-End)")
    print("=" * 70)

    war_room = IntegratedWarRoom(config_dir=".war-room-test")

    try:
        await war_room.start()

        # 시나리오 1: Docker 장애
        print("\n【시나리오 1】 Docker 장애 발생")
        print("-" * 70)
        docker_error = """
        docker: Error response from daemon: container not found
        """
        result1 = await war_room.handle_incident(docker_error, auto_approve=True)
        print(f"결과: {result1.get('message', 'N/A')}")

        await asyncio.sleep(1)

        # 시나리오 2: Postgres 장애
        print("\n【시나리오 2】 PostgreSQL 장애 발생")
        print("-" * 70)
        postgres_error = """
        psql: error: connection refused
        """
        result2 = await war_room.handle_incident(postgres_error, auto_approve=True)
        print(f"결과: {result2.get('message', 'N/A')}")

        await asyncio.sleep(1)

        # 최종 상태
        print("\n【최종 상태】")
        print("-" * 70)
        await war_room.show_status()

        # 최적화
        print("\n【시스템 최적화】")
        print("-" * 70)
        await war_room.optimize()

    except Exception as e:
        print(f"\n⚠️ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await war_room.shutdown()

    print("\n✅ 전체 시나리오 테스트 완료\n")


async def main():
    """모든 테스트 실행"""
    print("\n" + "=" * 70)
    print("🧪 War Room 2.0 - 통합 MVP 테스트 스위트")
    print("=" * 70)

    # 테스트 순서
    await test_tier_manager()
    await test_container_orchestrator()
    await test_integrated_war_room()

    # 전체 시나리오 (선택적)
    run_full = input("\n전체 시나리오 테스트를 실행하시겠습니까? (yes/no): ").strip().lower()
    if run_full in ['yes', 'y']:
        await test_full_scenario()

    print("\n" + "=" * 70)
    print("✅ 모든 테스트 완료!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
