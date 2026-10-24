import time
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from database import get_settings, update_settings, get_user_state, update_user_state
from moderation import check_flood, check_spam

logger = logging.getLogger(__name__)

async def is_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except TelegramError:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("SuperGuard Bot is active. Use /help to see commands.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "*SuperGuard Bot Commands:*\n"
        "/settings - View current group settings\n"
        "/addword `<word>` - Add a blocked word\n"
        "/removeword `<word>` - Remove a blocked word\n"
        "/adddomain `<domain>` - Add a blocked domain\n"
        "/removedomain `<domain>` - Remove a blocked domain\n"
        "/warn `<reply>` - Warn a user\n"
        "/mute `<reply>` - Mute a user\n"
        "/ban `<reply>` - Ban a user\n"
        "Admins are automatically protected from moderation.",
        parse_mode="Markdown"
    )
    await update.message.reply_text(help_text)

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        await update.message.reply_text("Only admins can view settings.")
        return
        
    settings = get_settings(update.effective_chat.id)
    msg = (
        f"*Group Settings:*\n"
        f"Anti-Spam: {'Enabled' if settings['anti_spam'] else 'Disabled'}\n"
        f"Anti-Flood: {'Enabled' if settings['anti_flood'] else 'Disabled'}\n"
        f"Blocked Words: {', '.join(settings['blocked_words']) or 'None'}\n"
        f"Blocked Domains: {', '.join(settings['blocked_domains']) or 'None'}\n"
        f"Warn Limit: {settings['warn_limit']}\n"
        f"Mute Duration: {settings['mute_duration']} mins"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return await update.message.reply_text("Admins only.")
    if not context.args:
        return await update.message.reply_text("Usage: /addword <word>")
        
    word = context.args[0].strip().lower()
    settings = get_settings(update.effective_chat.id)
    if word not in settings["blocked_words"]:
        settings["blocked_words"].append(word)
        update_settings(update.effective_chat.id, "blocked_words", settings["blocked_words"])
        await update.message.reply_text(f"Added `{word}` to blocked words.", parse_mode="Markdown")
    else:
        await update.message.reply_text("Word already blocked.")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_user:
        return
        
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.effective_message.text
    
    # Protect admins
    if await is_admin(context.bot, chat_id, user_id):
        return
        
    settings = get_settings(chat_id)
    state = get_user_state(chat_id, user_id)
    
    # Check if currently muted
    if state["muted_until"] > time.time():
        try:
            await update.effective_message.delete()
        except TelegramError:
            pass
        return

    # Check Spam
    if check_spam(text, settings):
        try:
            await update.effective_message.delete()
            await warn_user(context.bot, chat_id, user_id, settings, reason="Spam (Blocked word/domain)")
        except TelegramError as e:
            logger.error(f"Failed to delete spam: {e}")
        return

    # Check Flood
    is_flooding, count = check_flood(chat_id, user_id, settings)
    if is_flooding:
        try:
            await update.effective_message.delete()
            await mute_user(context.bot, chat_id, user_id, settings, reason=f"Flooding ({count} messages)")
        except TelegramError as e:
            logger.error(f"Failed to handle flood: {e}")

async def warn_user(bot, chat_id, user_id, settings, reason="Violation"):
    state = get_user_state(chat_id, user_id)
    state["warnings"] += 1
    
    if state["warnings"] >= settings["warn_limit"]:
        await mute_user(bot, chat_id, user_id, settings, reason=f"Reached {settings['warn_limit']} warnings")
        state["warnings"] = 0
    else:
        try:
            await bot.send_message(chat_id, f"User {user_id} warned ({state['warnings']}/{settings['warn_limit']}). Reason: {reason}")
        except TelegramError:
            pass
    update_user_state(chat_id, user_id, state)

async def mute_user(bot, chat_id, user_id, settings, reason="Violation"):
    state = get_user_state(chat_id, user_id)
    state["muted_until"] = int(time.time()) + (settings["mute_duration"] * 60)
    update_user_state(chat_id, user_id, state)
    
    try:
        await bot.restrict_chat_member(
            chat_id, user_id, 
            ChatPermissions(can_send_messages=False),
            until_date=state["muted_until"]
        )
        await bot.send_message(chat_id, f"User {user_id} muted for {settings['mute_duration']} mins. Reason: {reason}")
    except TelegramError as e:
        logger.error(f"Failed to mute user: {e}")
