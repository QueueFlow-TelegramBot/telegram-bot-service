from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware.auth import require_role
from bot.keyboards.inline import rooms_keyboard, next_keyboard
from services.user_client import get_cached_user
from services.scheduling_client import create_room, get_rooms, next_in_queue
from logger import get_logger

log = get_logger(__name__)


@require_role("secretary")
async def create_room_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /create_room [room_name]."""
    telegram_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Usage: /create_room [room_name]")
        return

    room_name = " ".join(context.args)
    user = get_cached_user(telegram_id)
    creator_id = user["user_id"]

    log.info("create_room command", extra={"telegram_id": telegram_id, "room_name": room_name})

    try:
        data = await create_room(room_name, creator_id)
    except Exception as e:
        log.error("Failed to create room", extra={"error": str(e)})
        await update.message.reply_text("Could not create the room. Please try again later.")
        return

    room_id = data.get("room_id", "unknown")
    await update.message.reply_text(
        f"Room created!\n"
        f"Name: {room_name}\n"
        f"Share this ID with students: `{room_id}`",
        parse_mode="Markdown",
    )


@require_role("secretary")
async def get_rooms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /get_rooms — list active rooms."""
    telegram_id = update.effective_user.id
    user = get_cached_user(telegram_id)
    creator_id = user["user_id"]

    log.info("get_rooms command", extra={"telegram_id": telegram_id})

    try:
        rooms = await get_rooms(creator_id)
    except Exception as e:
        log.error("Failed to get rooms", extra={"error": str(e)})
        await update.message.reply_text("Could not fetch rooms. Please try again later.")
        return

    if not rooms:
        await update.message.reply_text("You have no active rooms.")
        return

    await update.message.reply_text(
        "Your rooms:",
        reply_markup=rooms_keyboard(rooms),
    )


@require_role("secretary")
async def next_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /next [room_id] — call next person in queue."""
    telegram_id = update.effective_user.id

    if not context.args:
        # Show inline keyboard with rooms to pick from
        user = get_cached_user(telegram_id)
        try:
            rooms = await get_rooms(user["user_id"])
        except Exception as e:
            log.error("Failed to get rooms for next", extra={"error": str(e)})
            await update.message.reply_text("Could not fetch rooms.")
            return

        if not rooms:
            await update.message.reply_text("You have no active rooms.")
            return

        await update.message.reply_text(
            "Select a room to call next:",
            reply_markup=next_keyboard(rooms),
        )
        return

    room_id = context.args[0]
    log.info("next command", extra={"telegram_id": telegram_id, "room_id": room_id})

    try:
        data = await next_in_queue(room_id)
    except Exception as e:
        log.error("Failed to call next", extra={"error": str(e)})
        await update.message.reply_text("Failed to call next person. Please try again.")
        return

    if data.get("error") == "queue_empty":
        await update.message.reply_text(f"Queue is empty for room {room_id}.")
    else:
        await update.message.reply_text("Next user has been notified!")


async def next_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callback for next:room_id."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("next:"):
        return

    room_id = data.split(":", 1)[1]
    log.info("next callback", extra={"room_id": room_id})

    try:
        result = await next_in_queue(room_id)
    except Exception as e:
        log.error("Failed to call next (callback)", extra={"error": str(e)})
        await query.edit_message_text("Failed to call next person. Please try again.")
        return

    if result.get("error") == "queue_empty":
        await query.edit_message_text(f"Queue is empty for room {room_id}.")
    else:
        await query.edit_message_text("Next user has been notified!")
