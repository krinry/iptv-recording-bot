from datetime import datetime, timedelta
from telethon import events
from telethon.sync import TelegramClient
from config import ADMIN_ID
from utils.admin_checker import add_temp_admin, remove_temp_admin

async def add_temp_admin_command(event: events.NewMessage):
    if event.sender_id not in ADMIN_ID:
        await event.reply("⚠️ Unauthorized.")
        return

    parts = event.text.split()
    if len(parts) != 3:
        await event.reply("Usage: /addadmin user_id HH:MM:SS")
        return

    try:
        user_id = int(parts[1])
        hours, minutes, seconds = map(int, parts[2].split(":"))
        expiry_time = datetime.now() + timedelta(hours=hours, minutes=minutes, seconds=seconds)

        if await add_temp_admin(user_id, expiry_time):
            await event.reply(
                f"✅ Temporary admin `{user_id}` added till `{expiry_time.strftime('%Y-%m-%d %H:%M:%S')}`",
                parse_mode="Markdown"
            )
            
            await event.client.send_message(
                entity=user_id,
                message=f"🎉 **Admin Access Granted!**\n\n"
                     f"You have been granted temporary admin access till `{expiry_time.strftime('%Y-%m-%d %H:%M:%S')}`.\n\n"
                     f"Thank you for your patience! 😊",
                parse_mode="Markdown"
            )
        else:
            await event.reply(f"❌ Error adding temporary admin `{user_id}`.")

    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def remove_admin_command(event: events.NewMessage):
    if event.sender_id not in ADMIN_ID:
        await event.reply("⚠️ Unauthorized.")
        return

    parts = event.text.split()
    if len(parts) != 2:
        await event.reply("Usage: /removeadmin user_id")
        return

    try:
        user_id = int(parts[1])
        if await remove_temp_admin(user_id):
            await event.reply(
                f"✅ Temporary admin `{user_id}` removed successfully.",
                parse_mode="Markdown"
            )
        else:
            await event.reply(
                f"⚠️ User ID `{user_id}` not found in the admin list.",
                parse_mode="Markdown"
            )
    except ValueError:
        await event.reply("❌ Invalid user ID. Please provide an integer.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
