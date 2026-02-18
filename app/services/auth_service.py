from fastapi import HTTPException, status

from app.core.logger import get_logger
from app.core.security import verify_password
from app.infra.db.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate(self, name: str, password: str):
        user = self.user_repo.get_user_by_name(name)
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais invalidas",
            )
        return user
