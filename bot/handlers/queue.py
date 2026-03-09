from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware.auth import require_role
from services.user_client import get_cached_user
from services.scheduling_client import join_room
from logger import get_logger

log = get_logger(__name__)

# In-memory tracking: telegram_id -> {room_id, position}
active_queues: dict[int, dict] = {}


@require_role("student", "secretary", "admin")
async def join_queue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /join_queue [room_id]."""
    telegram_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Usage: /join_queue [room_id]")
        return

    room_id = context.args[0]
    user = get_cached_user(telegram_id)
    user_id = user["user_id"]

    log.info("join_queue command", extra={"telegram_id": telegram_id, "room_id": room_id})

    try:
        data = await join_room(room_id, user_id)
    except Exception as e:
        log.error("Failed to join room", extra={"error": str(e)})
        await update.message.reply_text(
            "Could not join the queue. Please check the room ID and try again."
        )
        return

    position = data.get("no_of_people_in_front", 0)
    room_name = data.get("room_name", room_id)
    active_queues[telegram_id] = {"room_id": room_id, "position": position}

    await update.message.reply_text(
        f"You are #{position + 1} in queue for {room_name}.\n"
        f"We'll notify you when it's your turn!"
    )


@require_role("student", "secretary", "admin")
async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status — show current queue position."""
    telegram_id = update.effective_user.id

    queue_info = active_queues.get(telegram_id)
    if not queue_info:
        await update.message.reply_text("You are not in any queue.")
        return

    await update.message.reply_text(
        f"You are in queue for room {queue_info['room_id']}.\n"
        f"Position: #{queue_info['position'] + 1}"
    )


@require_role("student", "secretary", "admin")
async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel — leave the current queue."""
    telegram_id = update.effective_user.id

    if telegram_id not in active_queues:
        await update.message.reply_text("You are not in any queue.")
        return

    room_id = active_queues.pop(telegram_id)["room_id"]
    log.info("User left queue", extra={"telegram_id": telegram_id, "room_id": room_id})

    await update.message.reply_text(f"You have left the queue for room {room_id}.")
