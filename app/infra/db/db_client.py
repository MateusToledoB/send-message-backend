from sqlalchemy import create_engine, inspect, text
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
        self.ensure_message_requests_columns()

    def ensure_message_requests_columns(self):
        inspector = inspect(self.engine)
        if "message_requests" not in inspector.get_table_names():
            return

        existing_columns = {col["name"] for col in inspector.get_columns("message_requests")}
        if "send_messages" in existing_columns:
            return

        # Backward-compatible migration for existing databases.
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE message_requests "
                    "ADD COLUMN send_messages INTEGER NOT NULL DEFAULT 0"
                )
            )

    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


db_client = DbClient()
