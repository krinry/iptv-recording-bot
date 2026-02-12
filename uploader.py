import os
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
            self.last_update = {}
            self.speed_data = {}  # {chat_id: {'last_bytes': 0, 'last_time': 0, 'start_time': 0}}
            self.telethon_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    async def init_client(self):
        if not self.telethon_client.is_connected():
            await self.telethon_client.start()

    def upload_progress_callback(self, current: int, total: int, chat_id: int, file_name: str):
        """Wrapper to safely call async progress updates from sync context"""
        loop = asyncio.get_running_loop()
        loop.create_task(self.async_upload_progress_callback(current, total, chat_id, file_name))

    async def async_upload_progress_callback(self, current: int, total: int, chat_id: int, file_name: str):
        """Enhanced progress callback with speed calculation"""
        current_time = asyncio.get_event_loop().time()
        
        # Initialize speed data if missing
        if chat_id not in self.speed_data:
            self.speed_data[chat_id] = {'last_bytes': 0, 'last_time': current_time, 'start_time': current_time, 'last_console_time': 0}

        data = self.speed_data[chat_id]
        
        # Calculate Speed (MB/s)
        time_diff = current_time - data['last_time']
        speed_str = "0.0 MB/s"
        
        if time_diff > 0.5: # Update speed every 0.5s for accuracy
            bytes_diff = current - data['last_bytes']
            speed = (bytes_diff / 1024 / 1024) / time_diff # MB/s
            speed_str = f"{speed:.2f} MB/s"
            data['last_bytes'] = current
            data['last_time'] = current_time
            data['speed_str'] = speed_str # Cache logic
        else:
            speed_str = data.get('speed_str', "Calculating...")

        # Console Update (Every 1 second)
        if current_time - data.get('last_console_time', 0) >= 1 or current == total:
            percent = min(100, (current / total) * 100)
            uploaded_mb = current / 1024 / 1024
            total_mb = total / 1024 / 1024
            print(f"[Uploader] [INFO] Uploading {file_name}: {percent:.1f}% | {uploaded_mb:.1f}/{total_mb:.1f} MB | 🚀 {speed_str}")
            data['last_console_time'] = current_time

        # Telegram Update (Every 3 seconds)
        if chat_id in self.last_update and current_time - self.last_update[chat_id] < 3:
            return
        
        self.last_update[chat_id] = current_time
        percent = min(100, (current / total) * 100)
        uploaded_mb = current / 1024 / 1024
        total_mb = total / 1024 / 1024

        # Visual progress bar
        bar = '⬢' * int(percent/5) + '⬡' * (20 - int(percent/5))
        
        progress_text = (
            f"**📤 Uploading:** `{file_name}`\n"
            f"**📊 Progress:** {percent:.1f}%\n"
            f"🔹 {uploaded_mb:.1f}MB / {total_mb:.1f}MB\n"
            f"🚀 **Speed:** {speed_str}\n"
            f"{bar}\n"
            f"**⚡ Status:** Uploading..."
        )

        try:
            # If msg_id is already set (meaning it's an edit), or if user_msg_id was provided
            if self.progress_data[chat_id]['msg_id'] is not None:
                await self.telethon_client.edit_message(
                    entity=chat_id,
                    message=self.progress_data[chat_id]['msg_id'],
                    text=progress_text,
                )
            elif self.progress_data[chat_id]['user_msg_id'] is not None: # Use user_msg_id for initial edit
                 await self.telethon_client.edit_message(
                    entity=chat_id,
                    message=self.progress_data[chat_id]['user_msg_id'],
                    text=progress_text,
                )
                 self.progress_data[chat_id]['msg_id'] = self.progress_data[chat_id]['user_msg_id']
            else:
                # First progress update - send new message
                message = await self.telethon_client.send_message(
                    entity=chat_id,
                    message=progress_text,
                )
                self.progress_data[chat_id]['msg_id'] = message.id
        except FloodWaitError as fwe:
            print(f"[Uploader] [WARNING] FloodWaitError while updating upload progress: {fwe}")
            await asyncio.sleep(fwe.seconds)
        except MessageNotModifiedError:
            pass  # Already up to date, ignore
        except Exception as e:
            print(f"[Uploader] [ERROR] Progress update failed: {e}")

    async def send_uploaded_message(self, chat_id: int, file_name: str, success: bool = True, error_msg: str = None):
        """Enhanced final message with better formatting"""
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
                await self.telethon_client.send_message(
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
                await self.telethon_client.edit_message(
                    entity=chat_id,
                    message=self.progress_data[chat_id]['msg_id'],
                    text=final_text,
                )
            except MessageNotModifiedError:
                pass  # Already updated
            except Exception as edit_err:
                # If edit fails, send new final message
                print(f"[Uploader] [ERROR] Final message edit failed: {edit_err}")
                await self.telethon_client.send_message(
                    entity=chat_id,
                    message=final_text,
                    reply_to=self.progress_data[chat_id]['user_msg_id'],
                )
        except Exception as e:
            print(f"[Uploader] [ERROR] Final message error: {e}")
        finally:
            # Clean up tracking data
            self.progress_data.pop(chat_id, None)
            self.last_update.pop(chat_id, None)

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
                'msg_id': user_msg_id, # Use user_msg_id as initial msg_id
                'user_msg_id': user_msg_id,
                'file': file_name
            }
            # Reset speed tracking
            self.speed_data[chat_id] = {'last_bytes': 0, 'last_time': asyncio.get_event_loop().time(), 'start_time': asyncio.get_event_loop().time(), 'last_console_time': 0}

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

            result = await self.telethon_client.upload_file(
                file=file_path,
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