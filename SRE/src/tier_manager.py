"""
Tier-based Server Manager
사용 패턴에 따른 MCP 서버 계층화 관리
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ServerTier(Enum):
    """서버 티어"""
    TIER_1_HOT = "tier1_hot"      # 자주 사용 (주 10회+)
    TIER_2_WARM = "tier2_warm"    # 가끔 사용 (주 3-9회)
    TIER_3_COLD = "tier3_cold"    # 드물게 사용 (주 0-2회)

    def __str__(self):
        return self.value

    @property
    def display_name(self) -> str:
        """표시용 이름"""
        names = {
            self.TIER_1_HOT: "Hot Pool (자주 사용)",
            self.TIER_2_WARM: "Warm Pool (가끔 사용)",
            self.TIER_3_COLD: "Cold Pool (드물게 사용)"
        }
        return names[self]

    @property
    def expected_start_time(self) -> int:
        """예상 시작 시간 (초)"""
        times = {
            self.TIER_1_HOT: 3,
            self.TIER_2_WARM: 5,
            self.TIER_3_COLD: 30
        }
        return times[self]


@dataclass
class ServerInfo:
    """서버 정보 및 통계"""
    name: str
    package: str
    version: str
    tier: ServerTier

    # 통계
    total_usage_count: int = 0
    weekly_usage_count: int = 0
    last_used_at: Optional[datetime] = None
    first_seen_at: Optional[datetime] = None

    # 이미지 정보
    image_name: Optional[str] = None
    image_cached: bool = False
    image_size_mb: int = 0

    # 메타데이터
    last_tier_adjustment: Optional[datetime] = None

    def should_promote(self) -> bool:
        """Tier 승격 필요 여부"""
        if self.tier == ServerTier.TIER_3_COLD and self.weekly_usage_count >= 3:
            return True
        if self.tier == ServerTier.TIER_2_WARM and self.weekly_usage_count >= 10:
            return True
        return False

    def should_demote(self) -> bool:
        """Tier 강등 필요 여부"""
        if self.tier == ServerTier.TIER_1_HOT and self.weekly_usage_count < 3:
            return True
        if self.tier == ServerTier.TIER_2_WARM and self.weekly_usage_count < 1:
            return True
        return False

    def record_usage(self):
        """사용 기록"""
        self.total_usage_count += 1
        self.weekly_usage_count += 1
        self.last_used_at = datetime.now()

        if self.first_seen_at is None:
            self.first_seen_at = datetime.now()


class TierManager:
    """
    Tier 기반 MCP 서버 관리자

    주요 기능:
    - 사용 패턴 기반 자동 티어 조정
    - 티어별 이미지 캐싱 전략
    - 주간 사용 통계 리셋
    - 티어 최적화
    """

    def __init__(self, config_path: str = ".war-room/tier-config.json"):
        """
        Args:
            config_path: 티어 설정 파일 경로
        """
        self.config_path = Path(config_path)
        self.servers: Dict[str, ServerInfo] = {}
        self.tier_thresholds = {
            ServerTier.TIER_1_HOT: 10,   # 주간 10회 이상
            ServerTier.TIER_2_WARM: 3,   # 주간 3-9회
            ServerTier.TIER_3_COLD: 0    # 주간 0-2회
        }

        # 설정 디렉토리 생성
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # 기존 설정 로드
        self._load_config()

        # 마지막 주간 리셋 시간
        self.last_weekly_reset = self._get_last_weekly_reset()

    def _load_config(self):
        """설정 파일 로드"""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            for server_data in data.get("servers", []):
                # datetime 복원
                if server_data.get("last_used_at"):
                    server_data["last_used_at"] = datetime.fromisoformat(
                        server_data["last_used_at"]
                    )
                if server_data.get("first_seen_at"):
                    server_data["first_seen_at"] = datetime.fromisoformat(
                        server_data["first_seen_at"]
                    )
                if server_data.get("last_tier_adjustment"):
                    server_data["last_tier_adjustment"] = datetime.fromisoformat(
                        server_data["last_tier_adjustment"]
                    )

                # ServerTier enum 복원
                server_data["tier"] = ServerTier(server_data["tier"])

                server = ServerInfo(**server_data)
                self.servers[server.name] = server

            logger.info(f"티어 설정 로드 완료: {len(self.servers)}개 서버")

        except Exception as e:
            logger.error(f"티어 설정 로드 실패: {e}")

    def _save_config(self):
        """설정 파일 저장"""
        try:
            data = {
                "servers": [
                    {
                        **asdict(server),
                        "tier": server.tier.value,
                        "last_used_at": server.last_used_at.isoformat() if server.last_used_at else None,
                        "first_seen_at": server.first_seen_at.isoformat() if server.first_seen_at else None,
                        "last_tier_adjustment": server.last_tier_adjustment.isoformat() if server.last_tier_adjustment else None,
                    }
                    for server in self.servers.values()
                ],
                "last_weekly_reset": datetime.now().isoformat()
            }

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"티어 설정 저장 실패: {e}")

    def register_server(
        self,
        name: str,
        package: str,
        version: str,
        initial_tier: Optional[ServerTier] = None
    ) -> ServerInfo:
        """
        새 서버 등록

        Args:
            name: 서버 이름
            package: NPM 패키지명
            version: 버전
            initial_tier: 초기 티어 (기본: TIER_3_COLD)

        Returns:
            ServerInfo: 등록된 서버 정보
        """
        if name in self.servers:
            logger.info(f"이미 등록된 서버: {name}")
            return self.servers[name]

        # Official 서버는 Tier 2로 시작
        tier = initial_tier or (
            ServerTier.TIER_2_WARM if "@modelcontextprotocol" in name
            else ServerTier.TIER_3_COLD
        )

        server = ServerInfo(
            name=name,
            package=package,
            version=version,
            tier=tier,
            first_seen_at=datetime.now()
        )

        self.servers[name] = server
        self._save_config()

        logger.info(f"새 서버 등록: {name} (Tier: {tier.display_name})")
        return server

    def record_usage(self, server_name: str):
        """
        서버 사용 기록

        Args:
            server_name: 서버 이름
        """
        if server_name not in self.servers:
            logger.warning(f"미등록 서버 사용: {server_name}")
            return

        server = self.servers[server_name]
        server.record_usage()
        self._save_config()

        logger.debug(f"사용 기록: {server_name} (주간: {server.weekly_usage_count}회)")

    def get_tier(self, server_name: str) -> Optional[ServerTier]:
        """서버의 현재 티어 조회"""
        server = self.servers.get(server_name)
        return server.tier if server else None

    def get_servers_by_tier(self, tier: ServerTier) -> List[ServerInfo]:
        """특정 티어의 서버 목록"""
        return [
            server for server in self.servers.values()
            if server.tier == tier
        ]

    def adjust_tiers(self) -> Dict[str, str]:
        """
        모든 서버의 티어 자동 조정

        Returns:
            변경 사항 딕셔너리 {서버명: "tier1 -> tier2"}
        """
        changes = {}

        for name, server in self.servers.items():
            old_tier = server.tier
            new_tier = self._calculate_tier(server)

            if old_tier != new_tier:
                server.tier = new_tier
                server.last_tier_adjustment = datetime.now()
                changes[name] = f"{old_tier.display_name} → {new_tier.display_name}"

                logger.info(f"티어 조정: {name} - {changes[name]}")

        if changes:
            self._save_config()

        return changes

    def _calculate_tier(self, server: ServerInfo) -> ServerTier:
        """사용 패턴 기반 티어 계산"""
        usage = server.weekly_usage_count

        # Official 서버는 최소 Tier 2
        is_official = "@modelcontextprotocol" in server.name

        if usage >= self.tier_thresholds[ServerTier.TIER_1_HOT]:
            return ServerTier.TIER_1_HOT
        elif usage >= self.tier_thresholds[ServerTier.TIER_2_WARM]:
            return ServerTier.TIER_2_WARM
        elif is_official and server.tier == ServerTier.TIER_2_WARM:
            # Official은 Tier 2 유지
            return ServerTier.TIER_2_WARM
        else:
            return ServerTier.TIER_3_COLD

    def reset_weekly_stats(self):
        """주간 통계 리셋 (매주 월요일 00:00)"""
        logger.info("주간 통계 리셋 중...")

        for server in self.servers.values():
            server.weekly_usage_count = 0

        self.last_weekly_reset = datetime.now()
        self._save_config()

        logger.info(f"주간 통계 리셋 완료: {len(self.servers)}개 서버")

    def _get_last_weekly_reset(self) -> datetime:
        """마지막 주간 리셋 시간 조회"""
        if not self.config_path.exists():
            return datetime.now()

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                reset_str = data.get("last_weekly_reset")
                if reset_str:
                    return datetime.fromisoformat(reset_str)
        except Exception:
            pass

        return datetime.now()

    def should_reset_weekly(self) -> bool:
        """주간 리셋 필요 여부 확인 (7일 경과)"""
        return datetime.now() - self.last_weekly_reset > timedelta(days=7)

    def optimize(self):
        """
        티어 최적화
        - 주간 리셋 확인
        - 티어 자동 조정
        - 미사용 서버 정리
        """
        # 주간 리셋
        if self.should_reset_weekly():
            self.reset_weekly_stats()

        # 티어 조정
        changes = self.adjust_tiers()

        if changes:
            logger.info(f"티어 최적화 완료: {len(changes)}개 서버 조정")
            for name, change in changes.items():
                logger.info(f"  - {name}: {change}")
        else:
            logger.info("티어 최적화: 변경 사항 없음")

        return changes

    def get_stats(self) -> Dict:
        """통계 정보"""
        tier_counts = {
            tier: len(self.get_servers_by_tier(tier))
            for tier in ServerTier
        }

        total_usage = sum(s.total_usage_count for s in self.servers.values())
        weekly_usage = sum(s.weekly_usage_count for s in self.servers.values())

        # 가장 많이 사용된 서버
        most_used = None
        if self.servers:
            most_used = max(
                self.servers.values(),
                key=lambda s: s.total_usage_count
            )

        return {
            "total_servers": len(self.servers),
            "tier_distribution": {
                tier.display_name: count
                for tier, count in tier_counts.items()
            },
            "total_usage": total_usage,
            "weekly_usage": weekly_usage,
            "most_used_server": {
                "name": most_used.name,
                "tier": most_used.tier.display_name,
                "usage": most_used.total_usage_count,
                "weekly_usage": most_used.weekly_usage_count
            } if most_used else None,
            "last_weekly_reset": self.last_weekly_reset.isoformat()
        }

    def get_recommended_servers(self, limit: int = 5) -> List[ServerInfo]:
        """
        추천 서버 목록 (자주 사용되는 것 우선)

        Args:
            limit: 반환할 최대 서버 수

        Returns:
            사용 빈도 순으로 정렬된 서버 목록
        """
        servers = sorted(
            self.servers.values(),
            key=lambda s: (s.tier.value, -s.weekly_usage_count)
        )
        return servers[:limit]

    def should_cache_image(self, server_name: str) -> bool:
        """
        이미지 캐싱 여부 결정

        Tier 1/2는 항상 캐싱
        Tier 3는 최근 사용 시만
        """
        server = self.servers.get(server_name)
        if not server:
            return False

        # Tier 1, 2는 항상 캐싱
        if server.tier in [ServerTier.TIER_1_HOT, ServerTier.TIER_2_WARM]:
            return True

        # Tier 3는 최근 7일 내 사용 시만
        if server.last_used_at:
            days_since_use = (datetime.now() - server.last_used_at).days
            return days_since_use < 7

        return False

    def mark_image_cached(self, server_name: str, image_name: str, size_mb: int):
        """이미지 캐싱 완료 표시"""
        server = self.servers.get(server_name)
        if server:
            server.image_name = image_name
            server.image_cached = True
            server.image_size_mb = size_mb
            self._save_config()
            logger.info(f"이미지 캐싱 완료: {server_name} ({size_mb}MB)")

    def get_cache_summary(self) -> Dict:
        """캐시 요약 정보"""
        cached_servers = [s for s in self.servers.values() if s.image_cached]
        total_size = sum(s.image_size_mb for s in cached_servers)

        return {
            "cached_count": len(cached_servers),
            "total_size_mb": total_size,
            "by_tier": {
                tier.display_name: {
                    "count": sum(1 for s in cached_servers if s.tier == tier),
                    "size_mb": sum(s.image_size_mb for s in cached_servers if s.tier == tier)
                }
                for tier in ServerTier
            }
        }
