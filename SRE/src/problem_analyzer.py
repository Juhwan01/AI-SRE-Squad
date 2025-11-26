"""
Problem Analyzer - 문제 분석 및 도구 추론
AI를 활용한 장애 로그 분석 및 필요한 MCP 서버 추론
"""

import re
from typing import List, Dict, Tuple
from anthropic import Anthropic


class ProblemAnalyzer:
    """문제 분석 및 도구 추론 엔진"""

    # 간단한 패턴 매칭 규칙 (AI 호출 전 빠른 필터링)
    PATTERN_RULES = {
        "docker": [
            r"docker",
            r"container",
            r"image.*not found",
            r"cannot connect to the docker daemon"
        ],
        "kubernetes": [
            r"kubectl",
            r"k8s",
            r"pod",
            r"deployment",
            r"service.*kubernetes"
        ],
        "postgres": [
            r"postgres",
            r"psql",
            r"pg_",
            r"database.*connection"
        ],
        "redis": [
            r"redis",
            r"ECONNREFUSED.*6379",
            r"cache"
        ],
        "aws": [
            r"aws",
            r"s3",
            r"ec2",
            r"lambda",
            r"dynamodb"
        ],
        "mongodb": [
            r"mongodb",
            r"mongo",
            r"ECONNREFUSED.*27017"
        ]
    }

    def __init__(self, anthropic_api_key: str = None):
        """
        Args:
            anthropic_api_key: Anthropic API 키 (옵션, 없으면 패턴 매칭만 사용)
        """
        self.anthropic_client = None
        if anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=anthropic_api_key)

    def analyze_problem(self, error_log: str) -> List[str]:
        """
        문제 분석 및 필요한 도구 키워드 추출

        Args:
            error_log: 에러 로그 또는 문제 설명

        Returns:
            검색 키워드 리스트 (우선순위 순)
        """
        # 1단계: 빠른 패턴 매칭
        pattern_keywords = self._pattern_match(error_log)

        # 2단계: AI 분석 (옵션)
        if self.anthropic_client:
            ai_keywords = self._ai_analyze(error_log)
            # AI 결과와 패턴 결과 병합 (AI 우선)
            combined = ai_keywords + [k for k in pattern_keywords if k not in ai_keywords]
            return combined[:5]  # 최대 5개

        return pattern_keywords[:5]

    def _pattern_match(self, text: str) -> List[str]:
        """패턴 매칭을 통한 키워드 추출"""
        text_lower = text.lower()
        matches = []

        for keyword, patterns in self.PATTERN_RULES.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    if keyword not in matches:
                        matches.append(keyword)
                    break

        return matches

    def _ai_analyze(self, error_log: str) -> List[str]:
        """AI를 활용한 심층 분석"""
        try:
            prompt = f"""다음 에러 로그를 분석하고, 이 문제를 해결하기 위해 필요한 시스템/도구를 추론하세요.

에러 로그:
```
{error_log}
```

다음 형식으로 답변하세요:
1. 문제 요약: [한 문장]
2. 필요한 도구: [쉼표로 구분된 키워드, 최대 5개]

예시:
1. 문제 요약: Redis 서버에 연결할 수 없습니다
2. 필요한 도구: redis, cache, connection pool

답변:"""

            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            return self._parse_ai_response(content)

        except Exception as e:
            print(f"⚠️ AI 분석 실패: {e}")
            return []

    def _parse_ai_response(self, response: str) -> List[str]:
        """AI 응답 파싱"""
        try:
            # "필요한 도구:" 라인 찾기
            lines = response.split("\n")
            for line in lines:
                if "필요한 도구" in line or "도구:" in line:
                    # 콜론 뒤의 내용 추출
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        keywords_str = parts[1].strip()
                        # 쉼표로 분리
                        keywords = [k.strip() for k in keywords_str.split(",")]
                        return [k for k in keywords if k]
            return []
        except Exception as e:
            print(f"⚠️ AI 응답 파싱 실패: {e}")
            return []

    def generate_search_strategy(self, keywords: List[str]) -> List[Tuple[str, float]]:
        """
        검색 전략 생성 (키워드별 우선순위)

        Args:
            keywords: 키워드 리스트

        Returns:
            (키워드, 우선순위) 튜플 리스트
        """
        # 간단한 우선순위 부여
        # 첫 번째 키워드가 가장 중요
        strategy = []
        for i, keyword in enumerate(keywords):
            priority = 1.0 - (i * 0.1)  # 1.0, 0.9, 0.8, ...
            strategy.append((keyword, priority))

        return strategy


# MVP용 간단한 버전
def quick_analyze(error_log: str) -> List[str]:
    """
    빠른 문제 분석 (AI 없이 패턴 매칭만)

    Args:
        error_log: 에러 로그

    Returns:
        검색 키워드 리스트
    """
    analyzer = ProblemAnalyzer()
    return analyzer.analyze_problem(error_log)
