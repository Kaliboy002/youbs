import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Send me a YouTube URL and I'll try to download the video for you.\n"
        "Note: Some videos may require authentication and might not work."
    )

def download_video(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'merge_output_format': 'mp4',
        'max_filesize': 50_000_000,  # 50MB limit for Telegram
        'quiet': True,
        'no_warnings': True,
        'user_agent': random.choice(USER_AGENTS),  # Rotate user agents
        'nocheckcertificate': True,  # Bypass SSL issues
        'geo_bypass': True,  # Attempt to bypass geo-restrictions
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "Sign in to confirm" in error_msg or "bot" in error_msg:
            return "AUTH_REQUIRED"
        return error_msg
    except Exception as e:
        return str(e)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id
    
    # Send processing message
    status_msg = await update.message.reply_text("Processing your video...")
    
    # Download video
    filename = download_video(url)
    
    if os.path.exists(filename):
        # Check file size (Telegram has 50MB limit for bots)
        if os.path.getsize(filename) > 50_000_000:
            await status_msg.edit_text("Video is too large (>50MB) for Telegram!")
            os.remove(filename)
            return
            
        # Send video
        await status_msg.edit_text("Uploading video to Telegram...")
        with open(filename, 'rb') as video:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video,
                supports_streaming=True
            )
        
        # Cleanup
        await status_msg.delete()
        os.remove(filename)
    elif filename == "AUTH_REQUIRED":
        await status_msg.edit_text(
            "This video requires authentication. I can’t download it without YouTube login credentials.\n"
            "Try a different public video or check yt-dlp documentation for cookie setup."
        )
    else:
        await status_msg.edit_text(f"Error: {filename}")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Something went wrong. Please try again with a valid YouTube URL.")

def main():
    # Create the Application instance directly
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_error_handler(error)
    
    # Start polling
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
