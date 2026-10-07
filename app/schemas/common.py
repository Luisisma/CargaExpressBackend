from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class EnvelopeResponse(BaseModel, Generic[DataT]):
    """Esquema de respuesta estándar para todas las operaciones exitosas."""
    success: bool = True
    data: Optional[DataT] = None
    message: Optional[str] = None


# Alias para compatibilidad de nomenclatura
SuccessResponse = EnvelopeResponse


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: Optional[List[ErrorDetail]] = None


class ErrorResponse(BaseModel):
    """Esquema estándar para todas las respuestas de error de la API."""
    success: bool = False
    error: ErrorPayload
