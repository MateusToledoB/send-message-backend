from datetime import timedelta
import secrets

from fastapi import Response

from app.core.security import create_access_token
from app.core.settings import settings


def create_token_for_user(user) -> str:
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": str(user.id), "name": user.name},
        expires_delta=access_token_expires,
    )


def set_auth_cookie(response: Response, access_token: str) -> None:
    max_age_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    csrf_token = secrets.token_urlsafe(32)

    response.set_cookie(
        key=settings.JWT_COOKIE_NAME,
        value=access_token,
        max_age=max_age_seconds,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path=settings.JWT_COOKIE_PATH,
    )
    response.set_cookie(
        key=settings.JWT_CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age_seconds,
        httponly=False,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path=settings.JWT_COOKIE_PATH,
    )
