from datetime import datetime
from utils.utils import format_bytes, format_duration

# ━━━ Modern Progress Bar Styles ━━━

def create_progress_bar(progress, length=15):
    """Sleek modern progress bar"""
    filled = int(progress * length)
    empty = length - filled
    return '▰' * filled + '▱' * empty

def create_mini_bar(progress, length=10):
    """Compact bar for inline use"""
    filled = int(progress * length)
    return '━' * filled + '╌' * (length - filled)

def seconds_to_hms(seconds):
    seconds = int(round(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def smart_duration(seconds):
    """Human-friendly duration like '2h 30m' or '45s'"""
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s" if s else f"{m}m"
    else:
        h, rem = divmod(seconds, 3600)
        m = rem // 60
        return f"{h}h {m}m" if m else f"{h}h"


# ━━━ Recording Captions ━━━

def caption_recording_started(title, channel, duration_sec, start_time_str):
    duration_display = "∞ Unlimited" if duration_sec == 0 else seconds_to_hms(duration_sec)
    return (
        f"🔴 **RECORDING**\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 `{title}`\n"
        f"📡 `{channel}`\n"
        f"⏱ `{duration_display}`\n"
        f"🕐 `{start_time_str}`\n\n"
        f"⏳ Initializing stream..."
    )

def caption_recording_progress(title, channel, total_duration, start_time_str, elapsed_sec, remaining_sec, error_msg=None):
    elapsed_hms = seconds_to_hms(elapsed_sec)
    
    if total_duration == 0:
        # Unlimited recording
        return (
            f"🔴 **RECORDING** • `{elapsed_hms}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 `{title}`\n"
            f"📡 `{channel}`\n"
            f"⏱ `∞ Unlimited`\n"
            f"🕐 `{start_time_str}`\n\n"
            f"▶️ Elapsed: **{smart_duration(elapsed_sec)}**\n\n"
            f"{'❌ ' + error_msg if error_msg else '🟢 Recording...'}"
        )
    
    progress = min(elapsed_sec / total_duration, 1)
    pct = int(progress * 100)
    bar = create_progress_bar(progress)
    remaining_hms = seconds_to_hms(remaining_sec)
    total_hms = seconds_to_hms(total_duration)
    
    status = f"❌ {error_msg}" if error_msg else "🟢 Recording..."
    
    return (
        f"🔴 **RECORDING** • `{pct}%`\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 `{title}`\n"
        f"📡 `{channel}`\n"
        f"⏱ `{total_hms}`\n"
        f"🕐 `{start_time_str}`\n\n"
        f"{bar} **{pct}%**\n"
        f"▶️ `{elapsed_hms}` │ ⏳ `{remaining_hms}` left\n\n"
        f"{status}"
    )

def caption_recording_completed(title, channel, duration_sec, start_time_str):
    duration_hms = seconds_to_hms(duration_sec)
    end_time_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    return (
        f"✅ **RECORDING DONE**\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 `{title}`\n"
        f"📡 `{channel}`\n"
        f"⏱ `{duration_hms}`\n"
        f"🕐 `{start_time_str}`\n"
        f"🏁 `{end_time_str}`\n\n"
        f"📤 Preparing upload..."
    )


# ━━━ Upload Captions ━━━

async def caption_uploading(title, uploaded_size, total_size, speed_bps):
    progress = uploaded_size / total_size if total_size else 0
    uploaded_str = await format_bytes(uploaded_size)
    total_str = await format_bytes(total_size)
    speed_str = await format_bytes(speed_bps)
    bar = create_progress_bar(progress)
    pct = int(progress * 100)
    
    return (
        f"📤 **UPLOADING** • `{pct}%`\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 `{title}`\n\n"
        f"{bar} **{pct}%**\n"
        f"💾 `{uploaded_str}` / `{total_str}`\n"
        f"🚀 `{speed_str}/s`"
    )

def caption_uploaded(title: str, resolution: str, duration: str, size: str) -> str:
    return (
        f"📦 **UPLOADED**\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 `{title}`\n"
        f"🎞 `{resolution}`\n"
        f"⏱ `{duration}`\n"
        f"💾 `{size}`\n"
        f"📡 IPTV WEB-DL\n\n"
        f"@Krinry"
    )
