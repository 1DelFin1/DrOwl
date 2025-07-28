from typing import Optional
from uuid import UUID, uuid4
from PIL import Image
import io

from faststream.rabbit import RabbitBroker
from fastapi import UploadFile

from minio.error import S3Error

import pytesseract
from pdf2image import convert_from_bytes

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.clients import minio_client, broker
from app.models import DocumentModel
from app.schemas import OCRTaskSchema


class OCRManager:
    @staticmethod
    @broker.subscriber(queue="ocr_tasks")
    async def process_ocr(task: OCRTaskSchema, session: AsyncSession):
        doc_id = task.doc_id

        try:
            file_data = minio_client.get_object("documents", task.file_path)
            file_bytes = file_data.read()

            if task.file_path.endswith(".pdf"):
                images = convert_from_bytes(file_bytes)
                text = "\n".join(pytesseract.image_to_string(img) for img in images)
            else:
                try:
                    image = Image.open(io.BytesIO(file_bytes))
                    text = pytesseract.image_to_string(image)
                except Exception as img_e:
                    raise ValueError(f"Failed to process image: {str(img_e)}")
            processed_path = f"users/{task.user_id}/processed/{doc_id}.txt"
            minio_client.put_object(
                bucket_name="documents",
                object_name=processed_path,
                data=io.BytesIO(text.encode()),
                length=len(text),
            )

            # await es_client.index(
            #     index="documents",
            #     id=str(doc_id),
            #     document={
            #         "text": text,
            #         "user_id": task.user_id,
            #         "original_path": task.file_path,
            #     },
            # )

            doc = await session.get(DocumentModel, doc_id)
            if doc:
                doc.status = "processed"
                doc.processed_path = processed_path
                doc.processed_text = text
                await session.commit()
            else:
                raise ValueError(f"Document with id {doc_id} not found")

        except Exception as e:
            raise e


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
    async def _create_minio_bucket():
        try:
            if not minio_client.bucket_exists("documents"):
                minio_client.make_bucket("documents")
        except S3Error as e:
            print(f"Error creating minio bucket: {e}")  # реализовать logger

    async def _download_file(self):
        await self._read_file()

        file_obj = io.BytesIO(self._file_data)
        file_obj.seek(0)

        await self._create_minio_bucket()

        minio_client.put_object(
            bucket_name="documents",
            object_name=self.file_path,
            data=file_obj,
            length=len(self._file_data),
        )

    async def _upload_file(self, session: AsyncSession):
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

    async def _send_file_to_broker(self, broker_mq):
        task_schema = OCRTaskSchema(
            doc_id=self.doc_id, user_id=self.user_id, file_path=self.file_path
        )
        await broker_mq.publish(
            task_schema,
            queue="ocr_tasks",
        )
        return task_schema

    async def execute_task(self, session: AsyncSession, broker_mq: RabbitBroker):
        await self._download_file()
        await self._upload_file(session)
        task = await self._send_file_to_broker(broker_mq)
        manager = OCRManager()
        await manager.process_ocr(task, session)
