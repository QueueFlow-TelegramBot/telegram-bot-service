import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import config
from logger import get_logger
from bot.handlers.start import start_handler, help_handler
from bot.handlers.queue import join_queue_handler, status_handler, cancel_handler
from bot.handlers.room import create_room_handler, get_rooms_handler, next_handler, next_callback_handler
from bot.handlers.profile import profile_handler, CHANGE_PREFIX
from bot.notifications.consumer import start_consumer, set_bot_app

log = get_logger(__name__)


async def post_init(application):
    """Called after the bot app is fully initialized — start background tasks."""
    if not config.MOCK_SERVICES:
        asyncio.create_task(start_consumer())
        log.info("RabbitMQ consumer task scheduled")


def main():
    if not config.BOT_TOKEN:
        log.error("BOT_TOKEN is not set")
        raise SystemExit("BOT_TOKEN environment variable is required")

    log.info(
        "Starting QueueFlow bot",
        extra={"mock_services": config.MOCK_SERVICES},
    )

    app = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Register command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("join_queue", join_queue_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("cancel", cancel_handler))
    app.add_handler(CommandHandler("create_room", create_room_handler))
    app.add_handler(CommandHandler("get_rooms", get_rooms_handler))
    app.add_handler(CommandHandler("next", next_handler))

    # Callback query handler for inline keyboards
    app.add_handler(CallbackQueryHandler(next_callback_handler, pattern=r"^next:"))

    # Text handler for display name updates
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(f"^{CHANGE_PREFIX}"),
        profile_handler,
    ))

    # Set bot app reference for RabbitMQ notifications
    set_bot_app(app)

    log.info("Bot is running")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
