from datetime import datetime, date
from typing import Optional, List, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AgenciaPublicaResponse(BaseModel):
    id: int
    codigo_agencia: int
    nombre: str
    departamento: str
    provincia: str
    distrito: str
    direccion: str
    telefono: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class CotizacionRequest(BaseModel):
    agencia_origen_id: int = Field(..., gt=0, description="ID de la agencia origen")
    agencia_destino_id: int = Field(..., gt=0, description="ID de la agencia destino")
    tipo_envio: Literal["agencia_agencia", "agencia_domicilio", "domicilio_agencia", "domicilio_domicilio"] = Field(
        ..., description="Modalidad de entrega"
    )
    peso_kg: float = Field(..., gt=0, le=1000, description="Peso físico en kilogramos")
    largo_cm: float = Field(..., gt=0, le=300, description="Largo del bulto en cm")
    ancho_cm: float = Field(..., gt=0, le=300, description="Ancho del bulto en cm")
    alto_cm: float = Field(..., gt=0, le=300, description="Alto del bulto en cm")

    model_config = ConfigDict(extra="forbid")


class CotizacionResponse(BaseModel):
    peso_fisico: float
    peso_volumetrico: float
    peso_liquidable: float
    tarifa_base: float
    tarifa_peso_adicional: float
    recargo_domicilio: float
    recargo_recojo: float = 0.0
    precio_total: float


class TrackingHitoResponse(BaseModel):
    estado: str
    descripcion: Optional[str] = None
    ubicacion: Optional[str] = None
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)


class TrackingPublicoResponse(BaseModel):
    codigo_tracking: str
    estado: str
    tipo_envio: str
    tipo_paquete: str
    remitente: str          # PII enmascarada (Ej: J*** P****)
    destinatario: str       # PII enmascarada (Ej: M**** G****)
    origen: str
    destino: str
    fecha_estimada: Optional[date] = None
    estado_pago: str
    precio_total: float
    creado_en: datetime
    historial: List[TrackingHitoResponse]


class ClientePublicoResponse(BaseModel):
    encontrado: bool
    fuente: Optional[str] = None  # "local", "reniec", "sunat", "manual"
    tipo_documento: Optional[str] = None
    numero_documento: Optional[str] = None
    nombre_completo: Optional[str] = None
    tipo_cliente: Optional[str] = None
    telefono_enmascarado: Optional[str] = None
    email_enmascarado: Optional[str] = None
    mensaje: Optional[str] = None


class RegistroPedidoPublicoRequest(BaseModel):
    # Remitente
    rem_tipo_doc: Literal["dni", "ruc", "ce", "pas"]
    rem_num_doc: str = Field(..., min_length=8, max_length=11)
    rem_nombre: str = Field(..., min_length=2, max_length=200)
    rem_email: str = Field(..., max_length=150, pattern=r"^\S+@\S+\.\S+$")
    rem_telefono: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")

    # Destinatario
    dest_tipo_doc: Literal["dni", "ruc", "ce", "pas"]
    dest_num_doc: str = Field(..., min_length=8, max_length=11)
    dest_nombre: str = Field(..., min_length=2, max_length=200)
    dest_email: str = Field(..., max_length=150, pattern=r"^\S+@\S+\.\S+$")
    dest_telefono: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")

    # Envío
    agencia_origen_id: int = Field(..., gt=0)
    agencia_destino_id: int = Field(..., gt=0)
    tipo_envio: Literal["agencia_agencia", "agencia_domicilio", "domicilio_agencia", "domicilio_domicilio"]
    tipo_paquete: Literal["caja", "sobre", "paquete", "saco"]
    peso_kg: float = Field(..., gt=0, le=500)
    largo_cm: Optional[float] = Field(default=20.0, gt=0, le=300)
    ancho_cm: Optional[float] = Field(default=20.0, gt=0, le=300)
    alto_cm: Optional[float] = Field(default=20.0, gt=0, le=300)
    descripcion: Optional[str] = Field(default="Encomienda general", max_length=500)
    direccion_recojo: Optional[str] = Field(None, max_length=300)
    direccion_entrega: Optional[str] = Field(None, max_length=300)

    model_config = ConfigDict(extra="forbid")

    @field_validator("rem_num_doc", "dest_num_doc")
    @classmethod
    def validar_documento(cls, v: str) -> str:
        v_limpio = v.strip()
        if not v_limpio.isalnum():
            raise ValueError("El documento debe ser alfanumérico.")
        return v_limpio


class PedidoCreadoResponse(BaseModel):
    codigo_tracking: str
    precio_estimado: float
    monto_subtotal: float
    monto_igv: float
    estado: str
    mensaje: str


class CancelarPedidoRequest(BaseModel):
    numero_documento_remitente: str = Field(..., description="Documento del remitente para validar propiedad")
    motivo: str = Field(default="Cancelación solicitada por el cliente antes del pago", max_length=200)

class CancelarPedidoResponse(BaseModel):
    codigo_tracking: str
    estado: str
    mensaje: str
