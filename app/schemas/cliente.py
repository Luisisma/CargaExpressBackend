from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ClienteListItem(BaseModel):
    id: int
    tipo_documento: str
    numero_documento: str
    nombre_completo: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    tipo_cliente: str
    activo: bool
    total_envios: int
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)
