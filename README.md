# SuperGuard Bot

A secure, multi-group Telegram anti-spam and moderation bot built with Python.

## Features
- **Anti-Spam:** Detects and deletes messages containing blocked words or domains.
- **Anti-Flood:** Restricts users sending too many messages in a short timeframe.
- **Automated Moderation:** Warns, mutes, or bans users based on configurable thresholds.
- **Admin Protection:** Automatically ignores administrators to prevent accidental moderation.
- **Multi-Group Support:** Independent settings for every group the bot is added to.
- **Secure:** Uses SQLite for local storage, environment variables for secrets, and parameterized queries.

## Setup & Deployment

1. **Clone and Install:**
```bash
   git clone <your-repo-url>
   cd superguard-bot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and add your bot token from [@BotFather](https://t.me/BotFather).
```bash
   cp .env.example .env
   nano .env
```

3. **Telegram Bot Settings:**
   - Open [@BotFather](https://t.me/BotFather).
   - Send `/mybots`, select your bot, go to **Bot Settings** -> **Group Privacy** -> **Turn off**.
   - Add the bot to your group and promote it to **Admin** with rights to *Delete messages*, *Ban users*, and *Restrict users*.

4. **Run the Bot:**
```bash
   python bot.py
```

## Running Tests
```bash
pytest tests/
```
