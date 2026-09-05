import asyncio
from telethon import TelegramClient
from app.config import settings
from app.bot.router import register
from app.web import app as fastapi_app
import uvicorn

client = TelegramClient("food_delivery_bot", settings.telegram_api_id, settings.telegram_api_hash)

async def serve_web():
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    register(client)
    await client.start(bot_token=settings.bot_token)
    await asyncio.gather(client.run_until_disconnected(), serve_web())

if __name__ == "__main__":
    asyncio.run(main())
