import asyncio
import os
import sys
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ----------------------------------------------------
# 1) Load .env file
# ----------------------------------------------------
load_dotenv()

# ----------------------------------------------------
# 2) Read environment variables
# ----------------------------------------------------
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_TEAM_ID = os.getenv("SLACK_TEAM_ID")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")
MCP_SERVER_PKG = os.getenv("MCP_SERVER_PKG", "@modelcontextprotocol/server-slack")

# 환경변수 export (Slack MCP 서버가 읽도록)
os.environ["SLACK_BOT_TOKEN"] = SLACK_BOT_TOKEN
os.environ["SLACK_TEAM_ID"] = SLACK_TEAM_ID


# ----------------------------------------------------
# 3) MCP Server Parameters (npx 실행)
# ----------------------------------------------------
def get_server_params() -> StdioServerParameters:
    command = "npx.cmd" if sys.platform == "win32" else "npx"
    
    return StdioServerParameters(
        command=command,
        args=["-y", MCP_SERVER_PKG],
        env=os.environ
    )


# ----------------------------------------------------
# 4) Slack 메시지 전송 함수
# ----------------------------------------------------
async def send_slack_message(session: ClientSession, channel_id: str, text: str):
    print(f"📤 Sending message to {channel_id}...")

    try:
        result = await session.call_tool(
            name="slack_post_message",
            arguments={
                "channel_id": channel_id,
                "text": text
            }
        )

        output = result.content[0].text if result.content else "No content"
        print(f"✅ Success: {output}")

    except Exception as e:
        print(f"❌ Failed: {str(e)}")


# ----------------------------------------------------
# 5) Main
# ----------------------------------------------------
async def main():
    server_params = get_server_params()

    print("🔌 Connecting to Slack MCP server...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("🔹 Session initialized")

            await send_slack_message(
                session=session,
                channel_id=TARGET_CHANNEL,
                text="🚀 반갑습니다!"
            )

if __name__ == "__main__":
    asyncio.run(main())