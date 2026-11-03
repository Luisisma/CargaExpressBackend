from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class MovimientoCajaItem(BaseModel):
    id: int
    hora: str
    codigo_tracking: str
    remitente: str
    tipo_documento: str
    forma_pago: str
    monto: float
    cajero: str
    estado: str


class ResumenCajaResponse(BaseModel):
    agencia_id: int
    agencia_nombre: str
    cajero_nombre: str
    cajero_rol: str
    saldo_inicial: float
    efectivo_cobrado: float
    digital_cobrado: float
    tarjeta_cobrado: float
    total_recaudado: float
    efectivo_esperado_cajon: float
    total_transacciones: int
    estado_turno: str = "abierto"
    apertura_hora: str = "08:00 AM"
    movimientos: List[MovimientoCajaItem] = []


class ArqueoCajaRequest(BaseModel):
    efectivo_contado: float = Field(..., ge=0, description="Monto en efectivo físico contado en el cajón")
    digital_verificado: Optional[float] = Field(None, ge=0, description="Monto en billeteras digitales validado")
    observaciones: Optional[str] = Field(None, max_length=500)


class ArqueoCajaResponse(BaseModel):
    cuadre: str  # "cuadrado", "sobrante", "faltante"
    efectivo_esperado: float
    efectivo_contado: float
    diferencia: float
    digital_esperado: float
    digital_verificado: float
    mensaje: str
    fecha_cierre: str


class GestionSobrepagoRequest(BaseModel):
    codigo_tracking: str = Field(..., min_length=5, max_length=30, description="Código de la encomienda")
    numero_operacion: str = Field(..., min_length=4, max_length=30, description="N° de operación bancaria/Yape")
    monto_real_flete: float = Field(..., gt=0, description="Monto oficial del flete según balanza")
    monto_transferido: float = Field(..., gt=0, description="Monto transferido por el cliente")
    tipo_resolucion: str = Field(..., description="Opciones: 'vuelto_efectivo', 're_yapeo_digital', 'saldo_a_favor'")
    cuenta_o_telefono_destino: Optional[str] = Field(None, max_length=50, description="Teléfono/cuenta del titular para re-yapeo")
    observaciones: Optional[str] = Field(None, max_length=300)


class GestionSobrepagoResponse(BaseModel):
    codigo_tracking: str
    diferencia_exceso: float
    tipo_resolucion: str
    estado: str
    mensaje: str
    codigo_autorizacion: str
    fecha_registro: str

