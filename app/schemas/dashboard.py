from datetime import datetime
from typing import List, Optional, Dict
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


class DistribucionPagoItem(BaseModel):
    medio: str
    cantidad: int
    monto: float
    porcentaje: float


class TopRutaItem(BaseModel):
    ruta: str
    total_envios: int
    ingresos: float


class DepartamentoDemandaItem(BaseModel):
    departamento: str
    total_envios: int
    ingresos: float


class ModalidadEnvioItem(BaseModel):
    modalidad: str
    nombre: str
    total_envios: int
    porcentaje: float


class TipoPaqueteItem(BaseModel):
    tipo: str
    total_envios: int
    porcentaje: float


class AdminStats(BaseModel):
    recaudacion_total: float
    recaudacion_hoy: float
    envios_totales: int
    envios_hoy: int
    pendientes_pago: int
    ticket_promedio: float
    distribucion_pagos: List[DistribucionPagoItem]
    estados_embudo: Dict[str, int]
    top_rutas: List[TopRutaItem]
    departamentos_demanda: Optional[List[DepartamentoDemandaItem]] = []
    modalidades_envio: Optional[List[ModalidadEnvioItem]] = []
    tipos_paquete: Optional[List[TipoPaqueteItem]] = []
    total_siniestrados: Optional[int] = 0
    tasa_siniestros: Optional[float] = 0.0
    monto_siniestrado: Optional[float] = 0.0
    total_cancelados: Optional[int] = 0
    tasa_cancelados: Optional[float] = 0.0
    monto_cancelado: Optional[float] = 0.0
    codigos_siniestrados: Optional[List[str]] = []


class CajeroStats(BaseModel):
    recaudacion_sede_hoy: float
    paquetes_admitidos_hoy: int
    pendientes_cobro_sede: int
    entregas_ventanilla_hoy: int
    desglose_pagos_sede: List[DistribucionPagoItem]


class AlmacenStats(BaseModel):
    pendientes_despacho: int
    en_transito_carretera: int
    en_bodega_destino: int
    kilos_movilizados_hoy: float


class TendenciaDiariaItem(BaseModel):
    fecha: str
    dia_label: str
    total_envios: int
    ingresos: float


class DashboardTendenciasResponse(BaseModel):
    dias: int
    fecha_inicio: str
    fecha_fin: str
    datos: List[TendenciaDiariaItem]


class DashboardResumenResponse(BaseModel):
    rol: str
    stats: DashboardStats
    stats_admin: Optional[AdminStats] = None
    stats_cajero: Optional[CajeroStats] = None
    stats_almacen: Optional[AlmacenStats] = None
    ultimos_envios: List[UltimoEnvioItem]
    fecha_hoy: str

