"""
Dynamic MCP Manager - 런타임 MCP 서버 관리
문제에 따라 동적으로 MCP 서버를 추가/제거하는 핵심 엔진
"""

import json
import subprocess
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from .mcp_catalog import MCPCatalogSync, MCPServerCandidate
from .problem_analyzer import ProblemAnalyzer


@dataclass
class MCPServerInstance:
    """실행 중인 MCP 서버 인스턴스"""
    name: str
    package: str
    version: str
    process: Optional[subprocess.Popen] = None
    status: str = "stopped"  # stopped, starting, running, error
    usage_count: int = 0


class DynamicMCPManager:
    """Dynamic MCP 관리자"""

    def __init__(self, config_path: str = ".war-room/mcp-config.json"):
        """
        Args:
            config_path: MCP 설정 파일 경로
        """
        self.config_path = Path(config_path)
        self.catalog = MCPCatalogSync()
        self.analyzer = ProblemAnalyzer()
        self.active_servers: Dict[str, MCPServerInstance] = {}

        # 설정 디렉토리 생성
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # 기존 설정 로드
        self._load_config()

    def _load_config(self):
        """기존 설정 로드"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    # 저장된 서버 정보 복원
                    for server_data in data.get("servers", []):
                        instance = MCPServerInstance(**server_data)
                        self.active_servers[instance.name] = instance
            except Exception:
                pass  # 첫 실행 시 파일 없음

    def _save_config(self):
        """현재 설정 저장"""
        try:
            data = {
                "servers": [
                    {k: v for k, v in asdict(server).items() if k != "process"}
                    for server in self.active_servers.values()
                ]
            }
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ 설정 저장 실패: {e}")

    def handle_problem(self, error_log: str, auto_approve: bool = False) -> Dict:
        """
        문제 분석 및 자동 해결

        Args:
            error_log: 에러 로그
            auto_approve: 자동 승인 여부 (False면 사용자 확인 필요)

        Returns:
            처리 결과 딕셔너리
        """
        # 1단계: 문제 분석
        keywords = self.analyzer.analyze_problem(error_log)

        if not keywords:
            return {
                "success": False,
                "message": "문제 분석 실패: 키워드를 찾을 수 없습니다"
            }

        # 2단계: MCP 서버 검색
        candidates = self.catalog.search_servers(keywords, limit=3)

        if not candidates:
            return {
                "success": False,
                "message": "적합한 MCP 서버를 찾을 수 없습니다"
            }

        # 3단계: 최적 후보 선택
        best_candidate = candidates[0]
        print(f"✅ 발견: {best_candidate.name} (점수: {best_candidate.score:.0f}/100)")

        # 4단계: 승인 확인
        if not auto_approve:
            approval = input("추가하시겠습니까? (yes/no): ").strip().lower()
            if approval not in ['yes', 'y']:
                return {
                    "success": False,
                    "message": "사용자가 거부했습니다"
                }

        # 5단계: 서버 추가
        result = self.add_server(best_candidate)

        return result

    def add_server(self, candidate: MCPServerCandidate) -> Dict:
        """
        MCP 서버 추가

        Args:
            candidate: 추가할 서버 정보

        Returns:
            성공 여부 및 메시지
        """
        # 이미 추가된 서버인지 확인
        if candidate.name in self.active_servers:
            self.active_servers[candidate.name].usage_count += 1
            self._save_config()
            return {
                "success": True,
                "message": f"기존 서버 재사용: {candidate.name}",
                "server": candidate.name
            }

        # NPM 패키지 설치 (실제로는 npx로 실행하므로 생략 가능)
        # 여기서는 메타데이터만 저장
        instance = MCPServerInstance(
            name=candidate.name,
            package=candidate.name,
            version=candidate.version,
            status="installed",
            usage_count=1
        )

        self.active_servers[candidate.name] = instance
        self._save_config()

        return {
            "success": True,
            "message": f"서버 추가 완료: {candidate.name}",
            "server": candidate.name
        }

    def remove_server(self, server_name: str) -> Dict:
        """
        MCP 서버 제거

        Args:
            server_name: 제거할 서버 이름

        Returns:
            성공 여부 및 메시지
        """
        if server_name not in self.active_servers:
            return {
                "success": False,
                "message": f"서버를 찾을 수 없습니다: {server_name}"
            }

        # 프로세스 종료 (실행 중인 경우)
        instance = self.active_servers[server_name]
        if instance.process:
            instance.process.terminate()

        # 목록에서 제거
        del self.active_servers[server_name]
        self._save_config()

        print(f"✅ 서버 제거 완료: {server_name}")
        return {
            "success": True,
            "message": f"서버 제거 완료: {server_name}"
        }

    def list_servers(self) -> List[Dict]:
        """활성화된 서버 목록"""
        return [
            {
                "name": server.name,
                "version": server.version,
                "status": server.status,
                "usage_count": server.usage_count
            }
            for server in self.active_servers.values()
        ]

    def get_stats(self) -> Dict:
        """통계 정보"""
        return {
            "total_servers": len(self.active_servers),
            "running_servers": sum(1 for s in self.active_servers.values() if s.status == "running"),
            "total_usage": sum(s.usage_count for s in self.active_servers.values()),
            "most_used": max(
                self.active_servers.values(),
                key=lambda s: s.usage_count
            ).name if self.active_servers else None
        }

    def optimize(self):
        """
        사용 패턴 기반 최적화
        - 사용 빈도가 낮은 서버 제거
        - 자주 사용되는 서버는 유지
        """
        # 사용 횟수가 0인 서버 찾기
        unused = [
            name for name, server in self.active_servers.items()
            if server.usage_count == 0
        ]

        if unused:
            print(f"\n🧹 최적화: {len(unused)}개 미사용 서버 제거")
            for name in unused:
                self.remove_server(name)

    def close(self):
        """리소스 정리"""
        # 모든 프로세스 종료
        for server in self.active_servers.values():
            if server.process:
                server.process.terminate()

        self.catalog.close()
        print("✅ Dynamic MCP Manager 종료")
