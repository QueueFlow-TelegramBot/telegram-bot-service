from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.keyboards.inline import cancel_confirm_keyboard
from services.scheduling_client import join_room
from logger import get_logger

log = get_logger(__name__)

# ConversationHandler state
WAITING_ROOM_ID = 0


async def join_queue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /join_queue [room_id] — if no args, ask for room_id."""
    if context.args:
        return await _do_join(update, context, context.args[0])

    await update.message.reply_text("Enter the room ID to join:")
    return WAITING_ROOM_ID


async def join_queue_room_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive room_id text after /join_queue prompt."""
    room_id = update.message.text.strip()
    if not room_id:
        await update.message.reply_text("Please enter a valid room ID.")
        return WAITING_ROOM_ID

    await _do_join(update, context, room_id)
    return ConversationHandler.END


async def _do_join(update: Update, context: ContextTypes.DEFAULT_TYPE, room_id: str):
    """Perform the actual join queue logic."""
    telegram_id = update.effective_user.id

    log.info("join_queue command", extra={"telegram_id": telegram_id, "room_id": room_id})

    try:
        data = await join_room(room_id, telegram_id)
    except Exception as e:
        log.error("Failed to join room", extra={"error": str(e)})
        await update.message.reply_text(
            "Could not join the queue. Please check the room ID and try again."
        )
        return ConversationHandler.END

    position = data.get("position", 1)
    room_name = data.get("room_name", room_id)

    await update.message.reply_text(
        f"You are #{position} in queue for {room_name}.\n"
        f"We'll notify you when it's your turn!"
    )
    return ConversationHandler.END


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Not implemented yet. Please check back later.")
    return

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


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Not implemented yet. Please check back later.")
    return

    """Handle /cancel — ask confirmation before leaving the queue."""
    telegram_id = update.effective_user.id

    if telegram_id not in active_queues:
        await update.message.reply_text("You are not in any queue.")
        return

    room_id = active_queues[telegram_id]["room_id"]
    await update.message.reply_text(
        f"Are you sure you want to leave the queue for room {room_id}?",
        reply_markup=cancel_confirm_keyboard(room_id),
    )


async def cancel_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Not implemented yet. Please check back later.")
    return

    """Handle do_cancel callback — actually leave the queue."""
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    room_id = query.data.split(":", 1)[1]

    if telegram_id in active_queues:
        active_queues.pop(telegram_id)
        log.info("User left queue", extra={"telegram_id": telegram_id, "room_id": room_id})
        await query.edit_message_text(f"You have left the queue for room {room_id}.")
    else:
        await query.edit_message_text("You are not in any queue.")
