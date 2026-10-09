from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class UltimoEnvioItem(BaseModel):
    id: int
    codigo_tracking: str
    remitente: str
    destino: str
    estado: str
    estado_pago: str
    precio_envio: float
    fecha: str

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    envios_total: int
    envios_hoy: int
    ingresos_hoy: float
    pendientes_pago: int


class DashboardResumenResponse(BaseModel):
    stats: DashboardStats
    ultimos_envios: List[UltimoEnvioItem]
    fecha_hoy: str
