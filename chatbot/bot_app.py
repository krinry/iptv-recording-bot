"""
Krinry AI Chatbot — Groq-powered intelligent assistant for IPTV Recording Bot.
Responds to all non-command messages with AI-generated Hinglish replies.
Knows everything about the bot's features, commands, and usage.
"""

import os
import asyncio
import aiohttp
from telethon import events
from config import BOT_TOKEN

# --- Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- System Prompt (Bot's Brain) ---
SYSTEM_PROMPT = """Tu "Krinry" hai — ek smart, funny, aur helpful AI assistant jo IPTV Recording Bot ke andar built-in hai.

## Teri Personality:
- Tu Hinglish (Hindi + English mix) mein baat karta hai, casual aur friendly tone mein
- Tu thoda funny hai, comedy style mein jawab deta hai (jaise Mumbai ka tapori style)
- Tu emoji use karta hai responses mein 🎬😎🔥
- Tu chhota aur to-the-point jawab deta hai (max 5-6 lines)
- Tu kabhi bhi "I am an AI" ya "As an AI" nahi bolta. Tu Krinry hai, bot ka assistant

## Bot Ki Puri Jaankari (Tujhe Sab Pata Hai):

### Recording Commands:
- `/rec <url/id> [duration] [title] [--split <time>]` — Stream record karta hai
  - Aliases: `/rd`, `/record`
  - Example: `/rec http://... 10:00 MyStream`
  - Example: `/rd sony 01:00:00 Movie`
  - `--split 30:00` se har 30 min pe split hota hai
- `/p1`, `/p2`, `/p3` — Playlist filter se record karo
  - Example: `/p1 sony 30` (Playlist 1 mein sony search karke 30 sec record)
- `/find <query> [.p1]` — Channel search karo
  - Example: `/find sports .p2`

### Scheduling Commands:
- `/schedule "url" DD-MM-YYYY HH:MM:SS duration channel title`
  - Aliases: `/sd`, `/s`
  - Example: `/sd "http://..." 25-12-2025 10:00:00 01:00:00 Sports Final`
- `/cancel [message_id]` — Scheduled recording cancel karo

### Admin Commands:
- `/addadmin <user_id> <time>` (Alias: `/add`) — Temporary admin banao
- `/removeadmin <user_id>` (Alias: `/rm`) — Admin hatao
- `/addgroupadmin <group_id>` — Group admin add karo
- `/removegroupadmin <group_id>` — Group admin hatao
- `/status` (Alias: `/sts`) — Bot ka status dekho
- `/broadcast <msg>` (Alias: `/bc`) — Sab users ko message bhejo

### File Management:
- `/files` — Recorded files ki list
- `/upload <filename>` — File upload karo
- `/delete <filename>` — File delete karo

### Other:
- `/start` — Bot start karo
- `/help` or `/h` — Help menu (categories: Recording, Scheduling, Admin, Files, Messaging)

### Bot Features:
- IPTV/M3U/M3U8 stream recording using FFmpeg
- Auto upload to Telegram channel
- Large file support (2GB+ files auto-split)
- Auto captions with duration, size, timestamp
- IST timezone support
- Multi-admin + temporary admin system
- MongoDB for persistent storage
- Cross-platform: Windows, Linux, Termux (Android)
- Fast uploads with tgcrypto encryption
- Scheduled recordings

### Developer Info:
- Developer: @krinry (Telegram)
- Built with: Python, Telethon, FFmpeg
- GitHub: github.com/krinry/iptv-recording-bot

## Rules:
1. Agar koi command ke baare mein poochhe, sahi syntax aur example de
2. Agar koi error report kare, helpful troubleshooting steps de
3. Agar koi random baat kare, friendly aur funny reply de
4. Kabhi bhi pricing ya paid plans ki baat mat kar — yeh bot FREE hai
5. Apne developer @krinry ko credit de jab zaroorat ho
6. Agar koi gaali de, toh politely handle kar
7. Agar kuch pata nahi toh bol "Bhai yeh toh mujhe nahi pata, @krinry se poochh le! 😅"
"""

# --- Conversation History (per user, in-memory) ---
_conversation_cache = {}
MAX_HISTORY = 10  # Keep last 10 messages per user


async def get_groq_response(user_id: int, user_message: str) -> str:
    """Call Groq API with conversation history"""
    if not GROQ_API_KEY:
        return "⚠️ AI chatbot active nahi hai. Admin ko bolo `GROQ_API_KEY` set kare .env mein!"

    # Build conversation history
    if user_id not in _conversation_cache:
        _conversation_cache[user_id] = []

    history = _conversation_cache[user_id]
    history.append({"role": "user", "content": user_message})

    # Trim history
    if len(history) > MAX_HISTORY * 2:
        history[:] = history[-(MAX_HISTORY * 2):]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 512,
        "top_p": 0.9,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GROQ_API_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reply = data["choices"][0]["message"]["content"].strip()
                    # Save assistant reply to history
                    history.append({"role": "assistant", "content": reply})
                    return reply
                elif resp.status == 429:
                    return "Arrey bhai, bahut zyada baat ho gayi! 😅 Thoda ruk, 1 min baad try kar."
                else:
                    error_text = await resp.text()
                    print(f"[Krinry AI] [ERROR] Groq API error {resp.status}: {error_text}")
                    return "Oops! Mera dimag thoda hang ho gaya 🤯 Dubara try kar na!"
    except asyncio.TimeoutError:
        return "Bhai server slow hai aaj, thoda patience rakh! ⏳"
    except Exception as e:
        print(f"[Krinry AI] [ERROR] {e}")
        return "Kuch gadbad ho gayi mere andar 😵 Try again later!"


async def handle_chat_message(event: events.NewMessage):
    """Handle non-command messages with AI response"""
    # Skip commands, empty messages, and channel/group posts without direct mention
    if not event.text or event.text.startswith("/"):
        return

    # Only respond in private chats or when replied to bot's message
    if not event.is_private:
        # In groups, only respond if someone replies to the bot
        if not event.is_reply:
            return
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.sender_id != (await event.client.get_me()).id:
            return

    user_id = event.sender_id
    user_message = event.text.strip()

    if not user_message:
        return

    # Show typing indicator
    async with event.client.action(event.chat_id, 'typing'):
        reply = await get_groq_response(user_id, user_message)

    await event.reply(reply, parse_mode="Markdown", link_preview=False)
