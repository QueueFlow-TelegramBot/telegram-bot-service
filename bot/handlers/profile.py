from telegram import Update
from telegram.ext import ContextTypes, filters
from services.user_client import get_cached_user, update_display_name, user_cache
from logger import get_logger

log = get_logger(__name__)

CHANGE_PREFIX = "Change Display Name "


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Change Display Name [new_name]' text message."""
    text = update.message.text or ""

    if not text.startswith(CHANGE_PREFIX):
        return

    telegram_id = update.effective_user.id
    user = get_cached_user(telegram_id)

    if not user:
        await update.message.reply_text("Please use /start first to register.")
        return

    new_name = text[len(CHANGE_PREFIX):].strip()
    if not new_name:
        await update.message.reply_text("Please provide a new display name.")
        return

    log.info("display name update", extra={"telegram_id": telegram_id, "new_name": new_name})

    try:
        success = await update_display_name(user["user_id"], new_name)
    except Exception as e:
        log.error("Failed to update display name", extra={"error": str(e)})
        await update.message.reply_text("Could not update display name. Please try again later.")
        return

    if success:
        user_cache[telegram_id]["display_name"] = new_name
        await update.message.reply_text(f"Display name updated to {new_name}.")
    else:
        await update.message.reply_text("Failed to update display name.")
