import asyncio
import aio_pika
import config
import json
from logger import get_logger


NOTIFICATION_QUEUE_NAME = "notifications"
NOTIFICATION_ROUTING_KEY = "notification.*"

log = get_logger(__name__)

# Will be set by main.py after bot app is created
_bot_app = None


def set_bot_app(app):
    global _bot_app
    _bot_app = app


async def on_notification(message: aio_pika.abc.AbstractIncomingMessage):
    """Handle incoming notification.[user_id] messages."""
    async with message.process():
        routing_key = message.routing_key or ""
        # routing_key format: notification.<telegram_id>
        parts = routing_key.split(".")
        if len(parts) < 2:
            log.warning("Invalid routing key", extra={"routing_key": routing_key})
            return

        telegram_id_str = parts[1]
        try:
            telegram_id = int(telegram_id_str)
        except ValueError:
            log.warning("Invalid telegram_id in routing key", extra={"routing_key": routing_key})
            return

        room = json.loads(message.body.decode("utf-8"))
        room_id = room.get("room_id", "unknown")
        room_name = room.get("room_name", room_id)
        log.info(
            "Notification received",
            extra={"telegram_id": telegram_id, "room_id": room_id, "room_name": room_name},
        )

        if _bot_app is None:
            log.error("Bot app not set, cannot send notification")
            return

        try:
            await _bot_app.bot.send_message(
                chat_id=telegram_id,
                text=f"It's your turn! Room: {room_name} (ID: {room_id})",
            )
            log.info("Notification sent", extra={"telegram_id": telegram_id})
        except Exception as e:
            log.error("Failed to send notification", extra={"error": str(e)})


async def start_consumer():
    """Connect to RabbitMQ and subscribe to notification.* topic."""
    if config.MOCK_SERVICES:
        log.info("MOCK_SERVICES=true, skipping RabbitMQ consumer")
        return

    retry_delay = 5
    while True:
        try:
            connection = await aio_pika.connect_robust(config.RABBITMQ_URL)
            channel = await connection.channel()

            exchange = await channel.declare_exchange(
                config.RABBITMQ_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
            )
            queue = await channel.declare_queue(NOTIFICATION_QUEUE_NAME, durable=True, auto_delete=False)
            await queue.bind(exchange, routing_key=NOTIFICATION_ROUTING_KEY)
            await queue.consume(on_notification)

            log.info("RabbitMQ consumer started, listening on notification.*")
            # Keep running until connection is lost
            await asyncio.Future()
        except Exception as e:
            log.error(
                "RabbitMQ connection failed, retrying",
                extra={"error": str(e), "retry_in": retry_delay},
            )
            await asyncio.sleep(retry_delay)
