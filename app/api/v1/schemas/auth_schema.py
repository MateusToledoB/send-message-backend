from pydantic import BaseModel
from app.core.logger import get_logger

logger = get_logger(__name__)

class AuthRequest(BaseModel):
    name: str
    password: str
