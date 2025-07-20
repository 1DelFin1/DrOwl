from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models import DocumentModel


class UserModel(Base, TimestampMixin):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    gender: Mapped[str] = mapped_column(String, nullable=False)
    birthday: Mapped[date] = mapped_column(DateTime, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)

    documents: Mapped["DocumentModel"] = relationship(
        "DocumentModel",
        back_populates="user",
    )
