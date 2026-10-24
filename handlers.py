import time
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from database import get_settings, update_settings, get_user_state, update_user_state
from moderation import check_message_rate, check_content_policy

logger = logging.getLogger(__name__)

async def is_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except TelegramError:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Community Assistant Bot is active. Use /help to see commands.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "*Community Assistant Commands:*\n"
        "/settings - View current group settings\n"
        "/addfilter `<term>` - Add a filtered term\n"
        "/removefilter `<term>` - Remove a filtered term\n"
        "/adddomainfilter `<domain>` - Add a filtered domain\n"
        "/removedomainfilter `<domain>` - Remove a filtered domain\n"
        "/notify `<reply>` - Issue a notification to a user\n"
        "/restrict `<reply>` - Restrict a user temporarily\n"
        "/limit `<reply>` - Apply a limit to a user\n"
        "Administrators are automatically protected.",
        parse_mode="Markdown"
    )
    await update.message.reply_text(help_text)

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        await update.message.reply_text("Only administrators can view settings.")
        return
        
    settings = get_settings(update.effective_chat.id)
    msg = (
        f"*Group Settings:*\n"
        f"Content Filter: {'Enabled' if settings['content_filter_enabled'] else 'Disabled'}\n"
        f"Rate Limit: {'Enabled' if settings['rate_limit_enabled'] else 'Disabled'}\n"
        f"Filtered Terms: {', '.join(settings['filtered_terms']) or 'None'}\n"
        f"Filtered Domains: {', '.join(settings['filtered_domains']) or 'None'}\n"
        f"Notification Limit: {settings['notify_limit']}\n"
        f"Restrict Duration: {settings['restrict_duration']} mins"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return await update.message.reply_text("Administrators only.")
    if not context.args:
        return await update.message.reply_text("Usage: /addfilter <term>")
        
    term = context.args[0].strip().lower()
    settings = get_settings(update.effective_chat.id)
    if term not in settings["filtered_terms"]:
        settings["filtered_terms"].append(term)
        update_settings(update.effective_chat.id, "filtered_terms", settings["filtered_terms"])
        await update.message.reply_text(f"Added `{term}` to filtered terms.", parse_mode="Markdown")
    else:
        await update.message.reply_text("Term already filtered.")

async def process_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_user:
        return
        
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.effective_message.text
    
    if await is_admin(context.bot, chat_id, user_id):
        return
        
    settings = get_settings(chat_id)
    state = get_user_state(chat_id, user_id)
    
    if state["restricted_until"] > time.time():
        try:
            await update.effective_message.delete()
        except TelegramError:
            pass
        return

    if check_content_policy(text, settings):
        try:
            await update.effective_message.delete()
            await notify_user(context.bot, chat_id, user_id, settings, reason="Content Policy Violation")
        except TelegramError as e:
            logger.error(f"Failed to handle content policy: {e}")
        return

    is_rate_limited, count = check_message_rate(chat_id, user_id, settings)
    if is_rate_limited:
        try:
            await update.effective_message.delete()
            await restrict_user(context.bot, chat_id, user_id, settings, reason=f"Rapid Messaging ({count} messages)")
        except TelegramError as e:
            logger.error(f"Failed to handle rate limit: {e}")

async def notify_user(bot, chat_id, user_id, settings, reason="Guideline Violation"):
    state = get_user_state(chat_id, user_id)
    state["notifications"] += 1
    
    if state["notifications"] >= settings["notify_limit"]:
        await restrict_user(bot, chat_id, user_id, settings, reason=f"Reached {settings['notify_limit']} notifications")
        state["notifications"] = 0
    else:
        try:
            await bot.send_message(chat_id, f"User {user_id} notified ({state['notifications']}/{settings['notify_limit']}). Reason: {reason}")
        except TelegramError:
            pass
    update_user_state(chat_id, user_id, state)

async def restrict_user(bot, chat_id, user_id, settings, reason="Guideline Violation"):
    state = get_user_state(chat_id, user_id)
    state["restricted_until"] = int(time.time()) + (settings["restrict_duration"] * 60)
    update_user_state(chat_id, user_id, state)
    
    try:
        await bot.restrict_chat_member(
            chat_id, user_id, 
            ChatPermissions(can_send_messages=False),
            until_date=state["restricted_until"]
        )
        await bot.send_message(chat_id, f"User {user_id} restricted for {settings['restrict_duration']} mins. Reason: {reason}")
    except TelegramError as e:
        logger.error(f"Failed to restrict user: {e}")
