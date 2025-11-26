"""
War Room 2.0 - Main Entry Point
Dynamic MCP 기반 자율 장애 대응 시스템
"""

import sys
from typing import Optional

from .dynamic_mcp_manager import DynamicMCPManager


class WarRoom:
    """War Room 2.0 메인 시스템"""

    def __init__(self, config_path: str = ".war-room/mcp-config.json"):
        """
        Args:
            config_path: 설정 파일 경로
        """
        self.manager = DynamicMCPManager(config_path)

    def handle_incident(self, error_log: str, auto_approve: bool = False):
        """
        장애 처리

        Args:
            error_log: 에러 로그
            auto_approve: 자동 승인 여부
        """
        result = self.manager.handle_problem(error_log, auto_approve)
        return result

    def show_status(self):
        """현재 상태 표시"""
        print("\n" + "=" * 60)
        print("📊 War Room 2.0 상태")
        print("=" * 60)

        servers = self.manager.list_servers()
        if not servers:
            print("\n현재 활성화된 MCP 서버가 없습니다.")
            print("문제가 발생하면 자동으로 필요한 도구를 찾아 추가합니다.")
        else:
            print(f"\n활성화된 MCP 서버: {len(servers)}개\n")
            for server in servers:
                print(f"  • {server['name']}")
                print(f"    버전: {server['version']}")
                print(f"    상태: {server['status']}")
                print(f"    사용 횟수: {server['usage_count']}회")
                print()

        stats = self.manager.get_stats()
        print(f"통계:")
        print(f"  • 총 서버 수: {stats['total_servers']}")
        print(f"  • 총 사용 횟수: {stats['total_usage']}")
        if stats['most_used']:
            print(f"  • 가장 많이 사용: {stats['most_used']}")

    def optimize(self):
        """시스템 최적화"""
        print("\n🧹 시스템 최적화 중...")
        self.manager.optimize()
        print("✅ 최적화 완료")

    def close(self):
        """종료"""
        self.manager.close()


def demo_scenarios():
    """데모 시나리오"""
    war_room = WarRoom()

    print("\n" + "="*60)
    print("🎬 War Room 2.0 데모 시나리오")
    print("="*60)

    # 시나리오 1: Docker 컨테이너 문제
    print("\n\n【시나리오 1】 Docker 컨테이너 시작 실패")
    print("-" * 60)
    error_1 = """
    Error: Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
    Is the docker daemon running?
    """
    war_room.handle_incident(error_1, auto_approve=True)

    # 시나리오 2: PostgreSQL 연결 문제
    print("\n\n【시나리오 2】 PostgreSQL 데이터베이스 연결 실패")
    print("-" * 60)
    error_2 = """
    psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed:
    Connection refused. Is the server running on that host and accepting TCP/IP connections?
    """
    war_room.handle_incident(error_2, auto_approve=True)

    # 시나리오 3: Kubernetes Pod 문제
    print("\n\n【시나리오 3】 Kubernetes Pod CrashLoopBackOff")
    print("-" * 60)
    error_3 = """
    kubectl get pods
    NAME                    READY   STATUS             RESTARTS   AGE
    api-deployment-abc123   0/1     CrashLoopBackOff   5          3m
    """
    war_room.handle_incident(error_3, auto_approve=True)

    # 최종 상태 확인
    war_room.show_status()

    # 최적화
    war_room.optimize()

    war_room.close()


def interactive_mode():
    """대화형 모드"""
    war_room = WarRoom()

    print("\n대화형 모드 시작")
    print("명령어:")
    print("  status  - 현재 상태 확인")
    print("  optimize - 시스템 최적화")
    print("  exit    - 종료")
    print("  기타    - 에러 로그로 인식하여 처리")
    print()

    try:
        while True:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() == "exit":
                break
            elif user_input.lower() == "status":
                war_room.show_status()
            elif user_input.lower() == "optimize":
                war_room.optimize()
            else:
                # 에러 로그로 처리
                war_room.handle_incident(user_input)

    except KeyboardInterrupt:
        print("\n\n종료 중...")

    finally:
        war_room.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_scenarios()
    else:
        interactive_mode()
