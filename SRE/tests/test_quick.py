"""
War Room 2.0 - 빠른 자동 테스트 (사용자 입력 없음)
"""

import asyncio
import sys


async def quick_test():
    """Docker 없이 할 수 있는 빠른 테스트"""
    print("\n" + "=" * 70)
    print("War Room 2.0 - Quick Test (자동 모드)")
    print("=" * 70)

    results = {}

    # 테스트 1: Imports
    print("\n[1/5] 모듈 Import...")
    try:
        from src.tier_manager import TierManager
        from src.mcp_catalog import MCPCatalogSync
        from src.problem_analyzer import ProblemAnalyzer
        from src.container_orchestrator import ContainerPoolOrchestrator
        from src.integrated_war_room import IntegratedWarRoom
        print("  ✅ 모든 모듈 import 성공")
        results['import'] = True
    except Exception as e:
        print(f"  ❌ Import 실패: {e}")
        results['import'] = False
        return results

    # 테스트 2: Tier Manager
    print("\n[2/5] Tier Manager...")
    try:
        tier_mgr = TierManager(".war-room-test/tier.json")
        server = tier_mgr.register_server(
            "@modelcontextprotocol/server-docker",
            "@modelcontextprotocol/server-docker",
            "1.0.0"
        )

        # 12회 사용
        for _ in range(12):
            tier_mgr.record_usage(server.name)

        # 티어 조정
        changes = tier_mgr.adjust_tiers()

        print(f"  ✅ 서버 등록, 사용 기록, 티어 조정 완료")
        print(f"     초기: {server.tier.value} → 변경: {len(changes)}건")
        results['tier_manager'] = True
    except Exception as e:
        print(f"  ❌ Tier Manager 실패: {e}")
        results['tier_manager'] = False

    # 테스트 3: MCP Catalog
    print("\n[3/5] MCP Catalog 검색...")
    try:
        catalog = MCPCatalogSync()
        servers = catalog.search_servers(["docker"], limit=3)
        catalog.close()

        print(f"  ✅ {len(servers)}개 서버 발견")
        if servers:
            print(f"     최고 점수: {servers[0].name} ({servers[0].score:.0f}점)")
        results['catalog'] = True
    except Exception as e:
        print(f"  ❌ Catalog 실패: {e}")
        results['catalog'] = False

    # 테스트 4: Problem Analyzer
    print("\n[4/5] Problem Analyzer...")
    try:
        analyzer = ProblemAnalyzer()
        keywords = analyzer.analyze_problem("Error: Cannot connect to Docker daemon")

        print(f"  ✅ 키워드 추출: {keywords}")
        results['analyzer'] = True
    except Exception as e:
        print(f"  ❌ Analyzer 실패: {e}")
        results['analyzer'] = False

    # 테스트 5: Container Orchestrator (초기화만)
    print("\n[5/5] Container Orchestrator (초기화)...")
    try:
        from src.container_orchestrator import ContainerPoolOrchestrator, ContainerPoolConfig

        config = ContainerPoolConfig(network_name="war-room-test")
        orch = ContainerPoolOrchestrator(config)

        stats = orch.get_stats()
        print(f"  ✅ Orchestrator 초기화 성공")
        print(f"     컨테이너: {stats['total_containers']}개")

        await orch.shutdown()
        results['orchestrator'] = True
    except Exception as e:
        print(f"  ⚠️  Orchestrator 초기화만 가능 (Docker 미실행?): {e}")
        results['orchestrator'] = False

    # 결과
    print("\n" + "=" * 70)
    print("결과 요약")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name:20s}: {status}")

    print(f"\n총 {total}개 중 {passed}개 통과 ({passed/total*100:.0f}%)")

    if passed >= 4:  # Orchestrator 제외하고 4개 통과하면 OK
        print("\n🎉 핵심 기능 테스트 통과!")

    return results


async def docker_test():
    """Docker 필요한 테스트"""
    print("\n" + "=" * 70)
    print("Docker 테스트 (컨테이너 시작 시도)")
    print("=" * 70)

    try:
        from src.integrated_war_room import IntegratedWarRoom

        print("\n[1/3] War Room 초기화...")
        war_room = IntegratedWarRoom(".war-room-test")
        await war_room.start()
        print("  ✅ 초기화 완료")

        print("\n[2/3] 상태 확인...")
        await war_room.show_status()

        print("\n[3/3] 종료...")
        await war_room.shutdown()
        print("  ✅ 테스트 완료")

        return True

    except Exception as e:
        print(f"\n❌ Docker 테스트 실패: {e}")
        print("   Docker가 실행 중인지 확인하세요")
        import traceback
        traceback.print_exc()
        return False


async def full_scenario_test():
    """전체 시나리오 테스트 (MCP 서버 검색 및 추가)"""
    print("\n" + "=" * 70)
    print("전체 시나리오 테스트 (End-to-End)")
    print("=" * 70)

    try:
        from src.integrated_war_room import IntegratedWarRoom

        war_room = IntegratedWarRoom(".war-room-test")
        await war_room.start()

        # Docker 장애 시나리오
        print("\n시나리오: Docker 장애 발생")
        print("-" * 70)

        error = "Error: Cannot connect to Docker daemon"

        print(f"\n에러: {error}")
        print("\n처리 중...")

        result = await war_room.handle_incident(error, auto_approve=True)

        if result['success']:
            print(f"\n✅ 성공!")
            print(f"   메시지: {result['message']}")
            print(f"   서버: {result.get('server_name')}")
            print(f"   티어: {result.get('tier')}")
        else:
            print(f"\n⚠️  실패: {result['message']}")
            if 'error' in result:
                print(f"   오류: {result['error']}")

        print("\n최종 상태:")
        await war_room.show_status()

        await war_room.shutdown()

        return result['success']

    except Exception as e:
        print(f"\n❌ 시나리오 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 실행"""
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "quick"

    if mode == "quick":
        await quick_test()
    elif mode == "docker":
        await quick_test()
        print("\n")
        await docker_test()
    elif mode == "full":
        await quick_test()
        print("\n")
        await docker_test()
        print("\n")
        await full_scenario_test()
    else:
        print("사용법: python test_quick.py [quick|docker|full]")
        print("  quick: 빠른 테스트 (기본)")
        print("  docker: Docker 포함 테스트")
        print("  full: 전체 시나리오 테스트")


if __name__ == "__main__":
    asyncio.run(main())
