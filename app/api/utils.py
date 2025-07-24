from datetime import timedelta, datetime
from typing import Optional
from uuid import UUID, uuid4
import jwt

from faststream.rabbit import RabbitBroker

from minio.error import S3Error

from fastapi import Response, UploadFile

from sqlalchemy.ext.asyncio import AsyncSession

import io

from app.api.clients import minio_client
from app.api.exceptions import INCORRECT_DATA_EXCEPTION
from app.api.request_forms import OAuth2EmailRequestForm
from app.api.security import verify_password
from app.core.config import settings
from app.crud import users_crud
from app.models import DocumentModel
from app.schemas import OCRTaskSchema


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


class FileManager:
    def __init__(self, file: UploadFile, user_id: UUID):
        self.doc_id = str(uuid4())
        self.user_id = user_id
        self.file = file
        self.file_path = (
            f"users/{self.user_id}/original/{self.doc_id}_{self.file.filename}"
        )
        self._file_data: Optional[bytes] = None

    async def _read_file(self):
        if self._file_data is None:
            self._file_data = await self.file.read()

    @staticmethod
    async def create_minio_bucket():
        try:
            if not minio_client.bucket_exists("documents"):
                minio_client.make_bucket("documents")
        except S3Error as e:
            print(f"Error creating minio bucket: {e}")  # реализовать logger

    async def download_file(self):
        await self._read_file()

        file_obj = io.BytesIO(self._file_data)
        file_obj.seek(0)

        await self.create_minio_bucket()

        minio_client.put_object(
            bucket_name="documents",
            object_name=self.file_path,
            data=file_obj,
            length=len(self._file_data),
        )

    async def upload_file(self, session: AsyncSession):
        try:
            doc = DocumentModel(
                id=self.doc_id,
                user_id=self.user_id,
                original_path=self.file_path,
                status="uploaded",
            )
            session.add(doc)
            await session.commit()
            await session.refresh(doc)
            return doc
        except Exception as e:
            await session.rollback()
            raise ValueError(f"Failed to upload document:")

    async def send_file_to_broker(self, broker_mq):
        await broker_mq.publish(
            OCRTaskSchema(
                doc_id=self.doc_id,
                user_id=self.user_id,
                file_path=self.file_path,
            ),
            queue="ocr_tasks",
        )

    async def execute_task(self, session: AsyncSession, broker_mq: RabbitBroker):
        await self.download_file()
        await self.upload_file(session)
        await self.send_file_to_broker(broker_mq)
