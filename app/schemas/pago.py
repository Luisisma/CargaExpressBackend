from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class WebhookPagoRequest(BaseModel):
    transaction_id: str = Field(..., description="ID único de transacción (idempotencia)")
    codigo_tracking: str = Field(..., description="Código de seguimiento de la encomienda (e.g. CE-2026-00001)")
    monto_pagado: Decimal = Field(..., description="Monto cobrado en la pasarela")
    moneda: str = Field("PEN", description="Moneda de la transacción")
    metodo_pago: str = Field(..., description="YAPE, PLIN, TARJETA_POS, EFECTIVO")
    estado: str = Field(..., description="Estado de la transacción (COMPLETED, FAILED)")
    
class WebhookPagoResponse(BaseModel):
    success: bool
    message: str
    transaction_id: str
