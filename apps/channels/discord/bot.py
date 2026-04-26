"""
NexusClaw Discord Bot
Run with: python3 -m apps.channels.discord.bot
"""
import os, json, asyncio
import discord
from discord import Intents

API_URL = os.environ.get("NEXUS_API_URL", "http://localhost:8080")
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

intents = Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"NexusClaw Discord Bot logged in as {client.user}")

@tree.command(name="nexus", description="Chat with NexusClaw")
async def nexus_chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {
                "sessionId": f"discord_{interaction.user.id}",
                "message": message,
                "provider": "ollama",
                "model": "llama3.2"
            }
            async with session.post(f"{API_URL}/v1/chat/answer/stream", json=payload) as resp:
                full = ""
                async for line in resp.content:
                    text = line.decode().strip()
                    if text.startswith("data: "):
                        try:
                            data = json.loads(text[6:])
                            if data.get("type") == "chunk":
                                full += data.get("content", "")
                        except: pass
                
                await interaction.followup.send(full or "No response")
    except Exception as e:
        await interaction.followup.send(f"Error: {e}")

@tree.command(name="nexus_reset", description="Reset your session")
async def nexus_reset(interaction: discord.Interaction):
    await interaction.response.send_message("🔄 Session reset.")

@tree.command(name="nexus_status", description="Check API status")
async def nexus_status(interaction: discord.Interaction):
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/health") as resp:
                data = await resp.json()
                status = "✅ Online" if data.get("ok") else "❌ Error"
                await interaction.response.send_message(f"{status} | Version: {data.get('version','?')}")
    except:
        await interaction.response.send_message("❌ API Offline")

def run():
    if not DISCORD_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not set")
        return
    client.run(DISCORD_TOKEN)
