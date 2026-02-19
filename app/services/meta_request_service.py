from typing import Any

import httpx

from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger(__name__)


class MetaRequestService:
    async def send_template_message(self, payload: dict[str, Any]) -> None:
        if not settings.WHATSAPP_TOKEN:
            raise ValueError("Configuracao da Meta incompleta. Defina WHATSAPP_TOKEN.")

        whatsapp_number = payload["whatsapp_number"]
        template_name = payload.get("template_name") or payload.get("template_type")
        if not template_name:
            raise ValueError("Payload sem template_name/template_type.")
        components = payload.get("components") or self._build_components(payload)

        request_body = {
            "messaging_product": "whatsapp",
            "to": f"55{whatsapp_number}",
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "pt_BR"},
                "components": components,
            },
        }

        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.META_MESSAGES_URL, headers=headers, json=request_body
            )
            response.raise_for_status()

    def _build_components(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        # Mantem o formato generico: qualquer campo (exceto metadados)
        # vira parametro do template na ordem de insercao do payload.
        ignored_keys = {"whatsapp_number", "template_type", "user_id"}
        parameters = [
            {"type": "text", "text": str(value)}
            for key, value in payload.items()
            if key not in ignored_keys
        ]

        if not parameters:
            return []

        return [{"type": "body", "parameters": parameters}]
