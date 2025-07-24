from datetime import date
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBaseSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr = Field(max_length=255)
    gender: str
    birthday: date
    is_active: bool = True
    is_superuser: bool = False


class UserCreateSchema(UserBaseSchema):
    password: str = Field(max_length=40, min_length=3)


class UserOutSchema(UserBaseSchema):
    id: UUID

    class Config:
        from_attributes = True


class UserUpdateSchema(UserBaseSchema):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    gender: str | None = None
    birthday: date | None = None
    password: str | None = None


class UserInDBSchema(UserBaseSchema):
    id: UUID
    hashed_password: str


class DocumentCreateSchema(BaseModel):
    user_id: UUID


class DocumentResponseSchema(BaseModel):
    id: UUID
    statis: str


class OCRTaskSchema(BaseModel):
    doc_id: UUID
    user_id: UUID
    file_path: str
