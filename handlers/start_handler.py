import random
from telethon import events
from telethon.tl.custom import Button

async def start(event: events.NewMessage):
    user = await event.get_sender()
    
    keyboard = [
        [Button.url("Help / Contact Developer", "https://t.me/krinry")],
        [Button.inline("Request Admin Access", b"request_admin")]
    ]
    
    welcome_text = f"**Welcome {user.first_name}**\n\nThis bot helps you record IPTV with ease."
    
    try:
        # Try random images first
        image_files = [f'assets/recording{i}.jpg' for i in range(1, 11)]  # recording1.jpg to recording10.jpg
        random.shuffle(image_files)
        sent = False
        
        for image_file in image_files:
            try:
                # Telethon's event.reply can send files directly
                await event.reply(
                    file=image_file,
                    message=welcome_text,
                    buttons=keyboard
                )
                sent = True
                break
            except FileNotFoundError:
                continue
            except Exception as photo_error:
                print(f"Error sending photo {image_file}: {photo_error}")
                continue
        
        # Fallback to text if no images worked
        if not sent:
            await event.reply(
                message=welcome_text,
                buttons=keyboard
            )
                
    except Exception as e:
        print(f"Error in start handler: {e}")
        # Final fallback
        await event.reply(
            message=welcome_text,
            buttons=keyboard
        )
