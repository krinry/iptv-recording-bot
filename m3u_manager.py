import requests
import re
import os
import time
import json
import logging
from typing import Dict, Optional, List
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = "playlist_cache"
CACHE_EXPIRY = 3600  # 1 hour in seconds

class M3UManager:
    def __init__(self, playlist_urls: List[str]):
        self.playlists = {}
        self.channels = {}
        self.url_to_source = {}
        
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        for idx, url in enumerate(playlist_urls):
            self.add_playlist(url, idx + 1)

    def _get_cache_path(self, url: str) -> str:
        """Generate a file path for the cache based on the URL."""
        return os.path.join(CACHE_DIR, f"{hash(url)}.json")

    def _load_from_cache(self, url: str) -> Optional[dict]:
        """Load playlist data from cache if it's not expired."""
        cache_path = self._get_cache_path(url)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_data = json.load(f)
                
                if time.time() - cached_data.get('timestamp', 0) < CACHE_EXPIRY:
                    logger.info(f"Loading playlist from cache: {url}")
                    return cached_data['data']
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Invalid cache file for {url}: {e}")
        return None

    def _save_to_cache(self, url: str, data: dict):
        """Save playlist data to a cache file."""
        cache_path = self._get_cache_path(url)
        try:
            with open(cache_path, 'w') as f:
                json.dump({'timestamp': time.time(), 'data': data}, f)
        except IOError as e:
            logger.error(f"Failed to write to cache for {url}: {e}")

    def add_playlist(self, playlist_url: str, playlist_num: int):
        playlist_id = f"p{playlist_num}"
        
        # Try loading from cache first
        cached_playlist = self._load_from_cache(playlist_url)
        if cached_playlist:
            self.playlists[playlist_id] = cached_playlist
            self._register_channels(playlist_id)
            return

        logger.info(f"Fetching new playlist: {playlist_url}")
        try:
            response = requests.get(playlist_url, timeout=10)
            response.raise_for_status()
            
            self.playlists[playlist_id] = {
                'url': playlist_url,
                'channels': {},
                'number': playlist_num
            }
            
            self._parse_and_add_channels(response.text, playlist_id)
            self._save_to_cache(playlist_url, self.playlists[playlist_id])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error loading playlist {playlist_url}: {e}")

    def _parse_and_add_channels(self, playlist_text: str, playlist_id: str):
        channel_info = {}
        for line in playlist_text.splitlines():
            if line.startswith('#EXTINF'):
                channel_id_match = re.search(r'tvg-id="([^"]+)"', line)
                channel_name_match = re.search(r',(.+)$', line)
                
                channel_info = {
                    'id': f"{playlist_id}:{channel_id_match.group(1) if channel_id_match else ''}",
                    'name': channel_name_match.group(1).strip() if channel_name_match else "Unknown",
                    'original_id': self._clean_channel_id(channel_id_match.group(1)) if channel_id_match else '',
                    'playlist': playlist_id
                }
            elif line.startswith('http'):
                if channel_info:
                    combined_id = channel_info['id']
                    self.playlists[playlist_id]['channels'][combined_id] = {
                        'name': channel_info['name'],
                        'url': line.strip(),
                        'original_id': channel_info['original_id'],
                        'playlist': playlist_id
                    }
                channel_info = {}
        self._register_channels(playlist_id)

    def _register_channels(self, playlist_id: str):
        """Helper to register channels in the main lookup dictionary."""
        playlist_data = self.playlists.get(playlist_id, {})
        for combined_id, info in playlist_data.get('channels', {}).items():
            self.channels[combined_id] = info
            if info.get('original_id'):
                self.channels[info['original_id']] = info
            self.channels[info['name'].lower()] = info
            self.url_to_source[info['url']] = playlist_id
            
    def _clean_channel_id(self, channel_id: str) -> str:
        if not channel_id:
            return ""
        # Keep alphanumeric, dots, and hyphens, remove others
        return re.sub(r'[^a-zA-Z0-9.-]', '', channel_id)

    def get_channel_url(self, identifier: str) -> Optional[str]:
        """Get channel URL by ID, name, or partial match"""
        identifier = identifier.lower()
        
        # Try exact match first
        if identifier in self.channels:
            return self.channels[identifier]['url']
        
        # Try partial ID match
        for channel_id, info in self.channels.items():
            if isinstance(channel_id, str) and ':' in channel_id:
                if identifier in info['original_id'].lower():
                    return info['url']
                if identifier in info['name'].lower():
                    return info['url']
        
        return None

    def search_channels(self, search_term: str, playlist_id: Optional[str] = None) -> Dict[str, dict]:
        """Search channels across all playlists or a specific playlist"""
        results = {}
        search_term = search_term.lower()
        
        for channel_id, info in self.channels.items():
            if isinstance(channel_id, str) and ':' in channel_id:
                if (search_term in info['name'].lower() or 
                    search_term in info['original_id'].lower()):
                    if not playlist_id or info['playlist'] == playlist_id:
                        results[channel_id] = info
        return results

    def get_channel_info(self, identifier: str) -> Optional[dict]:
        """Get complete channel info by ID, name, or partial match"""
        identifier = identifier.lower()
        
        # Try exact match first
        if identifier in self.channels:
            return self.channels[identifier]
        
        # Try partial ID match
        for channel_id, info in self.channels.items():
            if isinstance(channel_id, str) and ':' in channel_id:
                if identifier in info['original_id'].lower():
                    return info
                if identifier in info['name'].lower():
                    return info
        
        return None

from config import M3U_PLAYLISTS

# Initialize with multiple playlists from config
m3u_manager = M3UManager(M3U_PLAYLISTS)
