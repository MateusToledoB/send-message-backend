from datetime import timedelta

from fastapi import APIRouter, Depends, Response, status
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

logger = get_logger(__name__)

router = APIRouter()


def _create_token_for_user(user) -> str:
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": str(user.id), "name": user.name},
        expires_delta=access_token_expires,
    )


def _set_auth_cookie(response: Response, access_token: str) -> None:
    max_age_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=settings.JWT_COOKIE_NAME,
        value=access_token,
        max_age=max_age_seconds,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path=settings.JWT_COOKIE_PATH,
    )


@router.post("/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(db_client.get_session),
):
    user_repo = UserRepository(session)
    service = AuthService(user_repo)
    user = service.authenticate(form_data.username, form_data.password)

    access_token = _create_token_for_user(user)
    _set_auth_cookie(response, access_token)
    return TokenResponse(access_token=access_token)


@router.post("/authenticate", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_json(
    data: AuthRequest,
    response: Response,
    session: Session = Depends(db_client.get_session),
):
    user_repo = UserRepository(session)
    service = AuthService(user_repo)
    user = service.authenticate(data.name, data.password)

    access_token = _create_token_for_user(user)
    _set_auth_cookie(response, access_token)
    return TokenResponse(access_token=access_token)
