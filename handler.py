from telethon.sync import TelegramClient
from telethon import events
from telethon.tl.custom import Button

# Import handler functions (will be modified to accept Telethon events)
from handlers.start_handler import start
from handlers.admin_handler import handle_admin_request
from handlers.help_handler import send_help, help_callback # Import help_callback
from handlers.schedule_handler import handle_schedule
from handlers.record_handler import handle_instant_record
from handlers.temp_admin_handler import add_temp_admin_command, remove_admin_command
from handlers.group_admin_handler import add_group_admin_command, remove_group_admin_command
# from features.messaging import get_message_handlers # To be converted later
from handlers.record_handler import handle_find_channel
from handlers.record_handler import show_help
from handlers.help_handler import cancel_recording_callback
from features.status_broadcast import status_command, broadcast_command
from handlers.cancel_handler import handle_cancel, handle_cancel_button
from handlers.file_handler import handle_list_files, handle_upload_file, handle_delete_file
from chatbot.bot_app import handle_chat_message
# from features.verify import setup_verify_handlers # To be converted later

def register_handlers(client: TelegramClient):
    """Register all handlers with the Telethon client"""
    
    # Command Handlers
    client.add_event_handler(start, events.NewMessage(pattern='/start'))
    client.add_event_handler(send_help, events.NewMessage(pattern='/h$|/help$'))
    client.add_event_handler(handle_schedule, events.NewMessage(pattern='/schedule|/sd'))
    client.add_event_handler(handle_instant_record, events.NewMessage(pattern='/rec|/rd|/record'))
    client.add_event_handler(add_temp_admin_command, events.NewMessage(pattern='/addadmin|/add'))
    client.add_event_handler(remove_admin_command, events.NewMessage(pattern='/removeadmin|/rm'))
    client.add_event_handler(add_group_admin_command, events.NewMessage(pattern='/addgroupadmin'))
    client.add_event_handler(remove_group_admin_command, events.NewMessage(pattern='/removegroupadmin'))
    client.add_event_handler(handle_find_channel, events.NewMessage(pattern='/find'))
    client.add_event_handler(handle_instant_record, events.NewMessage(pattern='/p1'))
    client.add_event_handler(handle_instant_record, events.NewMessage(pattern='/p2'))
    client.add_event_handler(handle_instant_record, events.NewMessage(pattern='/p3'))
    client.add_event_handler(status_command, events.NewMessage(pattern='/status|/sts'))
    client.add_event_handler(broadcast_command, events.NewMessage(pattern='/broadcast|/bc'))
    client.add_event_handler(handle_cancel, events.NewMessage(pattern='/cancel'))
    client.add_event_handler(handle_list_files, events.NewMessage(pattern='/files'))
    client.add_event_handler(handle_upload_file, events.NewMessage(pattern='/upload'))
    client.add_event_handler(handle_delete_file, events.NewMessage(pattern='/delete'))

    # CallbackQuery Handlers
    client.add_event_handler(handle_admin_request, events.CallbackQuery(pattern=b'^request_admin$'))
    client.add_event_handler(handle_cancel_button, events.CallbackQuery(pattern=b'^cancel_recording_'))
    client.add_event_handler(help_callback, events.CallbackQuery(pattern=b'^help_')) # Register help_callback

    # AI Chatbot (Krinry) — catch-all for non-command messages (must be LAST)
    client.add_event_handler(
        handle_chat_message,
        events.NewMessage(func=lambda e: e.text and not e.text.startswith('/'))
    )

    # Verify Handlers (to be converted later)
    # setup_verify_handlers(client)
