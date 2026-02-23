import asyncio
import json
from collections.abc import Callable
from typing import Any

import aio_pika

from app.core.logger import get_logger, setup_logging
from app.core.settings import settings
from app.infra.db.db_client import db_client
from app.infra.db.models import MessageRequest
from app.infra.rabbitmq.rabbitmq_client import RabbitMQ
from app.services.meta_request_service import MetaRequestService

setup_logging()
logger = get_logger(__name__)


class MetaQueueWorker:
    def __init__(self):
        self.rabbitmq_client = RabbitMQ()
        self.meta_request_service = MetaRequestService()
        self.queue_handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            settings.RABBITMQ_QUEUE_FOLHA_PONTO_ATIVOS: self._build_folha_ponto_ativos_meta_payload,
            settings.RABBITMQ_QUEUE_FOLHA_PONTO_INATIVOS: self._build_folha_ponto_inativos_meta_payload,
            settings.RABBITMQ_QUEUE_FOLHA_PONTO_ATIVOS_TORRE: self._build_folha_ponto_ativos_torre_meta_payload,
            settings.RABBITMQ_QUEUE_VAGAS: self._build_vagas_meta_payload,
        }

    async def start(self) -> None:
        for queue_name in self.queue_handlers:
            await self.rabbitmq_client.ensure_queue(queue_name)
            logger.info("Worker aguardando mensagens na fila '%s'", queue_name)

        consumers = [
            asyncio.create_task(self._consume_queue(queue_name))
            for queue_name in self.queue_handlers
        ]
        await asyncio.gather(*consumers)

    async def _consume_queue(self, queue_name: str) -> None:
        queue = await self.rabbitmq_client.channel.get_queue(queue_name)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await self._handle_message(queue_name, message)

    async def _handle_message(self, queue_name: str, message: aio_pika.IncomingMessage) -> None:
        payload: dict[str, Any] | None = None
        try:
            payload = json.loads(message.body.decode())
            meta_payload = self._build_meta_payload(queue_name, payload)
            meta_response = await self.meta_request_service.send_template_message(meta_payload)
            self._assert_meta_delivery_success(meta_response)
            self._register_delivery_success(payload)
            await message.ack()
            logger.info(
                "Mensagem enviada para Meta com sucesso. fila=%s template=%s user_id=%s",
                queue_name,
                meta_payload.get("template_name"),
                payload.get("user_id"),
            )
        except Exception as exc:
            logger.exception("Falha no envio para Meta: %s", exc)
            try:
                await self._publish_backup(queue_name, payload, message.body, str(exc))
                await message.ack()
            except Exception as backup_exc:
                logger.exception(
                    "Falha ao mover mensagem para backup, reencaminhando para reprocessamento: %s",
                    backup_exc,
                )
                await message.nack(requeue=True)

    def _build_meta_payload(self, queue_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        build_payload = self.queue_handlers.get(queue_name)
        if build_payload is None:
            raise ValueError(f"Fila sem handler configurado: {queue_name}")
        return build_payload(payload)

    def _assert_meta_delivery_success(self, meta_response: dict[str, Any]) -> None:
        messages = meta_response.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("Retorno da Meta sem confirmacao de mensagem enviada.")

    def _register_delivery_success(self, payload: dict[str, Any]) -> None:
        message_request_id = payload.get("message_request_id")
        if message_request_id is None:
            logger.warning("Payload sem message_request_id; contabilizacao ignorada.")
            return

        session = db_client.SessionLocal()
        try:
            request = session.get(MessageRequest, int(message_request_id))
            if request is None:
                logger.warning(
                    "MessageRequest nao encontrado para id=%s; contabilizacao ignorada.",
                    message_request_id,
                )
                return

            request.send_messages += 1
            if request.published_messages > 0 and request.send_messages >= request.published_messages:
                request.status = "finish"

            session.commit()
        finally:
            session.close()

    def _build_folha_ponto_ativos_meta_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._build_folha_ponto_meta_payload(payload, template_name="folha_ponto_ativo")

    def _build_folha_ponto_inativos_meta_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._build_folha_ponto_meta_payload(payload, template_name="folha_ponto_inativo")

    def _build_folha_ponto_ativos_torre_meta_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._build_folha_ponto_meta_payload(payload, template_name="folha_ponto_ativo_torre")

    def _build_folha_ponto_meta_payload(
        self,
        payload: dict[str, Any],
        template_name: str,
    ) -> dict[str, Any]:
        whatsapp_number = payload.get("whatsapp_number")
        name = payload.get("name")
        month_folha_ponto = payload.get("month_folha_ponto")

        if not whatsapp_number or name is None or month_folha_ponto is None:
            raise ValueError(
                "Payload invalido para folha_ponto: esperado whatsapp_number, name e month_folha_ponto."
            )

        return {
            "whatsapp_number": str(whatsapp_number),
            "template_name": template_name,
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

    def _build_vagas_meta_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        whatsapp_number = payload.get("whatsapp_number")
        if not whatsapp_number:
            raise ValueError("Payload invalido para vagas: esperado whatsapp_number.")

        template_name = str(payload.get("template_type") or "vagas")
        ignored_keys = {"whatsapp_number", "template_type", "user_id", "message_request_id"}
        parameters = [
            {"type": "text", "text": str(value)}
            for key, value in payload.items()
            if key not in ignored_keys
        ]
        components = [{"type": "body", "parameters": parameters}] if parameters else []

        return {
            "whatsapp_number": str(whatsapp_number),
            "template_name": template_name,
            "components": components,
        }

    async def _publish_backup(
        self,
        queue_name: str,
        payload: dict[str, Any] | None,
        raw_body: bytes,
        error: str,
    ) -> None:
        backup_payload: dict[str, Any]
        if payload is None:
            backup_payload = {
                "source_queue": queue_name,
                "raw_body": raw_body.decode(errors="ignore"),
                "error": error,
            }
        else:
            backup_payload = {**payload, "source_queue": queue_name, "error": error}

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
