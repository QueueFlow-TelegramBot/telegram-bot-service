from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from services.user_client import get_cached_user
from logger import get_logger

log = get_logger(__name__)

ROLE_HIERARCHY = {"admin": 3, "secretary": 2, "student": 1}


def require_role(*allowed_roles: str):
    """Decorator that checks if the user has one of the allowed roles."""

    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            telegram_id = update.effective_user.id
            user = get_cached_user(telegram_id)

            if not user:
                await update.message.reply_text(
                    "Please use /start first to register."
                )
                log.warning("Unregistered user attempted action", extra={"telegram_id": telegram_id})
                return

            user_role = user.get("role", "student")
            # Admin can do everything
            if user_role == "admin" or user_role in allowed_roles:
                return await func(update, context)

            await update.message.reply_text(
                f"Access denied. This command requires one of: {', '.join(allowed_roles)}"
            )
            log.warning(
                "Access denied",
                extra={"telegram_id": telegram_id, "role": user_role, "required": allowed_roles},
            )

        return wrapper

    return decorator
