from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class GraphState(BaseModel):
    # 1) Supervisor가 최초로 입력받는 장애 이벤트 정보
    event: Dict[str, Any] = {}
    # 예: {"type": "db_connection_error", "service": "auth", "timestamp": ...}

    # 2) Supervisor가 다음에 호출할 전문가 에이전트를 결정하여 기록
    next_agent: Optional[str] = None

    # 3) 각 에이전트의 분석 결과/조치 내용을 저장
    context: Dict[str, Any] = {}

    # 4) 전체 실행 로그 (모든 Agent가 append)
    logs: List[str] = []

    # 5) 최종 결과(Manager가 Slack 보고서 생성 시 여기에 저장)
    result: Optional[Any] = None
