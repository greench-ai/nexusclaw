"""
NexusClaw Telegram Bot
Run with: python3 -m apps.channels.telegram.bot
"""
import os, asyncio, json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

API_URL = os.environ.get("NEXUS_API_URL", "http://localhost:8080")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 NexusClaw Bot\n\n"
        "Your framework. Your rules.\n\n"
        "Commands:\n"
        "/chat <message> — Chat with Nexus\n"
        "/reset — Start new session\n"
        "/model <name> — Switch model\n"
        "/status — Connection status"
    )

async def chat_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /chat <message>")
        return
    
    message = " ".join(ctx.args)
    user_id = str(update.effective_user.id)
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {
                "sessionId": f"telegram_{user_id}",
                "message": message,
                "provider": ctx.user_data.get("provider", "ollama"),
                "model": ctx.user_data.get("model", "llama3.2")
            }
            async with session.post(f"{API_URL}/v1/chat/answer/stream", json=payload) as resp:
                if resp.ok:
                    full = ""
                    async for line in resp.content:
                        text = line.decode().strip()
                        if text.startswith("data: "):
                            try:
                                data = json.loads(text[6:])
                                if data.get("type") == "chunk":
                                    full += data.get("content", "")
                            except: pass
                    await update.message.reply_text(full or "No response")
                else:
                    await update.message.reply_text(f"Error: API offline ({resp.status})")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def reset_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["session_id"] = None
    await update.message.reply_text("🔄 Session reset. New chat started.")

async def model_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(f"Current: {ctx.user_data.get('model', 'llama3.2')}")
        return
    ctx.user_data["model"] = ctx.args[0]
    await update.message.reply_text(f"✅ Model set to {ctx.args[0]}")

async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/health") as resp:
                data = await resp.json()
                status = "✅ Online" if data.get("ok") else "❌ Error"
                await update.message.reply_text(f"{status}\nVersion: {data.get('version','?')}")
    except:
        await update.message.reply_text("❌ API Offline")

async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Try /start")

def run():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("chat", chat_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("model", model_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_cmd))
    
    print(f"NexusClaw Telegram Bot running...")
    app.run_polling()
