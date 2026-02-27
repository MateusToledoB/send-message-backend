from typing import Any
import re

import httpx

from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger(__name__)


class MetaRequestService:
    async def send_template_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not settings.WHATSAPP_TOKEN:
            raise ValueError("Configuracao da Meta incompleta. Defina WHATSAPP_TOKEN.")

        whatsapp_number = self._normalize_whatsapp_number(payload["whatsapp_number"])
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
            try:
                return response.json()
            except ValueError:
                return {}

    def _normalize_whatsapp_number(self, value: Any) -> str:
        raw_value = str(value).strip()
        if not raw_value or raw_value.lower() == "nan":
            raise ValueError("whatsapp_number invalido no payload.")

        # Corrige numeros lidos do Excel como float, ex: 41998233073.0
        if re.fullmatch(r"\d+\.0+", raw_value):
            raw_value = raw_value.split(".", 1)[0]

        digits = "".join(char for char in raw_value if char.isdigit())
        if not digits:
            raise ValueError("whatsapp_number invalido no payload.")

        # Evita duplicar DDI no envio (request_body ja prefixa com 55)
        if digits.startswith("55") and len(digits) > 11:
            digits = digits[2:]

        return digits

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
