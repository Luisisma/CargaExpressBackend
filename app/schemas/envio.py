from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class EnvioListItem(BaseModel):
    id: int
    codigo_tracking: str
    origen: str
    destino: str
    remitente: str
    destinatario: str
    total: float
    estado: str
    estado_pago: str
    tipo_envio: str
    tipo_paquete: str
    peso_kg: float
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class ClienteDetalle(BaseModel):
    id: int
    tipo_documento: str
    numero_documento: str
    nombre_completo: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None


class AgenciaDetalle(BaseModel):
    id: int
    codigo_agencia: int
    nombre: str
    departamento: str
    provincia: str
    distrito: str
    direccion: str


class HistorialDetalle(BaseModel):
    id: int
    estado: str
    descripcion: Optional[str] = None
    ubicacion: Optional[str] = None
    creado_en: datetime


class EnvioDetalleResponse(BaseModel):
    id: int
    codigo_tracking: str
    tipo_envio: str
    tipo_paquete: str
    peso_kg: float
    peso_volumetrico: Optional[float] = None
    alto_cm: Optional[float] = None
    ancho_cm: Optional[float] = None
    largo_cm: Optional[float] = None
    descripcion: Optional[str] = None
    direccion_recojo: Optional[str] = None
    direccion_entrega: Optional[str] = None
    
    monto_subtotal: float
    monto_igv: float
    precio_envio: float
    forma_pago: str
    estado_pago: str
    lugar_pago: str
    estado: str
    
    tipo_documento: str
    numero_documento: Optional[str] = None
    serie_documento: Optional[str] = None
    
    remitente: ClienteDetalle
    destinatario: ClienteDetalle
    agencia_origen: AgenciaDetalle
    agencia_destino: AgenciaDetalle
    historial: List[HistorialDetalle]
    
    creado_en: datetime
    actualizado_en: datetime


class RecepcionEnvioRequest(BaseModel):
    peso_real_kg: float = Field(..., gt=0)
    largo_real_cm: float = Field(..., gt=0)
    ancho_real_cm: float = Field(..., gt=0)
    alto_real_cm: float = Field(..., gt=0)
    observaciones: Optional[str] = Field(None, max_length=200, description="Observaciones sobre el estado del bulto al recibirlo")


class DespachoArriboRequest(BaseModel):
    notas: Optional[str] = Field(None, max_length=200, description="Notas del chofer o almacenero")


class EntregaEnvioRequest(BaseModel):
    dni_receptor: str = Field(..., min_length=8, max_length=15, description="DNI o documento de quien recibe físicamente")
    nombre_receptor: str = Field(..., min_length=2, max_length=200, description="Nombres completos de quien recibe")
    parentesco_o_relacion: Optional[str] = Field("Titular", max_length=50, description="Titular, Familiar, Apoderado con Carta Poder")
    observaciones: Optional[str] = Field(None, max_length=250, description="Observaciones finales de la entrega")

