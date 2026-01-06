from telethon import events
from telethon.tl.custom import Button
from config import ADMIN_ID
from datetime import datetime, timedelta
from utils.admin_checker import get_admin_expiry_time, add_temp_admin, is_temp_admin
from telethon.errors.rpcerrorlist import PeerIdInvalidError

async def handle_admin_request(event: events.CallbackQuery):
    user = await event.get_sender()
    
    # First check permanent admin status
    is_permanent_admin = user.id in ADMIN_ID
    
    # Then check temporary admin status (only if not permanent admin)
    is_temp = False
    remaining_time = ""
    if not is_permanent_admin:
        is_temp = await is_temp_admin(user.id)
        if is_temp:
            expiry_time = await get_admin_expiry_time(user.id)
            if expiry_time:
                time_left = expiry_time - datetime.now()
                hours = time_left.seconds // 3600
                minutes = (time_left.seconds % 3600) // 60
                remaining_time = (
                    f"\n\n⏳ Your temporary admin access expires in: "
                    f"{hours} hours, {minutes} minutes"
                )

    # Only show admin status message if they actually are an admin
    if is_permanent_admin or is_temp:
        try:
            await event.client.send_message(
                entity=user.id,
                message=f"🌟 **Admin Status**\n\n"
                     f"You already have admin access!\n"
                     f"{'⏳ This is a permanent admin account' if is_permanent_admin else remaining_time}\n\n"
                     f"No need to request again. 😊",
                parse_mode="Markdown"
            )
        except PeerIdInvalidError:
            print(f"Could not send admin status to user {user.id}. User has not started a conversation with the bot.")
            # Optionally, notify main admins here that user couldn't be messaged
        return
    
    # Rest of the function for non-admin users...
    request_msg = (
        "🆕 **NEW ADMIN REQUEST** 🆕\n\n"
        f"👤 **Requester:** {user.first_name}\n"
        f"🆔 **User ID:** `{user.id}`\n"
    )

    if user.username:
        request_msg += f"🔗 @{user.username}\n"

    request_msg += (
        "\nTo grant temporary access:\n"
        f"`/add {user.id} 04:00:00` (for 4 hours)\n\n"
        "Or make permanent admin via config.py\n\n"
        f"Request received at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


    # Send to all admins
    for admin_chat_id in ADMIN_ID:
        try:
            await event.client.send_message(
                entity=admin_chat_id,
                message=request_msg,
                parse_mode="Markdown",
                # Telethon does not have disable_notification directly in send_message
                # Use silent=True if you want to disable notification
            )
        except Exception as e:
            print(f"Error notifying admin {admin_chat_id}: {e}")

    # Send confirmation to user - enhanced version

    user_response = (
        "✅ **Admin Request Received**\n\n"
        "🔹 Your request has been sent to the bot admins.\n"
        "🔹 You'll receive a notification when approved.\n"
        "🔹 Average approval time: 6-12 hours.\n\n"
    
        "📌 **Important Notes:**\n"
        "• Temporary access will be granted (e.g., 4-12 hours initially).\n"
        "• Admins ***will not*** auto-approve requests.\n"
        "• For urgent requests, please contact the developer.\n\n"
    
        "Thank you for your patience! 😊"
    )

# Add the inline keyboard button
    keyboard = [[Button.url("Help / Contact Developer", "https://t.me/krinry123")]]

    try:
        await event.client.send_message(
            entity=user.id,
            message=user_response,
            parse_mode="Markdown",
            buttons=keyboard
        )
    except PeerIdInvalidError:
        bot_entity = await event.client.get_me()
        bot_username = bot_entity.username
        bot_start_link = f"https://t.me/{bot_username}?start"
        
        await event.edit(
            f"⚠️ **Admin Request Failed!**\n\n"
            f"Aapne abhi tak bot ke saath private chat start nahi ki hai.\n"
            f"Pehle yahan click karke bot ko start karein: [Start Bot]({bot_start_link})\n\n"
            f"Uske baad, aap dobara request kar sakte hain.",
            parse_mode="Markdown",
            buttons=[[Button.url("Start Bot", bot_start_link)]]
        )
        print(f"Could not send confirmation to user {user.id}. User has not started a conversation with the bot.")
        for admin_chat_id in ADMIN_ID:
            try:
                await event.client.send_message(
                    entity=admin_chat_id,
                    message=f"⚠️ User {user.first_name} ({user.id}) requested admin access but could not be messaged directly. They need to start a conversation with the bot first.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error notifying admin {admin_chat_id} about unmessagable user: {e}")
    
    
    
    
    
    
async def handle_approval(event: events.CallbackQuery):
    await event.answer()
    
    # Extract user ID and duration from callback_data
    # Telethon callback_query.data is bytes, decode it
    _, user_id, duration = event.data.decode('utf-8').split("_")
    user_id = int(user_id)
    duration = int(duration)
    
    # Add temporary admin
    expiry_time = datetime.now() + timedelta(hours=duration)
    await add_temp_admin(user_id, expiry_time)
    
    # Notify admin
    await event.edit(
        text=f"✅ Temporary admin access granted to user `{user_id}` for {duration} hours.",
        parse_mode="Markdown"
    )
    
    # Notify user
    try:
        await event.client.send_message(
            entity=user.id,
            message=f"🎉 **Admin Access Granted!**\n\n"
                 f"You have been granted temporary admin access for {duration} hours.\n\n"
                 f"Thank you for your patience! 😊",
            parse_mode="Markdown"
        )
    except PeerIdInvalidError:
        print(f"Could not send admin access granted message to user {user.id}. User has not started a conversation with the bot.")
        for admin_chat_id in ADMIN_ID:
            try:
                await event.client.send_message(
                    entity=admin_chat_id,
                    message=f"⚠️ Admin access granted to user {user.first_name} ({user.id}) but could not be messaged directly. They need to start a conversation with the bot first.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error notifying admin {admin_chat_id} about unmessagable user: {e}")
        
    
 