from telethon import events
from telethon.tl.custom import Button
from config import ADMIN_ID
from utils.admin_checker import is_admin, is_temp_admin

# --- Help Text Content ---

def get_main_help_text():
    return """🔸 **Bot Commands Help** 🔸

Select a category below to see the available commands."""

def get_recording_help_text():
    return """🎥 **Recording Commands**

`/rec <url/id> [duration] [title] [--split <time>]`
Aliases: `/rd`, `/record`
├ Records a stream.
└ **Examples:**
  ├ `/rec http://... 10:00 MyStream`
  ├ `/rec sony 01:00:00 Movie`
  └ `/rd news --split 30:00` (Splits every 30m)

**Shortcuts (Playlist Filtering):**
`/p1`, `/p2`, `/p3` ...
├ Equivalent to `/rec` but filters by playlist.
└ Ex: `/p1 sony 30` (Search 'sony' only in Playlist 1)

**Find Channels:**
`/find <query> [.p1]`
└ Search channel names/IDs.
  Ex: `/find sports .p2`"""

def get_scheduling_help_text():
    return """📅 **Scheduling Commands**

`/schedule "url" DD-MM-YYYY HH:MM:SS duration channel title`
Aliases: `/sd`, `/s`
├ Schedule a future recording.
└ **Example:**
  `/sd "http://..." 25-12-2025 10:00:00 01:00:00 Sports Final Match`

`/cancel [message_id]`
└  Cancel a scheduled recording. Reply to the scheduled message or provide ID."""

def get_admin_help_text():
    return """🛡️ **Admin Management**

**Temporary Admin:**
`/addadmin <user_id> <time>` (Alias: `/add`)
└ Add temp admin. Ex: `/add 12345 04:00:00`

`/removeadmin <user_id>` (Alias: `/rm`)
└ Remove admin access.

**Group Admin:**
`/addgroupadmin <group_id>`
`/removegroupadmin <group_id>`

**Status & Broadcast:**
`/status` (Alias: `/sts`) - Check resources/admin status.
`/broadcast <msg>` (Alias: `/bc`) - Send msg to all users."""

def get_file_management_help_text():
    return """📁 **File Management**

`/files`
└ List all recorded files in storage.

`/upload <filename>`
└ Force upload of a specific file.

`/delete <filename>`
└ Delete a file from storage permanently."""

def get_messaging_help_text():
    return """📩 **Messaging**

`/reply <user_id> <message>`
└ Reply to a specific user.

Replying to a forwarded message also works."""

# --- Keyboard Layouts ---

def get_main_keyboard():
    keyboard = [
        [
            Button.inline("🎥 Recording", b"help_recording"),
            Button.inline("📅 Scheduling", b"help_scheduling"),
        ],
        [
            Button.inline("🛡️ Admin", b"help_admin"),
            Button.inline("📁 Files", b"help_file_management"),
        ],
        [
            Button.inline("📩 Messaging", b"help_messaging"),
        ]
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

    # Extract section name after "help_" prefix (handle multi-underscore names)
    help_section = event.data.decode('utf-8').split("_", 1)[1]

    text = ""
    reply_markup = get_back_keyboard()

    if help_section == "main":
        text = get_main_help_text()
        reply_markup = get_main_keyboard()
    elif help_section == "recording":
        text = get_recording_help_text()
    elif help_section == "scheduling":
        text = get_scheduling_help_text()
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
