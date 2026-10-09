import hmac
import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.envio import Envio, HistorialEnvio
from app.schemas.pago import WebhookPagoRequest

class PagoService:
    @staticmethod
    def validar_firma_hmac(payload_bytes: bytes, signature_header: str) -> bool:
        if not signature_header:
            return False
            
        secret_bytes = settings.WEBHOOK_SECRET_KEY.encode('utf-8')
        expected_signature = hmac.new(
            secret_bytes, 
            payload_bytes, 
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature_header)

    @staticmethod
    def procesar_webhook(db: Session, request_data: WebhookPagoRequest) -> dict:
        if request_data.estado.upper() != "COMPLETED":
            return {"success": True, "message": "Ignorado (estado distinto a COMPLETED)", "transaction_id": request_data.transaction_id}
            
        # Buscar el envío
        envio = db.execute(
            select(Envio).where(Envio.codigo_tracking == request_data.codigo_tracking)
        ).scalar_one_or_none()
        
        if not envio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Envío {request_data.codigo_tracking} no encontrado."
            )
            
        # Validación de Idempotencia u orden ya pagada
        if envio.estado_pago == "pagado":
            return {"success": True, "message": "El envío ya se encuentra pagado. Idempotencia aplicada.", "transaction_id": request_data.transaction_id}
            
        # Actualizar envío
        envio.estado_pago = "pagado"
        envio.forma_pago = request_data.metodo_pago.lower()
        envio.actualizado_en = datetime.now(timezone.utc)
        
        # Guardar en historial
        historial = HistorialEnvio(
            envio_id=envio.id,
            estado="pagado",
            descripcion=f"Pago recibido por {request_data.metodo_pago}. Transacción: {request_data.transaction_id}"
        )
        db.add(historial)
        
        # Se requiere enviar correo aquí según SDD (Notificación 2)
        # TODO: Integrar email_service
        
        db.commit()
        
        return {
            "success": True, 
            "message": "Pago registrado exitosamente y estado actualizado.", 
            "transaction_id": request_data.transaction_id
        }
