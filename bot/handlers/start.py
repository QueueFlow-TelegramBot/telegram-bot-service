from telegram import Update
from telegram.ext import ContextTypes
from services.user_client import create_user, get_user_by_telegram_id
from logger import get_logger

log = get_logger(__name__)

WELCOME_MSG = (
    "Welcome to QueueFlow!\n\n"
    "Available commands:\n"
    "/help — Show commands for your role\n"
    "/join_queue [room_id] — Join a queue\n"
    "/status — Check your position\n"
    "/cancel — Leave the queue\n"
)

SECRETARY_COMMANDS = (
    "\nSecretary commands:\n"
    "/create_room [name] — Create a queue room\n"
    "/get_rooms — List your rooms\n"
    "/next [room_id] — Call next person\n"
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

    role = data.get("role", "student")
    msg = WELCOME_MSG
    if role in ("secretary", "admin"):
        msg += SECRETARY_COMMANDS
    if role == "admin":
        msg += "\nYou have admin privileges."

    await update.message.reply_text(msg)
    log.info("User registered", extra={"telegram_id": telegram_id, "role": role})


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help — show commands based on role."""
    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("Please use /start first to register.")
        return

    role = user.get("role", "student")
    msg = (
        "Available commands:\n\n"
        "/join_queue [room_id] — Join a queue\n"
        "/status — Check your position in the queue\n"
        "/cancel — Leave the current queue\n"
    )
    if role in ("secretary", "admin"):
        msg += (
            "\nSecretary commands:\n"
            "/create_room [name] — Create a new queue room\n"
            "/get_rooms — List your active rooms\n"
            "/next [room_id] — Call next person in queue\n"
        )
    if role == "admin":
        msg += "\nAdmin: You have full access to all commands."

    await update.message.reply_text(msg)
