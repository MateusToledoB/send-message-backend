from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from app.core.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    setor = Column(String, nullable=False)

class MessageRequest(Base):
    __tablename__ = "message_requests"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    published_messages = Column(Integer, nullable=False)
    send_messages = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    template_type = Column(String, nullable=False)
