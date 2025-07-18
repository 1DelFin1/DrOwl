from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncSession:
    async with AsyncSession() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]
