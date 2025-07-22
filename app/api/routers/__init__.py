from fastapi import APIRouter

from app.api.routers import users, auth

router = APIRouter()
router.include_router(users.router)
router.include_router(auth.router)

__all__ = ("router",)
