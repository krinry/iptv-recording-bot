import os
from telethon import events
from config import RECORDINGS_DIR
from utils.admin_checker import is_admin
from uploader import send_video

async def handle_list_files(event: events.NewMessage):
    if not await is_admin(event.sender_id, event.chat_id):
        await event.reply("⚠️ Unauthorized Access", parse_mode="Markdown")
        return

    try:
        files = os.listdir(RECORDINGS_DIR)
        if not files:
            await event.reply("No recordings found.")
            return

        message = "**Recorded Files:**\n\n"
        for f in files:
            message += f"- `{f}`\n"
        
        await event.reply(message, parse_mode="Markdown")

    except Exception as e:
        await event.reply(f"❌ Error listing files: {e}")

async def handle_upload_file(event: events.NewMessage):
    if not await is_admin(event.sender_id, event.chat_id):
        await event.reply("⚠️ Unauthorized Access", parse_mode="Markdown")
        return

    try:
        parts = event.text.split(" ", 1)
        if len(parts) < 2:
            await event.reply("**Usage:** /upload <filename>")
            return

        filename = parts[1]
        file_path = os.path.join(RECORDINGS_DIR, filename)

        if not os.path.exists(file_path):
            await event.reply(f"File `{filename}` not found.")
            return

        await event.reply(f"Uploading `{filename}`...")
        await send_video(
            file_path=file_path,
            caption=filename,
            chat_id=event.chat_id,
            user_msg_id=event.message.id
        )

    except Exception as e:
        await event.reply(f"❌ Error uploading file: {e}")

async def handle_delete_file(event: events.NewMessage):
    if not await is_admin(event.sender_id, event.chat_id):
        await event.reply("⚠️ Unauthorized Access", parse_mode="Markdown")
        return

    try:
        parts = event.text.split(" ", 1)
        if len(parts) < 2:
            await event.reply("**Usage:** /delete <filename>")
            return

        filename = parts[1]
        file_path = os.path.join(RECORDINGS_DIR, filename)

        if not os.path.exists(file_path):
            await event.reply(f"File `{filename}` not found.")
            return

        os.remove(file_path)
        await event.reply(f"File `{filename}` deleted successfully.")

    except Exception as e:
        await event.reply(f"❌ Error deleting file: {e}")
