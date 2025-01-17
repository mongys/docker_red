from fastapi import APIRouter
from src.presentation.api.user_router import router as user_router
from src.presentation.api.container_router import router as container_router

api_router = APIRouter()

api_router.include_router(user_router)
api_router.include_router(container_router)
