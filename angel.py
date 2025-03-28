import os
from pyrogram import Client, filters
from pytube import YouTube
from pytube.exceptions import PytubeError
from aiohttp import web
import asyncio

# Hardcoded variables
BOT_TOKEN = "7591396387:AAHqh_ARascqC6EwQiGPMiBCGj96K6sxJwY"
API_ID = 15787995
API_HASH = "e51a3154d2e0c45e5ed70251d68382de"

# Initialize Pyrogram Client
app = Client("yt_downloader_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Dummy web server for health check
async def health_check(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    web_app = web.Application()
    web_app.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "Welcome to the YouTube Video Downloader Bot! 🎥\n\n"
        "Send me a YouTube link, and I'll download the video for you."
    )

@app.on_message(filters.regex(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"))
async def download_video(client, message):
    url = message.text.strip()
    try:
        await message.reply_text("Processing your request... ⏳")
        yt = YouTube(url)
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        video_path = video.download()
        
        await client.send_video(
            chat_id=message.chat.id,
            video=video_path,
            caption=f"🎬 **{yt.title}**\n\nDownloaded successfully!"
        )
        os.remove(video_path)
    except PytubeError as pe:
        await message.reply_text(f"Pytube Error: {str(pe)}")
    except Exception as e:
        await message.reply_text(f"General Error: {str(e)}")

async def main():
    await asyncio.gather(
        start_web_server(),
        app.start()
    )

if __name__ == "__main__":
    asyncio.run(main())
