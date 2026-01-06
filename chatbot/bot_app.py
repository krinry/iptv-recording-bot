import sqlite3
import asyncio
from telethon import events
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row  # Dictionary format mein results
    return conn

# Start command handler
async def start(event: events.NewMessage):
    user = await event.get_sender()
    await event.reply(f"""
Namaste {user.first_name}! 🙏
Main ek sample bot hoon jo SQLite database se data fetch karta hoon.

Aap yeh poochh sakte hain:
• /products - Saare products dikhane ke liye
• /faqs - Common FAQs ke liye
• "iPhone ka price batao" - Specific product ke liye
""")

# Products command handler
async def products(event: events.NewMessage):
    conn = get_db_connection()
    products_data = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    
    response = "🛍️ Available Products:\n\n"
    for item in products_data:
        response += f"• {item['name']}\nPrice: ₹{item['price']}\nStock: {item['stock']} units\n\n"
    
    await event.reply(response)

# FAQs command handler
async def faqs(event: events.NewMessage):
    conn = get_db_connection()
    faqs_data = conn.execute('SELECT * FROM faqs').fetchall()
    conn.close()
    
    response = "❓ Frequently Asked Questions:\n\n"
    for item in faqs_data:
        response += f"Q: {item['question']}\nA: {item['answer']}\n\n"
    
    await event.reply(response)

# Message handler for dynamic queries
async def handle_message(event: events.NewMessage):
    user_input = event.text.lower()
    conn = get_db_connection()
    
    # Price check logic
    if 'price' in user_input:
        product_name = None
        if 'iphone' in user_input:
            product_name = 'iPhone 15'
        elif 'samsung' in user_input:
            product_name = 'Samsung S23'
        elif 'oneplus' in user_input:
            product_name = 'OnePlus 11'
            
        if product_name:
            product = conn.execute('SELECT * FROM products WHERE name LIKE ?', 
                                 (f'%{product_name}%',)).fetchone()
            if product:
                await event.reply(f"{product['name']} ka price hai ₹{product['price']}")
            else:
                await event.reply("Sorry, yeh product available nahi hai")
        else:
            await event.reply("Kripya product ka sahi naam likhein")
    
    # FAQ logic
    elif 'delivery' in user_input:
        faq = conn.execute("SELECT answer FROM faqs WHERE question LIKE '%Delivery%'").fetchone()
        await event.reply(f"Delivery ke bare mein: {faq['answer']}")
    
    else:
        await event.reply("Mujhe samajh nahi aaya, kripya /help dekhein")
    
    conn.close()

# Main function
async def main():
    print("Starting bot...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start(bot_token=BOT_TOKEN)
    
    # Command handlers
    client.add_event_handler(start, events.NewMessage(pattern='/start'))
    client.add_event_handler(products, events.NewMessage(pattern='/products'))
    client.add_event_handler(faqs, events.NewMessage(pattern='/faqs'))
    
    # Message handler
    client.add_event_handler(handle_message, events.NewMessage(func=lambda e: e.text and not e.text.startswith('/')))
    
    print("Polling...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
