from typing import TYPE_CHECKING
from uuid import uuid4, UUID

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.core.database import Base
from app.models.mixins import TimestampMixin


if TYPE_CHECKING:
    from app.models import UserModel


class DocumentModel(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    original_path: Mapped[String] = mapped_column(String(255), nullable=False)
    processed_text: Mapped[String] = mapped_column(String, nullable=True)
    status: Mapped[String] = mapped_column(String(50), nullable=False)

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="documents",
    )
