from telegram import Update
from telegram.ext import ContextTypes
from services.user_client import get_cached_user, user_cache
from logger import get_logger

log = get_logger(__name__)

VALID_ROLES = ("student", "secretary", "admin")


async def set_role_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /set_role [role] — debug command to change role (mock mode only)."""
    telegram_id = update.effective_user.id
    user = get_cached_user(telegram_id)

    if not user:
        await update.message.reply_text("Please use /start first to register.")
        return

    if not context.args:
        await update.message.reply_text(
            f"Usage: /set_role [role]\nValid roles: {', '.join(VALID_ROLES)}\n"
            f"Your current role: {user.get('role')}"
        )
        return

    new_role = context.args[0].lower()
    if new_role not in VALID_ROLES:
        await update.message.reply_text(
            f"Invalid role. Valid roles: {', '.join(VALID_ROLES)}"
        )
        return

    user_cache[telegram_id]["role"] = new_role
    log.info("Role changed (debug)", extra={"telegram_id": telegram_id, "new_role": new_role})
    await update.message.reply_text(f"Role changed to: {new_role}")
