from uuid import UUID

from fastapi import APIRouter
from pydantic import EmailStr

from app.api.deps import SessionDep
from app.crud import users_crud
from app.schemas import UserCreateSchema, UserUpdateSchema


router = APIRouter(tags=["users"], prefix="/user")


@router.post("")
async def create_user(session: SessionDep, user_data: UserCreateSchema):
    await users_crud.create_user(session, user_data)
    return {"ok": True}


@router.get("/{email}")
async def get_user(session: SessionDep, email: EmailStr):
    user = await users_crud.get_user_by_email(session, email)
    return user


@router.patch("/{user_id}")
async def update_user(session: SessionDep, user_data: UserUpdateSchema, user_id: UUID):
    await users_crud.update_user(session, user_data, user_id)
    return {"ok": True}


@router.delete("/{user_id}")
async def delete_user(session: SessionDep, user_id: UUID):
    await users_crud.delete_user(session, user_id)
    return {"ok": True}
