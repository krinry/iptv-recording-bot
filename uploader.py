import os
import time
import asyncio
import subprocess
from typing import Optional, List, Dict
from telethon.sync import TelegramClient
from telethon.tl.types import DocumentAttributeVideo
from telethon.sessions import StringSession
from telethon.errors.rpcerrorlist import FloodWaitError, MessageNotModifiedError
from config import API_ID, API_HASH, SESSION_NAME, STORE_CHANNEL_ID, BOT_TOKEN, SESSION_STRING
from captions import caption_uploaded

# Constants
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB

class UploadManager:
    _instance = None
    _lock = asyncio.Semaphore(1)
    _active_uploads = set()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialize()
        return cls._instance

    @classmethod
    def _initialize(cls):
        cls.session_dir = "session_files"
        os.makedirs(cls.session_dir, exist_ok=True)

    def __init__(self):
        if not hasattr(self, 'telethon_client'):
            self.progress_data = {}
            self.last_update = {}
            self._speed_data = {}  # For speed tracking
            self.telethon_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    async def init_client(self):
        if not self.telethon_client.is_connected():
            await self.telethon_client.start()

    def upload_progress_callback(self, current: int, total: int, chat_id: int, file_name: str):
        """Wrapper to safely call async progress updates from sync context"""
        # Speed tracking (pure sync — no async work)
        now = time.time()
        if chat_id not in self._speed_data:
            self._speed_data[chat_id] = {'last_bytes': 0, 'last_time': now, 'start_time': now, 'last_console': 0, 'last_tg_update': 0, 'speed': 0.0}
        
        sd = self._speed_data[chat_id]
        td = now - sd['last_time']
        if td > 0.5:
            sd['speed'] = (current - sd['last_bytes']) / td / 1048576
            sd['last_bytes'] = current
            sd['last_time'] = now
        
        # Console print every 1 second (pure sync print — zero async overhead)
        if now - sd['last_console'] >= 1 or current == total:
            pct = min(100, current / total * 100)
            elapsed = now - sd['start_time']
            if pct > 0 and pct < 100:
                eta_str = f"{int((elapsed / pct * 100) - elapsed)}s"
            elif current == total:
                eta_str = "Done!"
            else:
                eta_str = "--"
            print(f"[Uploader] [INFO] {file_name}: {pct:.1f}% | {current/1048576:.1f}/{total/1048576:.1f} MB | 🚀 {sd['speed']:.2f} MB/s | ⏱️ ETA: {eta_str}")
            sd['last_console'] = now

        # Schedule Telegram update only every 4 seconds (reduces async overhead dramatically)
        # Always update on completion (current == total)
        if current == total or now - sd.get('last_tg_update', 0) >= 4:
            sd['last_tg_update'] = now
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(
                    self.async_upload_progress_callback(current, total, chat_id, file_name)
                )
            )

    async def async_upload_progress_callback(self, current: int, total: int, chat_id: int, file_name: str):
        """Enhanced progress callback with better error handling"""
        current_time = asyncio.get_event_loop().time()
        
        # Throttle updates to every 10 seconds
        if chat_id in self.last_update and current_time - self.last_update[chat_id] < 5:
            return
        
        self.last_update[chat_id] = current_time
        percent = min(100, (current / total) * 100)
        uploaded_mb = current / 1024 / 1024
        total_mb = total / 1024 / 1024

        # Visual progress bar
        bar = '⬢' * int(percent/5) + '⬡' * (20 - int(percent/5))
        
        # Get speed from sync tracker
        speed = self._speed_data.get(chat_id, {}).get('speed', 0)
        elapsed = time.time() - self._speed_data.get(chat_id, {}).get('start_time', time.time())
        if percent > 0 and percent < 100:
            eta_str = f"{int((elapsed / percent * 100) - elapsed)}s"
        else:
            eta_str = "--"
        
        progress_text = (
            f"**📤 Uploading:** `{file_name}`\n"
            f"**📊 Progress:** {percent:.1f}%\n"
            f"🔹 {uploaded_mb:.1f}MB / {total_mb:.1f}MB\n"
            f"🚀 **Speed:** {speed:.2f} MB/s\n"
            f"⏱️ **ETA:** {eta_str}\n"
            f"{bar}\n"
            f"**⚡ Status:** Uploading..."
        )

        try:
            if chat_id not in self.progress_data:
                return
            edit_client = self.progress_data[chat_id].get('edit_client', self.telethon_client)
            if self.progress_data[chat_id]['msg_id'] is not None:
                # Edit the existing progress/status message
                await edit_client.edit_message(
                    entity=chat_id,
                    message=self.progress_data[chat_id]['msg_id'],
                    text=progress_text,
                    parse_mode='md',
                )
            elif not self.progress_data[chat_id].get('status_msg_id'):
                # No status message from bot — send a NEW progress message (fallback)
                message = await self.telethon_client.send_message(
                    entity=chat_id,
                    message=progress_text,
                    reply_to=self.progress_data[chat_id].get('user_msg_id'),
                )
                self.progress_data[chat_id]['msg_id'] = message.id
        except FloodWaitError as fwe:
            print(f"[Uploader] [WARNING] FloodWaitError while updating upload progress: {fwe}")
            await asyncio.sleep(fwe.seconds)
        except MessageNotModifiedError:
            pass
        except Exception as e:
            print(f"[Uploader] [ERROR] Progress update failed: {e}")

    async def send_uploaded_message(self, chat_id: int, file_name: str, success: bool = True, error_msg: str = None):
        """Enhanced final message with better formatting"""
        try:
            edit_client = self.progress_data.get(chat_id, {}).get('edit_client', self.telethon_client)
            msg_id = self.progress_data.get(chat_id, {}).get('msg_id')

            if success:
                final_text = (
                    f"📂 **File:** `{file_name}`\n"
                    "✅ **Uploaded Successfully!**\n"
                    "🎉 **Status:** Completed"
                )
            else:
                final_text = (
                    f"📂 **File:** `{file_name}`\n"
                    "❌ **Upload Failed!**\n"
                    f"⚠️ **Reason:** {error_msg or 'Unknown error'}"
                )

            if msg_id is not None:
                # Edit the existing status/progress message
                try:
                    await edit_client.edit_message(
                        entity=chat_id,
                        message=msg_id,
                        text=final_text,
                        parse_mode='md',
                    )
                except MessageNotModifiedError:
                    pass
                except Exception as edit_err:
                    print(f"[Uploader] [ERROR] Final message edit failed: {edit_err}")
            else:
                # No message to edit — send new one as fallback
                await self.telethon_client.send_message(
                    entity=chat_id,
                    message=final_text,
                    reply_to=self.progress_data.get(chat_id, {}).get('user_msg_id'),
                )
        except Exception as e:
            print(f"[Uploader] [ERROR] Final message error: {e}")
        finally:
            self.progress_data.pop(chat_id, None)
            self.last_update.pop(chat_id, None)
            self._speed_data.pop(chat_id, None)

    async def _split_video(self, file_path: str) -> List[str]:
        """Splits a video file into parts smaller than MAX_FILE_SIZE."""
        parts = []
        file_size = os.path.getsize(file_path)
        if file_size <= MAX_FILE_SIZE:
            return [file_path]

        part_size = MAX_FILE_SIZE - 50 * 1024 * 1024
        num_parts = -(-file_size // part_size)
        base_name, ext = os.path.splitext(file_path)

        for i in range(num_parts):
            part_path = f"{base_name}.part{i+1}{ext}"
            cmd = [
                "ffmpeg",
                "-y",
                "-i", file_path,
                "-c", "copy",
                "-map", "0",
                "-segment_time", str(int(i * part_size / (file_size/os.path.getsize(file_path)))),
                "-f", "segment",
                "-segment_format_options", "movflags=+faststart",
                "-reset_timestamps", "1",
                part_path
            ]
            process = await asyncio.create_subprocess_exec(*cmd)
            await process.wait()
            if process.returncode == 0:
                parts.append(part_path)
            else:
                for part in parts:
                    if os.path.exists(part):
                        os.remove(part)
                return []
        return parts

    async def _send_video_telethon_user_session(self, file_path: str, caption: str, thumbnail: Optional[str] = None, 
                                                duration: Optional[int] = None, chat_id: int = 0, 
                                                user_msg_id: Optional[int] = None,
                                                bot_client=None, status_msg_id: Optional[int] = None) -> Optional[int]:
        """Uploads video using Telethon with user session"""
        file_name = os.path.basename(file_path) if file_path else "Unknown File"
        try:
            # If bot_client + status_msg_id provided, edit the recording message directly
            # Otherwise, uploader sends its own messages (fallback)
            self.progress_data[chat_id] = {
                'msg_id': status_msg_id,  # Edit this message (None = will send new)
                'user_msg_id': user_msg_id,
                'file': file_name,
                'edit_client': bot_client if bot_client else self.telethon_client,
                'status_msg_id': status_msg_id,
            }
            self._speed_data.pop(chat_id, None)  # Reset speed

            if not os.path.exists(file_path):
                await self.send_uploaded_message(chat_id, file_name, False, "File not found")
                return None

            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                parts = await self._split_video(file_path)
                if not parts:
                    await self.send_uploaded_message(chat_id, file_name, False, "Failed to split video")
                    return None
                
                message_ids = []
                for i, part_path in enumerate(parts):
                    part_caption = f"{caption} (Part {i+1}/{len(parts)})"
                    message_id = await self._send_video_telethon_user_session(
                        part_path, part_caption, thumbnail, duration, chat_id, user_msg_id
                    )
                    if message_id:
                        message_ids.append(message_id)
                    if os.path.exists(part_path):
                        os.remove(part_path)
                return message_ids[0] if message_ids else None

            if not self.telethon_client.is_connected():
                await self.telethon_client.start()

            thumb = thumbnail if thumbnail and os.path.exists(thumbnail) else None

            # Only hold the lock during the actual upload + send, not during split/recursion
            async with self._lock:
                result = await self.telethon_client.upload_file(
                    file=file_path,
                    part_size_kb=512,  # Max chunk size (512KB) = 4x fewer API calls than default 128KB
                    file_size=file_size,  # Pre-provide size so Telethon skips stat() call
                    progress_callback=lambda current, total: self.upload_progress_callback(current, total, chat_id, file_name)
                )

                entity = await self.telethon_client.get_entity(STORE_CHANNEL_ID)

                message = await self.telethon_client.send_message(
                    entity=entity,
                    message=caption,
                    file=result,
                    attributes=[
                        DocumentAttributeVideo(
                            duration=duration or 0,
                            w=0,
                            h=0,
                            supports_streaming=True
                        )
                    ],
                    thumb=thumb
                )

            # Forward to user's chat using cached media reference (instant — no re-upload)
            if chat_id and str(chat_id) != str(STORE_CHANNEL_ID):
                try:
                    await self.telethon_client.send_message(
                        entity=chat_id,
                        message=caption,
                        file=message.media,
                        reply_to=user_msg_id
                    )
                    print(f"[Uploader] [INFO] ✅ Forwarded to user chat {chat_id}")
                except Exception as fwd_err:
                    print(f"[Uploader] [WARNING] Forward to user failed: {fwd_err}")

            # Send completion message outside the lock so it doesn't block other uploads
            await self.send_uploaded_message(chat_id, file_name, True)
            return message.id

        except Exception as e:
            error_msg = str(e)
            try:
                await self.send_uploaded_message(chat_id, file_name, False, error_msg)
            except Exception:
                print(f"[Uploader] [ERROR] Failed to send error message: {error_msg}")
            return None
        finally:
            # Always cleanup to prevent stale data from blocking future operations
            self.progress_data.pop(chat_id, None)
            self.last_update.pop(chat_id, None)
            self._speed_data.pop(chat_id, None)

    async def send_video(self, file_path: str, caption: str, thumbnail: Optional[str] = None, 
                        duration: Optional[int] = None, chat_id: int = 0, 
                        user_msg_id: Optional[int] = None,
                        bot_client=None, status_msg_id: Optional[int] = None) -> Optional[int]:
        """Main entry point for video upload, always uses Telethon."""
        if not file_path or not isinstance(file_path, str) or len(file_path) < 2:
            print(f"[Uploader] [ERROR] Invalid file_path received: {file_path}")
            await self.send_uploaded_message(chat_id, "Invalid File", False, "Invalid file path provided")
            return None

        if not os.path.exists(file_path):
            print(f"[Uploader] [ERROR] File not found: {file_path}")
            await self.send_uploaded_message(chat_id, os.path.basename(file_path), False, "File not found")
            return None

        file_name = os.path.basename(file_path)
        print(f"[Uploader] [INFO] Uploading {file_name} using Telethon (user session).")
        return await self._send_video_telethon_user_session(file_path, caption, thumbnail, duration, chat_id, user_msg_id, bot_client, status_msg_id)

    async def upload_sequence(self, video_list: List[Dict[str, str]], chat_id: int, user_msg_id: Optional[int] = None) -> List[int]:
        """Process multiple videos in sequence"""
        results = []
        for video in video_list:
            print(f"\n[Uploader] [INFO] Uploading {video.get('path')}")
            msg_id = await self.send_video(
                file_path=video.get('path'),
                caption=video.get('caption', ''),
                thumbnail=video.get('thumbnail'),
                duration=video.get('duration'),
                chat_id=chat_id,
                user_msg_id=user_msg_id
            )
            if msg_id:
                results.append(msg_id)
            else:
                print(f"[Uploader] [ERROR] Failed to upload {video.get('path')}")
        return results

# Public interfaces
upload_manager = UploadManager()

async def send_video(file_path: str, caption: str, thumbnail: Optional[str] = None, 
                    duration: Optional[int] = None, chat_id: int = 0, 
                    user_msg_id: Optional[int] = None,
                    bot_client=None, status_msg_id: Optional[int] = None) -> Optional[int]:
    """Public interface for single video upload"""
    return await upload_manager.send_video(
        file_path=file_path,
        caption=caption,
        thumbnail=thumbnail,
        duration=duration,
        chat_id=chat_id,
        user_msg_id=user_msg_id,
        bot_client=bot_client,
        status_msg_id=status_msg_id
    )

async def upload_videos(video_list: List[Dict[str, str]], chat_id: int, user_msg_id: Optional[int] = None) -> List[int]:
    """Public interface for batch upload"""
    return await upload_manager.upload_sequence(video_list, chat_id, user_msg_id)