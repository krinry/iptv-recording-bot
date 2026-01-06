from telethon import events
from scheduler import cancel_scheduled_recording, scheduled_jobs
from utils.admin_checker import is_admin
from config import ADMIN_ID

async def handle_cancel(event: events.NewMessage):
    user_id = event.sender_id

    args = event.text.split()
    if len(args) > 1 and args[1].isdigit():
        message_id = int(args[1])
    elif event.is_reply:
        reply_message = await event.get_reply_message()
        message_id = reply_message.id
    else:
        await event.reply("Please reply to the message of the recording you want to cancel or provide the message ID.")
        return

    if message_id not in scheduled_jobs:
        await event.reply("❌ Recording not found.")
        return

    job_user_id = scheduled_jobs[message_id].get('user_id')

    if user_id == job_user_id or user_id in ADMIN_ID:
        if cancel_scheduled_recording(message_id):
            await event.reply("✅ Recording cancelled successfully.")
        else:
            await event.reply("❌ Could not cancel the recording. It might have already completed or failed.")
    else:
        await event.reply("⚠️ You are not authorized to cancel this recording.")

async def handle_cancel_button(event: events.CallbackQuery):
    user_id = event.sender_id
    message_id = int(event.data.decode().split('_')[-1])

    if message_id not in scheduled_jobs:
        await event.answer("Recording not found.", alert=True)
        return

    job_user_id = scheduled_jobs[message_id].get('user_id')

    if user_id == job_user_id or user_id in ADMIN_ID:
        if cancel_scheduled_recording(message_id):
            await event.answer("Recording cancelled successfully.", alert=True)
        else:
            await event.answer("Could not cancel the recording.", alert=True)
    else:
        await event.answer("You are not authorized to cancel this recording.", alert=True)