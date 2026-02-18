from pydantic import BaseModel

from app.core.logger import get_logger

logger = get_logger(__name__)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
