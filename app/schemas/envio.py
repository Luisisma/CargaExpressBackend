from datetime import datetime, date, timezone
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_serializer


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

    @field_serializer("creado_en", when_used="json")
    def serializar_creado_en(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


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

    @field_serializer("creado_en", when_used="json")
    def serializar_creado_en(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


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

    @field_serializer("creado_en", "actualizado_en", when_used="json")
    def serializar_fechas(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class RecepcionEnvioRequest(BaseModel):
    peso_real_kg: float = Field(..., gt=0)
    largo_real_cm: float = Field(..., gt=0)
    ancho_real_cm: float = Field(..., gt=0)
    alto_real_cm: float = Field(..., gt=0)
    observaciones: Optional[str] = Field(None, max_length=200, description="Observaciones sobre el estado del bulto al recibirlo")
    forma_pago: Optional[str] = Field("efectivo", description="Medio de pago en ventanilla: efectivo, yape, plin, tarjeta")


class DespachoArriboRequest(BaseModel):
    notas: Optional[str] = Field(None, max_length=200, description="Notas del chofer o almacenero")


class EntregaEnvioRequest(BaseModel):
    dni_receptor: str = Field(..., min_length=8, max_length=15, description="DNI o documento de quien recibe físicamente")
    nombre_receptor: str = Field(..., min_length=2, max_length=200, description="Nombres completos de quien recibe")
    parentesco_o_relacion: Optional[str] = Field("Titular", max_length=50, description="Titular, Familiar, Apoderado con Carta Poder")
    observaciones: Optional[str] = Field(None, max_length=250, description="Observaciones finales de la entrega")


class DeclararSiniestroRequest(BaseModel):
    tipo_siniestro: str = Field(..., min_length=3, max_length=50, description="Tipo: robo_asalto, accidente_transito, extravio, dano_severo")
    numero_denuncia_policial: Optional[str] = Field(None, max_length=60, description="N° de Denuncia PNP o Parte Oficial")
    responsable_reporte: Optional[str] = Field(None, max_length=150, description="Nombre del colaborador o chofer que reporta el hecho")
    descripcion: str = Field(..., min_length=10, max_length=500, description="Detalle circunstanciado del hecho y ubicación")


class IniciarRepartoRequest(BaseModel):
    courier_id: Optional[int] = Field(None, description="ID del colaborador courier asignado. Opcional si el propio courier inicia ruta.")
    notas: Optional[str] = Field(None, max_length=200, description="Observaciones de salida a ruta (unidad, placa, etc.)")


class EntregaCourierRequest(BaseModel):
    dni_receptor: str = Field(..., min_length=6, max_length=15, description="DNI o documento del receptor")
    nombre_receptor: str = Field(..., min_length=2, max_length=200, description="Nombres completos del receptor en domicilio")
    parentesco_o_relacion: Optional[str] = Field("Titular", max_length=50, description="Titular, Familiar, Conserje, Vigilancia")
    observaciones: Optional[str] = Field(None, max_length=250, description="Detalle del lugar de entrega o incidencias")
    firma_base64: Optional[str] = Field(None, max_length=2000000, description="Firma digitalizada en canvas (Base64)")
    foto_evidencia_base64: Optional[str] = Field(None, max_length=4000000, description="Foto capturada en puerta (Base64)")
    cobro_contraentrega_confirmado: bool = Field(False, description="Confirmación de cobro en puerta para pagos pendientes")


class CourierEntregaItem(BaseModel):
    id: int
    codigo_tracking: str
    destinatario: str
    telefono: Optional[str] = None
    direccion_entrega: Optional[str] = None
    agencia_destino: str
    tipo_envio: str
    tipo_paquete: str
    peso_kg: float
    estado: str
    estado_pago: str
    precio_envio: float
    courier_id: Optional[int] = None
    courier_nombre: Optional[str] = None
    imagen_evidencia: Optional[str] = None
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("creado_en", when_used="json")
    def serializar_creado_en(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


