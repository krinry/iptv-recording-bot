import psutil
import os
import time
import asyncio
from telethon import events
from telethon.sync import TelegramClient
from config import ADMIN_ID, ACTIVE_RECORDINGS, RECORDINGS_DIR
from datetime import datetime, timedelta
from utils.admin_checker import is_admin

# Track bot start time for uptime
_bot_start_time = time.time()

# ━━━ Utility Functions ━━━

def _bar(value, max_val=100, length=10):
    """Mini bar chart for metrics"""
    ratio = min(value / max_val, 1.0) if max_val else 0
    filled = int(ratio * length)
    return '▰' * filled + '▱' * (length - filled)

def _format_bytes(b):
    """Sync version for status display"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"

def _uptime():
    """Format bot uptime"""
    elapsed = int(time.time() - _bot_start_time)
    days, rem = divmod(elapsed, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if mins: parts.append(f"{mins}m")
    parts.append(f"{secs}s")
    return " ".join(parts)

def _recordings_disk_usage():
    """Calculate disk usage of recordings directory"""
    total_size = 0
    file_count = 0
    try:
        if os.path.exists(RECORDINGS_DIR):
            for f in os.listdir(RECORDINGS_DIR):
                fp = os.path.join(RECORDINGS_DIR, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
                    file_count += 1
    except Exception:
        pass
    return total_size, file_count


# ━━━ Status Command ━━━

async def status_command(event: events.NewMessage):
    """Show enhanced system status dashboard"""
    user_id = event.sender_id
    if not await is_admin(user_id, event.chat_id):
        await event.reply("❌ Only admin can use this command")
        return

    # System metrics
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Recordings disk usage
    rec_size, rec_count = _recordings_disk_usage()

    # Active recordings
    active_count = len(ACTIVE_RECORDINGS)

    # Build dashboard
    msg = (
        "📊 **SYSTEM DASHBOARD**\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"

        f"⏱ **Uptime:** `{_uptime()}`\n\n"

        f"🖥 **CPU:** {_bar(cpu)} `{cpu:.1f}%`\n"
        f"🧠 **RAM:** {_bar(ram.percent)} `{_format_bytes(ram.used)}` / `{_format_bytes(ram.total)}`\n"
        f"💾 **Disk:** {_bar(disk.percent)} `{_format_bytes(disk.used)}` / `{_format_bytes(disk.total)}`\n\n"

        "━━━━━━━━━━━━━━━━━━━\n"
    )

    # Recordings storage info
    msg += (
        f"📁 **Recordings:** `{rec_count}` files • `{_format_bytes(rec_size)}`\n"
        f"📂 **Path:** `{os.path.abspath(RECORDINGS_DIR)}`\n\n"
    )

    # Active recordings
    if active_count > 0:
        msg += (
            f"🔴 **Active Recordings:** `{active_count}`\n"
            "━━━━━━━━━━━━━━━━━━━\n"
        )
        for rid, rec in ACTIVE_RECORDINGS.items():
            elapsed = ""
            try:
                start = datetime.strptime(rec['start_time'], "%Y-%m-%d %H:%M:%S")
                elapsed_sec = (datetime.now() - start).total_seconds()
                h, rem = divmod(int(elapsed_sec), 3600)
                m, s = divmod(rem, 60)
                elapsed = f"{h:02d}:{m:02d}:{s:02d}"
            except Exception:
                elapsed = "??:??:??"

            duration_display = "∞" if rec['duration'] == 0 else f"{rec['duration']}s"
            msg += (
                f"\n📌 `{rec['title']}`\n"
                f"   📡 `{rec['channel']}`\n"
                f"   ⏱ `{elapsed}` / `{duration_display}`\n"
                f"   👤 `{rec['user_id']}`\n"
            )
        msg += "\n"
    else:
        msg += "🟢 **No active recordings**\n\n"

    # Scheduled jobs info
    from scheduler import scheduled_jobs
    pending = len(scheduled_jobs)
    if pending > 0:
        msg += f"📅 **Queued Jobs:** `{pending}`\n"
    else:
        msg += "📅 **Queued Jobs:** `None`\n"

    msg += (
        "\n━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 `{datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')}`"
    )

    await event.reply(msg, parse_mode="Markdown")


# ━━━ Broadcast Command ━━━

async def broadcast_command(event: events.NewMessage):
    """Broadcast message to all users with active recordings"""
    user_id = event.sender_id
    if not await is_admin(user_id, event.chat_id):
        await event.reply("❌ Only admin can use this command")
        return
    
    args = event.text.split(maxsplit=1)
    if len(args) < 2:
        await event.reply(
            "❌ **Usage:** `/broadcast <message>`",
            parse_mode="Markdown"
        )
        return
    
    message_to_broadcast = (
        "📢 **BROADCAST**\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        + args[1]
    )
    
    # Get unique user IDs from active recordings
    user_ids = {recording['user_id'] for recording in ACTIVE_RECORDINGS.values()}
    
    if not user_ids:
        await event.reply("⚠️ No active users to broadcast to.")
        return
    
    success = 0
    failed = 0
    
    for chat_id in user_ids:
        try:
            await event.client.send_message(entity=chat_id, message=message_to_broadcast, parse_mode="Markdown")
            success += 1
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")
            failed += 1
        await asyncio.sleep(0.1)  # Rate limiting
    
    await event.reply(
        f"📢 **Broadcast Complete**\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Sent: `{success}`\n"
        f"❌ Failed: `{failed}`",
        parse_mode="Markdown"
    )


# ━━━ Active Recording Tracking ━━━

def add_active_recording(details):
    """Add a recording to active recordings tracking"""
    from config import ACTIVE_RECORDINGS
    import time as _time
    recording_id = str(int(_time.time()))
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


# ━━━ Verification System ━━━

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
