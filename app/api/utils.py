from datetime import timedelta, datetime
import jwt

from fastapi import Response

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.exceptions import INCORRECT_DATA_EXCEPTION
from app.api.request_forms import OAuth2EmailRequestForm
from app.api.security import verify_password
from app.core.config import settings
from app.crud import users_crud


class JWTAuthenticator:
    @staticmethod
    def create_jwt_token(
        payload,
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        expire_timedelta: timedelta | None = None,
    ):
        to_encode = payload.copy()
        if expire_timedelta:
            expire = datetime.now() + expire_timedelta
        else:
            expire = datetime.now() + timedelta(minutes=expire_minutes)
        to_encode.update(
            exp=expire,
            iat=datetime.now(),
        )
        encoded = jwt.encode(to_encode, key, algorithm)
        return encoded

    @staticmethod
    def decode_jwt_token(
        payload,
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    ):
        return jwt.decode(payload, key, algorithm)


class Authorization:
    @staticmethod
    async def login(
        session: AsyncSession,
        form_data: OAuth2EmailRequestForm,
        response: Response,
    ):
        user = await users_crud.get_user_by_email(session, form_data.username)
        if not user:
            raise INCORRECT_DATA_EXCEPTION
        if not verify_password(form_data.password, user.hashed_password):
            raise INCORRECT_DATA_EXCEPTION

        user_data = {
            "id": str(user.id),
            "username": user.email,
            "email": user.email,
            "gender": user.gender,
            "birthday": str(user.birthday.isoformat()),
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        token = JWTAuthenticator.create_jwt_token(user_data)
        response.set_cookie(
            key="token",
            value=token,
            max_age=int(timedelta(days=7).total_seconds()),
            httponly=False,
            secure=settings.IS_PROD,
            samesite="lax",
        )
