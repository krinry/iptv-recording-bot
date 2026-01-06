from datetime import datetime, timedelta
from typing import Optional
from utils.database import get_database
from config import ADMIN_ID, CHANNEL_ID

async def is_temp_admin(user_id: int) -> bool:
    db = get_database()
    if db is None:
        return False
    
    temp_admins_collection = db["temp_admins"]
    admin_entry = await temp_admins_collection.find_one({"user_id": user_id})

    if not admin_entry:
        return False

    expiry_time = admin_entry.get("expiry_date")
    if not expiry_time:
        return False

    return datetime.now() < expiry_time

async def is_group_admin(chat_id: int) -> bool:
    db = get_database()
    if db is None:
        return False
    
    group_admins_collection = db["group_admins"]
    group_entry = await group_admins_collection.find_one({"chat_id": chat_id})
    return group_entry is not None

async def add_group_admin(chat_id: int) -> bool:
    db = get_database()
    if db is None:
        return False

    group_admins_collection = db["group_admins"]
    try:
        await group_admins_collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error adding group admin to MongoDB: {e}")
        return False

async def remove_group_admin(chat_id: int) -> bool:
    db = get_database()
    if db is None:
        return False

    group_admins_collection = db["group_admins"]
    result = await group_admins_collection.delete_one({"chat_id": chat_id})
    return result.deleted_count > 0

async def is_admin(user_id: int, chat_id: int) -> bool:
    # Main ADMIN_ID always has full access
    if user_id in ADMIN_ID:
        return True

    # Temporary admins have access
    if await is_temp_admin(user_id):
        return True

    # All users in the designated CHANNEL_ID group have basic access
    # Note: This assumes CHANNEL_ID is a group chat ID. 
    # For private chats, chat_id will be the user_id itself.
    if chat_id == CHANNEL_ID:
        return True

    # Check if the chat itself is an admin group
    if await is_group_admin(chat_id):
        return True

    return False

async def remove_temp_admin(user_id: int) -> bool:
    db = get_database()
    if db is None:
        return False

    temp_admins_collection = db["temp_admins"]
    result = await temp_admins_collection.delete_one({"user_id": user_id})
    return result.deleted_count > 0

async def add_temp_admin(user_id: int, expiry: datetime) -> bool:
    db = get_database()
    if db is None:
        return False

    temp_admins_collection = db["temp_admins"]
    try:
        await temp_admins_collection.update_one(
            {"user_id": user_id},
            {"$set": {"expiry_date": expiry}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error adding temporary admin to MongoDB: {e}")
        return False

async def cleanup_expired_admins() -> None:
    db = get_database()
    if db is None:
        return

    temp_admins_collection = db["temp_admins"]
    try:
        await temp_admins_collection.delete_many({"expiry_date": {"$lt": datetime.now()}})
    except Exception as e:
        print(f"Error cleaning up expired admins from MongoDB: {e}")

async def get_admin_expiry_time(user_id: int) -> Optional[datetime]:
    db = get_database()
    if db is None:
        return None

    temp_admins_collection = db["temp_admins"]
    admin_entry = await temp_admins_collection.find_one({"user_id": user_id})

    if not admin_entry:
        return None

    return admin_entry.get("expiry_date")
