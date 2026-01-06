import os
from datetime import datetime
from pytz import timezone
from telethon.sync import TelegramClient
from config import LOG_CHANNEL

async def log_to_channel(telethon_client: TelegramClient, user_id: int, username: str, command: str, start_time_str: str, filename: str):
    """Async function to log events to Telegram channel using Telethon."""
    print(f"[Log] Attempting to log to channel: {LOG_CHANNEL}")
    try:
        # Get current IST time
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist).strftime("%d-%m-%Y %H:%M:%S")

        log_message = (
            "📝 **New Recording Log**\n\n"
            f"👤 **User:** `{username}` (ID: `{user_id}`)\n"
            f"⏰ **Time:** `{current_time}`\n"
            f"📂 **File:** `{filename}`\n"
            f"🔖 **Command:** `{command}`\n"
            f"⏱️ **Scheduled Time:** `{start_time_str}`"
        )

        await telethon_client.send_message(
            entity=LOG_CHANNEL,
            message=log_message,
            parse_mode="markdown" # Telethon handles MarkdownV2 automatically
        )
    except Exception as e:
        print(f"Failed to log to channel: {e}")

# Make sure the function is exported
__all__ = ['log_to_channel']
