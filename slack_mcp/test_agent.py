import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CONFIG = {
    "SLACK_BOT_TOKEN": "key",
    "SLACK_TEAM_ID": "id",
    "TARGET_CHANNEL": "ch",
    "MCP_SERVER_PKG": "@modelcontextprotocol/server-slack"
}

os.environ["SLACK_BOT_TOKEN"] = CONFIG["SLACK_BOT_TOKEN"]
os.environ["SLACK_TEAM_ID"] = CONFIG["SLACK_TEAM_ID"]

def get_server_params() -> StdioServerParameters:
    command = "npx.cmd" if sys.platform == "win32" else "npx"
    
    return StdioServerParameters(
        command=command,
        args=["-y", CONFIG["MCP_SERVER_PKG"]],
        env=os.environ
    )

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

async def main():
    server_params = get_server_params()
    
    print("🔌 Connecting to Slack MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("🔹 Session initialized")

            await send_slack_message(
                session=session,
                channel_id=CONFIG["TARGET_CHANNEL"],
                text="🚀 반갑습니다! Slack MCP 테스트 코드입니다!"
            )

if __name__ == "__main__":
    asyncio.run(main())