import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env 파일 불러오기
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = os.getenv("SLACK_CHANNEL_IDS")

client = WebClient(token=SLACK_BOT_TOKEN)

try:
    result = client.chat_postMessage(
        channel=CHANNEL_ID,
        text="Hello"
    )
    logger.info(result)

except SlackApiError as e:
    logger.error(f"Error posting message: {e}")