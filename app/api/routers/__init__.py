from fastapi import APIRouter

from app.api.routers import users

router = APIRouter()
router.include_router(users.router)

__all__ = ("router",)
