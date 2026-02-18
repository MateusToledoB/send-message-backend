from fastapi import FastAPI
from app.api.v1.routes import router as v1_router
from app.core.logger import get_logger, setup_logging
from app.core.settings import settings
from app.infra.db.db_client import db_client
from fastapi.middleware.cors import CORSMiddleware

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_FASTAPI_NAME
)

allowed_origins = [
    origin.strip()
    for origin in settings.CORS_ALLOW_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    db_client.create_tables()


app.include_router(v1_router, prefix="/api/v1")
