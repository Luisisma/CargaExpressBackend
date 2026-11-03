from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class AgenciaBase(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=150, description="Nombre descriptivo de la agencia")
    departamento: str = Field(..., min_length=2, max_length=100)
    departamento_id: Optional[int] = Field(None, ge=1, le=25)
    provincia: str = Field(..., min_length=2, max_length=100)
    distrito: str = Field(..., min_length=2, max_length=100)
    direccion: str = Field(..., min_length=5, max_length=250)
    estado: Optional[Literal["habilitado", "deshabilitado"]] = Field(default="habilitado")


class AgenciaCreateRequest(AgenciaBase):
    codigo_agencia: Optional[int] = Field(None, description="Código numérico opcional (se autogenera si se omite)")


class AgenciaUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=150)
    departamento: Optional[str] = Field(None, min_length=2, max_length=100)
    departamento_id: Optional[int] = Field(None, ge=1, le=25)
    provincia: Optional[str] = Field(None, min_length=2, max_length=100)
    distrito: Optional[str] = Field(None, min_length=2, max_length=100)
    direccion: Optional[str] = Field(None, min_length=5, max_length=250)
    estado: Optional[Literal["habilitado", "deshabilitado"]] = None


class AgenciaResponse(BaseModel):
    id: int
    codigo_agencia: int
    nombre: str
    departamento: str
    departamento_id: Optional[int] = None
    provincia: str
    distrito: str
    direccion: str
    estado: str
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

