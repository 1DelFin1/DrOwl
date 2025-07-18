from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

engine = create_async_engine(str(settings.POSTGRES_URL_ASYNC), echo=settings.ECHO)


class Base(DeclarativeBase):
    pass
