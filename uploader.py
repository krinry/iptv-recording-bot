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
    _lock = asyncio.Lock()
    _active_uploads = set()  # Track active uploads to prevent duplicates

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
            self.progress_data = {}  # {chat_id: {'msg_id': int, 'user_msg_id': int, 'file': str}}
            self._upload_state = {}  # {chat_id: {'current': 0, 'total': 0, ...}} — shared with poller
            self.telethon_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
            self.bot_client = None  # Separate bot connection for progress messages

    def set_bot_client(self, client):
        """Set the bot client for progress message edits (separate connection from upload)"""
        self.bot_client = client
        print('[Uploader] [INFO] ✅ Bot client set for progress messages (separate connection)')

    async def init_client(self):
        if not self.telethon_client.is_connected():
            await self.telethon_client.start()

    def upload_progress_callback(self, current: int, total: int, chat_id: int, file_name: str):
        """100% SYNC callback — NO async work, NO create_task.
        Just stores data in dict and prints to console.
        This prevents blocking the upload_file chunk pipeline."""
        now = time.time()
        
        if chat_id not in self._upload_state:
            self._upload_state[chat_id] = {
                'current': 0, 'total': total, 'file_name': file_name,
                'start_time': now, 'last_bytes': 0, 'last_speed_time': now,
                'last_console': 0, 'speed': 0.0, 'done': False
            }
        
        state = self._upload_state[chat_id]
        state['current'] = current
        state['total'] = total
        
        # Calculate speed (update every 0.5s for smoothing)
        td = now - state['last_speed_time']
        if td > 0.5:
            state['speed'] = (current - state['last_bytes']) / td / 1024 / 1024  # MB/s
            state['last_bytes'] = current
            state['last_speed_time'] = now
        
        # Console print every 1 second
        if now - state['last_console'] >= 1 or current == total:
            pct = min(100, current / total * 100)
            spd = state['speed']
            elapsed = now - state['start_time']
            # ETA calculation
            if pct > 0 and pct < 100:
                eta_sec = (elapsed / pct * 100) - elapsed
                eta_str = f"{int(eta_sec)}s"
            elif current == total:
                eta_str = "Done!"
            else:
                eta_str = "--"
            print(f"[Uploader] [INFO] {file_name}: {pct:.1f}% | {current/1048576:.1f}/{total/1048576:.1f} MB | 🚀 {spd:.2f} MB/s | ⏱️ ETA: {eta_str}")
            state['last_console'] = now
        
        if current == total:
            state['done'] = True

    async def _progress_poller(self, chat_id: int):
        """Background task that updates Telegram progress message every 5 seconds.
        Runs INDEPENDENTLY from the upload_file loop — never blocks chunk uploads."""
        try:
            while True:
                await asyncio.sleep(5)  # 5 seconds between Telegram edits
                state = self._upload_state.get(chat_id)
                if not state or state['done']:
                    break
                
                pct = min(100, state['current'] / state['total'] * 100)
                uploaded_mb = state['current'] / 1048576
                total_mb = state['total'] / 1048576
                speed = state['speed']
                elapsed = time.time() - state['start_time']
                if pct > 0 and pct < 100:
                    eta_sec = (elapsed / pct * 100) - elapsed
                    eta_str = f"{int(eta_sec)}s"
                else:
                    eta_str = "--"
                
                bar = '⬢' * int(pct/5) + '⬡' * (20 - int(pct/5))
                
                progress_text = (
                    f"**📤 Uploading:** `{state['file_name']}`\n"
                    f"**📊 Progress:** {pct:.1f}%\n"
                    f"🔹 {uploaded_mb:.1f}MB / {total_mb:.1f}MB\n"
                    f"🚀 **Speed:** {speed:.2f} MB/s\n"
                    f"⏱️ **ETA:** {eta_str}\n"
                    f"{bar}\n"
                    f"**⚡ Status:** Uploading..."
                )
                
                # Use bot_client for edits (separate connection — won't block upload chunks)
                msg_client = self.bot_client or self.telethon_client
                try:
                    if self.progress_data[chat_id]['msg_id'] is not None:
                        await msg_client.edit_message(
                            entity=chat_id,
                            message=self.progress_data[chat_id]['msg_id'],
                            text=progress_text,
                        )
                    elif self.progress_data[chat_id]['user_msg_id'] is not None:
                        await msg_client.edit_message(
                            entity=chat_id,
                            message=self.progress_data[chat_id]['user_msg_id'],
                            text=progress_text,
                        )
                        self.progress_data[chat_id]['msg_id'] = self.progress_data[chat_id]['user_msg_id']
                    else:
                        message = await msg_client.send_message(
                            entity=chat_id,
                            message=progress_text,
                        )
                        self.progress_data[chat_id]['msg_id'] = message.id
                except FloodWaitError as fwe:
                    print(f"[Uploader] [WARNING] FloodWait: sleeping {fwe.seconds}s")
                    await asyncio.sleep(fwe.seconds)
                except MessageNotModifiedError:
                    pass
                except Exception as e:
                    print(f"[Uploader] [ERROR] Progress update failed: {e}")
        except asyncio.CancelledError:
            pass  # Normal cleanup when upload finishes

    async def send_uploaded_message(self, chat_id: int, file_name: str, success: bool = True, error_msg: str = None):
        """Enhanced final message with better formatting"""
        msg_client = self.bot_client or self.telethon_client
        try:
            if chat_id not in self.progress_data or self.progress_data[chat_id]['msg_id'] is None:
                # If no message ID to edit, send a new message
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
                await msg_client.send_message(
                    entity=chat_id,
                    message=final_text,
                    reply_to=self.progress_data.get(chat_id, {}).get('user_msg_id'),
                )
                return

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

            try:
                await msg_client.edit_message(
                    entity=chat_id,
                    message=self.progress_data[chat_id]['msg_id'],
                    text=final_text,
                )
            except MessageNotModifiedError:
                pass  # Already updated
            except Exception as edit_err:
                # If edit fails, send new final message
                print(f"[Uploader] [ERROR] Final message edit failed: {edit_err}")
                await msg_client.send_message(
                    entity=chat_id,
                    message=final_text,
                    reply_to=self.progress_data[chat_id]['user_msg_id'],
                )
        except Exception as e:
            print(f"[Uploader] [ERROR] Final message error: {e}")
        finally:
            # Clean up tracking data
            self.progress_data.pop(chat_id, None)

    async def _split_video(self, file_path: str) -> List[str]:
        """Splits a video file into parts smaller than MAX_FILE_SIZE."""
        parts = []
        file_size = os.path.getsize(file_path)
        if file_size <= MAX_FILE_SIZE:
            return [file_path]

        part_size = MAX_FILE_SIZE - 50 * 1024 * 1024  # 1.95GB to be safe
        num_parts = -(-file_size // part_size)  # Ceiling division
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
                # Cleanup created parts if splitting fails
                for part in parts:
                    if os.path.exists(part):
                        os.remove(part)
                return []
        return parts

    async def _send_video_telethon_user_session(self, file_path: str, caption: str, thumbnail: Optional[str] = None, 
                                                duration: Optional[int] = None, chat_id: int = 0, 
                                                user_msg_id: Optional[int] = None) -> Optional[int]:
        """Uploads video using Telethon with user session"""
        try:
            file_name = os.path.basename(file_path) if file_path else "Unknown File"
            # Initialize progress tracking
            self.progress_data[chat_id] = {
                'msg_id': user_msg_id,
                'user_msg_id': user_msg_id,
                'file': file_name
            }
            # Reset upload state for speed tracking
            self._upload_state.pop(chat_id, None)

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

            # Start background poller for Telegram progress updates (does NOT block upload)
            poller = asyncio.create_task(self._progress_poller(chat_id))

            result = await self.telethon_client.upload_file(
                file=file_path,
                progress_callback=lambda current, total: self.upload_progress_callback(current, total, chat_id, file_name)
            )

            # Stop poller immediately after upload finishes
            poller.cancel()
            try:
                await poller
            except asyncio.CancelledError:
                pass
            self._upload_state.pop(chat_id, None)

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

            await self.send_uploaded_message(chat_id, file_name, True)
            return message.id

        except Exception as e:
            error_msg = str(e)
            await self.send_uploaded_message(chat_id, file_name, False, error_msg)
            return None

    async def send_video(self, file_path: str, caption: str, thumbnail: Optional[str] = None, 
                        duration: Optional[int] = None, chat_id: int = 0, 
                        user_msg_id: Optional[int] = None) -> Optional[int]:
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

        # Prevent duplicate uploads
        if file_path in self._active_uploads:
            print(f"[Uploader] [WARNING] Upload already in progress for {file_name}. Skipping duplicate.")
            return None

        self._active_uploads.add(file_path)
        print(f"[Uploader] [INFO] Uploading {file_name} using Telethon (user session).")
        try:
            return await self._send_video_telethon_user_session(file_path, caption, thumbnail, duration, chat_id, user_msg_id)
        finally:
            self._active_uploads.discard(file_path)

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
                    user_msg_id: Optional[int] = None) -> Optional[int]:
    """Public interface for single video upload"""
    return await upload_manager.send_video(
        file_path=file_path,
        caption=caption,
        thumbnail=thumbnail,
        duration=duration,
        chat_id=chat_id,
        user_msg_id=user_msg_id
    )

async def upload_videos(video_list: List[Dict[str, str]], chat_id: int, user_msg_id: Optional[int] = None) -> List[int]:
    """Public interface for batch upload"""
    return await upload_manager.upload_sequence(video_list, chat_id, user_msg_id)


# For testing (CLI)
if __name__ == "__main__":
    async def test_upload():
        # Create dummy files for testing
        small_file_path = r"recordings\small_video.mp4"
        large_file_path = r"recordings\large_video.mp4"
        # Ensure the recordings directory exists for the dummy files
        os.makedirs("recordings", exist_ok=True)
        with open(small_file_path, "wb") as f:
            f.seek(10 * 1024 * 1024 - 1) # 10MB
            f.write(b"\0")
        with open(large_file_path, "wb") as f:
            f.seek(2147483648 - 1) # 2GB
            f.write(b"\0")

        videos = [
            {'path': small_file_path, 'caption': 'Small Video Test', 'duration': 10},
            {'path': large_file_path, 'caption': 'Large Video Test', 'duration': 15}
        ]
        # Replace 12345 and 67890 with actual chat_id and user_msg_id for testing
        await upload_videos(videos, chat_id=12345, user_msg_id=67890)

        # Clean up dummy files
        #os.remove(small_file_path)
        #os.remove(large_file_path)

    asyncio.run(test_upload())