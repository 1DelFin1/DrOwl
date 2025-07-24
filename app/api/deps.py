from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.clients import broker
from app.core.database import engine


async def get_db() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session


async def get_broker():
    broker_mq = broker
    try:
        await broker_mq.connect()
        yield broker_mq
    finally:
        await broker_mq.close()


SessionDep = Annotated[AsyncSession, Depends(get_db)]
