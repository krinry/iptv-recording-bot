from datetime import datetime
from utils.utils import format_bytes, format_duration

def create_progress_bar(progress, length=10):
    done = int(progress * length)
    left = length - done
    return f"[{'█' * done}{'░' * left}]"

def seconds_to_hms(seconds):
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def caption_recording_started(title, channel, duration_sec, start_time_str):
    duration_hms = "Unlimited" if duration_sec == 0 else seconds_to_hms(duration_sec)
    return (
        f"� **Recording Started**\n\n"
        f"📌 **Title:** `{title}`\n"
        f"📺 **Channel:** `{channel}`\n"
        f"⏱ **Duration:** `{duration_hms}`\n"
        f"⏰ **Started At:** `{start_time_str}`\n\n"
        f"🔄 **Status:** Preparing to record..."
    )

def caption_recording_progress(title, channel, total_duration, start_time_str, elapsed_sec, remaining_sec, error_msg=None):
    progress = min(elapsed_sec / total_duration, 1)
    progress_bar = create_progress_bar(progress)
    
    elapsed_hms = seconds_to_hms(elapsed_sec)
    remaining_hms = seconds_to_hms(remaining_sec)
    total_hms = seconds_to_hms(total_duration)
    
    status = "❌ Failed" if error_msg else "🔄 Recording..."
    error_line = f"\n❗ **Error:** `{error_msg}`" if error_msg else ""
    
    return (
        f"⏳ **Recording in Progress**\n\n"
        f"📌 **Title:** `{title}`\n"
        f"📺 **Channel:** `{channel}`\n"
        f"⏱ **Duration:** `{total_hms}`\n"
        f"⏰ **Started At:** `{start_time_str}`\n\n"
        f"[{progress_bar}] {progress * 100:.1f}%\n"
        f"▶️ **Elapsed:** `{elapsed_hms}`\n"
        f"⏭ **Remaining:** `{remaining_hms}`\n\n"
        f"**Status:** {status}{error_line}"
    )

def caption_recording_completed(title, channel, duration_sec, start_time_str):
    duration_hms = seconds_to_hms(duration_sec)
    end_time_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    return (
        f"✅ **Recording Completed**\n\n"
        f"📌 **Title:** `{title}`\n"
        f"📺 **Channel:** `{channel}`\n"
        f"⏱  **Duration:** `{duration_hms}`\n"
        f"⏰ **Started At:** `{start_time_str}`\n"
        f"🕒 **Ended At:** `{end_time_str}`\n\n"
        f"📤 **Status:** Preparing for upload..."
    )

def caption_uploading(title, uploaded_size, total_size, speed_bps):
    progress = uploaded_size / total_size if total_size else 0
    return (
        f"⏫ *Uploading*\\*\\.\\*\\*\n\n"  # Escaped asterisks and period
        f"**Title:** `{title}`\n"
        f"Progress: {create_progress_bar(progress)} {int(progress*100)}%\n"
        f"Uploaded: {format_bytes(uploaded_size)} / {format_bytes(total_size)}\n"
        f"Speed: {format_bytes(speed_bps)}/s"
    )

def caption_uploaded(title: str, resolution: str, duration: str, size: str) -> str:
    return (
        f"**Filename:** {title}\n"
        f"**Resolution:** {resolution}\n"
        f"**Duration:** {duration}\n"
        f"**File Size:** {size}\n"
        f"**Type:** IPTV Recording\n"
        f"**Source:** @dfmdb"
    )
