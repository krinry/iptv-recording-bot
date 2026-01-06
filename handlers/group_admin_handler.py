from telethon import events
from config import ADMIN_ID
from utils.admin_checker import add_group_admin, remove_group_admin

async def add_group_admin_command(event: events.NewMessage):
    if event.sender_id not in ADMIN_ID:
        await event.reply("⚠️ Unauthorized. Only main admins can use this command.")
        return

    parts = event.text.split()
    if len(parts) != 2:
        await event.reply("Usage: /addgroupadmin <chat_id>")
        return

    try:
        chat_id = int(parts[1])
        if await add_group_admin(chat_id):
            await event.reply(f"✅ Group `{chat_id}` added as an admin group.")
        else:
            await event.reply(f"❌ Error adding group `{chat_id}` as admin.")
    except ValueError:
        await event.reply("❌ Invalid chat ID. Please provide an integer.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def remove_group_admin_command(event: events.NewMessage):
    if event.sender_id not in ADMIN_ID:
        await event.reply("⚠️ Unauthorized. Only main admins can use this command.")
        return

    parts = event.text.split()
    if len(parts) != 2:
        await event.reply("Usage: /removegroupadmin <chat_id>")
        return

    try:
        chat_id = int(parts[1])
        if await remove_group_admin(chat_id):
            await event.reply(f"✅ Group `{chat_id}` removed from admin groups.")
        else:
            await event.reply(f"⚠️ Group `{chat_id}` not found in admin groups.")
    except ValueError:
        await event.reply("❌ Invalid chat ID. Please provide an integer.")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")
