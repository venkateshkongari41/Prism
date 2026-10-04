from pydantic import BaseModel


class ErrorDetail(BaseModel):
    type: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail