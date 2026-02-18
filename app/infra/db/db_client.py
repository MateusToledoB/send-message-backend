from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.logger import get_logger
from app.core.settings import settings
from app.infra.db.models import Base

logger = get_logger(__name__)


class DbClient:
    def __init__(self):
        self.db_url = settings.DATABASE_URL
        self.engine = create_engine(self.db_url, echo=True, future=True)
        self.SessionLocal = self.create_session_factory()

    def create_session_factory(self):
        return sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


db_client = DbClient()
