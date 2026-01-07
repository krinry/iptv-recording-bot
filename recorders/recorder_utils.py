import aiohttp
import subprocess
from subprocess import check_output


async def resolve_stream(url):
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
        print(f"[Stream Resolver] Error: {e}")
        return url


async def get_stream_quality(file_path):
    """Detect video quality using ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            file_path
        ]
        resolution = subprocess.check_output(cmd).decode().strip()
        if '1920x1080' in resolution:
            return "FHD"
        elif '1280x720' in resolution:
            return "HD"
        elif '720x480' in resolution:
            return "SD"
        return "HQ"
    except Exception:
        return "Quality"

async def get_accurate_duration(file_path):
    """Get accurate duration using ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        duration = float(subprocess.check_output(cmd).decode().strip())
        return duration
    except Exception:
        return None

