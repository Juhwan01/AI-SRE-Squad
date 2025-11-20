import asyncio
import json
import sys
import os
import boto3
from typing import Optional, Any
from contextlib import AsyncExitStack

# MCP Libraries
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# -- 상수 설정 --
# AWS CLI 인증 정보를 사용합니다. 필요시 리전 및 모델 ID 변경 가능.
AWS_REGION = "us-east-1"
CLAUDE_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'


class MCPClient:
    def __init__(self):
        # 1. MCP 세션 관리용 객체 초기화
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # 2. Boto3 Bedrock 클라이언트 초기화. AWS CLI 설정이 자동으로 사용됨.
        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=AWS_REGION
        )

    async def _invoke_claude_with_tools(self, current_messages: list[dict], current_tools: list[dict]) -> dict:
        """Bedrock에 Claude 3 모델을 호출하는 비동기 헬퍼 함수"""
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": current_messages,
            "tools": current_tools
        }
        
        # Boto3는 동기식이므로, asyncio.to_thread로 감싸 비동기 환경에서 사용합니다.
        response_body = await asyncio.to_thread(
            self.bedrock.invoke_model,
            modelId=CLAUDE_MODEL_ID,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(payload)
        )
        return json.loads(response_body.get('body').read())

    async def connect_to_server(self, server_script_path: str):
        """MCP 서버에 연결 및 초기화"""
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """쿼리 처리 및 도구 호출 관리"""
        # Messages API 형식에 맞춰 질문을 리스트로 구성
        messages = [
            {"role": "user", "content": [{"type": "text", "text": query}]}
        ]

        # 1. 서버로부터 도구 목록 가져오기
        tools_response = await self.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in tools_response.tools]

        # 2. 초기 Claude 호출 (Bedrock 사용)
        bedrock_response = await self._invoke_claude_with_tools(messages, available_tools)
        print(f"\n[DEBUG] Initial response stop_reason: {bedrock_response.get('stop_reason')}")

        final_text = []
        max_iterations = 5  # 무한 루프 방지
        iteration = 0

        # 3. 도구 호출(Tool Call) 처리 루프: 도구 사용 요청이 없을 때까지 반복
        while iteration < max_iterations:
            iteration += 1
            print(f"\n[DEBUG] Iteration {iteration}, stop_reason: {bedrock_response.get('stop_reason')}")

            # 응답에서 tool_use 타입의 콘텐츠를 찾습니다.
            tool_uses = [c for c in bedrock_response.get('content', []) if c['type'] == 'tool_use']
            print(f"[DEBUG] Found {len(tool_uses)} tool uses")

            if not tool_uses:
                # 도구 사용 요청이 없으면 최종 텍스트만 추출하고 루프 종료
                for content in bedrock_response.get('content', []):
                    if content['type'] == 'text':
                        final_text.append(content['text'])
                print(f"[DEBUG] No tool uses, breaking. Final text length: {len(final_text)}")
                break
            
            # --- 3a. Claude의 Tool Use 요청 처리 ---
            # Claude의 응답을 메시지 리스트에 추가 (Assistant 역할)
            messages.append({"role": "assistant", "content": bedrock_response['content']})

            tool_results = []
            for tool_use in tool_uses:
                tool_name = tool_use['name']
                tool_args = tool_use['input']
                tool_use_id = tool_use['id']

                # 3b. MCP 서버에 도구 실행 요청
                result = await self.session.call_tool(tool_name, tool_args)

                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # 3c. 도구 실행 결과를 메시지 리스트에 추가 (Tool Result 역할)
                # result.content는 TextContent 객체의 리스트이므로 텍스트 추출 필요
                result_text = ""
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        result_text += content_item.text

                print(f"[DEBUG] Tool result (first 300 chars): {result_text[:300]}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": [{"type": "text", "text": result_text}]
                })
                
            # 3d. 도구 결과를 담아 User 메시지로 다시 전송
            messages.append({"role": "user", "content": tool_results})

            # 3e. 도구 결과를 바탕으로 Claude에게 다음 응답 요청
            bedrock_response = await self._invoke_claude_with_tools(messages, available_tools)

        # 루프 종료 후 최종 응답 확인
        if iteration >= max_iterations:
            print(f"[DEBUG] Max iterations reached")

        return "\n".join(final_text) if final_text else "No response generated."

    async def chat_loop(self):
        """대화형 채팅 루프"""
        print("\nMCP Client Started (via AWS Bedrock)!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """자원 정리"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    if 'sys' not in globals():
        import sys
        
    asyncio.run(main())