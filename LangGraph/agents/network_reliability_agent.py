import json
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

from state import GraphState

load_dotenv()

# =========================
# LLM
# =========================
model = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0
)

# =========================
# 1️⃣ 로그 → 수정 파일 찾기
# =========================
FILE_PROMPT = """
너는 네트워크/웹서버 장애 분석 전문가다.

nginx 오류 로그, 502/504 오류, SSL 인증서 오류, 파일 권한 오류 로그를 보고
수정해야 할 파일을 추정하라.

규칙:
- nginx 관련이면 nginx.conf, sites-enabled 설정 파일 포함
- SSL 관련이면 인증서 설정 파일 포함
- upstream 연결 오류면 upstream 설정 파일 포함
- 파일 권한 오류면 해당 파일 경로 포함
- 반드시 JSON 배열만 출력 (설명 없이)

예시 출력:
["nginx/nginx.conf", "nginx/sites-enabled/default"]
"""

file_agent = create_react_agent(model, tools=[])


def find_files_from_log(log_text: str) -> List[str]:
    result = file_agent.invoke({
        "messages": [("system", FILE_PROMPT), ("user", log_text)]
    })
    try:
        return json.loads(result["messages"][-1].content)
    except Exception:
        return []


# =========================
# 2️⃣ 설정 파일 → 원인 + diff
# =========================
FIX_PROMPT = """
너는 네트워크/웹서버 장애 대응 전문가다.

nginx 오류 로그와 설정 파일을 보고 수정안을 만들어라.

다루는 문제:
- 502 Bad Gateway / 504 Gateway Timeout
- nginx upstream 연결 실패
- SSL/TLS 인증서 오류
- 파일 권한(Permission Denied) 문제
- 백엔드 헬스체크 실패

반드시 아래 형식으로 출력:

[문제 원인]
- ...

[해결 방법]
- ...

[변경 Patch]
- unified diff 형식
- 파일 경로 포함
- 설명 금지
- 변경 없으면 NO_CHANGE
"""

fix_agent = create_react_agent(model, tools=[])


def generate_fix(log_text: str, code_map: Dict[str, str]) -> str:
    context = ""
    for path, content in code_map.items():
        context += f"\n===== FILE: {path} =====\n{content}\n"

    message = f"""
다음은 서버/설정 파일이다:
{context}

다음은 장애 로그이다:
{log_text}
"""
    result = fix_agent.invoke({
        "messages": [("system", FIX_PROMPT), ("user", message)]
    })
    return result["messages"][-1].content


# =========================
# 전체 파이프라인
# =========================
def run_network_fix_pipeline(log_text: str, code_repo: Dict[str, str]) -> Dict:
    print("\n===== 1️⃣ 수정 대상 파일 찾기 =====")
    files = find_files_from_log(log_text)
    print(files)

    if not files:
        return {
            "files": [],
            "analysis": "수정 대상 파일을 찾지 못했습니다.",
            "patch": None
        }

    code_map = {f: code_repo.get(f, f"# {f} 파일 내용 없음") for f in files}

    print("\n===== 2️⃣ 원인 + diff 생성 =====")
    fix_result = generate_fix(log_text, code_map)
    print(fix_result)

    return {
        "files": files,
        "analysis": fix_result,
        "patch": fix_result
    }


# =========================
# GraphState Agent
# =========================
def network_reliability_agent(state: GraphState) -> GraphState:
    """
    Network Reliability Agent
    - 502/504 오류 분석
    - nginx 설정 검사
    - 백엔드 헬스체크
    - SSL 인증서 문제
    - 파일 권한 문제 해결
    """
    event = state.event
    log_text = event.get("log", "")
    code_repo = event.get("code_repo", {})

    if not log_text:
        state.context["network"] = {
            "analysis": "로그 없음",
            "actions": None
        }
        state.logs.append("[Network-Agent] 로그 없음. 분석 스킵.")
        return state

    result = run_network_fix_pipeline(log_text, code_repo)

    state.context["network"] = {
        "files": result["files"],
        "analysis": result["analysis"],
        "patch": result["patch"],
        "actions": f"수정 대상 파일: {result['files']}"
    }

    state.logs.append(f"[Network-Agent] 분석 완료. 대상 파일: {result['files']}")
    return state