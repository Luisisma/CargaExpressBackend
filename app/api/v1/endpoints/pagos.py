from fastapi import APIRouter, Depends, Header, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.pago import WebhookPagoRequest, WebhookPagoResponse
from app.services.pago_service import PagoService

router = APIRouter()

@router.post(
    "/webhook-simulado",
    response_model=WebhookPagoResponse,
    summary="Webhook para simulación de pagos (Yape/Tarjetas)",
    description="Endpoint consumido por el pasarela de pagos para confirmar que una transacción ha sido exitosa."
)
async def webhook_simulado(
    request: Request,
    payload: WebhookPagoRequest,
    x_webhook_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    # Obtener el cuerpo de la petición crudo para verificar la firma HMAC
    body_bytes = await request.body()
    
    if not PagoService.validar_firma_hmac(body_bytes, x_webhook_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma HMAC-SHA256 inválida o ausente."
        )
        
    resultado = PagoService.procesar_webhook(db, payload)
    
    return WebhookPagoResponse(**resultado)
