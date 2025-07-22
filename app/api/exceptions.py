from fastapi import status, HTTPException

INCORRECT_DATA_EXCEPTION = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Неверный email или пароль",
)
