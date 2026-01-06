import sys
import logging
import warnings
import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon import events
from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING

# Configure logging and warnings
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Suppress unwanted logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('pyrogram').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('telegram.ext').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def main():
    """Main asynchronous bot function"""
    try:
        logger.info("Initializing bot...")
        
        # Initialize Telethon client
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.start(bot_token=BOT_TOKEN)

        # Initialize and start uploader's Telethon client
        from uploader import upload_manager
        await upload_manager.init_client()
        
        logger.info("Bot is running. Press Ctrl+C to stop.")
        
        # Register handlers
        from handler import register_handlers
        register_handlers(client) # Pass the Telethon client to register handlers
        
        # Run until disconnected
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("\nBot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}") # Telethon handles markdown automatically
    finally:
        logger.info("Clean shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
