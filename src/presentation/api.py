from fastapi import APIRouter
from src.presentation.routers.user_router import router as user_router
from src.presentation.routers.container_router import router as container_router

api_router = APIRouter()

# Включаем отдельные роутеры
api_router.include_router(user_router)
api_router.include_router(container_router)
