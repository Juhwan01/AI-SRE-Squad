"""
War Room 2.0 - Docker 없이 실행 가능한 테스트
Container Orchestrator를 Mock으로 대체
"""

import asyncio
from unittest.mock import Mock, AsyncMock


async def test_without_docker():
    """Docker 없이 War Room 핵심 기능 테스트"""
    print("\n" + "=" * 70)
    print("War Room 2.0 - Docker 없이 테스트")
    print("=" * 70)

    results = {}

    # 1. Tier Manager
    print("\n[1/6] Tier Manager 테스트...")
    try:
        from src.tier_manager import TierManager, ServerTier

        tier_mgr = TierManager(".war-room-test/tier.json")

        # 여러 서버 등록
        servers = [
            ("@modelcontextprotocol/server-docker", "1.0.0"),
            ("@modelcontextprotocol/server-postgres", "1.0.0"),
            ("redis-mcp", "0.5.0"),
        ]

        for name, version in servers:
            tier_mgr.register_server(name, name, version)

        # Docker 서버 많이 사용 (Tier 1로 승격되어야 함)
        for _ in range(15):
            tier_mgr.record_usage("@modelcontextprotocol/server-docker")

        # Postgres 적당히 사용 (Tier 2 유지)
        for _ in range(5):
            tier_mgr.record_usage("@modelcontextprotocol/server-postgres")

        # 티어 조정
        changes = tier_mgr.adjust_tiers()

        stats = tier_mgr.get_stats()

        print(f"  ✅ 서버: {stats['total_servers']}개")
        print(f"     티어 변경: {len(changes)}건")
        print(f"     가장 많이 사용: {stats['most_used_server']['name']}")

        # 티어 분포 확인
        for name, server in tier_mgr.servers.items():
            print(f"     - {name[:40]:40s} | {server.tier.display_name:20s} | {server.weekly_usage_count}회")

        results['tier_manager'] = True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        results['tier_manager'] = False

    # 2. MCP Catalog
    print("\n[2/6] MCP Catalog 검색...")
    try:
        from src.mcp_catalog import MCPCatalogSync

        catalog = MCPCatalogSync()

        # 여러 키워드로 검색
        keywords = ["docker", "postgres", "kubernetes"]
        all_servers = []

        for keyword in keywords:
            servers = catalog.search_servers([keyword], limit=2)
            all_servers.extend(servers)
            if servers:
                print(f"  '{keyword}': {servers[0].name} ({servers[0].score:.0f}점)")

        catalog.close()

        print(f"  ✅ 총 {len(all_servers)}개 서버 발견")
        results['catalog'] = True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        results['catalog'] = False

    # 3. Problem Analyzer
    print("\n[3/6] Problem Analyzer 테스트...")
    try:
        from src.problem_analyzer import ProblemAnalyzer

        analyzer = ProblemAnalyzer()

        test_cases = {
            "Docker": "Error: Cannot connect to the Docker daemon",
            "PostgreSQL": "FATAL: password authentication failed for user",
            "Kubernetes": "pod 'api-server' is in CrashLoopBackOff state",
            "Redis": "ECONNREFUSED 127.0.0.1:6379",
            "MongoDB": "MongoNetworkError: failed to connect to server",
        }

        print("  키워드 추출:")
        for service, error in test_cases.items():
            keywords = analyzer.analyze_problem(error)
            print(f"     {service:12s}: {keywords}")

        results['analyzer'] = True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        results['analyzer'] = False

    # 4. Mock Orchestrator (Docker 없이)
    print("\n[4/6] Mock Container Orchestrator...")
    try:
        # Docker 없이 로직만 테스트
        from src.container_orchestrator import ContainerStatus
        from datetime import datetime, timedelta

        # Mock 컨테이너 상태 생성
        mock_container = ContainerStatus(
            container_id="mock-123",
            mcp_server_name="@modelcontextprotocol/server-docker",
            status="running",
            started_at=datetime.now(),
            last_used_at=datetime.now(),
            auto_stop_at=datetime.now() + timedelta(minutes=30)
        )

        # 테스트: Idle 확인
        assert not mock_container.is_idle()

        # 테스트: 마지막 사용 업데이트
        mock_container.update_last_used()
        assert mock_container.status == "running"

        print("  ✅ ContainerStatus 로직 테스트 성공")
        print(f"     Mock 컨테이너: {mock_container.mcp_server_name}")
        print(f"     상태: {mock_container.status}")
        print(f"     자동 종료: {mock_container.auto_stop_at.strftime('%H:%M:%S')}")

        results['orchestrator_logic'] = True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        results['orchestrator_logic'] = False

    # 5. 통합 플로우 (Mock)
    print("\n[5/6] 통합 플로우 시뮬레이션...")
    try:
        from src.mcp_catalog import MCPCatalogSync
        from src.problem_analyzer import ProblemAnalyzer
        from src.tier_manager import TierManager

        # 장애 시나리오
        error_log = "Error: Cannot connect to the Docker daemon"

        # 1. 문제 분석
        analyzer = ProblemAnalyzer()
        keywords = analyzer.analyze_problem(error_log)
        print(f"     1. 키워드 추출: {keywords}")

        # 2. MCP 서버 검색
        catalog = MCPCatalogSync()
        candidates = catalog.search_servers(keywords, limit=3)
        best = candidates[0] if candidates else None
        print(f"     2. 최적 서버: {best.name if best else 'N/A'} ({best.score:.0f}점)")

        # 3. 티어 확인
        tier_mgr = TierManager(".war-room-test/tier.json")
        if best:
            server = tier_mgr.servers.get(best.name)
            if server:
                print(f"     3. 티어: {server.tier.display_name}")
            else:
                print(f"     3. 신규 서버 (Tier 3 예상)")

        # 4. (실제로는 여기서 컨테이너 시작)
        print(f"     4. [Mock] 컨테이너 시작 시뮬레이션")

        # 5. 사용 기록
        if best:
            tier_mgr.record_usage(best.name)
            print(f"     5. 사용 기록 완료")

        catalog.close()

        print("  ✅ 전체 플로우 시뮬레이션 성공")
        results['integration'] = True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        results['integration'] = False

    # 6. 티어 최적화
    print("\n[6/6] 시스템 최적화...")
    try:
        from src.tier_manager import TierManager

        tier_mgr = TierManager(".war-room-test/tier.json")

        # 주간 통계 확인
        stats = tier_mgr.get_stats()
        print(f"     총 사용: {stats['total_usage']}회")
        print(f"     주간 사용: {stats['weekly_usage']}회")

        # 티어 조정
        changes = tier_mgr.adjust_tiers()
        if changes:
            print(f"     티어 변경: {len(changes)}건")
        else:
            print(f"     티어 변경: 없음")

        # 캐시 요약
        cache = tier_mgr.get_cache_summary()
        print(f"     캐시된 이미지: {cache['cached_count']}개")

        results['optimization'] = True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        results['optimization'] = False

    # 결과 요약
    print("\n" + "=" * 70)
    print("결과 요약")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name:25s}: {status}")

    print(f"\n총 {total}개 중 {passed}개 통과 ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 Docker 없이 모든 핵심 기능 테스트 성공!")
        print("\n💡 Docker를 시작하면 실제 컨테이너 관리 기능까지 테스트 가능합니다.")
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_without_docker())
