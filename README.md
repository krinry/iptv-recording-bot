# 🎥 IPTV Recording Bot

A powerful Telegram bot for recording IPTV/M3U8 streams and uploading them directly to Telegram channels. Built with **Telethon** and **FFmpeg**.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-0088cc?logo=telegram&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-green?logo=ffmpeg&logoColor=white)
![License](https://img.shields.io/badge/License-GPLv3-blue)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎬 **IPTV Recording** | Record live streams from M3U/M3U8 playlists using FFmpeg |
| 📤 **Auto Upload** | Automatically upload recorded videos to Telegram channels |
| ⏱️ **Scheduled Recording** | Schedule recordings for specific times |
| 🔄 **Large File Support** | Split and upload files larger than 2GB |
| 📝 **Auto Captions** | Generate captions with duration, size, and timestamp |
| 🕐 **IST Timezone** | Indian Standard Time support |
| 👥 **Multi-Admin** | Support for multiple admins and temporary admin access |
| 📊 **Logging** | Detailed logging to dedicated log channels |
| 🗃️ **MongoDB** | Persistent storage for settings and state |
| 🐧 **Cross-Platform** | Optimized for Windows, Linux, and Android (Termux) |
| 🚀 **High Performance** | Fast uploads with `tgcrypto` and smart connection pooling |

---

## 📁 Project Structure

```
iptv-recording-bot/
├── main.py              # Bot entry point
├── config.py            # Configuration loader
├── handler.py           # Handler registration
├── recorder.py          # FFmpeg recording logic
├── uploader.py          # Telegram upload manager
├── scheduler.py         # Recording scheduler
├── m3u_manager.py       # M3U playlist parser
├── captions.py          # Caption generator
├── handlers/            # Command handlers
│   ├── start_handler.py
│   ├── help_handler.py
│   ├── record_handler.py
│   ├── cancel_handler.py
│   ├── schedule_handler.py
│   ├── admin_handler.py
│   └── ...
├── utils/               # Utility functions
├── features/            # Additional features
├── chatbot/             # Chatbot integration
└── assets/              # Bot assets
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- FFmpeg installed and accessible in PATH
- MongoDB database
- Telegram Bot Token & API credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/krinry/iptv-recording-bot.git
   cd iptv-recording-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your credentials (see [Configuration](#-configuration))

4. **Generate session string**
   ```bash
   python generate_session.py
   ```

5. **Run the bot**
   ```bash
   python main.py
   ```

---

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Telegram Bot Configuration
ADMIN_ID=your_admin_telegram_id
BOT_TOKEN=your_bot_token_from_botfather

# Telegram API Credentials (get from my.telegram.org)
API_ID=your_api_id
API_HASH=your_api_hash

# Session Configuration
SESSION_NAME=session_iptv
SESSION_STRING=your_session_string_here

# Channel IDs
CHANNEL_ID=-100xxxxxxxxxx
LOG_CHANNEL=-100xxxxxxxxxx
STORE_CHANNEL_ID=-100xxxxxxxxxx

# Recordings Directory
RECORDINGS_DIR=recordings

# MongoDB Connection
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

> 💡 **Tip:** Get `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org)

---

## 📱 Bot Commands
| Command | Description | Usage |
|---------|-------------|-------|
| **Recording** | | |
| `/rec` | Start recording | `/rec <url> [time] [title]` |
| `/rd` | Alias for /rec | `/rd <url>` |
| `/p1`, `/p2`... | Record from playlist | `/p1 <channel_name>` |
| `/find` | Search channels | `/find <query> [.p1]` |
| `/cancel` | Cancel recording | Reply to recording message |
| **Scheduling** | | |
| `/schedule` | Schedule recording | `/sd "url" DD-MM-YYYY HH:MM:SS duration title` |
| `/s`, `/sd` | Alias for /schedule | |
| **Admin** | | |
| `/addadmin` | Add temp admin | `/addadmin <id> HH:MM:SS` |
| `/removeadmin` | Remove admin | `/rm <id>` |
| `/addgroupadmin` | Add group admin | `/addgroupadmin <group_id>` |
| `/status` | Check resources | `/sts` |
| `/broadcast` | Broadcast msg | `/bc <message>` |
| **Files** | | |
| `/files` | List recordings | `/files` |
| `/upload` | Upload file | `/upload <filename>` |
| `/delete` | Delete file | `/delete <filename>` |

## 🐧 Termux Installation

For running on Android using Termux:

```bash
# Update packages
pkg update -y && pkg upgrade -y

# Install required packages
pkg install -y python clang ffmpeg git libffi

# Clone and setup
git clone https://github.com/krinry/iptv-recording-bot.git
cd iptv-recording-bot
pip install -r requirements.txt

# Configure and run
cp .env.example .env
# Edit .env with your credentials
python main.py
```

---

## 🐳 Docker (Optional)

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

```bash
docker build -t iptv-bot .
docker run -d --env-file .env iptv-bot
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `telethon` | Telegram MTProto client |
| `tgcrypto` | Fast encryption for Telegram |
| `ffmpeg-python` | FFmpeg wrapper for recording |
| `python-dotenv` | Environment variable management |
| `apscheduler` | Task scheduling |
| `pymongo` / `motor` | MongoDB driver |
| `aiohttp` / `aiofiles` | Async HTTP and file operations |
| `pytz` | Timezone handling |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This bot is intended for personal use only. Please ensure you have the right to record and distribute any content. The developers are not responsible for any misuse of this software.

---

## 📞 Support

If you encounter any issues or have questions, please open an [issue](https://github.com/krinry/iptv-recording-bot/issues).

---

<p align="center">Made with ❤️ by <a href="https://github.com/krinry">Krishnanamdev</a></p>
