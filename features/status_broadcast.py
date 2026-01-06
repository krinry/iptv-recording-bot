from telethon import events
from telethon.sync import TelegramClient
from config import ADMIN_ID, ACTIVE_RECORDINGS
import asyncio
from datetime import datetime
from utils.admin_checker import is_admin

async def status_command(event: events.NewMessage):
    """Show current active recordings"""
    user_id = event.sender_id
    if not await is_admin(user_id, event.chat_id):
        await event.reply("❌ Only admin can use this command")
        return
    
    if not ACTIVE_RECORDINGS:
        await event.reply("ℹ️ No active recordings currently")
        return
    
    message = "📊 Current Active Recordings:\n\n"
    for recording_id, recording in ACTIVE_RECORDINGS.items():
        message += (
            f"📌 Title: {recording['title']}\n"
            f"📺 Channel: {recording['channel']}\n"
            f"⏱ Duration: {recording['duration']}\n"
            f"🕒 Started: {recording['start_time']}\n"
            f"👤 User: {recording['user_id']}\n\n"
        )
    
    await event.reply(message)

async def broadcast_command(event: events.NewMessage):
    """Broadcast message to all users with active recordings"""
    user_id = event.sender_id
    if not await is_admin(user_id, event.chat_id):
        await event.reply("❌ Only admin can use this command")
        return
    
    args = event.text.split(maxsplit=1) # Split command and message
    if len(args) < 2:
        await event.reply("Usage: /broadcast <message>")
        return
    
    message_to_broadcast = "📢 Admin Broadcast:\n\n" + args[1]
    
    # Get unique user IDs from active recordings
    user_ids = {recording['user_id'] for recording in ACTIVE_RECORDINGS.values()}
    
    if not user_ids:
        await event.reply("ℹ️ No active users to broadcast to")
        return
    
    success = 0
    failed = 0
    
    for chat_id in user_ids:
        try:
            await event.client.send_message(entity=chat_id, message=message_to_broadcast)
            success += 1
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")
            failed += 1
        await asyncio.sleep(0.1)  # Rate limiting
    
    await event.reply(
        f"Broadcast complete!\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}"
    )

def add_active_recording(details):
    """Add a recording to active recordings tracking"""
    from config import ACTIVE_RECORDINGS
    import time
    recording_id = str(int(time.time()))  # Simple ID based on timestamp
    ACTIVE_RECORDINGS[recording_id] = {
        'title': details['title'],
        'channel': details['channel'],
        'duration': details['duration'],
        'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user_id': details['user_id']
    }
    return recording_id

def remove_active_recording(recording_id):
    """Remove a recording from tracking"""
    from config import ACTIVE_RECORDINGS
    if recording_id in ACTIVE_RECORDINGS:
        del ACTIVE_RECORDINGS[recording_id]



# In a new file or existing database file
from datetime import datetime, timedelta

user_db = {}

def is_user_verified(user_id):
    """Check if user has active verification"""
    user = user_db.get(user_id, {})
    expiry = user.get('recording_expiry')
    return expiry and expiry > datetime.now()

def add_verification_time(user_id, minutes):
    """Add recording time to user"""
    if user_id not in user_db:
        user_db[user_id] = {}
    
    current_expiry = user_db[user_id].get('recording_expiry', datetime.now())
    new_expiry = current_expiry + timedelta(minutes=minutes)
    user_db[user_id]['recording_expiry'] = new_expiry
    return new_expiry
    
