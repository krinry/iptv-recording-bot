import aiohttp
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def resolve_stream(url: str) -> str:
    """
    Resolves stream URLs, follows redirects for m3u8 streams.
    
    Args:
        url: Stream URL to resolve
        
    Returns:
        Resolved URL string
    """
    if url.endswith(".m3u8"):
        return url
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "*/*",
            "Referer": "https://www.tataplay.com/",
            "Origin": "https://www.tataplay.com"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10, allow_redirects=True) as response:
                return str(response.url) if response.url != url else url
    except Exception as e:
        logger.error(f"[Stream Resolver] Error resolving stream: {e}")
        return url


async def get_video_duration(file_path: str) -> Optional[float]:
    """
    Gets the duration of a video file using ffprobe.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Duration in seconds as float, or None if error occurs
    """
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
            duration_str = stdout.decode().strip()
            if duration_str:
                return float(duration_str)
            else:
                logger.warning(f"[FFprobe] Empty duration output for {file_path}")
                return None
        else:
            logger.error(f"[FFprobe] Error getting duration: {stderr.decode().strip()}")
            return None
            
    except FileNotFoundError:
        logger.error("[FFprobe] ffprobe not found. Please ensure FFmpeg is installed and in your PATH.")
        return None
    except ValueError as e:
        logger.error(f"[FFprobe] Invalid duration value: {e}")
        return None
    except Exception as e:
        logger.error(f"[FFprobe] Unexpected error getting video duration: {e}")
        return None


async def get_stream_quality(file_path: str) -> str:
    """
    Detects video quality/resolution using ffprobe.
    
    Args:
        file_path: Path to video file
        
    Returns:
        Quality string: "FHD", "HD", "SD", "HQ", or "Unknown"
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0",
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
            resolution = stdout.decode().strip()
            
            if not resolution:
                logger.warning(f"[FFprobe] Empty resolution output for {file_path}")
                return "Unknown"
            
            # Parse resolution
            if '1920x1080' in resolution or '1920' in resolution:
                return "FHD"
            elif '1280x720' in resolution or '1280' in resolution:
                return "HD"
            elif '854x480' in resolution or '720x480' in resolution:
                return "SD"
            elif 'x' in resolution:
                # Has valid resolution format
                return "HQ"
            else:
                return "Unknown"
        else:
            logger.error(f"[FFprobe] Error getting resolution: {stderr.decode().strip()}")
            return "Unknown"
            
    except FileNotFoundError:
        logger.error("[FFprobe] ffprobe not found. Please ensure FFmpeg is installed and in your PATH.")
        return "Unknown"
    except Exception as e:
        logger.error(f"[FFprobe] Unexpected error getting stream quality: {e}")
        return "Unknown"
