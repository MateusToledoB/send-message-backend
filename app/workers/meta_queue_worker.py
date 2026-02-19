import asyncio
import json
from typing import Any

import aio_pika

from app.core.logger import get_logger, setup_logging
from app.core.settings import settings
from app.infra.rabbitmq.rabbitmq_client import RabbitMQ
from app.services.meta_request_service import MetaRequestService

setup_logging()
logger = get_logger(__name__)


class MetaQueueWorker:
    def __init__(self):
        self.rabbitmq_client = RabbitMQ()
        self.meta_request_service = MetaRequestService()

    async def start(self) -> None:
        await self.rabbitmq_client.ensure_queue(settings.RABBITMQ_WORKER_QUEUE)
        queue = await self.rabbitmq_client.channel.get_queue(settings.RABBITMQ_WORKER_QUEUE)

        logger.info("Worker aguardando mensagens na fila '%s'", settings.RABBITMQ_WORKER_QUEUE)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await self._handle_message(message)

    async def _handle_message(self, message: aio_pika.IncomingMessage) -> None:
        payload: dict[str, Any] | None = None
        try:
            payload = json.loads(message.body.decode())
            meta_payload = self._build_folha_ponto_meta_payload(payload)
            await self.meta_request_service.send_template_message(meta_payload)
            await message.ack()
            logger.info(
                "Mensagem enviada para Meta com sucesso. fila=%s template=%s user_id=%s",
                settings.RABBITMQ_WORKER_QUEUE,
                meta_payload.get("template_name"),
                payload.get("user_id"),
            )
        except Exception as exc:
            logger.exception("Falha no envio para Meta: %s", exc)
            try:
                await self._publish_backup(payload, message.body, str(exc))
                await message.ack()
            except Exception as backup_exc:
                logger.exception(
                    "Falha ao mover mensagem para backup, reencaminhando para reprocessamento: %s",
                    backup_exc,
                )
                await message.nack(requeue=True)

    def _build_folha_ponto_meta_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        whatsapp_number = payload.get("whatsapp_number")
        name = payload.get("name")
        month_folha_ponto = payload.get("month_folha_ponto")

        if not whatsapp_number or name is None or month_folha_ponto is None:
            raise ValueError(
                "Payload invalido para folha_ponto: esperado whatsapp_number, name e month_folha_ponto."
            )

        return {
            "whatsapp_number": str(whatsapp_number),
            "template_name": "folha_ponto_ativo",
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(name)},
                        {"type": "text", "text": str(month_folha_ponto)},
                    ],
                }
            ],
        }

    async def _publish_backup(
        self, payload: dict[str, Any] | None, raw_body: bytes, error: str
    ) -> None:
        backup_payload: dict[str, Any]
        if payload is None:
            backup_payload = {"raw_body": raw_body.decode(errors="ignore"), "error": error}
        else:
            backup_payload = {**payload, "error": error}

        await self.rabbitmq_client.publish(settings.RABBITMQ_QUEUE_FOLHA_PONTO_BACKUP, backup_payload)
        logger.warning(
            "Mensagem movida para fila de backup '%s'",
            settings.RABBITMQ_QUEUE_FOLHA_PONTO_BACKUP,
        )


async def main() -> None:
    worker = MetaQueueWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
