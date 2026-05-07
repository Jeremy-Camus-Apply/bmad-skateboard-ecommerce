"""v1 API surface."""

from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.ops import router as ops_router

router = APIRouter(prefix="/v1")
router.include_router(ops_router)
router.include_router(chat_router)
