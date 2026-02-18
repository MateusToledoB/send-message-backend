from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.folha_ponto_schema import FolhaPontoRequest
from app.core.logger import get_logger
from app.core.security import get_current_user
from app.infra.db.db_client import db_client
from app.infra.db.models import User
from app.services.folha_ponto_service import FolhaPontoService

logger = get_logger(__name__)

router = APIRouter()


@router.post("/send_folha_ponto", status_code=status.HTTP_200_OK)
async def send_folha_ponto(
    file: UploadFile = File(...),
    data: FolhaPontoRequest = Depends(FolhaPontoRequest.as_form),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(db_client.get_session),
):
    service = FolhaPontoService(session=session)
    return await service.loop_folha_ponto(
        file=file,
        column_name=data.column_name,
        column_month=data.column_month,
        column_contact=data.column_contact,
        user_id=current_user.id,
        template_type=data.template_type,
    )
