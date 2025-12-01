"""
Quick Demo - War Room 2.0 자동 테스트
"""
import asyncio
from src.integrated_war_room import IntegratedWarRoom


async def quick_demo():
    """빠른 데모"""
    print("\n" + "=" * 70)
    print("War Room 2.0 - Quick Demo")
    print("=" * 70)

    war_room = IntegratedWarRoom()

    try:
        await war_room.start()
        print("\n[1] 초기 상태 확인")
        await war_room.show_status()

        print("\n" + "=" * 70)
        print("[2] Docker 장애 시뮬레이션")
        print("=" * 70)

        docker_error = """
        Error: Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
        Is the docker daemon running?
        """

        result = await war_room.handle_incident(docker_error, auto_approve=True)

        if result['success']:
            print(f"\n>>> 성공: {result['message']}")
            print(f">>> 서버: {result.get('server_name')}")
            print(f">>> 컨테이너 ID: {result.get('container_id', '')[:12]}")
        else:
            print(f"\n>>> 실패: {result['message']}")

        print("\n[3] 변경된 상태 확인")
        await war_room.show_status()

        print("\n" + "=" * 70)
        print("[4] PostgreSQL 장애 시뮬레이션")
        print("=" * 70)

        pg_error = """
        psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed:
        Connection refused. Is the server running?
        """

        result = await war_room.handle_incident(pg_error, auto_approve=True)

        if result['success']:
            print(f"\n>>> 성공: {result['message']}")
            print(f">>> 서버: {result.get('server_name')}")
        else:
            print(f"\n>>> 실패: {result['message']}")

        print("\n[5] 최종 상태")
        await war_room.show_status()

        print("\n[6] 시스템 최적화")
        await war_room.optimize()

    finally:
        print("\n[7] 종료 중...")
        await war_room.shutdown()
        print("완료!")


if __name__ == "__main__":
    asyncio.run(quick_demo())
