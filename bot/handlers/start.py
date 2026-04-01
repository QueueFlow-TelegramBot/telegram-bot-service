from telegram import Update
from telegram.ext import ContextTypes
from services.user_client import create_user, get_user_by_telegram_id
from logger import get_logger

log = get_logger(__name__)

HELP_MSG = (
        "Available commands:\n\n"
        "/join_queue [room_id] — Join a queue\n"
        # "/status — Check your position in the queue\n"
        # "/cancel — Leave the current queue\n"
        "/create_room [name] — Create a new queue room\n"
        # "/get_rooms — List your active rooms\n"
        "/next [room_id] — Call next person in queue\n"
        "/get_rooms — List your active rooms\n"
    )

WELCOME_MSG = (
    "Welcome to QueueFlow!\n\n"
    f"{HELP_MSG}"
)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start — register user and show welcome."""
    telegram_id = update.effective_user.id
    display_name = update.effective_user.full_name or "User"

    log.info("start command received", extra={"telegram_id": telegram_id})

    # First check if user is already registered (e.g. from cache), to avoid unnecessary API call
    data = await get_user_by_telegram_id(telegram_id)
    if not data:
        try:
            data = await create_user(telegram_id, display_name)
        except Exception as e:
            log.error("Failed to create user", extra={"error": str(e)})
            await update.message.reply_text(
                "Sorry, registration failed. Please try again later."
            )
            return

    await update.message.reply_text(WELCOME_MSG)
    log.info("User registered", extra={"telegram_id": telegram_id})


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help — show commands based on role."""
    await update.message.reply_text(HELP_MSG)
