import time
import shlex
import asyncio
from datetime import timedelta, datetime
from telethon import events
from telethon.sync import TelegramClient
from utils.admin_checker import is_admin
from scheduler import start_recording_instantly
from utils.logging import log_to_channel
from config import ADMIN_ID
from m3u_manager import m3u_manager


async def send_long_message(client: TelegramClient, chat_id: int, text: str, parse_mode: str = None):
    """Splits long messages into chunks of 4096 characters."""
    max_length = 4096
    for i in range(0, len(text), max_length):
        chunk = text[i:i + max_length]
        await client.send_message(entity=chat_id, message=chunk, parse_mode=parse_mode)

def parse_time(time_str: str) -> int:
    """Parses a time string (seconds or HH:MM:SS) and returns seconds."""
    if ":" in time_str:
        time_parts = list(map(int, time_str.split(":")))
        if len(time_parts) == 3:  # HH:MM:SS
            return time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]
        elif len(time_parts) == 2:  # MM:SS
            return time_parts[0] * 60 + time_parts[1]
        else:
            raise ValueError("Invalid time format")
    else:
        return int(time_str)

async def handle_instant_record(event: events.NewMessage):
    user_id = event.sender_id
    
    if not await is_admin(user_id, event.chat_id):
        await event.reply("⚠️ Unauthorized Access", parse_mode="Markdown")
        return

    try:
        # Parse command and extract playlist filter
        command = event.text.split()[0]  # /rec, /p1, /p2, etc.
        playlist_filter = None
        
        if command.startswith("/p") and command[2:].isdigit():
            playlist_filter = f"p{command[2:]}"
        
        parts = shlex.split(event.text)
        if len(parts) < 2:
            await event.reply(
                "❗ **Usage:**\n"
                "`/rd <url/id> [duration] [title] [--split <time>]`\n"
                "Example: `/rd http://... 10:00 My Recording`",
                parse_mode="Markdown"
            )
            return

        identifier = parts[1]
        remaining_args = parts[2:]
        
        duration_str = "0" # Default to unlimited
        title = "Untitled"
        split_duration_sec = None

        # Find --split
        if "--split" in remaining_args:
            split_index = remaining_args.index("--split")
            if split_index + 1 < len(remaining_args):
                split_duration_str = remaining_args[split_index + 1]
                try:
                    split_duration_sec = parse_time(split_duration_str)
                except ValueError:
                    await event.reply("Invalid format for --split time. Use seconds or HH:MM:SS.")
                    return
                # remove --split and its value
                del remaining_args[split_index:split_index+2]
            else:
                await event.reply("`--split` requires a time value.")
                return

        # The first remaining arg could be duration or part of the title.
        if remaining_args:
            try:
                # if it's a time, it's duration
                parse_time(remaining_args[0])
                duration_str = remaining_args[0]
                title_parts = remaining_args[1:]
                if title_parts:
                    title = " ".join(title_parts)
            except ValueError:
                # if not a time, it's part of the title
                title = " ".join(remaining_args)

        chat_id = event.chat_id

        # Parse duration
        try:
            duration_sec = parse_time(duration_str)
            duration_display = str(timedelta(seconds=duration_sec))
        except (ValueError, TypeError):
            await event.reply(
                "❌ **Invalid duration format!**\n"
                "Valid formats: 10, 00:10, 00:00:10",
                parse_mode="Markdown"
            )
            return

        # Get URL - handles both direct M3U8 links and channel identifiers
        if identifier.startswith(('http://', 'https://')):
            url = identifier
            channel_name = "Direct Stream"
        else:
            # Find channel with playlist filter
            channel_info = None
            if playlist_filter:
                # Search only in the specified playlist
                for channel_id, info in m3u_manager.channels.items():
                    if isinstance(channel_id, str) and ':' in channel_id:
                        if info.get('playlist') == playlist_filter and (
                            identifier.lower() == info['name'].lower() or
                            identifier.lower() == info.get('original_id', '').lower()
                        ):
                            channel_info = info
                            break
            else:
                # Search in all playlists
                channel_info = m3u_manager.get_channel_info(identifier)
            
            if not channel_info:
                # Try finding similar channels
                similar = m3u_manager.search_channels(identifier, playlist_filter)
                if similar:
                    response = "🔍 Similar channels found:\n" + "\n".join(
                        f"{info['name']} (ID: {info['original_id']})" 
                        for info in similar.values()
                    )
                    await send_long_message(event.client, chat_id, response, parse_mode="Markdown")
                else:
                    await event.reply(
                        f"❌ Channel not found: {identifier}\n"
                        "Use /find to search channels",
                        parse_mode="Markdown"
                    )
                return
            url = channel_info['url']
            channel_name = channel_info.get('name', identifier)

        # Start recording
        message_id = event.message.id
        
        asyncio.create_task(start_recording_instantly(
            event.client, url, duration_display, channel_name, title, 
            chat_id, message_id, user_id, split_duration_sec=split_duration_sec
        ))
      
        start_time_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        username = event.sender.username if event.sender.username else "Unknown"
        asyncio.create_task(log_to_channel(
            telethon_client=event.client,
            user_id=user_id,
            username=username,
            command=event.text,
            start_time_str=start_time_str,
            filename=title
        ))

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        await send_long_message(event.client, chat_id, error_msg, parse_mode="Markdown")


async def handle_find_channel(event: events.NewMessage):
    try:
        # Telethon event.pattern_match.string is the full matched string
        # event.pattern_match.group(0) is the full matched string
        # event.pattern_match.group(1) is the first captured group
        # For commands, event.text.split() gives arguments
        args = event.text.split()[1:] # Get arguments after the command

        if not args:
            await event.reply(
                "❗ **Usage:**\n"
                "`/find <channel_name> [.p1|.p2|...]`\n"
                "Example: `/find dd news .p1`",
                parse_mode="Markdown"
            )
            return

        # Combine all arguments except playlist filter
        search_parts = []
        playlist_filter = None
        
        for arg in args:
            if arg.startswith('.'):
                playlist_filter = arg[1:]  # Remove the dot
            else:
                search_parts.append(arg.lower())
                
        search_query = ' '.join(search_parts)
        
        # Search channels with exact match first
        exact_results = {}
        partial_results = {}
        
        for channel_id, info in m3u_manager.channels.items():
            if isinstance(channel_id, str) and ':' in channel_id:  # Only real channels
                # Apply playlist filter if specified
                if playlist_filter and info.get('playlist') != f"p{playlist_filter}":
                    continue
                
                # Check for exact match
                channel_name = info['name'].lower()
                channel_id_lower = info.get('original_id', '').lower()
                
                if search_query == channel_name or search_query == channel_id_lower:
                    exact_results[channel_id] = info
                elif all(term in (channel_name + ' ' + channel_id_lower) 
                         for term in search_query.split()):
                    partial_results[channel_id] = info

        # Combine results (exact matches first)
        results = {**exact_results, **partial_results}

        if not results:
            await event.reply(
                "❌ No channels found matching your search",
                parse_mode="Markdown"
            )
            return

        # Group results by playlist and paginate
        grouped_results = {}
        for channel_id, info in results.items():
            playlist_id = info['playlist']
            if playlist_id not in grouped_results:
                grouped_results[playlist_id] = []
            grouped_results[playlist_id].append(
                f"{info['name']} (ID: {info['original_id']})"
            )

        # Send results with pagination (max 10 items per message)
        for playlist_id, channels in grouped_results.items():
            header = f"📡 **Playlist {playlist_id.upper()}** ({len(channels)} results)\n"
            message = header
            
            for i, channel in enumerate(channels, 1):
                if i % 10 == 0:  # Send every 10 channels
                    await event.client.send_message(
                        entity=event.chat_id,
                        message=message,
                        parse_mode="Markdown"
                    )
                    message = header
                message += f"{channel}\n"
            
            if message != header:  # Send remaining channels
                await event.client.send_message(
                    entity=event.chat_id,
                    message=message,
                    parse_mode="Markdown"
                )

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        await send_long_message(event.client, event.chat_id, error_msg, parse_mode="Markdown")


async def show_help(event: events.NewMessage):
    help_text = (
        "📝 **Usage:**\n\n"
        "• By URL:\n`/rec http://example.com/stream 30 channel title`\n"
        "• By Channel ID:\n`/rec 123 00:01:00 channel title`\n"
        "• By Channel Name:\n`/rec sony 1:00:00 channel title`\n\n"
        "⏱ **Duration formats:**\n"
        "`30` (seconds)\n`1:30` (minutes:seconds)\n`1:00:00` (hours:minutes:seconds)\n\n"
        "🔍 Search channels with `/find name`"
    )
    await event.reply(help_text, parse_mode="Markdown")

