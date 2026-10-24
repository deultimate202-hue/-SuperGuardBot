# Community Assistant Bot

A secure, multi-group Telegram community management and content filtering bot built with Python.

## Overview
This is a defensive, administrative moderation tool designed to protect Telegram groups from abuse and maintain community guidelines.

## Features
- **Content Filtering:** Detects and removes messages containing filtered terms or domains.
- **Rate Limiting:** Restricts users sending too many messages in a short timeframe.
- **Automated Notifications:** Notifies, restricts, or limits users based on configurable thresholds.
- **Admin Protection:** Automatically ignores administrators to prevent accidental restrictions.
- **Multi-Group Support:** Independent settings for every group the bot is added to.
- **Secure:** Uses SQLite for local storage, environment variables for secrets, and parameterized queries.

## Setup & Deployment

1. **Install Dependencies:**
```bash
   pip install -r requirements.txt
```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and add your bot token from [@BotFather](https://t.me/BotFather).
```bash
   cp .env.example .env
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
