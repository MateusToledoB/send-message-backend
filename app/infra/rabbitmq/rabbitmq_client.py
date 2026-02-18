import json
import aio_pika
from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger(__name__)

class RabbitMQ:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        if not self.connection or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                settings.RABBITMQ_EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True
            )

    async def ensure_queue(self, queue_name: str):
        await self.connect()
        queue = await self.channel.declare_queue(queue_name, durable=True)
        await queue.bind(self.exchange, routing_key=queue_name)

    async def publish(self, queue_name: str, payload: dict):
        await self.ensure_queue(queue_name)
        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
            ),
            routing_key=queue_name,
        )
