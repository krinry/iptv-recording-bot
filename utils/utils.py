import os
import asyncio
from datetime import timedelta
from typing import List
import aiofiles

async def format_bytes(size: int) -> str:
    """
    Convert bytes to a human-readable format (KB, MB, GB, etc.).
    
    Args:
        size: Size in bytes.
        
    Returns:
        Formatted string with appropriate unit (e.g., "1.23 GB").
    """
    if not isinstance(size, (int, float)) or size < 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}".replace(".00", "").rstrip(" ")
        size /= 1024.0
    return f"{size:.2f} PB"

async def format_duration(duration_str: str) -> str:
    """
    Format a duration string (HH:MM:SS) into a human-readable format.
    Preserves the exact input duration without any conversion.
    
    Args:
        duration_str: Duration in "HH:MM:SS" format.
        
    Returns:
        Formatted string (e.g., "2hr, 30min, 15sec" or "Original: 01:30:00").
    """
    try:
        # First try to parse as HH:MM:SS
        h, m, s = map(int, duration_str.split(":"))
        if h < 0 or m < 0 or s < 0 or m >= 60 or s >= 60:
            raise ValueError
        return f"{h}hr, {m}min, {s}sec (Original: {duration_str})"
    except (ValueError, AttributeError, IndexError):
        # If invalid format, return the original string
        return f"Original: {duration_str}"


async def get_video_duration(file_path: str) -> float:
    """
    Get the duration of a video file using ffprobe.
    
    Args:
        file_path: Path to the video file.
        
    Returns:
        Duration in seconds.
    """
    duration_cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", file_path
    ]
    proc = await asyncio.create_subprocess_exec(
        *duration_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe error: {stderr.decode()}")
    return float(stdout.decode().strip())

async def split_video(file_path: str, max_size: int = 2 * 1024 * 1024 * 1024) -> List[str]:
    """
    Split a video file into smaller parts if it exceeds the max size.
    
    Args:
        file_path: Path to the video file.
        max_size: Maximum size for each part in bytes (default: 2GB).
        
    Returns:
        List of paths to the split video parts.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    size = os.path.getsize(file_path)
    if size <= max_size:
        return [file_path]

    base_name = os.path.splitext(file_path)[0]
    parts = []

    try:
        total_duration = await get_video_duration(file_path)
        num_parts = (size // max_size) + 1
        part_duration = total_duration / num_parts

        for i in range(num_parts):
            start = i * part_duration
            out_file = f"{base_name}_part{i+1}.mp4"
            cmd = [
                "ffmpeg", "-i", file_path, "-ss", str(int(start)), "-t",
                str(int(part_duration)), "-c", "copy", out_file
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"ffmpeg error while splitting part {i+1}")
            parts.append(out_file)

        return parts
    except Exception as e:
        # Clean up any partially created files
        for part in parts:
            if os.path.exists(part):
                os.remove(part)
        raise RuntimeError(f"Failed to split video: {str(e)}")

async def cleanup_files(file_paths: List[str]) -> None:
    """
    Clean up a list of files.
    
    Args:
        file_paths: List of file paths to delete.
    """
    for path in file_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error deleting file {path}: {str(e)}")
