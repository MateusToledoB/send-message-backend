from sqlalchemy.orm import Session
from app.core.logger import get_logger
from app.infra.db.models import User

logger = get_logger(__name__)

class UserRepository:
    def __init__(self, session: Session): # Ele recebe uma sessão pronta
        self.session = session

    def get_all(self):
        return self.session.query(User).all()
    
    def get_user_by_name(self, name: str):
        return self.session.query(User).filter(User.name == name).first()
