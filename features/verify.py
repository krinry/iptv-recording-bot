import requests
import secrets
from datetime import datetime, timedelta
from telethon import events
from telethon.tl.custom import Button
from config import (
    VERIFICATION_LINKS,
    VERIFICATION_BASE_URL,
    BOT_NAME,
    VERIFICATION_REWARD_MINUTES
)

async def verify_command(event: events.NewMessage):
    """Send verification link to user"""
    user_id = event.sender_id
    chat_id = event.chat_id
    
    # Generate unique token
    token = secrets.token_urlsafe(16)
    verification_url = f"https://t.me/{BOT_NAME}?start=verify_{token}"
    
    # Shorten with VPLinks
    try:
        response = requests.get(f"{VERIFICATION_BASE_URL}{verification_url}")
        if response.status_code == 200:
            short_url = response.json().get('shortenedUrl', verification_url)
        else:
            short_url = verification_url
    except Exception:
        short_url = verification_url
    
    # Store verification token
    VERIFICATION_LINKS[token] = {
        'user_id': user_id,
        'chat_id': chat_id,
        'created_at': datetime.now(),
        'used': False
    }
    
    # Send message with button
    keyboard = [
        [Button.url("🔗 Verify Now", short_url)],
        [Button.inline("✅ I've Verified", data=f"verify_check_{token}".encode())]
    ]
    
    await event.reply(
        f"To verify and get {VERIFICATION_REWARD_MINUTES} minutes recording access:\n\n"
        "1. Click the button below\n"
        "2. Complete the verification\n"
        "3. Click 'I've Verified'\n\n"
        "Note: This link expires in 10 minutes",
        buttons=keyboard
    )

async def verify_callback(event: events.CallbackQuery):
    """Handle verification callback"""
    await event.answer()
    
    callback_data = event.data.decode('utf-8')
    if callback_data.startswith('verify_check_'):
        token = callback_data.split('_')[-1]
        verification = VERIFICATION_LINKS.get(token)
        
        if not verification:
            await event.edit("❌ Invalid or expired verification link")
            return
            
        if verification['used']:
            await event.edit("⚠️ This link has already been used")
            return
            
        # Mark as used
        VERIFICATION_LINKS[token]['used'] = True
        
        # Add recording time to user's account (you'll need to implement this)
        user_id = verification['user_id']
        expiry_time = datetime.now() + timedelta(minutes=VERIFICATION_REWARD_MINUTES)
        
        # Store verification in your user database
        # Implement your own user time tracking system here
        # Example: user_db[user_id]['recording_expiry'] = expiry_time
        
        await event.edit(
            f"✅ Verification successful!\n\n"
            f"You can now record for {VERIFICATION_REWARD_MINUTES} minutes "
            f"(until {expiry_time.strftime('%H:%M')})"
        )
