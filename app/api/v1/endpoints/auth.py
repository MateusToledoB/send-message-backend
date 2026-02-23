from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.auth_schema import AuthRequest
from app.api.v1.schemas.token_schema import TokenResponse
from app.api.v1.endpoints.utils import create_token_for_user, set_auth_cookie
from app.core.logger import get_logger
from app.infra.db.db_client import db_client
from app.infra.db.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

logger = get_logger(__name__)

router = APIRouter()


@router.post("/authenticate", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_json(
    data: AuthRequest,
    response: Response,
    session: Session = Depends(db_client.get_session),
):
    user_repo = UserRepository(session)
    service = AuthService(user_repo)
    user = service.authenticate(data.name, data.password)

    access_token = create_token_for_user(user)
    set_auth_cookie(response, access_token)
    return TokenResponse(access_token=access_token)
