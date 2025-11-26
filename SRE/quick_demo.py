#!/usr/bin/env python3
"""
War Room 2.0 Quick Demo
빠른 데모를 위한 간단한 스크립트
"""

from src.war_room import WarRoom


def main():
    """간단한 데모"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║              🚀 War Room 2.0 - Quick Demo                   ║
    ║                                                              ║
    ║  "AI가 문제를 보고 필요한 도구를 스스로 찾는다"              ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    war_room = WarRoom()

    # 시나리오 1: Docker 문제
    print("\n【시나리오 1】 Docker Daemon 연결 실패")
    error_1 = "Error: Cannot connect to the Docker daemon. Is the docker daemon running?"
    war_room.handle_incident(error_1, auto_approve=True)

    # 시나리오 2: PostgreSQL 문제
    print("\n【시나리오 2】 PostgreSQL 연결 실패")
    error_2 = "psql: error: connection to server at localhost (127.0.0.1) port 5432 failed: Connection refused"
    war_room.handle_incident(error_2, auto_approve=True)

    # 시나리오 3: Redis 문제
    print("\n【시나리오 3】 Redis 캐시 서버 다운")
    error_3 = "Error: ECONNREFUSED 127.0.0.1:6379. Redis connection failed."
    war_room.handle_incident(error_3, auto_approve=True)

    # 최종 상태
    print("\n" + "="*60)
    war_room.show_status()

    war_room.close()
    print("\n✅ 데모 완료")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n종료됨.")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
