import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Core Bot Configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the environment variables.")

API_ID = os.getenv("API_ID")
if not API_ID:
    raise ValueError("API_ID is not set in the environment variables. Get it from https://my.telegram.org")
try:
    API_ID = int(API_ID)
except ValueError:
    raise ValueError("API_ID must be a valid integer")

API_HASH = os.getenv("API_HASH")
if not API_HASH:
    raise ValueError("API_HASH is not set in the environment variables. Get it from https://my.telegram.org")

SESSION_STRING = os.getenv("SESSION_STRING")
if not SESSION_STRING:
    raise ValueError("SESSION_STRING is not set. Run generate_session.py to create one.")

SESSION_NAME = os.getenv("SESSION_NAME", "session_iptv")

# --- Admin and Channel Configuration ---
raw_admin_id = os.getenv("ADMIN_ID")
if not raw_admin_id:
    raise ValueError("ADMIN_ID is not set in the environment variables.")

try:
    ADMIN_ID = [int(admin_id.strip()) for admin_id in raw_admin_id.split(',')]
except ValueError:
    raise ValueError("ADMIN_ID must be comma-separated integers (e.g., 123456,789012)")

print(f"Parsed ADMIN_ID: {ADMIN_ID}")

ADMIN_FILE = os.getenv("ADMIN_FILE", "temp_admins.json")

try:
    CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", 0))
    STORE_CHANNEL_ID = int(os.getenv("STORE_CHANNEL_ID", 0))
except ValueError:
    raise ValueError("CHANNEL_ID, LOG_CHANNEL, and STORE_CHANNEL_ID must be valid integers")

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
VERIFICATION_BASE_URL = os.getenv("VERIFICATION_BASE_URL", "")
BOT_NAME = os.getenv("BOT_NAME", "iptvrecording_bot")
VERIFICATION_REWARD_MINUTES = int(os.getenv("VERIFICATION_REWARD_MINUTES", 10))

VERIFICATION_LINKS = {}
ACTIVE_RECORDINGS = {}
