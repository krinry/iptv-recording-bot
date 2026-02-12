from telethon import events
from scheduler import cancel_scheduled_recording, scheduled_jobs
from utils.admin_checker import is_admin
from config import ADMIN_ID

async def handle_cancel(event: events.NewMessage):
    """Handle /cancel command — cancel a recording by reply or message ID"""
    user_id = event.sender_id

    args = event.text.split()
    if len(args) > 1 and args[1].isdigit():
        message_id = int(args[1])
    elif event.is_reply:
        reply_message = await event.get_reply_message()
        message_id = reply_message.id
    else:
        await event.reply(
            "❌ **Usage:**\n"
            "`/cancel <message_id>` or reply to the recording message.",
            parse_mode="Markdown"
        )
        return

    if message_id not in scheduled_jobs:
        await event.reply("⚠️ Recording not found or already completed.")
        return

    job_user_id = scheduled_jobs[message_id].get('user_id')

    if user_id == job_user_id or user_id in ADMIN_ID:
        job = scheduled_jobs.get(message_id)
        if cancel_scheduled_recording(message_id):
            # Edit the recording status message to show cancelled
            try:
                await event.client.edit_message(
                    entity=event.chat_id,
                    message=job.get('status_msg_id') if job else None,
                    text=(
                        "⏹ **CANCELLED**\n"
                        "━━━━━━━━━━━━━━━━━━━\n\n"
                        f"🚫 Recording stopped by user\n"
                        f"👤 Cancelled by: `{user_id}`"
                    ),
                    parse_mode="Markdown",
                    buttons=None,  # Remove cancel button
                )
            except Exception:
                pass  # Status message might not exist
            await event.reply("✅ Recording cancelled successfully.")
        else:
            await event.reply("❌ Could not cancel. It may have already completed.")
    else:
        await event.reply("⚠️ You are not authorized to cancel this recording.")

async def handle_cancel_button(event: events.CallbackQuery):
    """Handle inline ❌ Cancel button click on recording messages"""
    user_id = event.sender_id
    message_id = int(event.data.decode().split('_')[-1])

    if message_id not in scheduled_jobs:
        await event.answer("Recording not found or already completed.", alert=True)
        return

    job_user_id = scheduled_jobs[message_id].get('user_id')

    if user_id == job_user_id or user_id in ADMIN_ID:
        if cancel_scheduled_recording(message_id):
            await event.answer("✅ Recording cancelled!", alert=True)
            # Edit the recording message to show cancelled status
            try:
                await event.edit(
                    text=(
                        "⏹ **CANCELLED**\n"
                        "━━━━━━━━━━━━━━━━━━━\n\n"
                        "🚫 Recording was cancelled by user.\n"
                        f"👤 `{user_id}`"
                    ),
                    parse_mode="Markdown",
                    buttons=None,  # Remove the cancel button
                )
            except Exception as e:
                print(f"[Cancel] [WARNING] Could not edit message: {e}")
        else:
            await event.answer("Could not cancel. It may have already completed.", alert=True)
    else:
        await event.answer("⚠️ You are not authorized to cancel this recording.", alert=True)