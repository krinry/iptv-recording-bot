import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Core Bot Configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the environment variables.")

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SESSION_NAME = os.getenv("SESSION_NAME", "session_iptv")

# --- Admin and Channel Configuration ---
raw_admin_id = os.getenv("ADMIN_ID")
if not raw_admin_id:
    raise ValueError("ADMIN_ID is not set in the environment variables.")
ADMIN_ID = [int(admin_id.strip()) for admin_id in raw_admin_id.split(',')]
print(f"Parsed ADMIN_ID: {ADMIN_ID}")

ADMIN_FILE = os.getenv("ADMIN_FILE", "temp_admins.json")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", 0))
STORE_CHANNEL_ID = int(os.getenv("STORE_CHANNEL_ID", 0))

# --- Recording and Uploading ---
RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "recordings")
MAX_PART_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB

# --- M3U Playlists ---
# Load playlists from a comma-separated string in the environment variable
raw_playlists = os.getenv("M3U_PLAYLISTS")
M3U_PLAYLISTS = [url.strip() for url in raw_playlists.split(',')] if raw_playlists else []
if not M3U_PLAYLISTS:
    print("Warning: M3U_PLAYLISTS is not set. The bot may not have any channels to record.")

# --- Verification ---
VERIFICATION_BASE_URL = os.getenv("VERIFICATION_BASE_URL", "https://vplinks.com/api?api_key=YOUR_API_KEY&url=")
BOT_NAME = os.getenv("BOT_NAME", "iptvrecording_bot")
VERIFICATION_REWARD_MINUTES = int(os.getenv("VERIFICATION_REWARD_MINUTES", 10))

VERIFICATION_LINKS = {}
ACTIVE_RECORDINGS = {}
