import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! Send me a YouTube URL and I'll try to download the video for you.\n"
        "Note: Some videos might not work due to restrictions."
    )

def get_download_link(youtube_url):
    try:
        # y2mate.is API endpoint (reverse-engineered from their site)
        api_url = "https://y2mate.is/api/convert"
        payload = {
            "url": youtube_url,
            "type": "youtube",
            "format": "mp4",
            "quality": "best"  # Could also use "720p", "480p", etc.
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Content-Type": "application/json"
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") == "success":
            return data["download_url"]
        else:
            return f"API Error: {data.get('message', 'Unknown error')}"
    except requests.RequestException as e:
        return f"Request Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id
    
    # Send processing message
    status_msg = await update.message.reply_text("Processing your video...")
    
    # Get download link
    download_url = get_download_link(url)
    
    if download_url.startswith("http"):
        # Stream video directly to Telegram
        await status_msg.edit_text("Uploading video to Telegram...")
        await context.bot.send_video(
            chat_id=chat_id,
            video=download_url,
            supports_streaming=True
        )
        await status_msg.delete()
    else:
        await status_msg.edit_text(download_url)  # Show error message

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
