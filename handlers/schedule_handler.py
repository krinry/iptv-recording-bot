import shlex  # Add this import at the top
from datetime import datetime
from telethon import events
from telethon.sync import TelegramClient
from utils.admin_checker import is_admin
from scheduler import schedule_recording
from utils.logging import log_to_channel
from config import ADMIN_ID

async def handle_schedule(event: events.NewMessage):
    # Ensure the command is actually /schedule or /s
    command = event.text.split()[0].lower()
    if command not in ['/schedule', '/s']:
        return # Ignore if it's not the schedule command

    user_id = event.sender_id
    
    # Check if the user is a permanent or temporary admin
    if not await is_admin(user_id, event.chat_id):
        await event.reply(
            "⚠️ **Unauthorized Access**\n\n"
            "You do not have permission to use this bot.\n"
            "Please request admin access using the /start command.",
            parse_mode="Markdown"
        )
        return
    
    # Proceed with the command logic
    try:
        parts = shlex.split(event.text)
        if len(parts) < 7:
            await event.reply(
                "❗ **Invalid Format!**\n\n"
                "Use this format:\n"
                "`/schedule \"url\" DD-MM-YYYY HH:MM:SS duration channel title`",
                parse_mode="Markdown"
            )
            return

        url = parts[1].strip('"')
        date = parts[2]
        time_part = parts[3]
        duration = parts[4]
        channel = parts[5]
        title = " ".join(parts[6:])
        start_time_str = f"{date} {time_part}"

        try:
            datetime.strptime(start_time_str, "%d-%m-%Y %H:%M:%S")
        except ValueError:
            await event.reply(
                "❌ **Invalid date/time format!**\nUse `DD-MM-YYYY HH:MM:SS`",
                parse_mode="Markdown"
            )
            return

        await event.reply(
            f"**Recording Scheduled Successfully!**\n\n"
            f"**Title:** `{title}`\n"
            f"**Channel:** `{channel}`\n"
            f"**Time:** `{start_time_str}`\n"
            f"**Duration:** `{duration}`",
            parse_mode="Markdown"
        )

        username = event.sender.username or "Unknown"
        await log_to_channel(event.client, user_id, username, event.text, start_time_str, title)
        
        await schedule_recording(event.client, url, start_time_str, duration, channel, title, event.chat_id, event.message.id)

    except Exception as e:
        await event.reply(f"❌ Error: `{str(e)}`", parse_mode="Markdown")
