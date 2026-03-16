import json
import logging
from datetime import datetime, timezone
from typing import Optional

import aio_pika
from aio_pika import ExchangeType

import config

log = logging.getLogger(__name__)


class RabbitMQPublisher:
    def __init__(self):
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.Channel] = None
        self._exchange: Optional[aio_pika.Exchange] = None

    async def connect(self):
        self._connection = await aio_pika.connect_robust(config.RABBITMQ_URL)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            config.RABBITMQ_EXCHANGE,
            ExchangeType.TOPIC,
            durable=True,
        )
        log.info("RabbitMQ connected", extra={"action": "connect", "success": True})

    async def disconnect(self):
        if self._connection:
            await self._connection.close()
        log.info("RabbitMQ disconnected", extra={"action": "disconnect", "success": True})


    async def publish(self, routing_key: str, body: dict):
        if self._exchange is None:
            raise RuntimeError("RabbitMQ not connected")

        # Declare and bind queue
        if routing_key.startswith("notification."):
            queue = await self._channel.declare_queue(routing_key, auto_delete=True)
        else:
            queue = await self._channel.declare_queue(routing_key, durable=True)
        await queue.bind(self._exchange, routing_key=routing_key)

        message = aio_pika.Message(
            body=json.dumps(body).encode(),
            content_type="application/json",
        )
        await self._exchange.publish(message, routing_key=routing_key)
        log.info(
            "Message published",
            extra={"action": "publish", "routing_key": routing_key, "queue_name": routing_key, "success": True},
        )

    @property
    def is_connected(self) -> bool:
        return self._connection is not None and not self._connection.is_closed


rabbitmq_publisher = RabbitMQPublisher()


async def get_rabbitmq() -> RabbitMQPublisher:
    return rabbitmq_publisher
