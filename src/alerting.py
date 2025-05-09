# src/alerting.py
import logging
from slack_sdk import WebClient

logger = logging.getLogger(__name__)

def send_alert(message: str):
    # Send alert via Slack or email
    client = WebClient(token="YOUR_SLACK_TOKEN")
    try:
        client.chat_postMessage(channel="#alerts", text=message)
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
