from uuid import UUID

from fastapi import status, HTTPException

from pydantic import EmailStr

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security import get_password_hash
from app.models import UserModel
from app.schemas import UserCreateSchema, UserUpdateSchema


async def create_user(
    session: AsyncSession,
    user_data: UserCreateSchema,
):
    new_user = user_data.model_dump(exclude={"password"})
    new_user["hashed_password"] = get_password_hash(user_data.password)
    user = UserModel(**new_user)
    session.add(user)
    await session.commit()


async def get_user_by_email(
    session: AsyncSession,
    email: EmailStr,
) -> UserModel | None:
    stmt = select(UserModel).where(UserModel.email == email)
    user = await session.scalar(stmt)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким email не найден",
        )
    return user


async def get_user_by_id(
    session: AsyncSession,
    user_id: UUID,
) -> UserModel | None:
    stmt = select(UserModel).where(UserModel.id == user_id)
    user = await session.scalar(stmt)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким id не найден",
        )
    return user


async def update_user(
    session: AsyncSession, new_user: UserUpdateSchema, user_id: UUID
) -> UserModel | None:
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким id не найден",
        )
    new_user_data = new_user.model_dump(exclude_unset=True)
    if "password" in new_user_data:
        password = new_user_data["password"]
        new_user_data["hashed_password"] = get_password_hash(password)
        del new_user_data["password"]
    for key, value in new_user_data.items():
        if new_user_data[key] != "":
            setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: UUID) -> None:
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователя не существует",
        )
    await session.delete(user)
    await session.commit()
