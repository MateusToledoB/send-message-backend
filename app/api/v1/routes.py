from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.send_folha_ponto import router as send_folha_ponto_router
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()
router.include_router(auth_router, tags=["auth"])
router.include_router(send_folha_ponto_router, tags=["folha_ponto"])

@router.get("/health", summary="Health Check Endpoint")
def healthcheck():
    return {"status": "ok"}
