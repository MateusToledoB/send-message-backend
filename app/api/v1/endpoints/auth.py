from datetime import timedelta

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.v1.schemas.auth_schema import AuthRequest
from app.api.v1.schemas.token_schema import TokenResponse
from app.core.logger import get_logger
from app.core.security import create_access_token
from app.core.settings import settings
from app.infra.db.db_client import db_client
from app.infra.db.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

# Criando um logger especifico para este modulo, facilitando o debug e o rastreio de informação
logger = get_logger(__name__)

# Instancia de APIrouter que serve como container de endpoints deste módulo
router = APIRouter()

# def que receb user e retorna um TokenResponse schema
def _build_token_for_user(user) -> TokenResponse:
    # objeto timedelta que representa os minutos de validade do token, configurados em settings 
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "name": user.name},
        expires_delta=access_token_expires,
    )
    return TokenResponse(access_token=access_token)


@router.post("/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(db_client.get_session),
):
    user_repo = UserRepository(session)
    service = AuthService(user_repo)
    user = service.authenticate(form_data.username, form_data.password)
    return _build_token_for_user(user)


@router.post("/authenticate", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_json(data: AuthRequest, session: Session = Depends(db_client.get_session)):
    user_repo = UserRepository(session)
    service = AuthService(user_repo)
    user = service.authenticate(data.name, data.password)
    return _build_token_for_user(user)
