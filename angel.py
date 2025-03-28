import os
from pyrogram import Client, filters
from pytube import YouTube

# Hardcoded variables instead of using .env
BOT_TOKEN = "7591396387:AAHqh_ARascqC6EwQiGPMiBCGj96K6sxJwY"
API_ID = 15787995
API_HASH = "e51a3154d2e0c45e5ed70251d68382de"

# Initialize Pyrogram Client
app = Client("yt_downloader_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

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
        video = yt.streams.get_highest_resolution()
        video_path = video.download()
        
        await client.send_video(
            chat_id=message.chat.id,
            video=video_path,
            caption=f"🎬 **{yt.title}**\n\nDownloaded successfully!"
        )
        os.remove(video_path)  # Clean up after sending
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

if __name__ == "__main__":
    app.run()
