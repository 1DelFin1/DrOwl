from uuid import UUID

from fastapi import APIRouter, UploadFile, Depends

from app.api.deps import SessionDep, get_broker
from app.api.managers import FileManager


router = APIRouter(tags=["documents"], prefix="/document")


@router.post("/upload")
async def upload_file(
    session: SessionDep,
    file: UploadFile,
    user_id: UUID,
    broker_mq=Depends(get_broker),
):
    manager = FileManager(file, user_id)
    await manager.execute_task(session, broker_mq)
    return {"doc_id": manager.doc_id, "status": "queued"}
