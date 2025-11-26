"""
MCP Catalog Search and Evaluation System
NPM Registry를 활용한 MCP 서버 검색 및 평가
"""

import httpx
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone


class MCPServerCandidate(BaseModel):
    """MCP 서버 후보"""
    name: str
    description: str
    version: str
    downloads: int
    last_updated: datetime
    official: bool
    score: float = 0.0

    def calculate_score(self) -> float:
        """
        후보 평가 점수 계산
        - Official/Community: 40%
        - Download Count: 25%
        - Last Updated: 20%
        - Capabilities Match: 15%
        """
        score = 0.0

        # Official bonus (40점)
        if self.official or "@modelcontextprotocol" in self.name:
            score += 40.0

        # Download count (25점)
        # 로그 스케일로 정규화 (1000 downloads = 15점, 10000 = 20점, 100000 = 25점)
        if self.downloads > 0:
            import math
            download_score = min(25.0, math.log10(self.downloads) * 5)
            score += download_score

        # Last updated (20점)
        # 6개월 이내 = 20점, 1년 이내 = 10점, 그 이상 = 0점
        days_since_update = (datetime.now(timezone.utc) - self.last_updated).days
        if days_since_update < 180:  # 6개월
            score += 20.0
        elif days_since_update < 365:  # 1년
            score += 10.0

        # Capabilities match는 나중에 description 분석으로 추가
        # 일단 기본 15점 부여
        score += 15.0

        self.score = score
        return score


class MCPCatalog:
    """MCP Catalog 검색 엔진"""

    NPM_REGISTRY_URL = "https://registry.npmjs.org"
    NPM_SEARCH_URL = "https://registry.npmjs.com/-/v1/search"

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)

    async def search_servers(self, keywords: List[str], limit: int = 5) -> List[MCPServerCandidate]:
        """
        MCP 서버 검색

        Args:
            keywords: 검색 키워드 리스트
            limit: 반환할 최대 결과 수

        Returns:
            평가 점수 순으로 정렬된 후보 리스트
        """
        candidates = []

        for keyword in keywords:
            # NPM에서 "mcp" + keyword로 검색
            search_query = f"mcp {keyword}"
            results = await self._search_npm(search_query)

            for result in results:
                candidate = self._parse_npm_result(result)
                if candidate and candidate not in candidates:
                    candidate.calculate_score()
                    candidates.append(candidate)

        # 점수 순으로 정렬
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:limit]

    async def _search_npm(self, query: str) -> List[Dict]:
        """NPM Registry 검색"""
        try:
            response = self.client.get(
                self.NPM_SEARCH_URL,
                params={
                    "text": query,
                    "size": 20
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("objects", [])
        except Exception as e:
            print(f"NPM 검색 실패: {e}")
            return []

    def _parse_npm_result(self, result: Dict) -> Optional[MCPServerCandidate]:
        """NPM 검색 결과 파싱"""
        try:
            package = result.get("package", {})
            name = package.get("name", "")

            # MCP 서버가 아닌 패키지 필터링
            if "mcp" not in name.lower() and "server" not in name.lower():
                return None

            # 점수 정보
            score_detail = result.get("score", {}).get("detail", {})

            return MCPServerCandidate(
                name=name,
                description=package.get("description", ""),
                version=package.get("version", "0.0.0"),
                downloads=score_detail.get("popularity", 0) * 1000000,  # 근사치
                last_updated=datetime.fromisoformat(
                    package.get("date", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")
                ),
                official="@modelcontextprotocol" in name or "@mcp" in name
            )
        except Exception as e:
            print(f"결과 파싱 실패: {e}")
            return None

    def get_package_details(self, package_name: str) -> Optional[Dict]:
        """패키지 상세 정보 조회"""
        try:
            response = self.client.get(f"{self.NPM_REGISTRY_URL}/{package_name}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"패키지 정보 조회 실패: {e}")
            return None

    def close(self):
        """HTTP 클라이언트 종료"""
        self.client.close()


# 동기 버전 (MVP용 간단한 버전)
class MCPCatalogSync:
    """동기 버전 MCP Catalog"""

    NPM_SEARCH_URL = "https://registry.npmjs.com/-/v1/search"

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)

    def search_servers(self, keywords: List[str], limit: int = 5) -> List[MCPServerCandidate]:
        """MCP 서버 검색 (동기)"""
        candidates = []

        for keyword in keywords:
            search_query = f"mcp {keyword}"
            results = self._search_npm(search_query)

            for result in results:
                candidate = self._parse_npm_result(result)
                if candidate:
                    # 중복 체크
                    if not any(c.name == candidate.name for c in candidates):
                        candidate.calculate_score()
                        candidates.append(candidate)

        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:limit]

    def _search_npm(self, query: str) -> List[Dict]:
        """NPM Registry 검색"""
        try:
            response = self.client.get(
                self.NPM_SEARCH_URL,
                params={"text": query, "size": 20}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("objects", [])
        except Exception as e:
            print(f"❌ NPM 검색 실패: {e}")
            return []

    def _parse_npm_result(self, result: Dict) -> Optional[MCPServerCandidate]:
        """NPM 검색 결과 파싱"""
        try:
            package = result.get("package", {})
            name = package.get("name", "")

            # MCP 서버 필터링
            if "mcp" not in name.lower():
                return None

            score_detail = result.get("score", {}).get("detail", {})

            return MCPServerCandidate(
                name=name,
                description=package.get("description", ""),
                version=package.get("version", "0.0.0"),
                downloads=int(score_detail.get("popularity", 0) * 1000000),
                last_updated=datetime.fromisoformat(
                    package.get("date", datetime.now().isoformat()).replace("Z", "+00:00")
                ),
                official="@modelcontextprotocol" in name
            )
        except Exception as e:
            print(f"⚠️ 결과 파싱 실패: {e}")
            return None

    def close(self):
        self.client.close()
