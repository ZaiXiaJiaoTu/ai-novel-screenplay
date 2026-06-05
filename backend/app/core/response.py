from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Any = None


def success(data: Any = None, message: str = "success") -> dict[str, Any]:
    return ApiResponse(code=200, message=message, data=data).model_dump()


def fail(message: str, code: int = 400, data: Any = None) -> dict[str, Any]:
    return ApiResponse(code=code, message=message, data=data).model_dump()
