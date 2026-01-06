import os
import asyncio
from telethon import events
from telethon.tl.custom import Button
from telethon.tl.types import User
from config import ADMIN_ID, LOG_CHANNEL, BOT_TOKEN
from features.auto_responses import AUTO_RESPONSES
from utils.database import get_database
from utils.admin_checker import is_admin

async def delete_after_delay(client, chat_id, message_id, delay=2):
    """Delete message after specified delay"""
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")

async def handle_message(event: events.NewMessage):
    """Main message handler"""
    # Ignore messages not addressed to the bot
    # Telethon's event.is_private checks if it's a private chat
    # For replies, check if the reply is to the bot itself
    if not (event.is_private or 
            (event.reply_to_msg_id and 
             (await event.get_reply_message()).sender_id == (await event.client.get_me()).id)):
        return

    user = await event.get_sender()
    message_text = event.text

    # Check for auto-responses first
    message_lower = message_text.lower()
    for keyword, response in AUTO_RESPONSES.items():
        if keyword in message_lower:
            await event.reply(response)
            return

    # Store message context in MongoDB
    db = get_database()
    if db is None:
        print("MongoDB not connected, cannot store message context.")
        return
    message_context_collection = db["message_context"]

    message_id = event.id
    context_data = {
        '_id': message_id,
        'user_id': user.id,
        'chat_id': event.chat_id,
        'is_group': not event.is_private,
        'original_msg_id': event.id
    }
    try:
        await message_context_collection.insert_one(context_data)
    except Exception as e:
        print(f"Error storing message context in MongoDB: {e}")

    # Forward to admins only for direct messages
    if event.is_private:
        for admin_id in ADMIN_ID:
            try:
                forwarded_message = await event.client.forward_messages(
                    entity=admin_id,
                    messages=event.message
                )
                
                # Store admin context in MongoDB
                admin_context_data = {
                    '_id': forwarded_message.id,
                    'source_message_id': message_id,
                    'is_admin_copy': True
                }
                await message_context_collection.insert_one(admin_context_data)
                
            except Exception as e:
                print(f"Error forwarding to admin {admin_id}: {e}")

        # Log and confirm
        if LOG_CHANNEL:
            await event.client.send_message(
                LOG_CHANNEL,
                f"#Message\nFrom: {user.first_name} {user.last_name or ''} (@{user.username or 'None'})\n"
                f"ID: {user.id}\nChat: {event.chat_id}\nMsg: {message_text}"
            )
        
        confirmation = await event.reply("✅ Aapka message admin tak pahunch gaya hai!")
        asyncio.create_task(delete_after_delay(event.client, event.chat_id, confirmation.id))

async def handle_reply(event: events.NewMessage):
    """Handle all replies"""
    if not event.reply_to_msg_id:
        return

    db = get_database()
    if db is None:
        print("MongoDB not connected, cannot retrieve message context.")
        return
    message_context_collection = db["message_context"]

    replied_msg_id = event.reply_to_msg_id
    
    # Check if this is an admin reply
    if await is_admin(event.sender_id, event.chat_id):
        source_context = await message_context_collection.find_one({"_id": replied_msg_id})
        
        if not source_context:
            return  # Ignore admin replies to non-tracked messages
            
        if source_context.get('is_admin_copy'):
            # This is admin replying to forwarded message
            original_message_id = source_context.get('source_message_id')
            original_context = await message_context_collection.find_one({"_id": original_message_id})
            
            if not original_context:
                return
                
            try:
                await event.client.send_message(
                    entity=original_context['chat_id'],
                    message=event.text,
                    reply_to=original_context['original_msg_id']
                )
                confirmation = await event.reply("✅ Reply bhej diya gaya hai!")
                asyncio.create_task(delete_after_delay(event.client, event.chat_id, confirmation.id))
                
                if LOG_CHANNEL:
                    await event.client.send_message(
                        LOG_CHANNEL,
                        f"#Reply\nAdmin: {event.sender.first_name} {event.sender.last_name or ''}\n"
                        f"To: {original_context['user_id']}\nMsg: {event.text}"
                    )
            except Exception as e:
                await event.reply(f"❌ Reply bhejne mein error aaya: {str(e)}")
        return
    
    # Handle user replies to bot messages
    reply_message = await event.get_reply_message()
    if reply_message and reply_message.sender_id == (await event.client.get_me()).id:
        await handle_message(event)  # Process as new message

async def admin_reply(event: events.NewMessage):
    """Handle /reply command"""
    if not await is_admin(event.sender_id, event.chat_id):
        return

    parts = event.text.split(maxsplit=2) # Split into command, user_id, message
    if len(parts) < 3:
        error_msg = await event.reply("Usage:\n/reply <user_id> <message>")
        asyncio.create_task(delete_after_delay(event.client, event.chat_id, error_msg.id))
        return
    
    try:
        user_id = int(parts[1])
        message_text = parts[2]
    except ValueError:
        error_msg = await event.reply("Invalid user ID.")
        asyncio.create_task(delete_after_delay(event.client, event.chat_id, error_msg.id))
        return
    
    try:
        await event.client.send_message(user_id, message_text)
        confirmation = await event.reply("✅ Reply bhej diya gaya hai!")
        asyncio.create_task(delete_after_delay(event.client, event.chat_id, confirmation.id))
        
        if LOG_CHANNEL:
            await event.client.send_message(
                LOG_CHANNEL,
                f"#Reply\nAdmin: {event.sender.first_name} {event.sender.last_name or ''}\n"
                f"To: {user_id}\nMsg: {message_text}"
            )
    except Exception as e:
        await event.reply(f"❌ Reply bhejne mein error aaya: {str(e)}")

async def user_info(event: events.NewMessage):
    """Handle /info command"""
    if not await is_admin(event.sender_id, event.chat_id):
        return
    
    if not event.reply_to_msg_id:
        error_msg = await event.reply("⚠️ Kisi forwarded message pe /info reply karein")
        return
    
    db = get_database()
    if db is None:
        error_msg = await event.reply("MongoDB not connected, cannot retrieve message context.")
        return
    message_context_collection = db["message_context"]

    replied_msg_id = event.reply_to_msg_id
    
    context_data = await message_context_collection.find_one({"_id": replied_msg_id})
    
    if not context_data:
        error_msg = await event.reply("⚠️ Is message ka context nahi mila")
        return
    
    user_id = context_data['user_id']
    
    try:
        user_entity = await event.client.get_entity(user_id)
        # Create copy buttons
        keyboard = [
            [Button.inline("Name Copy Karein", data=f"copy_name_{user_entity.first_name} {user_entity.last_name or ''}".encode())],
            [Button.inline("Username Copy Karein", data=f"copy_username_{user_entity.username or 'None'}".encode())],
            [Button.inline("ID Copy Karein", data=f"copy_id_{user_entity.id}".encode())]
        ]
        
        response = (
            f"👤 User Info:\n"
            f"Name: {user_entity.first_name} {user_entity.last_name or ''}\n"
            f"Username: @{user_entity.username or 'None'}\n"
            f"ID: {user_entity.id}\n\n"
            f"Copy karne ke liye niche click karein:"
        )
        
        await event.reply(
            response,
            buttons=keyboard
        )
    except Exception as e:
        await event.reply(f"❌ User info fetch karne mein error aaya: {str(e)}")

async def handle_copy_button(event: events.CallbackQuery):
    """Handle copy button clicks"""
    await event.answer()
    
    callback_data = event.data.decode('utf-8')
    if callback_data.startswith("copy_"):
        _, field, value = callback_data.split("_", 2)
        await event.edit(f"✅ {field.capitalize()} copy ho gaya: {value}")

# No longer needed as handlers are registered directly in handler.py
# def get_message_handlers():
#     return [
#         MessageHandler(
#             filters.TEXT & ~filters.COMMAND & ~filters.User(ADMIN_ID),
#             handle_message
#         ),
#         MessageHandler(
#             filters.TEXT & filters.REPLY,
#             handle_reply
#         ),
#         CommandHandler("reply", admin_reply),
#         CommandHandler("info", user_info),
#         CallbackQueryHandler(handle_copy_button)
#     ]
