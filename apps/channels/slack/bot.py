"""
NexusClaw Slack Bot
Run with: python3 -m apps.channels.slack.bot
"""
import os, json, asyncio
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
API_URL = os.environ.get("NEXUS_API_URL", "http://localhost:8080")

async def handle_message(client: WebClient, event: dict):
    """Handle incoming Slack message."""
    if event.get("type") != "message" or event.get("subtype"):
        return
    
    user = event.get("user")
    channel = event.get("channel")
    text = event.get("text", "")
    thread_ts = event.get("thread_ts")
    
    # Ignore bot messages
    if not text:
        return
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {
                "sessionId": f"slack_{user}",
                "message": text,
                "provider": "ollama",
                "model": "llama3.2"
            }
            async with session.post(f"{API_URL}/v1/chat/answer/stream", json=payload) as resp:
                if resp.ok:
                    full = ""
                    async for line in resp.content:
                        text_line = line.decode().strip()
                        if text_line.startswith("data: "):
                            try:
                                data = json.loads(text_line[6:])
                                if data.get("type") == "chunk":
                                    full += data.get("content", "")
                            except: pass
                    
                    # Send response
                    await client.chat_postMessage(
                        channel=channel,
                        text=full or "No response",
                        thread_ts=thread_ts
                    )
                else:
                    await client.chat_postMessage(channel=channel, text="API offline", thread_ts=thread_ts)
    except Exception as e:
        await client.chat_postMessage(channel=channel, text=f"Error: {e}", thread_ts=thread_ts)

def main():
    if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
        print("Error: SLACK_BOT_TOKEN and SLACK_APP_TOKEN required")
        print("Get from: api.slack.com/apps")
        return
    
    client = WebClient(token=SLACK_BOT_TOKEN)
    socket_client = SocketModeClient(app_token=SLACK_APP_TOKEN, web_client=client)
    
    @socket_client.socket_mode_request_listeners.append
    def handle_socket_mode(req: SocketModeRequest, client: WebClient):
        if req.type == "events_api":
            client.events_api_ack(event=req.payload["event"])
            asyncio.create_task(handle_message(client, req.payload["event"]))
    
    print("NexusClaw Slack Bot running...")
    socket_client.connect()
    socket_client.send_ping()

if __name__ == "__main__":
    main()
