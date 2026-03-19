from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.middleware.auth import require_role
from bot.keyboards.inline import rooms_keyboard, next_keyboard, room_actions_keyboard, next_confirm_keyboard
from services.user_client import get_user_by_telegram_id
from services.scheduling_client import create_room, get_rooms, next_in_queue
from logger import get_logger

log = get_logger(__name__)

# ConversationHandler state
WAITING_ROOM_NAME = 0


@require_role("student", "secretary", "admin")
async def create_room_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /create_room [room_name] — if no args, ask for room name."""
    if context.args:
        await _do_create_room(update, context, " ".join(context.args))
        return ConversationHandler.END

    await update.message.reply_text("Enter a name for the new room:")
    return WAITING_ROOM_NAME


async def create_room_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive room name text after /create_room prompt."""
    room_name = update.message.text.strip()
    if not room_name:
        await update.message.reply_text("Please enter a valid room name.")
        return WAITING_ROOM_NAME

    await _do_create_room(update, context, room_name)
    return ConversationHandler.END


async def _do_create_room(update: Update, context: ContextTypes.DEFAULT_TYPE, room_name: str):
    """Perform the actual create room logic."""
    telegram_id = update.effective_user.id

    log.info("create_room command", extra={"telegram_id": telegram_id, "room_name": room_name})

    try:
        data = await create_room(room_name, telegram_id)
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


@require_role("student", "secretary", "admin")
async def get_rooms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /get_rooms — list active rooms."""
    telegram_id = update.effective_user.id
    user = await get_user_by_telegram_id(telegram_id)

    log.info("get_rooms command", extra={"telegram_id": telegram_id})

    try:
        rooms = await get_rooms(telegram_id)
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


@require_role("student", "secretary", "admin")
async def next_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /next [room_id] — call next person in queue."""
    telegram_id = update.effective_user.id

    if not context.args:
        # Show inline keyboard with rooms to pick from
        try:
            rooms = await get_rooms(telegram_id)
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

    await update.message.reply_text(
        f"Call next person in room `{room_id}`?",
        parse_mode="Markdown",
        reply_markup=next_confirm_keyboard(room_id, room_id),
    )


async def room_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callback for room:room_id — show room actions."""
    query = update.callback_query
    await query.answer()

    room_id = query.data.split(":", 1)[1]
    log.info("room callback", extra={"room_id": room_id})

    await query.edit_message_text(
        f"Room `{room_id}` — choose an action:",
        parse_mode="Markdown",
        reply_markup=room_actions_keyboard(room_id),
    )


async def next_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirm_next:room_id and next:room_id — show confirmation before calling next."""
    query = update.callback_query
    await query.answer()

    room_id = query.data.split(":", 1)[1]
    log.info("next confirm callback", extra={"room_id": room_id})

    await query.edit_message_text(
        f"Call next person in room `{room_id}`?",
        parse_mode="Markdown",
        reply_markup=next_confirm_keyboard(room_id, room_id),
    )


async def do_next_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle do_next:room_id — actually call the next person."""
    query = update.callback_query
    await query.answer()

    room_id = query.data.split(":", 1)[1]
    log.info("do_next callback", extra={"room_id": room_id})

    try:
        result = await next_in_queue(room_id, update.effective_user.id)
    except Exception as e:
        log.error("Failed to call next (callback)", extra={"error": str(e)})
        await query.edit_message_text("Failed to call next person. Please try again.")
        return

    if result.get("error") == "queue_empty":
        await query.edit_message_text(f"Queue is empty for room {room_id}.")
    else:
        next_user = await get_user_by_telegram_id(result.get("next_user_id"))
        await query.edit_message_text("Next person called: {}".format(next_user.get("display_name", "Unknown")))


async def copyid_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callback for copyid:room_id — show copyable ID."""
    query = update.callback_query
    await query.answer()

    room_id = query.data.split(":", 1)[1]
    await query.edit_message_text(
        f"Share this room ID with students:\n`{room_id}`",
        parse_mode="Markdown",
    )


async def dismiss_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dismiss callback — cancel the confirmation prompt."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Action cancelled.")
