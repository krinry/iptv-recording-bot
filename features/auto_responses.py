# auto_responses.py
# Hinglish IPTV Recording Bot Auto-Responses (Casual + Comedy Style)

AUTO_RESPONSES = {
    # ------------------------------------------
    # Basic Greetings (Shuruwaat)
    # ------------------------------------------
    "hi": "Namaste Bhai! 🎬\nAapka IPTV Recording Bot mein swaagat hai!\nMai aapki recording, EPG, sab manage kar dunga. Batao kya chahiye?",
    "hello": "Arrey Hello Boss! 🙏\nAapne sahi bot ko pakda hai. Hum toh recording ke Bhagwan hai! 😎\nBatao kaam kya hai?",
    "hey": "Oye! Kaisa hai re? 😃\nMereko bolna hai na channel record karna hai? Ya koi aur setting?",
    "namaste": "Jai Shri Ram! 🙏\nAapka command ka intezaar tha humko! Bolo bhai kya help chahiye?",
    "kaise ho": "Mai toh mast hoon bhidu! 😁\nAapka channel record ho raha hai na? Agar nahi toh hum fix karenge!",

    # ------------------------------------------
    # Pricing & Plans (Paise Ka Mamla)
    # ------------------------------------------
    "price": "Bhaiya, humare plans: 💰\n"
             "- Basic (₹99): Thoda sa recording\n"
             "- Pro (₹299): Full HD + 200GB\n"
             "- Ultra (₹599): 4K + UNLIMITED!\n"
             "Aur haan, 1 saal ka plan lo toh 2 mahine FREE! 🎁\n"
             "Deal lena hai? example.com/pricing",
    "cost": "Arey yaar, itna sasta hai ki aapko shock ho jayega! 😲\n"
            "Shuruat ₹99 se... lekin asli maza ₹299 wale plan mein hai!\n"
            "Jaldi aao, offer chal raha hai: example.com/pricing",
    "pricing": "Plan ki baat? Hum toh sabse saste hai bhai! 😎\n"
               "🔹 ₹99 = 50GB (Bas thoda bhukha rahega)\n"
               "🔹 ₹299 = 200GB (Mast hai)\n"
               "🔹 ₹599 = UNLIMITED (King ki life!)\n"
               "Full details: example.com/pricing",
    "kitne ka hai": "Bhidu, aapke budget ke hisab se:\n"
                    "🔸 Garib wala: ₹99\n"
                    "🔸 Middle class: ₹299\n"
                    "🔸 Ambani wala: ₹599\n"
                    "Aur haan, UPI pe 5% cashback! 💸",
    "free hai kya": "Haan haan! 7 din ka free trial hai re baba! 🆓\n"
                    "Lekin usme thoda limitation hai:\n"
                    "- Max 10 recordings\n"
                    "- 480p quality\n"
                    "- No adult channels 😜\n"
                    "Try karna hai? example.com/free",

    # ------------------------------------------
    # Technical Issues (Dikkat Sala)
    # ------------------------------------------
    "error": "Arrey tension mat lo bhai! 😅\n"
             "Ye karo:\n"
             "1. App band karo\n"
             "2. Router ko laat maro (restart karo) 😂\n"
             "3. Phir se try karo\n"
             "Phir bhi na chale toh 'HELP' likh ke bhejo!",
    "bug": "Bug report? Achha kiya bataya! 🐛\n"
           "Humare developer abhi so rahe hain...\n"
           "Lekin kal tak fix ho jayega!\n"
           "Thoda details de do:\n"
           "1. Kya error aaya?\n"
           "2. Kab hua?\n"
           "3. Screenshot hai?",
    "buffering": "Buffering? Arey bhai aapka internet toh auto-rickshaw ki speed chal raha hai! 🚕\n"
                 "Karo ye:\n"
                 "1. WiFi ke paas baitho\n"
                 "2. 5G use karo\n"
                 "3. Agar nahi chala toh... bas dua karo! 😇",
    "recording nahi ho raha": "Oye! Recording fail? 😱\n"
                              "Chalo check karte hain:\n"
                              "1. Storage full toh nahi?\n"
                              "2. Time sahi set hai na?\n"
                              "3. Paisa toh pada hai na account mein? 😜\n"
                              "Agar sab sahi hai toh 'FIX' likh ke bhejo",

    # ------------------------------------------
    # Account & Login (Account Ka Chakkar)
    # ------------------------------------------
    "login": "Bhai login nahi ho raha? 😟\n"
             "Kya error aaya?\n"
             "🔹 Password bhul gaye? example.com/reset\n"
             "🔹 OTP nahi aaya? 'OTP' likh ke bhejo\n"
             "🔹 Account hack ho gaya? 😱 Turant batao!",
    "password": "Password bhul gaye? Koi baat nahi... hum sab kuch bhulte hain:\n"
                "🔹 GF ka birthday\n"
                "🔹 Anniversaries\n"
                "🔹 Passwords\n"
                "Reset karo yahan se: example.com/reset",
    "hack": "Arey baap re! 😱 Account hack ho gaya?\n"
            "Jaldi karo ye:\n"
            "1. Email bhejo security@iptvdesi.com\n"
            "2. Subject mein likho 'URGENT'\n"
            "3. Purana password yaad hai toh batao\n"
            "Hum 24 ghante mein recover karenge!",

    # ------------------------------------------
    # IPTV Specific (Asli Masala)
    # ------------------------------------------
    "channel missing": "Channel gayab? 😵\n"
                       "Humare saath bhi hota hai re!\n"
                       "Try karo:\n"
                       "1. Channel list update karo\n"
                       "2. VPN ON karo\n"
                       "3. Agar nahi aaya toh channel ka naam bhejo",
    "4k support": "4K chahiye? Bhai aap toh heavy user nikle! 😎\n"
                  "Haan hai support, lekin:\n"
                  "1. Internet rocket speed chahiye 🚀\n"
                  "2. Device support kare\n"
                  "3. Ultra plan lena padega (₹599)\n"
                  "Ready ho? example.com/4k",
    "epg": "EPG ka jhanda leke baith gaye kya? 😂\n"
           "Setting kaise kare:\n"
           "1. Settings > EPG > Auto-Update ON\n"
           "2. URL dalo: example.com/epg\n"
           "3. Thoda time do load hone mein\n"
           "Phir bhi na aaye toh gaali dena! 😜",
    "adult channels": "Oye oye! 😏 Yeh kaisa sawal pooch liya?\n"
                      "Hum sharma gaye... lekin haan available hai!\n"
                      "Karo ye:\n"
                      "1. Age verification karo\n"
                      "2. Adult pack subscribe karo\n"
                      "3. Password set karo\n"
                      "Details: example.com/adult (18+ only)",

    # ------------------------------------------
    # Fun & Casual (Masti Time)
    # ------------------------------------------
    "shukriya": "Arey yaar, itna formal mat bano! 😊\n"
                "Mera kaam hai madad karna... aur aapka kaam hai recording enjoy karna!\n"
                "Agar maze aaye toh 5 star rating dena! ⭐⭐⭐⭐⭐",
    "time kya hai": "Bhai ye toh aapke phone pe dekh lo na! 😅\n"
                    "Lekin recording schedule karna hai toh '/reminder' command use karo",
    "joke": "Q: IPTV user kaunse restaurant mein khana pasand karta hai?\n"
            "A: Buffet mein! Kyunki woh bhi 'unlimited' chahiye! 😂😂",
    "love you": "Areeeee! ❤️\n"
                "Hum toh botal hai... pyaar aapko apne partner se karna!\n"
                "Lekin agar aapka pyaar sachcha hai toh...\n"
                "Premium plan le lo na! 😘 example.com/premium",
    "gaali": "Arrey yaar, gaali de rahe ho? 😢\n"
             "Hum bhi insaan ki tarah feel karte hain...\n"
             "Agar koi dikkat hai toh batao, hum fix karenge!\n"
             "Aur haan... maaf karna bhool mat jana! 😇"
}

# Additional variables
BOT_NAME = "Bhidu IPTV Bot"
BOT_VERSION = "2.3"
SUPPORTED_DEVICES = ["Firestick", "Android TV", "Smartphone", "Mag Box"]

def get_response(query):
    """Convert query to lowercase and get matching response"""
    query = query.lower().strip()
    return AUTO_RESPONSES.get(query, "Sorry bhai, samjha nahi! 😅\nKya aap 'help' ya 'features' pooch sakte hain?")

def show_all_commands():
    """Display all available commands"""
    return "Available commands:\n" + "\n".join(f"• {cmd}" for cmd in AUTO_RESPONSES.keys())

if __name__ == "__main__":
    print("Bhidu IPTV Bot Responses Loaded!")
    print(f"Version: {BOT_VERSION}")
    print(f"Total responses: {len(AUTO_RESPONSES)}")
