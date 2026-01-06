from datetime import datetime
from utils.utils import format_bytes, format_duration

def create_progress_bar(progress, length=10):
    done = int(progress * length)
    left = length - done
    return f"[{'█' * done}{'░' * left}]"

def seconds_to_hms(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def caption_recording_started(title, channel, duration_sec, start_time_str):
    return (
        f"🎥 **Recording Started!**\n\n"
        f"**Title:** `{title}`\n"
        f"**Channel:** `{channel}`\n"
        f"**Start Time:** `{start_time_str}`\n"
        f"**Duration:** {seconds_to_hms(duration_sec)}\n\n"
        f"Progress: {create_progress_bar(0)} 0%\n"
        f"Time Left: {seconds_to_hms(duration_sec)} / {seconds_to_hms(duration_sec)}"
    )

def caption_recording_progress(title, channel, duration_sec, start_time_str, elapsed, time_left):
    progress = min(elapsed / duration_sec, 1)
    return (
        f"🎥 **Recording In Progress...**\n\n"
        f"**Title:** `{title}`\n"
        f"**Channel:** `{channel}`\n"
        f"**Start Time:** `{start_time_str}`\n"
        f"**Duration:** {seconds_to_hms(duration_sec)}\n\n"
        f"Progress: {create_progress_bar(progress)} {int(progress*100)}%\n"
        f"Time Left: {seconds_to_hms(time_left)} / {seconds_to_hms(duration_sec)}"
    )

def caption_recording_completed(title, channel, duration_sec, start_time_str):
    return (
        f"🎥 **Recording Completed!**\n\n"
        f"**Title:** `{title}`\n"
        f"**Channel:** `{channel}`\n"
        f"**Start Time:** `{start_time_str}`\n"
        f"**Duration:** {seconds_to_hms(duration_sec)}\n\n"
        f"Progress: {create_progress_bar(1)} 100%\n"
        f"Time Left: 00:00:00 / {seconds_to_hms(duration_sec)}"
    )

def caption_uploading(title, uploaded_size, total_size, speed_bps):
    progress = uploaded_size / total_size if total_size else 0
    return (
        f"⏫ *Uploading*\*\.\*\*\n\n"  # Escaped asterisks and period
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

