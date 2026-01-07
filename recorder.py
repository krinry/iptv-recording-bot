import os
import subprocess
import asyncio
import time
import glob
from datetime import datetime, timedelta
from pytz import timezone
import aiohttp
from typing import Optional, Dict
from config import RECORDINGS_DIR, BOT_TOKEN, STORE_CHANNEL_ID
from utils.utils import format_bytes, format_duration
from uploader import send_video
from telethon.sync import TelegramClient
from telethon import events, Button
from telethon.errors.rpcerrorlist import FloodWaitError
from recorders.recorder_utils import resolve_stream, get_stream_quality
from features.status_broadcast import add_active_recording, remove_active_recording
import re

from captions import create_progress_bar, seconds_to_hms, caption_recording_started, caption_recording_progress, caption_recording_completed

async def get_video_duration(file_path: str) -> Optional[float]:
    """Gets the duration of a video file using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return float(stdout.decode().strip())
        else:
            print(f"[Recorder] [ERROR] FFprobe error: {stderr.decode().strip()}")
            return None
    except FileNotFoundError:
        print("[Recorder] [ERROR] ffprobe not found. Please ensure FFmpeg is installed and in your PATH.")
        return None
    except Exception as e:
        print(f"[Recorder] [ERROR] Error getting video duration: {e}")
        return None

async def start_recording(telethon_client: TelegramClient, url: str, duration: str, channel: str, title: str, chat_id: int, message_id: int, scheduled_jobs: Dict[int, Dict[str, any]], split_duration_sec: int = None):
    recording_message = None
    last_caption = ""
    process = None
    start_ts = time.time()
    error_occurred = False
    
    try:
        ist = timezone("Asia/Kolkata")
        now = datetime.now(ist)

        try:
            if ":" in duration:
                h, m, s = map(int, duration.split(":"))
                total_seconds = h * 3600 + m * 60 + s
            else:
                total_seconds = int(duration)
        except ValueError:
            await telethon_client.send_message(chat_id, "⚠️ Invalid duration format. Use HH:MM:SS.")
            return
        
        is_unlimited = total_seconds == 0
        end_ts = start_ts + total_seconds if not is_unlimited else float('inf')
        end_time = now + timedelta(seconds=total_seconds) if not is_unlimited else None
        start_time_str = now.strftime("%d-%m-%Y %H:%M:%S")

        initial_caption = caption_recording_started(title, channel, total_seconds, start_time_str)
        last_caption = initial_caption
        
        try:
            buttons = [Button.inline("❌ Cancel", data=f"cancel_recording_{message_id}")]
            recording_message = await telethon_client.send_message(
                entity=chat_id,
                message=initial_caption,
                parse_mode="Markdown",
                reply_to=message_id,
                buttons=buttons
            )
        except Exception as e:
            print(f"[Recorder] [ERROR] Error sending recording notification: {e}")
            recording_message = await telethon_client.send_message(
                entity=chat_id,
                message=initial_caption,
                parse_mode="Markdown",
                reply_to=message_id
            )

        async def update_caption(caption_text, buttons=None):
            nonlocal last_caption
            if caption_text != last_caption:
                try:
                    await telethon_client.edit_message(
                        entity=chat_id,
                        message=recording_message.id,
                        text=caption_text,
                        parse_mode="Markdown",
                        buttons=buttons
                    )
                    last_caption = caption_text
                except FloodWaitError as fwe:
                    print(f"[Recorder] [WARNING] FloodWaitError while updating caption: {fwe}")
                    await asyncio.sleep(fwe.seconds)
                except Exception as e:
                    print(f"[Recorder] [ERROR] Error updating caption: {e}")

        async def update_progress_bar():
            nonlocal last_caption, process, start_ts, error_occurred
            last_update_time = start_ts

            while time.time() < end_ts:
                current_time = time.time()
                elapsed = current_time - start_ts
                
                if not is_unlimited:
                    time_left = max(0, end_ts - current_time)
                    if current_time - last_update_time >= 10:
                        progress = min(elapsed / total_seconds, 1)
                        print(f"[Recorder] [INFO] Recording {title} - {seconds_to_hms(elapsed)} / {seconds_to_hms(total_seconds)} ({progress:.1%})")
                        caption_text = caption_recording_progress(
                            title, channel, total_seconds, start_time_str,
                            elapsed, time_left
                        )
                        buttons = [Button.inline("❌ Cancel", data=f"cancel_recording_{message_id}")]
                        await update_caption(caption_text, buttons)
                        last_update_time = current_time
                else: # Unlimited recording
                    if current_time - last_update_time >= 10:
                        caption_text = f"🎬 **Recording Started**\n\n" \
                                       f"📌 **Title:** `{title}`\n" \
                                       f"📺 **Channel:** `{channel}`\n" \
                                       f"⏱ **Duration:** `Unlimited`\n" \
                                       f"⏰ **Started At:** `{start_time_str}`\n\n" \
                                       f"▶️ **Elapsed:** `{seconds_to_hms(elapsed)}`"
                        buttons = [Button.inline("❌ Cancel", data=f"cancel_recording_{message_id}")]
                        await update_caption(caption_text, buttons)
                        last_update_time = current_time

                await asyncio.sleep(10)

                if process and process.returncode is not None and process.returncode != 0:
                    if not error_occurred:
                        stderr = await process.stderr.read() if process.stderr else b'Unknown error'
                        error_msg = stderr.decode().strip()[:100]
                        if not is_unlimited:
                            caption_text = caption_recording_progress(
                                title, channel, total_seconds, start_time_str,
                                elapsed, time_left, error_msg
                            )
                            await update_caption(caption_text)
                        error_occurred = True
                    return

            if not is_unlimited:
                final_caption = caption_recording_completed(title, channel, total_seconds, start_time_str)
                await update_caption(final_caption)
            
            if process and process.returncode is None:
                await process.wait()

        progress_task = asyncio.create_task(update_progress_bar())

        base_temp_filename = f"temp_recording_{now.timestamp()}"
        temp_filename_pattern = f"{base_temp_filename}_%03d.mkv"
        temp_path_for_split = os.path.join(RECORDINGS_DIR, temp_filename_pattern)
        temp_path_single = os.path.join(RECORDINGS_DIR, f"{base_temp_filename}.mkv")
        
        os.makedirs(RECORDINGS_DIR, exist_ok=True)

        stream_url = await resolve_stream(url)
        recording_id = add_active_recording({
            'title': title,
            'channel': channel,
            'duration': total_seconds,
            'user_id': chat_id
        })

        cmd = [
            "ffmpeg", "-y", "-loglevel", "fatal",
            "-headers", f"User-Agent: Mozilla/5.0\r\nReferer: https://www.tataplay.com/\r\nOrigin: https://www.tataplay.com",
            "-i", stream_url,
        ]

        if not is_unlimited:
            cmd.extend(["-t", str(total_seconds)])

        if split_duration_sec:
            cmd.extend([
                "-f", "segment",
                "-segment_time", str(split_duration_sec),
                "-reset_timestamps", "1",
                "-c", "copy",
                "-map", "0",
                temp_path_for_split
            ])
        else:
            cmd.extend([
                "-map", "0:v?", "-map", "0:a?", "-map", "0:s?",
                "-c", "copy",
                temp_path_single
            ])

        process = await asyncio.create_subprocess_exec(*cmd)
        if message_id in scheduled_jobs:
            scheduled_jobs[message_id]['process'] = process

        return_code = await process.wait()
        progress_task.cancel()
        try:
            await progress_task
        except asyncio.CancelledError:
            pass

        if return_code != 0 and return_code != -15:
            if not error_occurred:
                error_msg = "❌ Recording failed (FFmpeg error)"
                if not is_unlimited:
                    caption_text = caption_recording_progress(
                        title, channel, total_seconds, start_time_str,
                        time.time() - start_ts, end_ts - time.time() if not is_unlimited else 0,
                        error_msg
                    )
                    await update_caption(caption_text)
            if split_duration_sec:
                for f in glob.glob(os.path.join(RECORDINGS_DIR, f"{base_temp_filename}_*.mkv")):
                    os.remove(f)
            elif os.path.exists(temp_path_single):
                os.remove(temp_path_single)
            return

        sanitized_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        sanitized_channel = re.sub(r'[<>:"/\\|?*]', '_', channel)
        time_format = "%H-%M-%S"

        files_to_upload = []
        if split_duration_sec:
            files_to_upload = sorted(glob.glob(os.path.join(RECORDINGS_DIR, f"{base_temp_filename}_*.mkv")))
        elif os.path.exists(temp_path_single):
            files_to_upload.append(temp_path_single)

        for i, file_path in enumerate(files_to_upload):
            part_num = f" part {i+1}" if len(files_to_upload) > 1 else ""
            final_filename = f"{sanitized_title}{part_num}.{sanitized_channel}.{now.strftime(time_format)}-{end_time.strftime(time_format) if not is_unlimited else 'UNLIMITED'}.{now.strftime('%d-%m-%Y')}.{int(now.timestamp())}.IPTV.WEB-DL.@Krinry123.mkv"
            output_path = os.path.join(RECORDINGS_DIR, final_filename)
            os.rename(file_path, output_path)

            thumbnail_path = os.path.join(RECORDINGS_DIR, f"{final_filename}.jpg")
            thumbnail_cmd = [
                "ffmpeg", "-y", "-loglevel", "error", "-i", output_path,
                "-ss", "00:00:01", "-vframes", "1", "-q:v", "2", "-vf", "scale=320:-1",
                thumbnail_path
            ]
            await (await asyncio.create_subprocess_exec(*thumbnail_cmd)).wait()

            actual_duration = await get_video_duration(output_path)
            if actual_duration is None:
                actual_duration = split_duration_sec if split_duration_sec else total_seconds

            readable_duration = seconds_to_hms(actual_duration)
            readable_size = format_bytes(os.path.getsize(output_path))

            caption = f"`📁 Filename: {final_filename}\n⏱ Duration: {readable_duration}\n💾 File-Size: {readable_size}`\n☎️ @krinry123"

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    new_message_id = await send_video(
                        output_path, caption, thumbnail=thumbnail_path, duration=int(actual_duration),
                        chat_id=chat_id, user_msg_id=recording_message.id
                    )
                    if new_message_id:
                        uploaded_message = await telethon_client.get_messages(STORE_CHANNEL_ID, ids=new_message_id)
                        if uploaded_message:
                            await telethon_client.send_message(
                                entity=chat_id,
                                message=uploaded_message.message,
                                file=uploaded_message.media,
                                reply_to=message_id
                            )
                        break
                except Exception as upload_error:
                    if attempt == max_retries - 1:
                        error_msg = f"❌ Upload failed: {str(upload_error)}"
                        # update caption with error
                    await asyncio.sleep(5)
            
            if os.path.exists(output_path): os.remove(output_path)
            if os.path.exists(thumbnail_path): os.remove(thumbnail_path)

        remove_active_recording(recording_id)

    except asyncio.CancelledError:
        progress_task.cancel()
        await update_caption("❌ Recording Cancelled")
        if process:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
        raise

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(f"[Recorder] [ERROR] {error_msg}")
        if recording_message and 'start_ts' in locals() and 'total_seconds' in locals():
            if not is_unlimited:
                caption_text = caption_recording_progress(
                    title, channel, total_seconds, start_time_str,
                    time.time() - start_ts, end_ts - time.time() if not is_unlimited else 0,
                    error_msg
                )
                await update_caption(caption_text)
    finally:
        # Cleanup any remaining temp files
        if 'base_temp_filename' in locals():
            for f in glob.glob(os.path.join(RECORDINGS_DIR, f"{base_temp_filename}*")):
                try:
                    os.remove(f)
                except Exception as e:
                    print(f"[Recorder] [ERROR] Error cleaning up temp file in finally: {e}")

