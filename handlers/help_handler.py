from telethon import events
from telethon.tl.custom import Button
from config import ADMIN_ID
from utils.admin_checker import is_admin, is_temp_admin

# --- Help Text Content ---

def get_main_help_text():
    return """
    🔸 **Bot Commands Help** 🔸

    Select a category below to see the available commands.
    """

def get_recording_help_text():
    return """
    🎥 **Recording Commands**

    `/rd <url> <duration> <title> --split <time>`
    ├ Records a stream with optional duration and splitting


    📝 Examples:
    ├ /rd http://... My Stream
    │  ↳ Unlimited recording
    ├ /rd http://... 10:00 Ten Min
    │  ↳ Records for 10 minutes
    ├ /rd http://... Stream --split 30:00
    │  ↳ Splits every 30 minutes
    └ /rd http://... 02:00:00 Movie --split 01:00:00
       ↳ 2 hour recording, split hourly

    **Scheduled Recording:**
    `/sd <url/id> <datetime> <duration> [title]`
    - **datetime:** In `DD-MM-YYYY HH:MM:SS` format.
    
    **Find Channels:**
    `/find <query>` - Search for channels by name or ID.
    """

def get_admin_help_text():
    return """
    🛡️ **Admin Management**

    `/add <user_id> [duration]`
    - Adds a temporary admin.
    - **duration:** (Optional) e.g., `1h`, `2d`.
    
    `/rm <user_id>`
    - Removes an admin or temporary admin.

    `/status`
    `/sts`
    - Check your admin status and remaining time.
    """

def get_messaging_help_text():
    return """
    📩 **Messaging Commands**

    `/reply <user_id> <message>`
    - Sends a message to a specific user.

    `/broadcast <message>`
    `/bd <message>`
    - Sends a message to all users.
    
    **Reply to a forwarded message** to send a response directly to that user.
    """

def get_file_management_help_text():
    return """
    📁 **File Management**

    ├ /files - List recorded videos
    ├ /upload <file> - Upload a video
    └ /delete <file> - Delete a video
    """

# --- Keyboard Layouts ---

def get_main_keyboard():
    keyboard = [
        [
            Button.inline("🎥 Recording", b"help_recording"),
            Button.inline("🛡️ Admin", b"help_admin"),
        ],
        [
            Button.inline("📩 Messaging", b"help_messaging"),
            Button.inline("📁 File Management", b"help_file_management"),
        ],
    ]
    return keyboard

def get_back_keyboard():
    keyboard = [[Button.inline("« Back to Help", b"help_main")]]
    return keyboard

# --- Handlers ---

async def send_help(event: events.NewMessage):
    user_id = event.sender_id
    
    if not await is_admin(user_id, event.chat_id):
        await event.reply(
            "⚠️ **Unauthorized Access**\n\n"
            "You don't have permission to use this bot.",
            parse_mode="Markdown"
        )
        return

    await event.reply(
        get_main_help_text(),
        buttons=get_main_keyboard(),
        parse_mode="Markdown",
        link_preview=False,
    )

async def help_callback(event: events.CallbackQuery):
    await event.answer()

    help_section = event.data.decode('utf-8').split("_")[1]

    text = ""
    reply_markup = get_back_keyboard()

    if help_section == "main":
        text = get_main_help_text()
        reply_markup = get_main_keyboard()
    elif help_section == "recording":
        text = get_recording_help_text()
    elif help_section == "admin":
        text = get_admin_help_text()
    elif help_section == "messaging":
        text = get_messaging_help_text()
    elif help_section == "file_management":
        text = get_file_management_help_text()

    await event.edit(
        text=text,
        buttons=reply_markup,
        parse_mode="Markdown",
        link_preview=False,
    )

async def cancel_recording_callback(event: events.CallbackQuery):
    await event.answer()
    user_id = event.sender_id
    chat_id = int(event.data.decode('utf-8').split("_")[-1])
    
    # Check authorization
    if user_id != chat_id and not await is_admin(user_id, chat_id):
        await event.answer("You are not authorized to cancel this recording.", alert=True)
        return

    # Cancel the recording
    # This part needs access to the recording process, which is currently in context.chat_data
    # This will need to be refactored to use a global or shared state for active recordings.
    # For now, I'll leave a placeholder for the cancellation logic.
    # recording_process = context.chat_data.get('recording_process')
    # if recording_process:
    #     try:
    #         recording_process.terminate()
    #         await event.answer("Recording cancelled successfully", alert=True)
    #         await event.edit("⏹ Recording cancelled by user/admin.")
    #     except Exception as e:
    #         await event.answer(f"Error cancelling: {str(e)}", alert=True)
    # else:
    #     await event.answer("No active recording to cancel", alert=True)
    
    await event.edit("⏹ Recording cancellation logic needs to be implemented with Telethon.")
