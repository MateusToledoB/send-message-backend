from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.folha_ponto_schema import FolhaPontoUploadRequest
from app.core.logger import get_logger
from app.core.security import get_current_user
from app.infra.db.db_client import db_client
from app.infra.db.models import User
from app.services.folha_ponto_ativos_service import FolhaPontoAtivosService

logger = get_logger(__name__)

router = APIRouter()

@router.post("/send_folha_ponto_ativos", status_code=status.HTTP_200_OK)
async def send_folha_ponto_ativos(
    payload: FolhaPontoUploadRequest = Depends(FolhaPontoUploadRequest.as_form),
    session: Session = Depends(db_client.get_session),
):
    service = FolhaPontoAtivosService(session=session)
    return await service.loop_folha_ponto_ativos(
        file=payload.file,
        column_name=payload.column_name,
        column_month=payload.column_month,
        column_contact=payload.column_contact,
        user_id=1,
        template_type=payload.template_type,
    )
