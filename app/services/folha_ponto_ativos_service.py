from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.core.settings import settings
from app.infra.db.models import MessageRequest
from app.infra.rabbitmq.rabbitmq_client import RabbitMQ
from app.utils.file_utils import xlsx_to_dataframe

logger = get_logger(__name__)


class FolhaPontoAtivosService:
    def __init__(self, session: Session):
        self.session = session
        self.rabbitmq_client = RabbitMQ()

    async def loop_folha_ponto_ativos(
        self,
        file,
        column_name: str,
        column_month: str,
        column_contact: str,
        user_id: int,
        template_type: str,
    ):
        request = MessageRequest(
            user_id=user_id,
            published_messages=0,
            send_messages=0,
            status="requested",
            template_type=template_type,
        )
        self.session.add(request)
        self.session.commit()
        self.session.refresh(request)

        df = await xlsx_to_dataframe(file)
        published = 0

        for _, row in df.iterrows():
            payload = {
                "name": str(row[column_name]),
                "month_folha_ponto": str(row[column_month]),
                "whatsapp_number": str(row[column_contact]),
                "user_id": user_id,
                "template_type": template_type,
                "message_request_id": request.id,
            }
            await self.rabbitmq_client.publish(settings.RABBITMQ_QUEUE_FOLHA_PONTO_ATIVOS, payload)
            published += 1

        request.published_messages = published
        request.status = "finish"
        self.session.commit()
        self.session.refresh(request)

        return {
            "message_request_id": request.id,
            "published_messages": request.published_messages,
            "send_messages": request.send_messages,
            "status": request.status,
            "template_type": request.template_type,
            "created_at": request.created_at,
        }
