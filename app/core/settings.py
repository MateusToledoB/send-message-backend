from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    PROJECT_FASTAPI_NAME: str
    DATABASE_URL: str
    DEBUG: bool = False

    # RabbitMQ
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int = 5672
    RABBITMQ_URL: str
    RABBITMQ_EXCHANGE: str
    RABBITMQ_QUEUE_FOLHA_PONTO: str
    RABBITMQ_QUEUE_FOLHA_PONTO_BACKUP: str = "folha_ponto_backup_queue"
    RABBITMQ_WORKER_QUEUE: str = "folha_ponto_queue"

    JWT_SECRET_KEY: str = "change-this-secret-in-env"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_COOKIE_NAME: str = "token_access"
    JWT_COOKIE_SECURE: bool = False
    JWT_COOKIE_SAMESITE: str = "lax"
    JWT_COOKIE_PATH: str = "/"
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"

    # Meta WhatsApp API
    META_MESSAGES_URL: str = "https://graph.facebook.com/v22.0/934626919742007/messages"
    WHATSAPP_TOKEN: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
