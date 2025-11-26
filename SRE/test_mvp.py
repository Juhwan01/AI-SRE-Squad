"""
War Room 2.0 MVP 테스트
간단한 기능 검증
"""

import sys
sys.path.insert(0, 'src')

from src.mcp_catalog import MCPCatalogSync
from src.problem_analyzer import quick_analyze
from src.dynamic_mcp_manager import DynamicMCPManager


def test_catalog_search():
    """MCP Catalog 검색 테스트"""
    print("\n" + "="*60)
    print("TEST 1: MCP Catalog 검색")
    print("="*60)

    catalog = MCPCatalogSync()

    # Docker 관련 MCP 서버 검색
    print("\n검색 키워드: ['docker']")
    results = catalog.search_servers(["docker"], limit=3)

    if results:
        print(f"\n✅ {len(results)}개 결과 발견:\n")
        for i, candidate in enumerate(results, 1):
            print(f"{i}. {candidate.name}")
            print(f"   설명: {candidate.description}")
            print(f"   점수: {candidate.score:.1f}/100")
            print(f"   공식: {'✅' if candidate.official else '❌'}")
            print()
    else:
        print("❌ 결과 없음")

    catalog.close()
    return len(results) > 0


def test_problem_analyzer():
    """문제 분석기 테스트"""
    print("\n" + "="*60)
    print("TEST 2: 문제 분석기")
    print("="*60)

    test_cases = [
        {
            "name": "Docker 연결 실패",
            "log": "Error: Cannot connect to the Docker daemon",
            "expected": ["docker"]
        },
        {
            "name": "PostgreSQL 연결 실패",
            "log": "psql: connection to server failed",
            "expected": ["postgres"]
        },
        {
            "name": "Redis 연결 실패",
            "log": "Error: ECONNREFUSED 127.0.0.1:6379",
            "expected": ["redis"]
        },
    ]

    all_passed = True

    for test in test_cases:
        print(f"\n테스트: {test['name']}")
        print(f"입력: {test['log']}")

        keywords = quick_analyze(test['log'])
        print(f"결과: {keywords}")

        # 예상 키워드가 포함되어 있는지 확인
        passed = any(exp in keywords for exp in test['expected'])
        print(f"{'✅ PASS' if passed else '❌ FAIL'}")

        all_passed = all_passed and passed

    return all_passed


def test_dynamic_manager():
    """Dynamic MCP Manager 테스트"""
    print("\n" + "="*60)
    print("TEST 3: Dynamic MCP Manager")
    print("="*60)

    manager = DynamicMCPManager(config_path=".war-room/test-config.json")

    # 초기 상태
    print("\n초기 상태:")
    print(f"  활성 서버: {len(manager.list_servers())}개")

    # Docker 문제 처리
    print("\n\n시나리오: Docker 문제 발생")
    error_log = "Error: Cannot connect to the Docker daemon"

    result = manager.handle_problem(error_log, auto_approve=True)

    if result["success"]:
        print(f"\n✅ 처리 성공")
        print(f"  추가된 서버: {result.get('server')}")

        # 상태 확인
        servers = manager.list_servers()
        print(f"\n현재 활성 서버: {len(servers)}개")
        for server in servers:
            print(f"  • {server['name']} (사용 {server['usage_count']}회)")

    manager.close()
    return result["success"]


def test_full_flow():
    """전체 플로우 테스트"""
    print("\n" + "="*60)
    print("TEST 4: 전체 플로우 (End-to-End)")
    print("="*60)

    from war_room import WarRoom

    war_room = WarRoom(config_path=".war-room/e2e-test-config.json")

    scenarios = [
        ("Docker 컨테이너 문제", "Cannot connect to the Docker daemon"),
        ("PostgreSQL DB 문제", "psql: connection to server failed"),
    ]

    success_count = 0

    for name, error in scenarios:
        print(f"\n\n시나리오: {name}")
        print("-" * 60)
        result = war_room.handle_incident(error, auto_approve=True)
        if result["success"]:
            success_count += 1

    war_room.show_status()
    war_room.close()

    print(f"\n\n결과: {success_count}/{len(scenarios)} 시나리오 성공")
    return success_count == len(scenarios)


def run_all_tests():
    """모든 테스트 실행"""
    print("🧪 War Room 2.0 MVP 테스트 시작")
    print("="*60)

    results = []

    # Test 1: Catalog Search
    try:
        results.append(("Catalog Search", test_catalog_search()))
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        results.append(("Catalog Search", False))

    # Test 2: Problem Analyzer
    try:
        results.append(("Problem Analyzer", test_problem_analyzer()))
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        results.append(("Problem Analyzer", False))

    # Test 3: Dynamic Manager
    try:
        results.append(("Dynamic Manager", test_dynamic_manager()))
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        results.append(("Dynamic Manager", False))

    # Test 4: Full Flow
    try:
        results.append(("Full Flow", test_full_flow()))
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        results.append(("Full Flow", False))

    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n총 {passed}/{total} 테스트 통과")

    if passed == total:
        print("\n🎉 모든 테스트 통과!")
    else:
        print(f"\n⚠️ {total - passed}개 테스트 실패")


if __name__ == "__main__":
    run_all_tests()
