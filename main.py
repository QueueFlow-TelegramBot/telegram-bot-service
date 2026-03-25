import asyncio
from telegram import BotCommand, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters,
)
import config
from logger import get_logger
from bot.handlers.start import start_handler, help_handler
from bot.handlers.queue import (
    join_queue_handler, join_queue_room_id_received, WAITING_ROOM_ID,
    status_handler, cancel_handler, cancel_confirm_callback,
)
from bot.handlers.room import (
    create_room_handler, create_room_name_received, WAITING_ROOM_NAME,
    get_rooms_handler, next_handler,
    room_callback_handler, next_confirm_callback, do_next_callback,
    copyid_callback_handler, dismiss_callback,
)
from bot.handlers.profile import profile_handler, CHANGE_PREFIX
from bot.notifications.consumer import start_consumer, set_bot_app

log = get_logger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler — logs exceptions and notifies the user."""
    log.error("Unhandled exception", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Something went wrong. Please try again later."
            )
        except Exception:
            pass


async def post_init(application):
    """Called after the bot app is fully initialized — start background tasks."""
    commands = [
        BotCommand("start", "Register and get welcome message"),
        BotCommand("help", "Show available commands"),
        BotCommand("join_queue", "Join a queue room"),
        # BotCommand("status", "Check your position in queue"),
        # BotCommand("cancel", "Leave the current queue"),
        BotCommand("create_room", "Create a new queue room"),
        BotCommand("get_rooms", "List your active rooms"),
        BotCommand("next", "Call next person in queue"),
    ]
    await application.bot.set_my_commands(commands)

    asyncio.create_task(start_consumer())
    log.info("RabbitMQ consumer task scheduled")


def main():
    if not config.BOT_TOKEN:
        log.error("BOT_TOKEN is not set")
        raise SystemExit("BOT_TOKEN environment variable is required")

    log.info("Starting QueueFlow bot")

    app = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    msg_only = filters.UpdateType.MESSAGE

    # Conversation: /join_queue → asks for room_id if not provided
    join_queue_conv = ConversationHandler(
        entry_points=[CommandHandler("join_queue", join_queue_handler, msg_only)],
        states={
            WAITING_ROOM_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_queue_room_id_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler, msg_only)],
    )
    app.add_handler(join_queue_conv)

    # Conversation: /create_room → asks for room name if not provided
    create_room_conv = ConversationHandler(
        entry_points=[CommandHandler("create_room", create_room_handler, msg_only)],
        states={
            WAITING_ROOM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_room_name_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler, msg_only)],
    )
    app.add_handler(create_room_conv)

    # Regular command handlers
    app.add_handler(CommandHandler("start", start_handler, msg_only))
    app.add_handler(CommandHandler("help", help_handler, msg_only))
    # app.add_handler(CommandHandler("status", status_handler, msg_only))
    # app.add_handler(CommandHandler("cancel", cancel_handler, msg_only))
    app.add_handler(CommandHandler("get_rooms", get_rooms_handler, msg_only))
    app.add_handler(CommandHandler("next", next_handler, msg_only))

    # Callback query handlers for inline keyboards
    app.add_handler(CallbackQueryHandler(room_callback_handler, pattern=r"^room:"))
    app.add_handler(CallbackQueryHandler(next_confirm_callback, pattern=r"^(next|confirm_next):"))
    app.add_handler(CallbackQueryHandler(do_next_callback, pattern=r"^do_next:"))
    app.add_handler(CallbackQueryHandler(cancel_confirm_callback, pattern=r"^do_cancel:"))
    app.add_handler(CallbackQueryHandler(copyid_callback_handler, pattern=r"^copyid:"))
    app.add_handler(CallbackQueryHandler(dismiss_callback, pattern=r"^dismiss$"))

    # Text handler for display name updates
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(f"^{CHANGE_PREFIX}"),
        profile_handler,
    ))

    # Global error handler
    app.add_error_handler(error_handler)

    # Set bot app reference for RabbitMQ notifications
    set_bot_app(app)

    log.info("Bot is running")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
