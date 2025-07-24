from fastapi import APIRouter

from app.api.routers import users, auth, documents

router = APIRouter()
router.include_router(users.router)
router.include_router(auth.router)
router.include_router(documents.router)

__all__ = ("router",)
